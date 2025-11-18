"""
PyTorch情感识别测试脚本
实时测试训练好的模型
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import torch
import cv2
import numpy as np
from config import config
from train.common import YOLOFaceDetector
from train.train_emotion_pytorch.model import create_model
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmotionRecognitionTester:
    """情感识别测试器"""
    
    def __init__(
        self,
        model_path: str = None,
        yolo_path: str = None,
        class_names: list = None,
        device: str = None
    ):
        """初始化测试器"""
        # 设置设备
        if device is None:
            self.device = config.get_device()
        else:
            self.device = torch.device(device)
        
        logger.info(f"使用设备: {self.device}")
        
        # 类别名称
        if class_names is None:
            self.class_names = config.EMOTION_CLASSES
        else:
            self.class_names = class_names
        
        # 加载YOLO
        if yolo_path is None:
            yolo_path = str(config.YOLO_MODEL)
        
        self.detector = YOLOFaceDetector(yolo_path)
        
        # 加载情感识别模型
        if model_path is None:
            model_path = str(config.EMOTION_PYTORCH_MODEL)
        
        logger.info(f"加载模型: {model_path}")
        
        # 加载模型
        checkpoint = torch.load(model_path, map_location=self.device)
        num_classes = checkpoint.get('num_classes', len(self.class_names))
        
        self.model = create_model('standard', num_classes).to(self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        
        logger.info("✓ 模型已加载")
    
    def preprocess_face(self, face_image: np.ndarray) -> torch.Tensor:
        """预处理人脸图像"""
        # 转灰度
        if len(face_image.shape) == 3:
            face_gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        else:
            face_gray = face_image
        
        # 调整大小
        face_resized = cv2.resize(face_gray, config.EMOTION_IMAGE_SIZE)
        
        # 归一化
        face_normalized = face_resized.astype(np.float32) / 255.0
        
        # 转tensor
        face_tensor = torch.from_numpy(face_normalized).unsqueeze(0).unsqueeze(0)
        face_tensor = face_tensor.to(self.device)
        
        return face_tensor
    
    def predict_emotion(self, face_image: np.ndarray) -> tuple:
        """
        预测情感
        
        Returns:
            (emotion_name, confidence)
        """
        face_tensor = self.preprocess_face(face_image)
        
        with torch.no_grad():
            outputs = self.model(face_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            confidence, predicted = probabilities.max(1)
        
        emotion_idx = predicted.item()
        emotion_name = self.class_names[emotion_idx]
        confidence_value = confidence.item()
        
        return emotion_name, confidence_value
    
    def test_realtime(self, camera_index: int = 0):
        """实时测试"""
        logger.info("=" * 60)
        logger.info("PyTorch情感识别实时测试")
        logger.info("=" * 60)
        logger.info("按 'q' 退出\n")
        
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            logger.error(f"无法打开摄像头 {camera_index}")
            return
        
        # 情感对应颜色
        emotion_colors = {
            'happy': (0, 255, 0),      # 绿色
            'sad': (255, 0, 0),        # 蓝色
            'surprised': (0, 255, 255) # 黄色
        }
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 检测人脸
            face = self.detector.detect_single_face(frame, margin=config.FACE_MARGIN)
            
            display_frame = frame.copy()
            
            if face is not None:
                try:
                    # 预测情感
                    emotion, confidence = self.predict_emotion(face)
                    
                    # 绘制结果
                    boxes = self.detector.detect_faces(frame)
                    if boxes:
                        x1, y1, x2, y2 = boxes[0]
                        
                        # 选择颜色
                        color = emotion_colors.get(emotion, (255, 255, 255))
                        
                        # 绘制边框
                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                        
                        # 绘制情感标签
                        text = f"{emotion} ({confidence:.2f})"
                        cv2.putText(
                            display_frame,
                            text,
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            color,
                            2
                        )
                        
                        # 绘制情感图标区域
                        cv2.putText(
                            display_frame,
                            f"Emotion: {emotion}",
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1.0,
                            color,
                            2
                        )
                
                except Exception as e:
                    logger.error(f"识别失败: {e}")
            else:
                cv2.putText(
                    display_frame,
                    "No face detected",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )
            
            cv2.imshow('Emotion Recognition Test', display_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
    
    def test_on_image(self, image_path: str, output_path: str = None):
        """测试单张图像"""
        # 读取图像
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"无法读取图像: {image_path}")
            return
        
        # 检测人脸
        face = self.detector.detect_single_face(image)
        
        if face is None:
            logger.warning("未检测到人脸")
            return
        
        # 预测情感
        emotion, confidence = self.predict_emotion(face)
        
        logger.info(f"预测结果: {emotion} (置信度: {confidence:.2f})")
        
        # 绘制结果
        boxes = self.detector.detect_faces(image)
        if boxes:
            x1, y1, x2, y2 = boxes[0]
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                image,
                f"{emotion} ({confidence:.2f})",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
        
        # 保存或显示
        if output_path:
            cv2.imwrite(output_path, image)
            logger.info(f"结果已保存: {output_path}")
        else:
            cv2.imshow('Result', image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()


def main():
    """测试入口"""
    tester = EmotionRecognitionTester()
    tester.test_realtime()


if __name__ == '__main__':
    main()
