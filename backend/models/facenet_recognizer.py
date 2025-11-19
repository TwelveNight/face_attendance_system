"""
FaceNet人脸识别器封装
使用FaceNet提取特征并使用SVM进行识别
支持数据增强和质量检测以提高识别准确率
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
            # 🎯 步骤1：提取特征
            embedding = self.extract_embedding(face_image)
            
            # 🎯 步骤2：特征归一化（与训练时保持一致）
            embedding = embedding / np.linalg.norm(embedding)
            
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
            
            # 🎯 步骤1：SVM预测
            prediction = self.svm_model.predict([embedding])[0]
            print(f"  - SVM预测: {prediction}")
            
            # 🎯 步骤2：获取概率分布（比决策函数更可靠）
            probabilities = self.svm_model.predict_proba([embedding])[0]
            classes = self.svm_model.classes_
            
            # 找到预测类别的索引
            pred_idx = np.where(classes == prediction)[0][0]
            confidence = float(probabilities[pred_idx])
            
            print(f"\n📊 概率分布分析:")
            print(f"  - 预测类别: {prediction}")
            print(f"  - 预测概率: {confidence:.6f}")
            
            # 显示前3个最高概率
            top3_indices = np.argsort(probabilities)[-3:][::-1]
            print(f"\n  Top 3 候选:")
            for i, idx in enumerate(top3_indices, 1):
                print(f"    {i}. 用户 {classes[idx]}: {probabilities[idx]:.6f}")
            
            # 🎯 步骤3：二次验证 - 检查与次高分的差距
            sorted_probs = np.sort(probabilities)[::-1]
            if len(sorted_probs) >= 2:
                max_prob = sorted_probs[0]
                second_max_prob = sorted_probs[1]
                prob_gap = max_prob - second_max_prob
                
                print(f"\n🔍 二次验证:")
                print(f"  - 最高概率: {max_prob:.6f}")
                print(f"  - 次高概率: {second_max_prob:.6f}")
                print(f"  - 概率差距: {prob_gap:.6f}")
                
                # 如果差距太小，说明模型不确定
                min_gap = 0.15  # 至少15%的差距
                if prob_gap < min_gap:
                    print(f"  ⚠️  概率差距过小 ({prob_gap:.6f} < {min_gap})")
                    print(f"  ⚠️  模型无法明确区分，拒绝识别")
                    print(f"\n❌ 未通过二次验证")
                    print(f"{'='*60}\n")
                    return None, confidence
                else:
                    print(f"  ✓ 概率差距充足 ({prob_gap:.6f} >= {min_gap})")
            
            # 🎯 步骤4：阈值检查
            print(f"\n🎯 阈值检查:")
            print(f"  - 置信度: {confidence:.6f}")
            print(f"  - 阈值: {Config.FACE_RECOGNITION_THRESHOLD}")
            
            if confidence < Config.FACE_RECOGNITION_THRESHOLD:
                print(f"\n❌ 未通过阈值检查:")
                print(f"  - 置信度 {confidence:.6f} < 阈值 {Config.FACE_RECOGNITION_THRESHOLD}")
                print(f"{'='*60}\n")
                return None, confidence
            
            print(f"\n✅ 通过所有检查:")
            print(f"  - 置信度: {confidence:.6f} >= 阈值 {Config.FACE_RECOGNITION_THRESHOLD}")
            
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
    
    def check_face_quality(self, face_image: np.ndarray) -> Tuple[bool, str]:
        """
        检查人脸图像质量
        
        Args:
            face_image: 人脸图像
            
        Returns:
            (是否合格, 原因说明)
        """
        try:
            # 转换为灰度图
            if len(face_image.shape) == 3:
                gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = face_image
            
            # 1. 模糊检测（拉普拉斯方差）
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if laplacian_var < 100:
                return False, f"图像模糊 (清晰度: {laplacian_var:.1f})"
            
            # 2. 光照检测
            mean_brightness = np.mean(gray)
            if mean_brightness < 50:
                return False, f"光线过暗 (亮度: {mean_brightness:.1f})"
            if mean_brightness > 200:
                return False, f"光线过亮 (亮度: {mean_brightness:.1f})"
            
            # 3. 对比度检测
            std_contrast = np.std(gray)
            if std_contrast < 30:
                return False, f"对比度过低 (对比度: {std_contrast:.1f})"
            
            return True, f"质量良好 (清晰度: {laplacian_var:.1f}, 亮度: {mean_brightness:.1f})"
        
        except Exception as e:
            return False, f"质量检测失败: {str(e)}"
    
    def augment_face(self, face_image: np.ndarray) -> List[np.ndarray]:
        """
        数据增强：生成人脸图像的多个变体
        
        Args:
            face_image: 原始人脸图像
            
        Returns:
            增强后的人脸图像列表（包含原图）
        """
        augmented = [face_image.copy()]  # 包含原图
        
        h, w = face_image.shape[:2]
        
        # 1. 轻微旋转 (-5°, +5°)
        for angle in [-5, 5]:
            M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
            rotated = cv2.warpAffine(face_image, M, (w, h), 
                                    borderMode=cv2.BORDER_REPLICATE)
            augmented.append(rotated)
        
        # 2. 亮度调整
        # 增亮10%
        hsv = cv2.cvtColor(face_image, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.1, 0, 255)
        brightened = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        augmented.append(brightened)
        
        # 降暗10%
        hsv = cv2.cvtColor(face_image, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 0.9, 0, 255)
        darkened = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        augmented.append(darkened)
        
        # 3. 水平翻转（镜像）
        flipped = cv2.flip(face_image, 1)
        augmented.append(flipped)
        
        return augmented
    
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
        
        # 🎯 步骤1：质量检测
        print(f"\n🔍 步骤1：质量检测 ({len(face_images)} 张原始图像)")
        quality_passed = []
        quality_failed = []
        
        for idx, face_image in enumerate(face_images):
            is_good, reason = self.check_face_quality(face_image)
            if is_good:
                quality_passed.append(face_image)
                print(f"  ✓ 图像 {idx+1}: {reason}")
            else:
                quality_failed.append((idx+1, reason))
                print(f"  ✗ 图像 {idx+1}: {reason}")
        
        if len(quality_failed) > 0:
            print(f"\n⚠️  {len(quality_failed)} 张图像未通过质量检测")
        
        if len(quality_passed) == 0:
            raise ValueError("没有图像通过质量检测，请重新采集")
        
        print(f"✓ 通过质量检测: {len(quality_passed)}/{len(face_images)} 张")
        
        # 🎯 步骤2：数据增强
        print(f"\n🔄 步骤2：数据增强")
        print(f"  - 原始图像: {len(quality_passed)} 张")
        print(f"  - 增强策略: 旋转、亮度调整、翻转")
        
        all_augmented = []
        for idx, face_image in enumerate(quality_passed):
            augmented = self.augment_face(face_image)
            all_augmented.extend(augmented)
            if (idx + 1) % 5 == 0 or idx == len(quality_passed) - 1:
                print(f"  - 已增强 {idx + 1}/{len(quality_passed)} 张 (生成 {len(augmented)} 个变体)")
        
        print(f"✓ 增强后总样本数: {len(all_augmented)} 张")
        
        # 🎯 步骤3：提取特征
        print(f"\n🔄 步骤3：提取特征向量")
        new_embeddings = []
        for idx, face_image in enumerate(all_augmented):
            embedding = self.extract_embedding(face_image)
            new_embeddings.append(embedding)
            if (idx + 1) % 10 == 0 or idx == len(all_augmented) - 1:
                print(f"  - 已提取 {idx + 1}/{len(all_augmented)} 张")
        
        new_embeddings = np.array(new_embeddings)
        
        # 🎯 步骤4：L2归一化（提高区分度）
        print(f"\n🔄 步骤4：特征归一化")
        norms = np.linalg.norm(new_embeddings, axis=1, keepdims=True)
        new_embeddings = new_embeddings / norms
        print(f"✓ 特征已L2归一化")
        
        # 🔧 关键修复：统一转为字符串类型，避免类型混乱
        user_id_str = str(user_id)
        new_labels = np.array([user_id_str] * len(new_embeddings), dtype=object)
        
        print(f"\n📦 新用户数据:")
        print(f"  - 用户ID: {user_id} -> '{user_id_str}' (字符串)")
        print(f"  - 原始图像: {len(face_images)} 张")
        print(f"  - 质量合格: {len(quality_passed)} 张")
        print(f"  - 增强后: {len(all_augmented)} 张")
        print(f"  - 最终样本数: {len(new_embeddings)} 个")
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
        """
        训练SVM分类器
        使用RBF核以提高对相似用户的区分能力
        """
        from sklearn.svm import SVC
        
        # 检查类别数量
        unique_labels = np.unique(self.labels)
        n_classes = len(unique_labels)
        n_samples = len(self.embeddings)
        
        if n_classes < 2:
            print(f"⚠️  只有 {n_classes} 个用户，跳过SVM训练（需要至少2个用户）")
            self.svm_model = None
            return
        
        print(f"🔄 训练SVM分类器...")
        print(f"  - 用户数: {n_classes}")
        print(f"  - 样本数: {n_samples}")
        print(f"  - 每用户平均样本: {n_samples/n_classes:.1f}")
        
        # 🎯 使用RBF核替代线性核，提高非线性分类能力
        print(f"  - 核函数: RBF (径向基函数)")
        print(f"  - 正则化参数 C: 10.0")
        print(f"  - 核系数 gamma: scale")
        
        self.svm_model = SVC(
            kernel='rbf',              # RBF核，适合非线性分类
            C=10.0,                    # 正则化参数，控制分类边界的软硬程度
            gamma='scale',             # 核系数，自动根据特征数量调整
            probability=True,          # 启用概率估计
            class_weight='balanced'    # 自动平衡类别权重
        )
        
        self.svm_model.fit(self.embeddings, self.labels)
        print(f"✓ SVM训练完成")
        print(f"  - 支持向量数: {len(self.svm_model.support_)}")
        print(f"  - 支持向量占比: {len(self.svm_model.support_)/n_samples*100:.1f}%")
    
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
