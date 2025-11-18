"""
模型管理器 (单例模式)
统一管理所有模型的加载和使用
"""
import threading
from typing import Optional
import torch

from .yolo_face_detector import YOLOFaceDetector
from .facenet_recognizer import FaceNetRecognizer


class ModelManager:
    """
    模型管理器单例类
    确保所有模型只加载一次,避免重复加载浪费资源
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化模型管理器"""
        if self._initialized:
            return
        
        self._initialized = True
        self._yolo_detector: Optional[YOLOFaceDetector] = None
        self._facenet_recognizer: Optional[FaceNetRecognizer] = None
        self._models_loaded = False
        
        print("=" * 60)
        print("模型管理器初始化")
        print("=" * 60)
    
    def load_models(self, force_reload: bool = False):
        """
        加载所有模型
        
        Args:
            force_reload: 是否强制重新加载
        """
        if self._models_loaded and not force_reload:
            print("模型已加载,跳过")
            return
        
        try:
            # 加载YOLO检测器
            print("\n[1/2] 加载YOLO人脸检测器...")
            self._yolo_detector = YOLOFaceDetector()
            
            # 加载FaceNet识别器
            print("\n[2/2] 加载FaceNet人脸识别器...")
            self._facenet_recognizer = FaceNetRecognizer()
            
            self._models_loaded = True
            
            print("\n" + "=" * 60)
            print("✓ 所有模型加载完成")
            print("=" * 60)
            
            # 打印GPU内存使用情况
            if torch.cuda.is_available():
                self.print_gpu_memory()
        
        except Exception as e:
            print(f"\n✗ 模型加载失败: {e}")
            raise
    
    @property
    def yolo_detector(self) -> YOLOFaceDetector:
        """获取YOLO检测器"""
        if self._yolo_detector is None:
            raise RuntimeError("YOLO检测器未加载,请先调用load_models()")
        return self._yolo_detector
    
    @property
    def facenet_recognizer(self) -> FaceNetRecognizer:
        """获取FaceNet识别器"""
        if self._facenet_recognizer is None:
            raise RuntimeError("FaceNet识别器未加载,请先调用load_models()")
        return self._facenet_recognizer
    
    def is_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self._models_loaded
    
    def unload_models(self):
        """卸载所有模型"""
        print("卸载模型...")
        
        if self._yolo_detector is not None:
            del self._yolo_detector
            self._yolo_detector = None
        
        if self._facenet_recognizer is not None:
            del self._facenet_recognizer
            self._facenet_recognizer = None
        
        # 清理GPU缓存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self._models_loaded = False
        print("✓ 模型已卸载")
    
    def reload_models(self):
        """重新加载所有模型"""
        self.unload_models()
        self.load_models()
    
    def get_status(self) -> dict:
        """获取模型状态"""
        status = {
            'loaded': self._models_loaded,
            'yolo_loaded': self._yolo_detector is not None,
            'facenet_loaded': self._facenet_recognizer is not None,
            'user_count': 0
        }
        
        if self._facenet_recognizer is not None:
            status['user_count'] = self._facenet_recognizer.get_user_count()
        
        if torch.cuda.is_available():
            status['gpu_available'] = True
            status['gpu_memory'] = self.get_gpu_memory()
        else:
            status['gpu_available'] = False
        
        return status
    
    @staticmethod
    def get_gpu_memory() -> dict:
        """获取GPU内存使用情况"""
        if not torch.cuda.is_available():
            return {}
        
        allocated = torch.cuda.memory_allocated() / 1024**2  # MB
        reserved = torch.cuda.memory_reserved() / 1024**2    # MB
        total = torch.cuda.get_device_properties(0).total_memory / 1024**2  # MB
        
        return {
            'allocated_mb': round(allocated, 2),
            'reserved_mb': round(reserved, 2),
            'total_mb': round(total, 2),
            'free_mb': round(total - allocated, 2)
        }
    
    @staticmethod
    def print_gpu_memory():
        """打印GPU内存使用情况"""
        if not torch.cuda.is_available():
            print("GPU不可用")
            return
        
        memory = ModelManager.get_gpu_memory()
        print(f"\nGPU内存使用:")
        print(f"  已分配: {memory['allocated_mb']:.2f} MB")
        print(f"  已保留: {memory['reserved_mb']:.2f} MB")
        print(f"  总内存: {memory['total_mb']:.2f} MB")
        print(f"  可用: {memory['free_mb']:.2f} MB")


# 创建全局单例实例
model_manager = ModelManager()


if __name__ == '__main__':
    # 测试模型管理器
    manager = ModelManager()
    
    # 加载模型
    manager.load_models()
    
    # 获取状态
    status = manager.get_status()
    print("\n模型状态:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # 测试检测和识别
    import cv2
    
    cap = cv2.VideoCapture(0)
    detector = manager.yolo_detector
    recognizer = manager.facenet_recognizer
    
    print("\n按 'q' 退出")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 检测人脸
        faces = detector.detect_faces(frame, return_confidence=True)
        
        for face in faces:
            x1, y1, x2, y2 = face[:4]
            
            # 裁剪并识别
            face_img = detector.crop_face(frame, face)
            if face_img is not None:
                user_id, confidence = recognizer.recognize(face_img)
                
                # 绘制
                color = (0, 255, 0) if user_id is not None else (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                text = f"User {user_id} ({confidence:.2f})" if user_id else "Unknown"
                cv2.putText(frame, text, (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        cv2.imshow('Attendance System', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
