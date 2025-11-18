"""
YOLO人脸检测模型测试脚本
实时测试训练好的YOLO人脸检测模型
"""
import sys
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

import cv2
from config import config
from train.common import YOLOFaceDetector
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_yolo_realtime(
    model_path: str = None,
    camera_index: int = 0,
    confidence_threshold: float = 0.5
):
    """
    实时测试YOLO人脸检测模型
    
    Args:
        model_path: 模型文件路径,None则使用配置中的路径
        camera_index: 摄像头索引
        confidence_threshold: 置信度阈值
    """
    if model_path is None:
        model_path = str(config.YOLO_MODEL)
    
    logger.info("=" * 60)
    logger.info("YOLO人脸检测实时测试")
    logger.info("=" * 60)
    logger.info(f"模型路径: {model_path}")
    logger.info(f"置信度阈值: {confidence_threshold}")
    logger.info("\n按 'q' 退出, 's' 截图保存\n")
    
    # 初始化检测器
    detector = YOLOFaceDetector(
        model_path=model_path,
        confidence_threshold=confidence_threshold
    )
    
    # 打开摄像头
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        logger.error(f"无法打开摄像头 {camera_index}")
        return
    
    frame_count = 0
    screenshot_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            logger.error("无法读取摄像头帧")
            break
        
        frame_count += 1
        
        # 检测人脸
        boxes = detector.detect_faces(frame)
        
        # 绘制检测框和信息
        result_frame = detector.draw_detections(frame, boxes)
        
        # 添加文本信息
        info_text = f"Faces: {len(boxes)} | Threshold: {confidence_threshold:.2f}"
        cv2.putText(
            result_frame,
            info_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )
        
        # 显示FPS
        if frame_count % 30 == 0:
            logger.info(f"检测到 {len(boxes)} 个人脸")
        
        # 显示结果
        cv2.imshow('YOLO Face Detection Test', result_frame)
        
        # 键盘控制
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            logger.info("退出测试")
            break
        elif key == ord('s'):
            # 保存截图
            screenshot_path = f'screenshot_{screenshot_count}.jpg'
            cv2.imwrite(screenshot_path, result_frame)
            screenshot_count += 1
            logger.info(f"截图已保存: {screenshot_path}")
    
    # 释放资源
    cap.release()
    cv2.destroyAllWindows()
    logger.info(f"总处理帧数: {frame_count}")


def test_yolo_on_image(
    image_path: str,
    model_path: str = None,
    confidence_threshold: float = 0.5,
    save_result: bool = True
):
    """
    在单张图像上测试YOLO人脸检测
    
    Args:
        image_path: 图像文件路径
        model_path: 模型文件路径
        confidence_threshold: 置信度阈值
        save_result: 是否保存结果
    """
    if model_path is None:
        model_path = str(config.YOLO_MODEL)
    
    logger.info(f"测试图像: {image_path}")
    
    # 初始化检测器
    detector = YOLOFaceDetector(
        model_path=model_path,
        confidence_threshold=confidence_threshold
    )
    
    # 读取图像
    frame = cv2.imread(image_path)
    if frame is None:
        logger.error(f"无法读取图像: {image_path}")
        return
    
    # 检测人脸
    boxes = detector.detect_faces(frame)
    logger.info(f"检测到 {len(boxes)} 个人脸")
    
    # 绘制结果
    result_frame = detector.draw_detections(frame, boxes)
    
    # 显示结果
    cv2.imshow('Detection Result', result_frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    # 保存结果
    if save_result:
        result_path = image_path.replace('.jpg', '_result.jpg')
        cv2.imwrite(result_path, result_frame)
        logger.info(f"结果已保存: {result_path}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='YOLO人脸检测测试')
    parser.add_argument('--mode', type=str, default='realtime', 
                        choices=['realtime', 'image'],
                        help='测试模式')
    parser.add_argument('--image', type=str, default=None,
                        help='图像路径(mode=image时使用)')
    parser.add_argument('--model', type=str, default=None,
                        help='模型路径')
    parser.add_argument('--threshold', type=float, default=0.5,
                        help='置信度阈值')
    parser.add_argument('--camera', type=int, default=0,
                        help='摄像头索引')
    
    args = parser.parse_args()
    
    if args.mode == 'realtime':
        test_yolo_realtime(
            model_path=args.model,
            camera_index=args.camera,
            confidence_threshold=args.threshold
        )
    else:
        if args.image is None:
            logger.error("请指定图像路径: --image <path>")
        else:
            test_yolo_on_image(
                image_path=args.image,
                model_path=args.model,
                confidence_threshold=args.threshold
            )
