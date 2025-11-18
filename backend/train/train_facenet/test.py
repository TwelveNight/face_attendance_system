"""
FaceNet人脸识别测试脚本
实时测试训练好的FaceNet+SVM模型
"""
import numpy as np
import pickle
import torch
import cv2
import logging
import sys
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from facenet_pytorch import InceptionResnetV1
from config import config
from train.common import YOLOFaceDetector

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FaceRecognitionTester:
    """人脸识别测试器"""
    
    def __init__(
        self,
        embeddings_path: str = None,
        svm_path: str = None,
        yolo_path: str = None,
        device: str = None
    ):
        """初始化测试器"""
        # 设置路径
        if embeddings_path is None:
            embeddings_path = str(config.FACENET_EMBEDDINGS)
        if svm_path is None:
            svm_path = str(config.FACENET_SVM)
        if yolo_path is None:
            yolo_path = str(config.YOLO_MODEL)
        
        # 设置设备
        if device is None:
            self.device = config.get_device()
        else:
            self.device = torch.device(device)
        
        logger.info(f"使用设备: {self.device}")
        
        # 加载YOLO
        self.detector = YOLOFaceDetector(
            model_path=yolo_path,
            confidence_threshold=config.YOLO_CONFIDENCE_THRESHOLD
        )
        
        # 加载FaceNet
        logger.info("加载FaceNet模型...")
        self.facenet = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)
        logger.info("✓ FaceNet已加载")
        
        # 加载SVM模型
        logger.info(f"加载SVM模型: {svm_path}")
        with open(svm_path, 'rb') as f:
            model_data = pickle.load(f)
        
        # 🔧 修复：兼容新旧格式
        # 新格式：直接保存SVC对象
        # 旧格式：保存字典 {'svm': SVC, 'label_encoder': LabelEncoder}
        if isinstance(model_data, dict):
            # 旧格式
            self.svm = model_data['svm']
            self.label_encoder = model_data['label_encoder']
            logger.info(f"✓ SVM已加载 (旧格式),支持 {len(self.label_encoder.classes_)} 个用户")
        else:
            # 新格式：直接是SVC对象
            self.svm = model_data
            self.label_encoder = None  # 新格式不需要label_encoder
            logger.info(f"✓ SVM已加载 (新格式),支持 {len(self.svm.classes_)} 个用户")
        
        # 显示用户列表
        if self.label_encoder:
            logger.info(f"  用户列表: {list(self.label_encoder.classes_)}")
        else:
            logger.info(f"  用户列表: {list(self.svm.classes_)}")
    
    def extract_embedding(self, face_image: np.ndarray) -> np.ndarray:
        """提取人脸嵌入向量"""
        # BGR to RGB
        face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        face_resized = cv2.resize(face_rgb, config.FACE_SIZE)
        
        # 转换为tensor
        face_tensor = torch.from_numpy(face_resized).float()
        face_tensor = face_tensor.permute(2, 0, 1)
        face_tensor = (face_tensor - 127.5) / 128.0
        face_tensor = face_tensor.unsqueeze(0).to(self.device)
        
        # 提取特征
        with torch.no_grad():
            embedding = self.facenet(face_tensor)
        
        return embedding.cpu().numpy().flatten()
    
    def recognize_face(self, face_image: np.ndarray) -> tuple:
        """
        识别人脸
        
        Returns:
            (用户名/ID, 置信度)
        """
        # 提取嵌入
        embedding = self.extract_embedding(face_image)
        
        # SVM预测
        prediction = self.svm.predict([embedding])[0]
        probabilities = self.svm.predict_proba([embedding])[0]
        
        # 🔧 修复：兼容新旧格式
        if self.label_encoder:
            # 旧格式：使用label_encoder解码
            user_name = self.label_encoder.inverse_transform([prediction])[0]
            confidence = probabilities[prediction]
        else:
            # 新格式：prediction直接是用户ID（字符串）
            user_name = prediction
            # 获取对应类别的概率
            class_idx = list(self.svm.classes_).index(prediction)
            confidence = probabilities[class_idx]
        
        return user_name, confidence
    
    def test_realtime(self, camera_index: int = 0, confidence_threshold: float = 0.5):
        """实时测试"""
        logger.info("\n" + "=" * 60)
        logger.info("FaceNet 人脸识别实时测试")
        logger.info("=" * 60)
        logger.info("按 'q' 退出\n")
        
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            logger.error(f"无法打开摄像头 {camera_index}")
            return
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 检测人脸
            face = self.detector.detect_single_face(frame, margin=20)
            
            # 显示画面
            display_frame = frame.copy()
            
            if face is not None:
                # 识别
                try:
                    user_name, confidence = self.recognize_face(face)
                    
                    # 绘制结果
                    boxes = self.detector.detect_faces(frame)
                    if boxes:
                        x1, y1, x2, y2 = boxes[0]
                        
                        # 根据置信度选择颜色
                        if confidence >= confidence_threshold:
                            color = (0, 255, 0)  # 绿色 - 识别成功
                            text = f"{user_name} ({confidence:.2f})"
                        else:
                            color = (0, 165, 255)  # 橙色 - 置信度低
                            text = f"Unknown ({confidence:.2f})"
                        
                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(
                            display_frame,
                            text,
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            color,
                            2
                        )
                    
                except Exception as e:
                    logger.error(f"识别失败: {e}")
            else:
                # 未检测到人脸
                cv2.putText(
                    display_frame,
                    "No face detected",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )
            
            cv2.imshow('Face Recognition Test', display_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()


def main():
    """测试入口"""
    tester = FaceRecognitionTester()
    tester.test_realtime(confidence_threshold=0.6)


if __name__ == '__main__':
    main()
