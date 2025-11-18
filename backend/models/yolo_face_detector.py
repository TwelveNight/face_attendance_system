"""
YOLO人脸检测器封装
使用YOLOv8进行人脸检测
"""
import numpy as np
import cv2
from typing import List, Tuple, Optional
from ultralytics import YOLO
import torch

from config.settings import Config


class YOLOFaceDetector:
    """YOLO人脸检测器"""
    
    def __init__(self, model_path: Optional[str] = None, confidence_threshold: Optional[float] = None):
        """
        初始化YOLO检测器
        
        Args:
            model_path: 模型文件路径
            confidence_threshold: 置信度阈值
        """
        self.model_path = model_path or Config.YOLO_MODEL
        self.confidence_threshold = confidence_threshold or Config.YOLO_CONFIDENCE_THRESHOLD
        self.device = Config.get_device()
        
        # 加载模型
        self.model = None
        self.load_model()
    
    def load_model(self):
        """加载YOLO模型"""
        try:
            print(f"加载YOLO模型: {self.model_path}")
            self.model = YOLO(str(self.model_path))
            
            # 移动到指定设备
            if torch.cuda.is_available() and Config.USE_CUDA:
                self.model.to(self.device)
            
            print(f"✓ YOLO模型加载成功 (设备: {self.device})")
        except Exception as e:
            print(f"✗ YOLO模型加载失败: {e}")
            raise
    
    def detect_faces(self, image: np.ndarray, return_confidence: bool = False) -> List[Tuple]:
        """
        检测图像中的人脸
        
        Args:
            image: 输入图像 (BGR格式)
            return_confidence: 是否返回置信度
            
        Returns:
            List of (x1, y1, x2, y2) or (x1, y1, x2, y2, confidence)
        """
        if self.model is None:
            raise RuntimeError("模型未加载")
        
        # YOLO推理
        results = self.model(image, conf=self.confidence_threshold, verbose=False)
        
        faces = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # 获取边界框坐标
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0])
                
                # 确保坐标在图像范围内
                h, w = image.shape[:2]
                x1, y1 = max(0, int(x1)), max(0, int(y1))
                x2, y2 = min(w, int(x2)), min(h, int(y2))
                
                if return_confidence:
                    faces.append((x1, y1, x2, y2, confidence))
                else:
                    faces.append((x1, y1, x2, y2))
        
        return faces
    
    def detect_largest_face(self, image: np.ndarray) -> Optional[Tuple]:
        """
        检测最大的人脸
        
        Args:
            image: 输入图像
            
        Returns:
            (x1, y1, x2, y2, confidence) or None
        """
        faces = self.detect_faces(image, return_confidence=True)
        
        if not faces:
            return None
        
        # 找到面积最大的人脸
        largest_face = max(faces, key=lambda f: (f[2] - f[0]) * (f[3] - f[1]))
        return largest_face
    
    def crop_face(self, image: np.ndarray, bbox: Tuple, margin: int = None) -> Optional[np.ndarray]:
        """
        根据边界框裁剪人脸
        
        Args:
            image: 输入图像
            bbox: 边界框 (x1, y1, x2, y2) or (x1, y1, x2, y2, confidence)
            margin: 边距(像素)
            
        Returns:
            裁剪后的人脸图像
        """
        if margin is None:
            margin = Config.FACE_MARGIN
        
        x1, y1, x2, y2 = bbox[:4]
        h, w = image.shape[:2]
        
        # 添加边距
        x1 = max(0, x1 - margin)
        y1 = max(0, y1 - margin)
        x2 = min(w, x2 + margin)
        y2 = min(h, y2 + margin)
        
        # 裁剪
        face = image[y1:y2, x1:x2]
        
        return face if face.size > 0 else None
    
    def draw_faces(self, image: np.ndarray, faces: List[Tuple], 
                   color: Tuple[int, int, int] = (0, 255, 0), 
                   thickness: int = 2) -> np.ndarray:
        """
        在图像上绘制人脸框
        
        Args:
            image: 输入图像
            faces: 人脸列表
            color: 框的颜色 (B, G, R)
            thickness: 线条粗细
            
        Returns:
            绘制后的图像
        """
        result = image.copy()
        
        for face in faces:
            x1, y1, x2, y2 = face[:4]
            cv2.rectangle(result, (x1, y1), (x2, y2), color, thickness)
            
            # 如果有置信度,显示
            if len(face) > 4:
                confidence = face[4]
                text = f'{confidence:.2f}'
                cv2.putText(result, text, (x1, y1 - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return result
    
    def __del__(self):
        """清理资源"""
        if self.model is not None:
            del self.model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()


if __name__ == '__main__':
    # 测试代码
    detector = YOLOFaceDetector()
    
    # 测试摄像头
    cap = cv2.VideoCapture(0)
    
    print("按 'q' 退出")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 检测人脸
        faces = detector.detect_faces(frame, return_confidence=True)
        
        # 绘制
        result = detector.draw_faces(frame, faces)
        
        # 显示
        cv2.imshow('YOLO Face Detection', result)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
