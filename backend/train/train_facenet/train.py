"""
FaceNet人脸识别训练脚本
使用facenet-pytorch提取人脸特征,训练SVM分类器
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

import numpy as np
import pickle
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import torch
from facenet_pytorch import InceptionResnetV1
import cv2
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
        
        # 初始化FaceNet模型(使用预训练权重)
        logger.info("加载FaceNet模型...")
        self.facenet = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)
        logger.info("✓ FaceNet模型已加载")
        
        self.X = []  # 特征向量
        self.y = []  # 标签
        self.label_encoder = LabelEncoder()
        self.svm_model = None
    
    def extract_face_embedding(self, face_image: np.ndarray) -> np.ndarray:
        """
        提取人脸嵌入向量
        
        Args:
            face_image: BGR格式人脸图像
        
        Returns:
            512维嵌入向量
        """
        # 预处理
        # BGR to RGB
        face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        
        # 调整大小到160x160
        face_resized = cv2.resize(face_rgb, config.FACE_SIZE)
        
        # 转换为tensor并归一化
        face_tensor = torch.from_numpy(face_resized).float()
        face_tensor = face_tensor.permute(2, 0, 1)  # HWC -> CHW
        face_tensor = (face_tensor - 127.5) / 128.0  # 归一化到[-1, 1]
        face_tensor = face_tensor.unsqueeze(0).to(self.device)  # 添加batch维度
        
        # 提取特征
        with torch.no_grad():
            embedding = self.facenet(face_tensor)
        
        # 转换为numpy
        embedding = embedding.cpu().numpy().flatten()
        
        return embedding
    
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
            user_name = user_dir.name
            logger.info(f"\n处理用户: {user_name}")
            
            # 加载该用户的所有图像
            images, _ = load_dataset_by_class(user_dir.parent / user_name)
            
            if len(images) == 0:
                logger.warning(f"  ⚠ 用户 {user_name} 没有图像,跳过")
                continue
            
            # 提取每张图像的嵌入向量
            embeddings = []
            for i, img in enumerate(images):
                try:
                    # 检测人脸
                    face = self.detector.detect_single_face(img)
                    
                    if face is None:
                        logger.warning(f"  ⚠ 图像 {i+1} 未检测到人脸,跳过")
                        continue
                    
                    # 提取嵌入
                    embedding = self.extract_face_embedding(face)
                    embeddings.append(embedding)
                    
                except Exception as e:
                    logger.warning(f"  ⚠ 处理图像 {i+1} 失败: {e}")
            
            if len(embeddings) > 0:
                self.X.extend(embeddings)
                self.y.extend([user_name] * len(embeddings))
                logger.info(f"  ✓ 成功处理 {len(embeddings)}/{len(images)} 张图像")
            else:
                logger.warning(f"  ⚠ 用户 {user_name} 没有有效图像")
        
        # 转换为numpy数组
        self.X = np.array(self.X)
        self.y = np.array(self.y)
        
        logger.info("\n" + "=" * 60)
        logger.info(f"数据集加载完成:")
        logger.info(f"  - 总样本数: {len(self.X)}")
        logger.info(f"  - 用户数: {len(set(self.y))}")
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
        np.savez_compressed(
            embeddings_path,
            embeddings=self.X,
            labels=self.y
        )
        logger.info(f"✓ 嵌入数据已保存: {embeddings_path}")
        
        # 保存SVM模型和标签编码器
        svm_path = config.FACENET_SVM
        model_data = {
            'svm': self.svm_model,
            'label_encoder': self.label_encoder
        }
        
        with open(svm_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"✓ SVM模型已保存: {svm_path}")
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
