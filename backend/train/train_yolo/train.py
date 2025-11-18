"""
YOLO人脸检测模型训练脚本
使用YOLOv8训练人脸检测模型
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from ultralytics import YOLO
from config import config
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def train_yolo_face_detection(
    data_yaml: str = "data.yaml",
    epochs: int = 50,
    img_size: int = 640,
    batch_size: int = 16,
    device: str = None,
    save_dir: str = "runs/detect/train"
):
    """
    训练YOLO人脸检测模型
    
    Args:
        data_yaml: 数据配置文件路径
        epochs: 训练轮数
        img_size: 图像大小
        batch_size: 批次大小
        device: 设备('cuda' 或 'cpu'),None则自动选择
        save_dir: 模型保存目录
    """
    logger.info("=" * 60)
    logger.info("YOLO人脸检测模型训练")
    logger.info("=" * 60)
    
    # 设置设备
    if device is None:
        device = 'cuda' if config.USE_CUDA else 'cpu'
    
    logger.info(f"使用设备: {device}")
    logger.info(f"训练轮数: {epochs}")
    logger.info(f"批次大小: {batch_size}")
    logger.info(f"图像大小: {img_size}")
    logger.info(f"数据配置: {data_yaml}")
    
    try:
        # 加载预训练模型或从头开始
        # model = YOLO("yolov8n.yaml")  # 从头开始
        model = YOLO("yolov8n.pt")  # 使用预训练权重(推荐)
        
        logger.info("✓ 模型已加载")
        
        # 开始训练
        logger.info("\n开始训练...\n")
        
        results = model.train(
            data=data_yaml,
            epochs=epochs,
            imgsz=img_size,
            batch=batch_size,
            device=device,
            project=save_dir,
            name="yolo_face",
            patience=10,  # 早停patience
            save=True,
            save_period=5,  # 每5个epoch保存一次
            val=True,
            plots=True,  # 生成训练图表
            verbose=True
        )
        
        logger.info("\n训练完成!")
        logger.info(f"最佳模型: {results.save_dir / 'weights' / 'best.pt'}")
        
        # 复制最佳模型到saved_models目录
        best_model_path = results.save_dir / 'weights' / 'best.pt'
        if best_model_path.exists():
            import shutil
            target_path = config.MODEL_DIR / 'yolov8n-face.pt'
            shutil.copy(best_model_path, target_path)
            logger.info(f"✓ 模型已保存到: {target_path}")
        
        # 验证模型
        logger.info("\n开始验证...")
        metrics = model.val()
        logger.info(f"mAP50: {metrics.box.map50:.4f}")
        logger.info(f"mAP50-95: {metrics.box.map:.4f}")
        
        return model, results
        
    except Exception as e:
        logger.error(f"训练失败: {e}")
        raise


if __name__ == '__main__':
    # 训练参数 (快速验证模式)
    EPOCHS = 3  # 快速验证,完整训练改为50-100
    BATCH_SIZE = 8  # 减小batch避免显存不足
    IMG_SIZE = 640
    
    # 开始训练
    model, results = train_yolo_face_detection(
        data_yaml="data.yaml",
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        img_size=IMG_SIZE
    )
    
    logger.info("\n" + "=" * 60)
    logger.info("训练完成!模型已保存。")
    logger.info("=" * 60)
