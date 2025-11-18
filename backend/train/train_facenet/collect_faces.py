"""
采集人脸数据脚本
使用YOLO检测人脸并保存,用于FaceNet训练
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

import cv2
from config import config
from train.common import YOLOFaceDetector, ensure_dir, save_face_image
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def collect_faces_for_user(
    user_name: str,
    num_images: int = None,
    camera_index: int = 0,
    save_dir: str = "dataset",
    yolo_model_path: str = None,
    face_size: tuple = None
):
    """
    为指定用户采集人脸图像
    
    Args:
        user_name: 用户名(将作为文件夹名)
        num_images: 采集图像数量,None则使用配置
        camera_index: 摄像头索引
        save_dir: 保存根目录
        yolo_model_path: YOLO模型路径
        face_size: 人脸尺寸(width, height)
    """
    if num_images is None:
        num_images = config.REGISTER_FACE_COUNT
    
    if yolo_model_path is None:
        yolo_model_path = str(config.YOLO_MODEL)
    
    if face_size is None:
        face_size = config.FACE_SIZE
    
    logger.info("=" * 60)
    logger.info(f"开始采集用户 '{user_name}' 的人脸数据")
    logger.info("=" * 60)
    logger.info(f"目标数量: {num_images} 张")
    logger.info(f"保存目录: {save_dir}/{user_name}")
    logger.info(f"人脸尺寸: {face_size}")
    logger.info("\n操作说明:")
    logger.info("  - 面对摄像头,保持不同角度和表情")
    logger.info("  - 系统会自动间隔采集")
    logger.info("  - 按 'q' 提前退出\n")
    
    # 创建保存目录
    user_dir = ensure_dir(Path(save_dir) / user_name)
    
    # 初始化YOLO检测器
    detector = YOLOFaceDetector(
        model_path=yolo_model_path,
        confidence_threshold=config.YOLO_CONFIDENCE_THRESHOLD
    )
    
    # 打开摄像头
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        logger.error(f"无法打开摄像头 {camera_index}")
        return False
    
    saved_count = 0
    frame_interval = 0  # 帧间隔计数器
    interval_frames = 15  # 每15帧采集一次
    
    logger.info("摄像头已就绪,开始采集...\n")
    
    while saved_count < num_images:
        ret, frame = cap.read()
        if not ret:
            logger.error("无法读取摄像头帧")
            break
        
        # 检测人脸
        face_region = detector.detect_single_face(frame, margin=config.FACE_MARGIN)
        
        # 显示信息
        display_frame = frame.copy()
        info_text = f"User: {user_name} | Saved: {saved_count}/{num_images}"
        cv2.putText(
            display_frame,
            info_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )
        
        if face_region is not None:
            # 绘制检测框
            boxes = detector.detect_faces(frame)
            if boxes:
                x1, y1, x2, y2 = boxes[0]
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 间隔采集
            if frame_interval == 0:
                # 调整大小
                face_resized = cv2.resize(face_region, face_size)
                
                # 保存
                filename = f"{user_name}_{saved_count + 1}.jpg"
                if save_face_image(face_resized, user_dir, filename):
                    saved_count += 1
                    logger.info(f"✓ 采集进度: {saved_count}/{num_images} - {filename}")
                    
                    # 重置间隔
                    frame_interval = interval_frames
                else:
                    logger.warning(f"保存失败: {filename}")
            else:
                frame_interval -= 1
            
            # 显示状态
            status_text = "Capturing..." if frame_interval == 0 else f"Wait {frame_interval}"
            cv2.putText(
                display_frame,
                status_text,
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2
            )
        else:
            # 未检测到人脸
            cv2.putText(
                display_frame,
                "No face detected",
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )
        
        # 显示画面
        cv2.imshow('Face Collection', display_frame)
        
        # 按键控制
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            logger.warning("用户中断采集")
            break
    
    # 释放资源
    cap.release()
    cv2.destroyAllWindows()
    
    # 总结
    logger.info("\n" + "=" * 60)
    if saved_count >= num_images:
        logger.info(f"✓ 采集完成!共保存 {saved_count} 张图像")
        logger.info(f"✓ 保存位置: {user_dir}")
        return True
    else:
        logger.warning(f"采集未完成,仅保存 {saved_count}/{num_images} 张图像")
        return False


def collect_multiple_users():
    """交互式采集多个用户的人脸数据"""
    logger.info("=" * 60)
    logger.info("FaceNet 人脸数据采集工具")
    logger.info("=" * 60)
    
    while True:
        user_name = input("\n请输入用户名 (输入 'q' 退出): ").strip()
        
        if user_name.lower() == 'q':
            logger.info("退出采集工具")
            break
        
        if not user_name:
            logger.warning("用户名不能为空")
            continue
        
        # 检查是否已存在
        user_dir = Path("dataset") / user_name
        if user_dir.exists():
            choice = input(f"用户 '{user_name}' 已存在,是否覆盖? (y/n): ").strip().lower()
            if choice != 'y':
                continue
        
        # 开始采集
        success = collect_faces_for_user(user_name)
        
        if success:
            logger.info(f"✓ 用户 '{user_name}' 数据采集完成")
        else:
            logger.warning(f"⚠ 用户 '{user_name}' 数据采集不完整")
        
        # 继续采集下一个用户
        choice = input("\n是否继续采集其他用户? (y/n): ").strip().lower()
        if choice != 'y':
            break
    
    logger.info("\n采集工具已关闭")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='FaceNet人脸数据采集')
    parser.add_argument('--user', type=str, default=None,
                        help='用户名')
    parser.add_argument('--num', type=int, default=None,
                        help='采集数量')
    parser.add_argument('--camera', type=int, default=0,
                        help='摄像头索引')
    parser.add_argument('--interactive', action='store_true',
                        help='交互模式(采集多个用户)')
    
    args = parser.parse_args()
    
    if args.interactive or args.user is None:
        # 交互模式
        collect_multiple_users()
    else:
        # 单用户模式
        collect_faces_for_user(
            user_name=args.user,
            num_images=args.num,
            camera_index=args.camera
        )
