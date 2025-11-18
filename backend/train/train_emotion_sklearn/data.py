"""
数据准备脚本
从文件夹加载图像并提取MediaPipe特征
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import numpy as np
import cv2
from tqdm import tqdm
import logging
from train.train_emotion_sklearn.utils import (
    FacialLandmarkExtractor,
    preprocess_image_for_mediapipe
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_data_from_folders(
    data_dir: str,
    use_normalized: bool = True,
    output_file: str = "emotion_features.npz"
):
    """
    从文件夹加载图像并提取特征
    
    文件夹结构:
    data/
      happy/
        img1.jpg
        img2.jpg
      sad/
      surprised/
    
    Args:
        data_dir: 数据目录
        use_normalized: 是否使用归一化特征
        output_file: 输出文件名
    """
    logger.info("=" * 60)
    logger.info("MediaPipe特征提取")
    logger.info("=" * 60)
    
    data_path = Path(data_dir)
    
    if not data_path.exists():
        logger.error(f"数据目录不存在: {data_dir}")
        return
    
    # 获取所有类别
    class_dirs = [d for d in data_path.iterdir() if d.is_dir()]
    class_names = sorted([d.name for d in class_dirs])
    
    logger.info(f"检测到类别: {class_names}")
    
    # 初始化特征提取器
    extractor = FacialLandmarkExtractor()
    
    X = []  # 特征
    y = []  # 标签
    
    # 遍历每个类别
    for label, class_name in enumerate(class_names):
        class_dir = data_path / class_name
        logger.info(f"\n处理类别: {class_name}")
        
        # 获取所有图像
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.jfif']
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(class_dir.glob(f'*{ext}'))
        
        logger.info(f"  找到 {len(image_files)} 张图像")
        
        # 提取特征
        success_count = 0
        
        for img_path in tqdm(image_files, desc=f"  提取 {class_name}"):
            # 读取图像(支持中文路径)
            img_data = np.fromfile(str(img_path), dtype=np.uint8)
            image = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
            
            if image is None:
                logger.warning(f"    无法读取: {img_path.name}")
                continue
            
            # 预处理
            image = preprocess_image_for_mediapipe(image)
            
            # 提取特征
            if use_normalized:
                features = extractor.extract_normalized_landmarks(image)
            else:
                features = extractor.extract_landmarks(image)
            
            if features is not None:
                X.append(features)
                y.append(label)
                success_count += 1
        
        logger.info(f"  ✓ 成功提取: {success_count}/{len(image_files)}")
    
    # 转换为numpy数组
    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.int32)
    
    logger.info("\n" + "=" * 60)
    logger.info("特征提取完成!")
    logger.info(f"  总样本数: {len(X)}")
    logger.info(f"  特征维度: {X.shape[1]}")
    logger.info(f"  类别数: {len(class_names)}")
    logger.info("=" * 60)
    
    # 保存数据
    save_path = Path(data_dir).parent / output_file
    np.savez_compressed(
        save_path,
        X=X,
        y=y,
        class_names=class_names
    )
    
    logger.info(f"\n特征已保存: {save_path}")
    
    return X, y, class_names


def load_extracted_features(file_path: str):
    """
    加载已提取的特征
    
    Returns:
        (X, y, class_names)
    """
    data = np.load(file_path, allow_pickle=True)
    return data['X'], data['y'], data['class_names']


def main():
    """数据准备入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MediaPipe特征提取')
    parser.add_argument(
        '--data_dir',
        type=str,
        default='data/train',
        help='数据目录'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='emotion_features.npz',
        help='输出文件名'
    )
    parser.add_argument(
        '--no_normalize',
        action='store_true',
        help='不使用归一化特征'
    )
    
    args = parser.parse_args()
    
    load_data_from_folders(
        args.data_dir,
        use_normalized=not args.no_normalize,
        output_file=args.output
    )


if __name__ == '__main__':
    main()
