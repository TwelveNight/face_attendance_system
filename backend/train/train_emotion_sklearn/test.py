"""
Sklearn情感识别测试脚本
实时测试MediaPipe+SVM模型
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import pickle
import cv2
import numpy as np
import logging

from config import config
from train.common import YOLOFaceDetector
from train.train_emotion_sklearn.utils import FacialLandmarkExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SklearnEmotionTester:
    """Sklearn情感识别测试器"""
    
    def __init__(
        self,
        model_path: str = None,
        yolo_path: str = None
    ):
        """初始化测试器"""
        # 加载模型
        if model_path is None:
            model_path = str(config.EMOTION_SKLEARN_MODEL)
        
        logger.info(f"加载模型: {model_path}")
        
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.svm = model_data['svm']
        self.scaler = model_data['scaler']
        self.class_names = model_data['class_names']
        
        logger.info(f"✓ 模型已加载")
        logger.info(f"  支持类别: {self.class_names}")
        
        # 加载YOLO
        if yolo_path is None:
            yolo_path = str(config.YOLO_MODEL)
        
        self.detector = YOLOFaceDetector(yolo_path)
        
        # MediaPipe特征提取器
        self.feature_extractor = FacialLandmarkExtractor(
            static_image_mode=False  # 视频模式
        )
    
    def predict_emotion(self, face_image: np.ndarray) -> tuple:
        """
        预测情感
        
        Args:
            face_image: 人脸图像
        
        Returns:
            (emotion_name, confidence)
        """
        # 提取MediaPipe特征
        features = self.feature_extractor.extract_normalized_landmarks(face_image)
        
        if features is None:
            return None, 0.0
        
        # 标准化
        features_scaled = self.scaler.transform([features])
        
        # 预测
        prediction = self.svm.predict(features_scaled)[0]
        probabilities = self.svm.predict_proba(features_scaled)[0]
        
        emotion_name = self.class_names[prediction]
        confidence = probabilities[prediction]
        
        return emotion_name, confidence
    
    def test_realtime(self, camera_index: int = 0):
        """实时测试"""
        logger.info("=" * 60)
        logger.info("Sklearn情感识别实时测试 (MediaPipe+SVM)")
        logger.info("=" * 60)
        logger.info("按 'q' 退出\n")
        
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            logger.error(f"无法打开摄像头 {camera_index}")
            return
        
        # 情感颜色
        emotion_colors = {
            'happy': (0, 255, 0),
            'sad': (255, 0, 0),
            'surprised': (0, 255, 255)
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
                    
                    if emotion is not None:
                        # 绘制结果
                        boxes = self.detector.detect_faces(frame)
                        if boxes:
                            x1, y1, x2, y2 = boxes[0]
                            
                            color = emotion_colors.get(emotion, (255, 255, 255))
                            
                            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                            cv2.putText(
                                display_frame,
                                f"{emotion} ({confidence:.2f})",
                                (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.7,
                                color,
                                2
                            )
                            
                            cv2.putText(
                                display_frame,
                                f"Emotion: {emotion}",
                                (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1.0,
                                color,
                                2
                            )
                    else:
                        cv2.putText(
                            display_frame,
                            "Face detected, but no landmarks",
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 165, 255),
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
            
            cv2.imshow('Sklearn Emotion Recognition Test', display_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
    
    def test_on_image(self, image_path: str, output_path: str = None):
        """测试单张图像"""
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"无法读取图像: {image_path}")
            return
        
        face = self.detector.detect_single_face(image)
        
        if face is None:
            logger.warning("未检测到人脸")
            return
        
        emotion, confidence = self.predict_emotion(face)
        
        if emotion:
            logger.info(f"预测结果: {emotion} (置信度: {confidence:.2f})")
            
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
        
        if output_path:
            cv2.imwrite(output_path, image)
            logger.info(f"结果已保存: {output_path}")
        else:
            cv2.imshow('Result', image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()


def main():
    """测试入口"""
    tester = SklearnEmotionTester()
    tester.test_realtime()


if __name__ == '__main__':
    main()
