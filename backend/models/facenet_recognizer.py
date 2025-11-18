"""
FaceNet人脸识别器封装
使用FaceNet提取特征并使用SVM进行识别
"""
import numpy as np
import cv2
import pickle
from typing import Optional, Tuple, List
from pathlib import Path
import torch
from facenet_pytorch import InceptionResnetV1
from PIL import Image

from config.settings import Config


class FaceNetRecognizer:
    """FaceNet人脸识别器"""
    
    def __init__(self, embeddings_path: Optional[str] = None, 
                 svm_path: Optional[str] = None):
        """
        初始化FaceNet识别器
        
        Args:
            embeddings_path: 人脸特征文件路径
            svm_path: SVM分类器路径
        """
        self.embeddings_path = embeddings_path or Config.FACENET_EMBEDDINGS
        self.svm_path = svm_path or Config.FACENET_SVM
        self.device = Config.get_device()
        
        # 模型和数据
        self.facenet_model = None
        self.svm_model = None
        self.embeddings = None
        self.labels = None
        self.label_to_id = {}
        self.id_to_label = {}
        
        # 加载模型
        self.load_models()
    
    def load_models(self):
        """加载FaceNet和SVM模型"""
        try:
            # 加载FaceNet模型
            print("加载FaceNet模型...")
            self.facenet_model = InceptionResnetV1(pretrained='vggface2').eval()
            self.facenet_model.to(self.device)
            print(f"✓ FaceNet模型加载成功 (设备: {self.device})")
            
            # 加载已保存的特征和SVM
            if Path(self.embeddings_path).exists() and Path(self.svm_path).exists():
                self.load_trained_data()
            else:
                print("⚠️  未找到训练数据,需要先训练模型")
        
        except Exception as e:
            print(f"✗ 模型加载失败: {e}")
            raise
    
    def load_trained_data(self):
        """加载训练好的数据"""
        try:
            # 加载特征（允许pickle以支持object类型的labels）
            data = np.load(self.embeddings_path, allow_pickle=True)
            self.embeddings = data['embeddings']
            self.labels = data['labels']
            
            # 创建标签映射
            unique_labels = np.unique(self.labels)
            self.label_to_id = {label: idx for idx, label in enumerate(unique_labels)}
            self.id_to_label = {idx: label for label, idx in self.label_to_id.items()}
            
            # 加载SVM
            with open(self.svm_path, 'rb') as f:
                self.svm_model = pickle.load(f)
            
            print(f"✓ 加载训练数据成功 (用户数: {len(unique_labels)})")
        
        except Exception as e:
            print(f"✗ 加载训练数据失败: {e}")
            raise
    
    def extract_embedding(self, face_image: np.ndarray) -> np.ndarray:
        """
        提取人脸特征
        
        Args:
            face_image: 人脸图像 (BGR格式)
            
        Returns:
            512维特征向量
        """
        if self.facenet_model is None:
            raise RuntimeError("FaceNet模型未加载")
        
        # 预处理
        face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        face_pil = Image.fromarray(face_rgb)
        face_resized = face_pil.resize(Config.FACE_SIZE)
        
        # 转换为tensor
        face_tensor = torch.from_numpy(np.array(face_resized)).float()
        face_tensor = face_tensor.permute(2, 0, 1)  # HWC -> CHW
        face_tensor = (face_tensor - 127.5) / 128.0  # 归一化到[-1, 1]
        face_tensor = face_tensor.unsqueeze(0).to(self.device)
        
        # 提取特征
        with torch.no_grad():
            embedding = self.facenet_model(face_tensor)
        
        return embedding.cpu().numpy().flatten()
    
    def recognize(self, face_image: np.ndarray) -> Tuple[Optional[int], float]:
        """
        识别人脸
        
        Args:
            face_image: 人脸图像
            
        Returns:
            (user_id, confidence) or (None, 0.0)
        """
        # 检查是否有训练数据
        if self.embeddings is None or self.labels is None:
            return None, 0.0
        
        try:
            # 提取特征
            embedding = self.extract_embedding(face_image)
            
            # 特殊情况：只有1个用户时，使用余弦相似度
            unique_labels = np.unique(self.labels)
            
            print(f"\n{'='*60}")
            print(f"🔍 [FaceNetRecognizer] 开始识别")
            print(f"{'='*60}")
            print(f"📊 模型状态:")
            print(f"  - 注册用户数: {len(unique_labels)}")
            print(f"  - 用户ID列表: {unique_labels}")
            print(f"  - 总样本数: {len(self.embeddings)}")
            
            if len(unique_labels) == 1:
                # 计算与所有已知特征的余弦相似度
                similarities = []
                for known_embedding in self.embeddings:
                    similarity = np.dot(embedding, known_embedding) / (
                        np.linalg.norm(embedding) * np.linalg.norm(known_embedding)
                    )
                    similarities.append(similarity)
                
                # 取最大相似度（范围 [-1, 1]）
                max_similarity = float(np.max(similarities))
                min_similarity = float(np.min(similarities))
                avg_similarity = float(np.mean(similarities))
                
                print(f"\n🎯 单用户模式 - 余弦相似度:")
                print(f"  - 最大相似度: {max_similarity:.6f}")
                print(f"  - 最小相似度: {min_similarity:.6f}")
                print(f"  - 平均相似度: {avg_similarity:.6f}")
                print(f"  - 样本数: {len(similarities)}")
                
                # 余弦相似度阈值（严格）
                # 对于单用户，要求至少 0.75 的余弦相似度（表示向量夹角 < 41度）
                # 这样可以有效防止未注册用户被误识别
                cosine_threshold = 0.75
                print(f"  - 阈值: {cosine_threshold}")
                
                if max_similarity < cosine_threshold:
                    # 未达到阈值，返回None
                    # 转换为 [0, 1] 范围用于显示
                    confidence = (max_similarity + 1) / 2
                    print(f"\n❌ 未通过阈值检查:")
                    print(f"  - 最大相似度 {max_similarity:.6f} < 阈值 {cosine_threshold}")
                    print(f"  - 转换后置信度: {confidence:.6f}")
                    print(f"{'='*60}\n")
                    return None, confidence
                
                # 通过阈值，返回用户ID和置信度
                confidence = (max_similarity + 1) / 2
                print(f"\n✅ 通过阈值检查:")
                print(f"  - 最大相似度 {max_similarity:.6f} >= 阈值 {cosine_threshold}")
                print(f"  - 转换后置信度: {confidence:.6f}")
                
                # 🔧 修复：尝试转换为整数，如果失败则返回字符串
                try:
                    user_id = int(unique_labels[0])
                    print(f"  - 识别用户ID: {user_id}")
                    print(f"{'='*60}\n")
                except (ValueError, TypeError):
                    # 如果是字符串类型的用户名，返回None（不是数字ID）
                    print(f"⚠️  单用户模式下的label不是数字ID: {unique_labels[0]}")
                    print(f"{'='*60}\n")
                    return None, confidence
                return user_id, confidence
            
            # 多用户情况：使用SVM
            print(f"\n🎯 多用户模式 - SVM分类:")
            
            if self.svm_model is None:
                print(f"❌ SVM模型未训练")
                print(f"{'='*60}\n")
                return None, 0.0
            
            # SVM预测
            prediction = self.svm_model.predict([embedding])[0]
            print(f"  - SVM预测: {prediction}")
            
            # 获取决策函数值(置信度)
            decision_values = self.svm_model.decision_function([embedding])
            print(f"  - 决策函数值: {decision_values}")
            
            # 计算置信度
            if len(decision_values.shape) > 1:
                # 多分类
                raw_confidence = float(np.max(decision_values))
                print(f"  - 多分类模式")
                print(f"  - 原始置信度: {raw_confidence:.6f}")
            else:
                # 二分类
                raw_confidence = float(abs(decision_values[0]))
                print(f"  - 二分类模式")
                print(f"  - 原始置信度: {raw_confidence:.6f}")
            
            # 归一化置信度到[0, 1]
            confidence = 1 / (1 + np.exp(-raw_confidence))
            print(f"  - 归一化置信度: {confidence:.6f}")
            print(f"  - 阈值: {Config.FACE_RECOGNITION_THRESHOLD}")
            
            # 检查阈值
            if confidence < Config.FACE_RECOGNITION_THRESHOLD:
                print(f"\n❌ 未通过阈值检查:")
                print(f"  - 置信度 {confidence:.6f} < 阈值 {Config.FACE_RECOGNITION_THRESHOLD}")
                print(f"{'='*60}\n")
                return None, confidence
            
            print(f"\n✅ 通过阈值检查:")
            print(f"  - 置信度 {confidence:.6f} >= 阈值 {Config.FACE_RECOGNITION_THRESHOLD}")
            
            # 🔧 修复：获取用户ID，尝试转换为整数
            try:
                user_id = int(prediction)
                print(f"  - 识别用户ID: {user_id}")
                print(f"{'='*60}\n")
            except (ValueError, TypeError):
                # 如果是字符串类型的用户名，返回None（不是数字ID）
                print(f"⚠️  SVM预测的label不是数字ID: {prediction}")
                print(f"{'='*60}\n")
                return None, confidence
            
            return user_id, confidence
        
        except Exception as e:
            print(f"识别失败: {e}")
            import traceback
            traceback.print_exc()
            return None, 0.0
    
    def recognize_batch(self, face_images: List[np.ndarray]) -> List[Tuple[Optional[int], float]]:
        """
        批量识别人脸
        
        Args:
            face_images: 人脸图像列表
            
        Returns:
            [(user_id, confidence), ...]
        """
        results = []
        for face_image in face_images:
            result = self.recognize(face_image)
            results.append(result)
        return results
    
    def add_user(self, user_id: int, face_images: List[np.ndarray]):
        """
        添加新用户
        
        Args:
            user_id: 用户ID
            face_images: 用户的人脸图像列表
        """
        print(f"\n{'='*60}")
        print(f"➕ [FaceNetRecognizer] 添加用户 {user_id}")
        print(f"{'='*60}")
        
        # 显示添加前的状态
        if self.embeddings is not None:
            unique_labels_before = np.unique(self.labels)
            print(f"\n📊 添加前状态:")
            print(f"  - 总样本数: {len(self.embeddings)}")
            print(f"  - 用户数: {len(unique_labels_before)}")
            print(f"  - 用户ID列表: {unique_labels_before}")
            print(f"  - Labels类型: {self.labels.dtype}")
            print(f"  - Labels示例: {self.labels[:3] if len(self.labels) > 0 else []}")
        else:
            print(f"\n📊 添加前状态: 空模型")
        
        # 提取所有人脸的特征
        print(f"\n🔄 提取 {len(face_images)} 张人脸的特征向量...")
        new_embeddings = []
        for idx, face_image in enumerate(face_images):
            embedding = self.extract_embedding(face_image)
            new_embeddings.append(embedding)
            if (idx + 1) % 5 == 0 or idx == len(face_images) - 1:
                print(f"  - 已提取 {idx + 1}/{len(face_images)} 张")
        
        new_embeddings = np.array(new_embeddings)
        # 🔧 关键修复：统一转为字符串类型，避免类型混乱
        user_id_str = str(user_id)
        new_labels = np.array([user_id_str] * len(new_embeddings), dtype=object)
        
        print(f"\n📦 新用户数据:")
        print(f"  - 用户ID: {user_id} -> '{user_id_str}' (字符串)")
        print(f"  - 样本数: {len(new_embeddings)}")
        print(f"  - Embedding维度: {new_embeddings.shape}")
        print(f"  - Labels类型: {new_labels.dtype}")
        
        # 合并到现有数据
        if self.embeddings is not None:
            print(f"\n🔄 合并到现有数据...")
            # 🔧 确保现有labels也是字符串类型
            if self.labels.dtype != object:
                print(f"  ⚠️  转换现有labels为字符串类型")
                self.labels = self.labels.astype(str)
            
            self.embeddings = np.vstack([self.embeddings, new_embeddings])
            self.labels = np.hstack([self.labels, new_labels])
        else:
            print(f"\n📦 创建新模型数据...")
            self.embeddings = new_embeddings
            self.labels = new_labels
        
        # 显示添加后的状态
        unique_labels_after = np.unique(self.labels)
        print(f"\n📊 添加后状态:")
        print(f"  - 总样本数: {len(self.embeddings)}")
        print(f"  - 用户数: {len(unique_labels_after)}")
        print(f"  - 用户ID列表: {unique_labels_after}")
        print(f"  - Labels类型: {self.labels.dtype}")
        
        # 重新训练SVM
        print(f"\n🔄 重新训练SVM...")
        self.train_svm()
        
        # 保存
        print(f"💾 保存模型数据...")
        self.save_trained_data()
        
        print(f"\n{'='*60}")
        print(f"✅ 用户 {user_id} 添加完成")
        print(f"{'='*60}\n")
    
    def train_svm(self):
        """训练SVM分类器"""
        from sklearn.svm import SVC
        
        # 检查类别数量
        unique_labels = np.unique(self.labels)
        n_classes = len(unique_labels)
        
        if n_classes < 2:
            print(f"⚠️  只有 {n_classes} 个用户，跳过SVM训练（需要至少2个用户）")
            self.svm_model = None
            return
        
        print(f"训练SVM分类器... ({n_classes} 个用户)")
        self.svm_model = SVC(kernel='linear', probability=True)
        self.svm_model.fit(self.embeddings, self.labels)
        print("✓ SVM训练完成")
    
    def save_trained_data(self):
        """保存训练数据"""
        # 保存特征
        np.savez(
            self.embeddings_path,
            embeddings=self.embeddings,
            labels=self.labels
        )
        
        # 保存SVM
        with open(self.svm_path, 'wb') as f:
            pickle.dump(self.svm_model, f)
        
        print(f"✓ 训练数据已保存")
    
    def remove_user(self, user_id: int):
        """
        删除用户
        
        Args:
            user_id: 用户ID
        """
        print(f"\n{'='*60}")
        print(f"🗑️  [FaceNetRecognizer] 开始删除用户 {user_id}")
        print(f"{'='*60}")
        
        if self.embeddings is None or self.labels is None:
            print("⚠️  没有训练数据，跳过删除")
            return
        
        # 显示删除前的状态
        unique_labels_before = np.unique(self.labels)
        print(f"\n📊 删除前状态:")
        print(f"  - 总样本数: {len(self.embeddings)}")
        print(f"  - 用户数: {len(unique_labels_before)}")
        print(f"  - 用户ID列表: {unique_labels_before}")
        
        # 统计要删除的用户的样本数
        # 注意：labels可能是字符串或整数，需要统一比较
        user_id_str = str(user_id)
        user_samples_int = np.sum(self.labels == user_id)
        user_samples_str = np.sum(self.labels == user_id_str)
        user_samples = user_samples_int + user_samples_str
        
        print(f"\n🎯 目标用户 {user_id}:")
        print(f"  - 样本数（整数匹配）: {user_samples_int}")
        print(f"  - 样本数（字符串匹配）: {user_samples_str}")
        print(f"  - 总样本数: {user_samples}")
        
        if user_samples == 0:
            print(f"⚠️  用户 {user_id} 没有样本，无需删除")
            return
        
        # 过滤掉该用户的数据（同时匹配整数和字符串）
        print(f"\n🔄 开始过滤数据...")
        mask = (self.labels != user_id) & (self.labels != user_id_str)
        self.embeddings = self.embeddings[mask]
        self.labels = self.labels[mask]
        
        # 显示删除后的状态
        unique_labels_after = np.unique(self.labels) if len(self.labels) > 0 else np.array([])
        print(f"\n📊 删除后状态:")
        print(f"  - 总样本数: {len(self.embeddings)}")
        print(f"  - 用户数: {len(unique_labels_after)}")
        print(f"  - 用户ID列表: {unique_labels_after}")
        print(f"  - 已删除样本数: {user_samples}")
        
        # 重新训练
        if len(self.embeddings) > 0:
            print(f"\n🔄 重新训练模型...")
            self.train_svm()
            print(f"💾 保存更新后的模型文件...")
            self.save_trained_data()
            print(f"✅ 模型已更新并保存")
        else:
            print("⚠️  所有用户已删除，清空模型")
            self.svm_model = None
        
        print(f"\n{'='*60}")
        print(f"✅ 用户 {user_id} 删除完成")
        print(f"{'='*60}\n")
    
    def get_user_count(self) -> int:
        """获取注册用户数量"""
        if self.labels is None:
            return 0
        return len(np.unique(self.labels))
    
    def __del__(self):
        """清理资源"""
        if self.facenet_model is not None:
            del self.facenet_model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


if __name__ == '__main__':
    # 测试代码
    recognizer = FaceNetRecognizer()
    
    print(f"注册用户数: {recognizer.get_user_count()}")
    
    # 测试识别
    cap = cv2.VideoCapture(0)
    from yolo_face_detector import YOLOFaceDetector
    detector = YOLOFaceDetector()
    
    print("按 'q' 退出")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 检测人脸
        faces = detector.detect_faces(frame, return_confidence=True)
        
        for face in faces:
            x1, y1, x2, y2 = face[:4]
            
            # 裁剪人脸
            face_img = detector.crop_face(frame, face)
            if face_img is not None:
                # 识别
                user_id, confidence = recognizer.recognize(face_img)
                
                # 绘制
                color = (0, 255, 0) if user_id is not None else (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                text = f"User {user_id} ({confidence:.2f})" if user_id else "Unknown"
                cv2.putText(frame, text, (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        cv2.imshow('Face Recognition', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
