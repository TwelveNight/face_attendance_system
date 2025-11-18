"""
数据处理工具函数
用于训练阶段的数据管理
"""
import os
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def ensure_dir(directory: Path or str) -> Path:
    """
    确保目录存在,不存在则创建
    
    Args:
        directory: 目录路径
    
    Returns:
        Path对象
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def save_face_image(
    face_image: np.ndarray,
    save_path: Path or str,
    filename: str,
    quality: int = 95
) -> bool:
    """
    保存人脸图像(支持中文路径)
    
    Args:
        face_image: 人脸图像
        save_path: 保存目录
        filename: 文件名
        quality: JPEG质量(1-100)
    
    Returns:
        是否保存成功
    """
    try:
        save_path = ensure_dir(save_path)
        full_path = save_path / filename
        
        # 使用imencode处理中文路径
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        result, encoded_img = cv2.imencode('.jpg', face_image, encode_param)
        
        if result:
            encoded_img.tofile(str(full_path))
            logger.debug(f"保存图像: {full_path}")
            return True
        else:
            logger.error(f"图像编码失败: {filename}")
            return False
            
    except Exception as e:
        logger.error(f"保存图像失败 {filename}: {e}")
        return False


def load_face_images(
    image_dir: Path or str,
    target_size: Optional[Tuple[int, int]] = None,
    extensions: Tuple[str] = ('.jpg', '.jpeg', '.png', '.bmp')
) -> List[np.ndarray]:
    """
    从目录加载所有人脸图像
    
    Args:
        image_dir: 图像目录
        target_size: 目标尺寸(width, height),None则保持原始尺寸
        extensions: 支持的文件扩展名
    
    Returns:
        图像数组列表
    """
    image_dir = Path(image_dir)
    images = []
    
    if not image_dir.exists():
        logger.warning(f"目录不存在: {image_dir}")
        return images
    
    # 遍历目录
    for ext in extensions:
        for img_path in image_dir.glob(f"*{ext}"):
            try:
                # 读取图像(支持中文路径)
                img_data = np.fromfile(str(img_path), dtype=np.uint8)
                img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
                
                if img is None:
                    logger.warning(f"无法读取图像: {img_path}")
                    continue
                
                # 调整大小
                if target_size is not None:
                    img = cv2.resize(img, target_size)
                
                images.append(img)
                
            except Exception as e:
                logger.error(f"加载图像失败 {img_path}: {e}")
    
    logger.info(f"从 {image_dir} 加载了 {len(images)} 张图像")
    return images


def load_dataset_by_class(
    dataset_dir: Path or str,
    target_size: Optional[Tuple[int, int]] = None
) -> Tuple[List[np.ndarray], List[str]]:
    """
    按类别加载数据集
    目录结构: dataset_dir/class_name/*.jpg
    
    Args:
        dataset_dir: 数据集根目录
        target_size: 目标尺寸
    
    Returns:
        (图像列表, 标签列表)
    """
    dataset_dir = Path(dataset_dir)
    all_images = []
    all_labels = []
    
    if not dataset_dir.exists():
        logger.error(f"数据集目录不存在: {dataset_dir}")
        return all_images, all_labels
    
    # 遍历每个类别子目录
    class_dirs = [d for d in dataset_dir.iterdir() if d.is_dir()]
    
    for class_dir in class_dirs:
        class_name = class_dir.name
        images = load_face_images(class_dir, target_size)
        
        # 添加标签
        labels = [class_name] * len(images)
        
        all_images.extend(images)
        all_labels.extend(labels)
        
        logger.info(f"类别 '{class_name}': {len(images)} 张图像")
    
    logger.info(f"总计加载: {len(all_images)} 张图像, {len(set(all_labels))} 个类别")
    
    return all_images, all_labels


def split_dataset(
    images: List[np.ndarray],
    labels: List[str],
    test_size: float = 0.2,
    random_state: int = 42,
    shuffle: bool = True
) -> Tuple[List[np.ndarray], List[np.ndarray], List[str], List[str]]:
    """
    分割数据集为训练集和测试集
    
    Args:
        images: 图像列表
        labels: 标签列表
        test_size: 测试集比例
        random_state: 随机种子
        shuffle: 是否打乱
    
    Returns:
        (X_train, X_test, y_train, y_test)
    """
    from sklearn.model_selection import train_test_split
    
    X_train, X_test, y_train, y_test = train_test_split(
        images,
        labels,
        test_size=test_size,
        random_state=random_state,
        shuffle=shuffle,
        stratify=labels if len(set(labels)) > 1 else None
    )
    
    logger.info(f"训练集: {len(X_train)} 样本")
    logger.info(f"测试集: {len(X_test)} 样本")
    
    return X_train, X_test, y_train, y_test


def preprocess_face_for_facenet(face_image: np.ndarray) -> np.ndarray:
    """
    预处理人脸图像用于FaceNet
    
    Args:
        face_image: BGR格式人脸图像
    
    Returns:
        预处理后的图像(RGB, float32, normalized)
    """
    # BGR to RGB
    face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
    
    # 归一化到[-1, 1]或[0, 1]取决于模型要求
    # FaceNet通常使用 (img - 127.5) / 128
    face_normalized = (face_rgb.astype('float32') - 127.5) / 128.0
    
    return face_normalized


def preprocess_face_for_emotion(face_image: np.ndarray) -> np.ndarray:
    """
    预处理人脸图像用于情绪识别
    
    Args:
        face_image: BGR格式人脸图像
    
    Returns:
        灰度图像
    """
    # 转换为灰度
    if len(face_image.shape) == 3:
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
    else:
        gray = face_image
    
    return gray


if __name__ == '__main__':
    # 测试代码
    import sys
    from pathlib import Path
    
    # 测试ensure_dir
    test_dir = Path('./test_data_utils')
    ensure_dir(test_dir)
    print(f"✓ 创建目录: {test_dir}")
    
    # 测试save_face_image
    test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    save_face_image(test_image, test_dir, 'test.jpg')
    print(f"✓ 保存测试图像")
    
    # 测试load_face_images
    images = load_face_images(test_dir)
    print(f"✓ 加载图像: {len(images)} 张")
    
    # 清理
    import shutil
    shutil.rmtree(test_dir)
    print(f"✓ 清理测试目录")
