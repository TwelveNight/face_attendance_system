"""
PyTorch情感识别数据集类
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import torch
from torch.utils.data import Dataset
import cv2
import numpy as np
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class EmotionDataset(Dataset):
    """情感识别数据集"""
    
    def __init__(
        self,
        image_paths: List[str],
        labels: List[int],
        image_size: Tuple[int, int] = (48, 48),
        augment: bool = False
    ):
        """
        初始化数据集
        
        Args:
            image_paths: 图像路径列表
            labels: 标签列表
            image_size: 图像尺寸 (width, height)
            augment: 是否进行数据增强
        """
        self.image_paths = image_paths
        self.labels = labels
        self.image_size = image_size
        self.augment = augment
        
        assert len(image_paths) == len(labels), "图像和标签数量不匹配"
    
    def __len__(self) -> int:
        return len(self.image_paths)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        """获取一个样本"""
        # 读取图像
        img_path = self.image_paths[idx]
        label = self.labels[idx]
        
        # 使用opencv读取(支持中文路径)
        image = cv2.imdecode(
            np.fromfile(img_path, dtype=np.uint8),
            cv2.IMREAD_GRAYSCALE
        )
        
        if image is None:
            logger.warning(f"无法读取图像: {img_path}")
            # 返回空白图像
            image = np.zeros(self.image_size, dtype=np.uint8)
        
        # 调整大小
        if image.shape != self.image_size:
            image = cv2.resize(image, self.image_size)
        
        # 数据增强
        if self.augment:
            image = self._augment(image)
        
        # 归一化到[0, 1]
        image = image.astype(np.float32) / 255.0
        
        # 转换为tensor: HxW -> 1xHxW
        image_tensor = torch.from_numpy(image).unsqueeze(0)
        
        return image_tensor, label
    
    def _augment(self, image: np.ndarray) -> np.ndarray:
        """数据增强"""
        # 随机水平翻转
        if np.random.rand() > 0.5:
            image = cv2.flip(image, 1)
        
        # 随机亮度调整
        if np.random.rand() > 0.5:
            alpha = np.random.uniform(0.8, 1.2)
            image = np.clip(image * alpha, 0, 255).astype(np.uint8)
        
        # 随机对比度调整
        if np.random.rand() > 0.5:
            alpha = np.random.uniform(0.8, 1.2)
            beta = 128 * (1 - alpha)
            image = np.clip(alpha * image + beta, 0, 255).astype(np.uint8)
        
        # 随机轻微旋转
        if np.random.rand() > 0.7:
            angle = np.random.uniform(-10, 10)
            h, w = image.shape[:2]
            M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
            image = cv2.warpAffine(image, M, (w, h))
        
        return image


class FER2013Dataset(Dataset):
    """FER2013数据集(用于从CSV加载)"""
    
    def __init__(
        self,
        csv_file: str,
        split: str = 'train',
        image_size: Tuple[int, int] = (48, 48),
        emotion_map: dict = None,
        augment: bool = False
    ):
        """
        从FER2013 CSV文件加载
        
        Args:
            csv_file: CSV文件路径
            split: 'train', 'val', 或 'test'
            image_size: 图像尺寸
            emotion_map: 情感映射字典(如果需要重映射标签)
            augment: 是否增强
        """
        import pandas as pd
        
        self.image_size = image_size
        self.augment = augment and split == 'train'
        
        # 读取CSV
        df = pd.read_csv(csv_file)
        
        # 根据split过滤
        usage_map = {
            'train': 'Training',
            'val': 'PublicTest',
            'test': 'PrivateTest'
        }
        
        if split in usage_map:
            df = df[df['Usage'] == usage_map[split]]
        
        # 提取像素和标签
        self.pixels = []
        self.labels = []
        
        for _, row in df.iterrows():
            # 解析像素字符串 "0 1 2 ... 255"
            pixels = np.array([int(p) for p in row['pixels'].split()], dtype=np.uint8)
            pixels = pixels.reshape(48, 48)
            
            label = int(row['emotion'])
            
            # 应用情感映射
            if emotion_map and label in emotion_map:
                label = emotion_map[label]
                self.pixels.append(pixels)
                self.labels.append(label)
            elif emotion_map is None:
                self.pixels.append(pixels)
                self.labels.append(label)
        
        logger.info(f"加载 {split} 集: {len(self.pixels)} 张图像")
    
    def __len__(self) -> int:
        return len(self.pixels)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        image = self.pixels[idx].copy()
        label = self.labels[idx]
        
        # 数据增强
        if self.augment:
            image = self._augment(image)
        
        # 归一化
        image = image.astype(np.float32) / 255.0
        
        # 转tensor
        image_tensor = torch.from_numpy(image).unsqueeze(0)
        
        return image_tensor, label
    
    def _augment(self, image: np.ndarray) -> np.ndarray:
        """数据增强(与EmotionDataset相同)"""
        if np.random.rand() > 0.5:
            image = cv2.flip(image, 1)
        
        if np.random.rand() > 0.5:
            alpha = np.random.uniform(0.8, 1.2)
            image = np.clip(image * alpha, 0, 255).astype(np.uint8)
        
        return image


def load_emotion_dataset_from_folders(
    data_dir: str,
    class_names: List[str] = None
) -> Tuple[List[str], List[int], List[str]]:
    """
    从文件夹结构加载情感数据集
    
    文件夹结构:
    data/
      train/
        happy/
          img1.jpg
          img2.jpg
        sad/
        surprised/
      test/
        happy/
        sad/
        surprised/
    
    Args:
        data_dir: 数据根目录
        class_names: 类别名称列表
    
    Returns:
        (图像路径列表, 标签列表, 类别名称列表)
    """
    data_path = Path(data_dir)
    
    # 自动检测类别
    if class_names is None:
        class_dirs = [d for d in data_path.iterdir() if d.is_dir()]
        class_names = sorted([d.name for d in class_dirs])
    
    logger.info(f"检测到类别: {class_names}")
    
    image_paths = []
    labels = []
    
    for label, class_name in enumerate(class_names):
        class_dir = data_path / class_name
        
        if not class_dir.exists():
            logger.warning(f"类别目录不存在: {class_dir}")
            continue
        
        # 支持的图像格式
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.jfif']
        
        for ext in image_extensions:
            for img_path in class_dir.glob(f'*{ext}'):
                image_paths.append(str(img_path))
                labels.append(label)
        
        logger.info(f"  {class_name}: {len([l for l in labels if l == label])} 张图像")
    
    return image_paths, labels, class_names


if __name__ == '__main__':
    # 测试数据集
    logging.basicConfig(level=logging.INFO)
    
    # 创建测试数据
    image_paths = ['test.jpg'] * 10
    labels = [0, 1, 2] * 3 + [0]
    
    dataset = EmotionDataset(image_paths, labels, augment=True)
    print(f"数据集大小: {len(dataset)}")
    
    # 测试加载(会失败,因为test.jpg不存在,但能看到结构)
    # img, label = dataset[0]
    # print(f"图像形状: {img.shape}, 标签: {label}")
