"""
统一配置管理模块
所有路径、模型参数、API配置集中管理
支持通过环境变量覆盖默认配置
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 基础路径
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent


class Config:
    """系统配置类"""
    
    # ==================== 路径配置 ====================
    MODEL_DIR = BASE_DIR / 'saved_models'
    DATA_DIR = BASE_DIR / 'data'
    LOG_DIR = BASE_DIR / 'logs'
    USER_FACES_DIR = DATA_DIR / 'user_faces'
    TRAIN_DIR = BASE_DIR / 'train'
    
    # 确保目录存在
    for directory in [MODEL_DIR, DATA_DIR, LOG_DIR, USER_FACES_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # ==================== 模型文件路径 ====================
    # YOLO人脸检测模型
    YOLO_MODEL = MODEL_DIR / 'yolov8n-face.pt'
    
    # FaceNet人脸识别相关
    FACENET_EMBEDDINGS = MODEL_DIR / 'facenet_embeddings.npz'
    FACENET_SVM = MODEL_DIR / 'facenet_svm.pkl'
    
    # ==================== 模型参数 ====================
    # YOLO检测阈值
    YOLO_CONFIDENCE_THRESHOLD = float(os.getenv('YOLO_THRESHOLD', 0.5))
    
    # 人脸处理参数
    FACE_SIZE = (160, 160)  # FaceNet输入尺寸
    FACE_MARGIN = 20  # 人脸裁剪边距(像素)
    
    # 人脸识别阈值
    FACE_RECOGNITION_THRESHOLD = float(os.getenv('FACE_RECOGNITION_THRESHOLD', 0.6))
    
    # 用户注册时采集的人脸图像数量
    REGISTER_FACE_COUNT = int(os.getenv('REGISTER_FACE_COUNT', 10))
    
    # ==================== 数据库配置 ====================
    DATABASE_PATH = DATA_DIR / 'attendance.db'
    DATABASE_URI = os.getenv('DATABASE_URI', f'sqlite:///{DATABASE_PATH}')
    
    # SQLAlchemy配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('SQL_ECHO', 'False').lower() == 'true'
    
    # ==================== API配置 ====================
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 8088))
    API_DEBUG = os.getenv('API_DEBUG', 'False').lower() == 'true'
    
    # CORS配置
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    
    # Flask密钥
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # ==================== 日志配置 ====================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = LOG_DIR / 'app.log'
    
    # ==================== GPU配置 ====================
    USE_CUDA = os.getenv('USE_CUDA', 'True').lower() == 'true'
    CUDA_DEVICE = int(os.getenv('CUDA_DEVICE', 0))
    
    # ==================== 摄像头配置 ====================
    CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', 0))
    VIDEO_FPS = int(os.getenv('VIDEO_FPS', 30))
    
    # ==================== 其他配置 ====================
    # 考勤记录保留天数
    ATTENDANCE_RETENTION_DAYS = int(os.getenv('ATTENDANCE_RETENTION_DAYS', 365))
    
    # 图像质量(JPEG压缩)
    IMAGE_QUALITY = int(os.getenv('IMAGE_QUALITY', 85))
    
    # Base64图像最大大小(KB)
    MAX_IMAGE_SIZE_KB = int(os.getenv('MAX_IMAGE_SIZE_KB', 500))
    
    @classmethod
    def validate(cls):
        """验证配置的有效性"""
        errors = []
        
        # 检查必需的模型文件
        if not cls.YOLO_MODEL.exists():
            errors.append(f"YOLO模型文件不存在: {cls.YOLO_MODEL}")
        
        # 检查目录权限
        for directory in [cls.DATA_DIR, cls.LOG_DIR, cls.MODEL_DIR]:
            if not os.access(directory, os.W_OK):
                errors.append(f"目录不可写: {directory}")
        
        if errors:
            raise ValueError(f"配置验证失败:\n" + "\n".join(errors))
        
        return True
    
    @classmethod
    def get_device(cls):
        """获取PyTorch设备"""
        import torch
        if cls.USE_CUDA and torch.cuda.is_available():
            return torch.device(f'cuda:{cls.CUDA_DEVICE}')
        return torch.device('cpu')
    
    @classmethod
    def print_config(cls):
        """打印当前配置(用于调试)"""
        print("=" * 60)
        print("系统配置:")
        print("-" * 60)
        print(f"基础路径: {cls.BASE_DIR}")
        print(f"模型目录: {cls.MODEL_DIR}")
        print(f"数据目录: {cls.DATA_DIR}")
        print(f"数据库: {cls.DATABASE_URI}")
        print(f"API地址: {cls.API_HOST}:{cls.API_PORT}")
        print(f"GPU加速: {cls.USE_CUDA}")
        print(f"设备: {cls.get_device()}")
        print("=" * 60)


# 创建配置实例
config = Config()


if __name__ == '__main__':
    # 测试配置
    config.print_config()
    config.validate()
