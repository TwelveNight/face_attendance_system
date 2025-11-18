"""
YOLO人脸检测器封装
统一的YOLO检测接口,用于训练和推理阶段
"""
import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Tuple, Optional
import torch


class YOLOFaceDetector:
    """YOLO人脸检测器封装类"""
    
    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.5,
        device: Optional[str] = None
    ):
        """
        初始化YOLO检测器
        
        Args:
            model_path: YOLO模型文件路径
            confidence_threshold: 检测置信度阈值
            device: 设备('cuda' 或 'cpu'),None则自动选择
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        
        # 自动选择设备
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        # 加载模型
        self.model = YOLO(model_path)
        print(f"✓ YOLO模型已加载: {model_path}")
        print(f"✓ 使用设备: {self.device}")
        print(f"✓ 置信度阈值: {self.confidence_threshold}")
    
    def detect_faces(
        self,
        frame: np.ndarray,
        return_boxes: bool = False
    ) -> List[Tuple[int, int, int, int]]:
        """
        检测图像中的人脸
        
        Args:
            frame: 输入图像(BGR格式)
            return_boxes: 是否返回边界框坐标
        
        Returns:
            边界框列表 [(x1, y1, x2, y2), ...]
        """
        # 运行检测
        results = self.model(frame, device=self.device)[0]
        
        boxes = []
        for result in results.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = result
            
            # 过滤低置信度检测
            if score > self.confidence_threshold:
                boxes.append((int(x1), int(y1), int(x2), int(y2)))
        
        return boxes
    
    def detect_single_face(
        self,
        frame: np.ndarray,
        margin: Optional[dict] = None
    ) -> Optional[np.ndarray]:
        """
        检测单个人脸并裁剪
        
        Args:
            frame: 输入图像
            margin: 边距字典 {'top': int, 'bottom': int, 'left': int, 'right': int}
        
        Returns:
            裁剪后的人脸图像,如果未检测到则返回None
        """
        boxes = self.detect_faces(frame)
        
        if len(boxes) == 0:
            return None
        
        # 只取第一个检测到的人脸
        x1, y1, x2, y2 = boxes[0]
        
        # 应用边距
        if margin is not None:
            h, w = frame.shape[:2]
            x1 = max(0, x1 - margin.get('left', 0))
            y1 = max(0, y1 - margin.get('top', 0))
            x2 = min(w, x2 + margin.get('right', 0))
            y2 = min(h, y2 + margin.get('bottom', 0))
        
        # 裁剪人脸
        face = frame[y1:y2, x1:x2]
        
        return face
    
    def draw_detections(
        self,
        frame: np.ndarray,
        boxes: Optional[List[Tuple[int, int, int, int]]] = None,
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2
    ) -> np.ndarray:
        """
        在图像上绘制检测框
        
        Args:
            frame: 输入图像
            boxes: 边界框列表,None则自动检测
            color: 框颜色(BGR)
            thickness: 线条粗细
        
        Returns:
            绘制后的图像
        """
        if boxes is None:
            boxes = self.detect_faces(frame)
        
        result_frame = frame.copy()
        
        for (x1, y1, x2, y2) in boxes:
            cv2.rectangle(result_frame, (x1, y1), (x2, y2), color, thickness)
        
        return result_frame
    
    def batch_detect(
        self,
        frames: List[np.ndarray]
    ) -> List[List[Tuple[int, int, int, int]]]:
        """
        批量检测多张图像
        
        Args:
            frames: 图像列表
        
        Returns:
            每张图像的边界框列表
        """
        all_boxes = []
        
        for frame in frames:
            boxes = self.detect_faces(frame)
            all_boxes.append(boxes)
        
        return all_boxes
    
    def __call__(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        使检测器可调用
        
        Args:
            frame: 输入图像
        
        Returns:
            边界框列表
        """
        return self.detect_faces(frame)


if __name__ == '__main__':
    # 测试代码
    import sys
    from pathlib import Path
    
    # 添加项目路径
    sys.path.append(str(Path(__file__).parent.parent.parent))
    
    from config import config
    
    # 初始化检测器
    detector = YOLOFaceDetector(
        model_path=str(config.YOLO_MODEL),
        confidence_threshold=config.YOLO_CONFIDENCE_THRESHOLD
    )
    
    # 测试摄像头检测
    print("\n按 'q' 退出...\n")
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 检测人脸
        boxes = detector.detect_faces(frame)
        print(f"检测到 {len(boxes)} 个人脸")
        
        # 绘制检测框
        result = detector.draw_detections(frame, boxes)
        
        cv2.imshow('YOLO Face Detection Test', result)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
