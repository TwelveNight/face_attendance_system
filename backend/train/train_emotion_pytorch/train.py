"""
PyTorch情感识别训练脚本
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split
import numpy as np
from tqdm import tqdm
import logging

from config import config
from train.train_emotion_pytorch.model import create_model
from train.train_emotion_pytorch.dataset import (
    EmotionDataset,
    load_emotion_dataset_from_folders
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmotionTrainer:
    """情感识别训练器"""
    
    def __init__(
        self,
        model_type: str = 'standard',
        num_classes: int = 3,
        device: str = None
    ):
        """初始化训练器"""
        # 设置设备
        if device is None:
            self.device = config.get_device()
        else:
            self.device = torch.device(device)
        
        logger.info(f"使用设备: {self.device}")
        
        # 创建模型
        self.model = create_model(model_type, num_classes).to(self.device)
        self.num_classes = num_classes
        
        # 损失函数和优化器
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = None
        
        # 训练历史
        self.history = {
            'train_loss': [],
            'train_acc': [],
            'val_loss': [],
            'val_acc': []
        }
    
    def prepare_dataloaders(
        self,
        data_dir: str,
        batch_size: int = 32,
        val_split: float = 0.2,
        num_workers: int = 0
    ):
        """准备数据加载器"""
        logger.info("=" * 60)
        logger.info("加载数据集...")
        logger.info("=" * 60)
        
        # 加载数据
        image_paths, labels, class_names = load_emotion_dataset_from_folders(data_dir)
        
        logger.info(f"总样本数: {len(image_paths)}")
        logger.info(f"类别: {class_names}")
        
        # 分割训练集和验证集
        train_paths, val_paths, train_labels, val_labels = train_test_split(
            image_paths,
            labels,
            test_size=val_split,
            random_state=42,
            stratify=labels
        )
        
        logger.info(f"训练集: {len(train_paths)}")
        logger.info(f"验证集: {len(val_paths)}")
        
        # 创建数据集
        train_dataset = EmotionDataset(
            train_paths,
            train_labels,
            image_size=config.EMOTION_IMAGE_SIZE,
            augment=True
        )
        
        val_dataset = EmotionDataset(
            val_paths,
            val_labels,
            image_size=config.EMOTION_IMAGE_SIZE,
            augment=False
        )
        
        # 创建数据加载器
        self.train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers
        )
        
        self.val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers
        )
        
        return class_names
    
    def train_epoch(self) -> tuple:
        """训练一个epoch"""
        self.model.train()
        
        running_loss = 0.0
        correct = 0
        total = 0
        
        pbar = tqdm(self.train_loader, desc='Training')
        
        for images, labels in pbar:
            images = images.to(self.device)
            labels = labels.to(self.device)
            
            # 前向传播
            self.optimizer.zero_grad()
            outputs = self.model(images)
            loss = self.criterion(outputs, labels)
            
            # 反向传播
            loss.backward()
            self.optimizer.step()
            
            # 统计
            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
            
            # 更新进度条
            pbar.set_postfix({
                'loss': running_loss / (pbar.n + 1),
                'acc': 100. * correct / total
            })
        
        epoch_loss = running_loss / len(self.train_loader)
        epoch_acc = 100. * correct / total
        
        return epoch_loss, epoch_acc
    
    def validate(self) -> tuple:
        """验证"""
        self.model.eval()
        
        running_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for images, labels in tqdm(self.val_loader, desc='Validation'):
                images = images.to(self.device)
                labels = labels.to(self.device)
                
                outputs = self.model(images)
                loss = self.criterion(outputs, labels)
                
                running_loss += loss.item()
                _, predicted = outputs.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()
        
        val_loss = running_loss / len(self.val_loader)
        val_acc = 100. * correct / total
        
        return val_loss, val_acc
    
    def train(
        self,
        data_dir: str,
        epochs: int = 50,
        batch_size: int = 32,
        learning_rate: float = 0.001,
        patience: int = 10
    ):
        """完整训练流程"""
        logger.info("=" * 60)
        logger.info("PyTorch 情感识别训练")
        logger.info("=" * 60)
        
        # 准备数据
        class_names = self.prepare_dataloaders(data_dir, batch_size)
        
        # 设置优化器
        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=learning_rate
        )
        
        # 学习率调度器
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='max',
            factor=0.5,
            patience=5,
            verbose=True
        )
        
        # Early stopping
        best_val_acc = 0
        patience_counter = 0
        
        logger.info(f"\n开始训练 {epochs} 个epochs...")
        logger.info("=" * 60)
        
        for epoch in range(epochs):
            logger.info(f"\nEpoch {epoch + 1}/{epochs}")
            
            # 训练
            train_loss, train_acc = self.train_epoch()
            
            # 验证
            val_loss, val_acc = self.validate()
            
            # 记录历史
            self.history['train_loss'].append(train_loss)
            self.history['train_acc'].append(train_acc)
            self.history['val_loss'].append(val_loss)
            self.history['val_acc'].append(val_acc)
            
            # 输出结果
            logger.info(
                f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%"
            )
            logger.info(
                f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%"
            )
            
            # 调整学习率
            scheduler.step(val_acc)
            
            # 保存最佳模型
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                patience_counter = 0
                self.save_model('best')
                logger.info(f"✓ 保存最佳模型 (Val Acc: {val_acc:.2f}%)")
            else:
                patience_counter += 1
            
            # Early stopping
            if patience_counter >= patience:
                logger.info(f"\nEarly stopping after {epoch + 1} epochs")
                break
        
        logger.info("\n" + "=" * 60)
        logger.info("训练完成!")
        logger.info(f"最佳验证准确率: {best_val_acc:.2f}%")
        logger.info("=" * 60)
        
        return best_val_acc
    
    def save_model(self, suffix: str = ''):
        """保存模型"""
        save_path = config.EMOTION_PYTORCH_MODEL
        
        if suffix:
            save_path = save_path.parent / f"{save_path.stem}_{suffix}{save_path.suffix}"
        
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'num_classes': self.num_classes,
            'history': self.history
        }, save_path)
        
        logger.info(f"模型已保存: {save_path}")


def main():
    """训练入口"""
    # 配置
    DATA_DIR = "data/train"  # 数据目录
    EPOCHS = 50
    BATCH_SIZE = 32
    LEARNING_RATE = 0.001
    MODEL_TYPE = 'standard'  # 'standard' or 'light'
    
    # 检查数据目录
    if not Path(DATA_DIR).exists():
        logger.error(f"数据目录不存在: {DATA_DIR}")
        logger.info("请创建以下结构:")
        logger.info("data/train/")
        logger.info("  happy/")
        logger.info("  sad/")
        logger.info("  surprised/")
        return
    
    # 创建训练器
    trainer = EmotionTrainer(
        model_type=MODEL_TYPE,
        num_classes=3
    )
    
    # 训练
    trainer.train(
        data_dir=DATA_DIR,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        patience=10
    )


if __name__ == '__main__':
    main()
