"""
PyTorch情感识别CNN模型
支持3种情感分类: happy, sad, surprised
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class EmotionCNN(nn.Module):
    """情感识别卷积神经网络"""
    
    def __init__(self, num_classes: int = 3, dropout_rate: float = 0.5):
        """
        初始化模型
        
        Args:
            num_classes: 情感类别数
            dropout_rate: Dropout比率
        """
        super(EmotionCNN, self).__init__()
        
        # 卷积层1: 48x48 -> 24x24
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(2, 2)
        
        # 卷积层2: 24x24 -> 12x12
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(2, 2)
        
        # 卷积层3: 12x12 -> 6x6
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.pool3 = nn.MaxPool2d(2, 2)
        
        # 卷积层4: 6x6 -> 3x3
        self.conv4 = nn.Conv2d(128, 256, kernel_size=3, padding=1)
        self.bn4 = nn.BatchNorm2d(256)
        self.pool4 = nn.MaxPool2d(2, 2)
        
        # 全连接层
        self.flatten = nn.Flatten()
        self.fc1 = nn.Linear(256 * 3 * 3, 512)
        self.dropout1 = nn.Dropout(dropout_rate)
        self.fc2 = nn.Linear(512, 256)
        self.dropout2 = nn.Dropout(dropout_rate)
        self.fc3 = nn.Linear(256, num_classes)
    
    def forward(self, x):
        """前向传播"""
        # Block 1
        x = self.pool1(F.relu(self.bn1(self.conv1(x))))
        
        # Block 2
        x = self.pool2(F.relu(self.bn2(self.conv2(x))))
        
        # Block 3
        x = self.pool3(F.relu(self.bn3(self.conv3(x))))
        
        # Block 4
        x = self.pool4(F.relu(self.bn4(self.conv4(x))))
        
        # 全连接
        x = self.flatten(x)
        x = F.relu(self.fc1(x))
        x = self.dropout1(x)
        x = F.relu(self.fc2(x))
        x = self.dropout2(x)
        x = self.fc3(x)
        
        return x


class LightEmotionCNN(nn.Module):
    """轻量级情感识别CNN(用于快速训练测试)"""
    
    def __init__(self, num_classes: int = 3):
        super(LightEmotionCNN, self).__init__()
        
        self.features = nn.Sequential(
            # 48x48 -> 24x24
            nn.Conv2d(1, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            
            # 24x24 -> 12x12
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            
            # 12x12 -> 6x6
            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 6 * 6, 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, num_classes)
        )
    
    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x


def create_model(model_type: str = 'standard', num_classes: int = 3) -> nn.Module:
    """
    创建情感识别模型
    
    Args:
        model_type: 模型类型 ('standard' 或 'light')
        num_classes: 类别数
    
    Returns:
        PyTorch模型
    """
    if model_type == 'light':
        return LightEmotionCNN(num_classes)
    else:
        return EmotionCNN(num_classes)


if __name__ == '__main__':
    # 测试模型
    model = create_model('standard', num_classes=3)
    print(model)
    
    # 测试前向传播
    x = torch.randn(1, 1, 48, 48)
    y = model(x)
    print(f"\n输入形状: {x.shape}")
    print(f"输出形状: {y.shape}")
    
    # 统计参数量
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\n总参数量: {total_params:,}")
    print(f"可训练参数: {trainable_params:,}")
