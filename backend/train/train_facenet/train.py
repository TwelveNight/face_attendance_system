"""
FaceNet人脸识别训练脚本
使用facenet-pytorch提取人脸特征,训练SVM分类器
"""
import cv2  # 先导入cv2避免DLL问题
import numpy as np
import pickle
import sys
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import torch
from facenet_pytorch import InceptionResnetV1
import mediapipe as mp
from config import config
from train.common import YOLOFaceDetector, load_dataset_by_class
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FaceNetTrainer:
    """FaceNet人脸识别训练器"""
    
    def __init__(
        self,
        dataset_dir: str = "dataset",
        yolo_model_path: str = None,
        device: str = None
    ):
        """
        初始化训练器
        
        Args:
            dataset_dir: 数据集目录
            yolo_model_path: YOLO模型路径
            device: 设备
        """
        self.dataset_dir = Path(dataset_dir)
        
        # 设置设备
        if device is None:
            self.device = config.get_device()
        else:
            self.device = torch.device(device)
        
        logger.info(f"使用设备: {self.device}")
        
        # 初始化YOLO检测器
        if yolo_model_path is None:
            yolo_model_path = str(config.YOLO_MODEL)
        
        self.detector = YOLOFaceDetector(
            model_path=yolo_model_path,
            confidence_threshold=config.YOLO_CONFIDENCE_THRESHOLD
        )
        
        # 初始化MediaPipe人脸关键点检测(用于对齐)
        logger.info("加载MediaPipe人脸对齐模型...")
        self.mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        logger.info("✓ MediaPipe模型已加载")
        
        # 初始化FaceNet模型(使用预训练权重)
        logger.info("加载FaceNet模型...")
        self.facenet = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)
        logger.info("✓ FaceNet模型已加载")
        
        self.X = []  # 特征向量
        self.y = []  # 标签
        self.label_encoder = LabelEncoder()
        self.svm_model = None
    
    def align_face(self, face_image: np.ndarray) -> np.ndarray:
        """
        使用MediaPipe进行人脸对齐
        
        Args:
            face_image: BGR格式人脸图像
        
        Returns:
            对齐后的人脸图像
        """
        try:
            # 转RGB
            face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            
            # 检测关键点
            results = self.mp_face_mesh.process(face_rgb)
            
            if not results.multi_face_landmarks:
                return face_image  # 未检测到关键点,返回原图
            
            # 获取关键点
            landmarks = results.multi_face_landmarks[0]
            h, w = face_image.shape[:2]
            
            # 提取眼睛关键点(用于对齐)
            # 左眼: 33, 右眼: 263
            left_eye = landmarks.landmark[33]
            right_eye = landmarks.landmark[263]
            
            # 计算眼睛中心点
            left_eye_pt = np.array([left_eye.x * w, left_eye.y * h])
            right_eye_pt = np.array([right_eye.x * w, right_eye.y * h])
            
            # 计算旋转角度
            dY = right_eye_pt[1] - left_eye_pt[1]
            dX = right_eye_pt[0] - left_eye_pt[0]
            angle = np.degrees(np.arctan2(dY, dX))
            
            # 计算眼睛中心
            eyes_center = ((left_eye_pt[0] + right_eye_pt[0]) / 2,
                          (left_eye_pt[1] + right_eye_pt[1]) / 2)
            
            # 获取旋转矩阵
            M = cv2.getRotationMatrix2D(eyes_center, angle, 1.0)
            
            # 旋转图像
            aligned = cv2.warpAffine(face_image, M, (w, h),
                                    flags=cv2.INTER_CUBIC,
                                    borderMode=cv2.BORDER_REPLICATE)
            
            return aligned
            
        except Exception as e:
            logger.debug(f"人脸对齐失败: {e}, 使用原图")
            return face_image
    
    def extract_face_embedding(self, face_image: np.ndarray, use_alignment: bool = True) -> np.ndarray:
        """
        提取人脸嵌入向量
        
        Args:
            face_image: BGR格式人脸图像
            use_alignment: 是否使用MediaPipe对齐
        
        Returns:
            512维嵌入向量
        """
        # 1. 人脸对齐
        if use_alignment:
            face_image = self.align_face(face_image)
        
        # 2. BGR to RGB
        face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        
        # 3. 调整大小到160x160
        face_resized = cv2.resize(face_rgb, config.FACE_SIZE)
        
        # 4. 转换为tensor并归一化
        face_tensor = torch.from_numpy(face_resized).float()
        face_tensor = face_tensor.permute(2, 0, 1)  # HWC -> CHW
        face_tensor = (face_tensor - 127.5) / 128.0  # 归一化到[-1, 1]
        face_tensor = face_tensor.unsqueeze(0).to(self.device)  # 添加batch维度
        
        # 5. 提取特征
        with torch.no_grad():
            embedding = self.facenet(face_tensor)
        
        # 6. 转换为numpy
        embedding = embedding.cpu().numpy().flatten()
        
        return embedding
    
    def augment_face(self, face_image: np.ndarray) -> list:
        """
        数据增强:生成轻微变换的人脸图像
        
        Args:
            face_image: 原始人脸图像
        
        Returns:
            增强后的人脸图像列表
        """
        augmented = [face_image]  # 包含原图
        
        h, w = face_image.shape[:2]
        
        # 轻微旋转 (-5, +5度)
        for angle in [-5, 5]:
            M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
            rotated = cv2.warpAffine(face_image, M, (w, h))
            augmented.append(rotated)
        
        # 亮度调整
        hsv = cv2.cvtColor(face_image, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 2] = hsv[:, :, 2] * 1.1  # 增亮10%
        hsv[:, :, 2] = np.clip(hsv[:, :, 2], 0, 255)
        brightened = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        augmented.append(brightened)
        
        hsv[:, :, 2] = hsv[:, :, 2] * 0.9  # 降暗10%
        darkened = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        augmented.append(darkened)
        
        return augmented
    
    def load_and_process_dataset(self):
        """加载并处理数据集"""
        logger.info("=" * 60)
        logger.info("加载数据集...")
        logger.info("=" * 60)
        
        if not self.dataset_dir.exists():
            logger.error(f"数据集目录不存在: {self.dataset_dir}")
            return False
        
        # 获取所有用户文件夹
        user_dirs = [d for d in self.dataset_dir.iterdir() if d.is_dir()]
        
        if len(user_dirs) == 0:
            logger.error("未找到用户数据")
            return False
        
        logger.info(f"找到 {len(user_dirs)} 个用户")
        
        # 处理每个用户
        for user_dir in user_dirs:
            user_folder_name = user_dir.name
            
            # 🔧 关键修改：尝试将文件夹名转换为数字ID
            # 如果文件夹名是数字，使用数字ID（转为字符串）
            # 如果不是数字，使用文件夹名（字符串）
            try:
                user_id = int(user_folder_name)
                user_label = str(user_id)  # 统一转为字符串类型
                logger.info(f"\n处理用户: {user_folder_name} -> ID: {user_label} (数字ID)")
            except ValueError:
                user_label = user_folder_name
                logger.warning(f"\n处理用户: {user_folder_name} (字符串用户名 - 不推荐)")
                logger.warning(f"  ⚠️  建议使用数字作为文件夹名，例如: 1, 2, 3...")
            
            # 直接加载该用户目录下的所有图像
            from train.common.data_utils import load_face_images
            images = load_face_images(user_dir)
            
            if len(images) == 0:
                logger.warning(f"  ⚠ 用户 {user_label} 没有图像,跳过")
                continue
            
            # 提取每张图像的嵌入向量(带数据增强)
            embeddings = []
            for i, img in enumerate(images):
                try:
                    # 检测人脸
                    face = self.detector.detect_single_face(img)
                    
                    if face is None:
                        logger.warning(f"  ⚠ 图像 {i+1} 未检测到人脸,跳过")
                        continue
                    
                    # 数据增强(每张原图生成多个变体)
                    augmented_faces = self.augment_face(face)
                    
                    # 对每个增强样本提取特征(使用MTCNN对齐)
                    for aug_face in augmented_faces:
                        embedding = self.extract_face_embedding(aug_face, use_alignment=True)
                        embeddings.append(embedding)
                    
                except Exception as e:
                    logger.warning(f"  ⚠ 处理图像 {i+1} 失败: {e}")
            
            if len(embeddings) > 0:
                self.X.extend(embeddings)
                # 🔧 使用统一的字符串类型label
                self.y.extend([user_label] * len(embeddings))
                logger.info(f"  ✓ 成功处理 {len(embeddings)}/{len(images)} 张图像 (Label: '{user_label}')")
            else:
                logger.warning(f"  ⚠ 用户 {user_label} 没有有效图像")
        
        # 转换为numpy数组
        self.X = np.array(self.X)
        # 🔧 确保labels是object类型（字符串）
        self.y = np.array(self.y, dtype=object)
        
        logger.info("\n" + "=" * 60)
        logger.info(f"数据集加载完成:")
        logger.info(f"  - 总样本数: {len(self.X)}")
        logger.info(f"  - 用户数: {len(set(self.y))}")
        logger.info(f"  - 用户ID列表: {np.unique(self.y)}")
        logger.info(f"  - Labels类型: {self.y.dtype}")
        logger.info(f"  - 特征维度: {self.X.shape[1]}")
        logger.info("=" * 60)
        
        return len(self.X) > 0
    
    def train_svm(self, test_size: float = 0.2):
        """训练SVM分类器"""
        logger.info("\n开始训练SVM分类器...")
        
        # 编码标签
        y_encoded = self.label_encoder.fit_transform(self.y)
        
        # 分割数据集
        X_train, X_test, y_train, y_test = train_test_split(
            self.X,
            y_encoded,
            test_size=test_size,
            random_state=42,
            stratify=y_encoded
        )
        
        logger.info(f"训练集大小: {len(X_train)}")
        logger.info(f"测试集大小: {len(X_test)}")
        
        # 训练SVM
        logger.info("\n训练中...")
        self.svm_model = SVC(kernel='linear', probability=True, random_state=42)
        self.svm_model.fit(X_train, y_train)
        
        # 评估
        y_pred = self.svm_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        logger.info("\n" + "=" * 60)
        logger.info("训练完成!")
        logger.info(f"测试集准确率: {accuracy * 100:.2f}%")
        logger.info("=" * 60)
        
        # 详细报告
        logger.info("\n分类报告:")
        logger.info("\n" + classification_report(
            y_test,
            y_pred,
            target_names=self.label_encoder.classes_
        ))
        
        # 混淆矩阵
        logger.info("混淆矩阵:")
        cm = confusion_matrix(y_test, y_pred)
        logger.info(f"\n{cm}")
        
        return accuracy
    
    def save_model(self):
        """保存模型和嵌入数据"""
        logger.info("\n保存模型...")
        
        # 保存嵌入向量和标签
        embeddings_path = config.FACENET_EMBEDDINGS
        # 🔧 使用allow_pickle=True以支持object类型的labels
        np.savez_compressed(
            embeddings_path,
            embeddings=self.X,
            labels=self.y
        )
        logger.info(f"✓ 嵌入数据已保存: {embeddings_path}")
        logger.info(f"  - Labels类型: {self.y.dtype}")
        logger.info(f"  - 用户ID列表: {np.unique(self.y)}")
        
        # 🔧 关键修改：直接保存SVM模型对象，不使用字典
        # 这样与系统注册保存的格式一致
        svm_path = config.FACENET_SVM
        
        with open(svm_path, 'wb') as f:
            pickle.dump(self.svm_model, f)
        
        logger.info(f"✓ SVM模型已保存: {svm_path}")
        logger.info(f"  - 模型类型: {type(self.svm_model).__name__}")
        logger.info(f"  - 类别数: {len(self.svm_model.classes_)}")
        logger.info("\n所有模型文件已保存!")


def main():
    """主训练流程"""
    logger.info("=" * 60)
    logger.info("FaceNet 人脸识别训练")
    logger.info("=" * 60)
    
    # 初始化训练器
    trainer = FaceNetTrainer(dataset_dir="dataset")
    
    # 加载数据集
    if not trainer.load_and_process_dataset():
        logger.error("数据集加载失败")
        return
    
    # 训练SVM
    accuracy = trainer.train_svm(test_size=0.2)
    
    # 保存模型
    trainer.save_model()
    
    logger.info("\n" + "=" * 60)
    logger.info("训练流程完成!")
    logger.info(f"最终准确率: {accuracy * 100:.2f}%")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
