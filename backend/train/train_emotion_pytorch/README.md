# PyTorch 情感识别训练

使用PyTorch CNN进行情感识别训练。

## 数据准备

### 方式1: 从文件夹加载

创建以下目录结构:

```
data/
├── train/
│   ├── happy/
│   │   ├── img1.jpg
│   │   ├── img2.jpg
│   │   └── ...
│   ├── sad/
│   │   └── ...
│   └── surprised/
│       └── ...
└── test/
    ├── happy/
    ├── sad/
    └── surprised/
```

**或从旧项目复制:**
```bash
# 复制训练数据
cp -r ../../../../emotion_attendance_system/train/train_tensorflow_emotion/data/train ./data/
cp -r ../../../../emotion_attendance_system/train/train_tensorflow_emotion/data/test ./data/
```

### 方式2: 使用FER2013数据集

如果有FER2013 CSV文件,可以使用`FER2013Dataset`类加载。

## 训练模型

```bash
python train.py
```

训练配置:
- **模型**: EmotionCNN (4个卷积块 + 3个全连接层)
- **输入**: 48x48灰度图像
- **输出**: 3类情感 (happy, sad, surprised)
- **优化器**: Adam
- **学习率**: 0.001 (带ReduceLROnPlateau调度)
- **数据增强**: 随机翻转、亮度/对比度调整、旋转

训练过程:
1. 自动从文件夹加载数据
2. 分割训练集/验证集 (80%/20%)
3. 训练with early stopping (patience=10)
4. 保存最佳模型到 `saved_models/emotion_pytorch.pth`

## 测试模型

### 实时测试
```bash
python test.py
```

### 测试单张图像
```python
from test import EmotionRecognitionTester

tester = EmotionRecognitionTester()
tester.test_on_image('test.jpg', 'result.jpg')
```

## 模型架构

### Standard Model (EmotionCNN)
```
Input: 1x48x48
Conv1: 32 filters, 3x3 -> 32x24x24
Conv2: 64 filters, 3x3 -> 64x12x12
Conv3: 128 filters, 3x3 -> 128x6x6
Conv4: 256 filters, 3x3 -> 256x3x3
FC1: 2304 -> 512
FC2: 512 -> 256
FC3: 256 -> 3
```

总参数: ~1.8M

### Light Model (LightEmotionCNN)
更轻量,用于快速测试,参数量约500K。

## 性能

- **训练速度**: ~1s/epoch (GPU, batch_size=32)
- **推理速度**: ~20ms/张 (GPU)
- **预期准确率**: 75-85% (取决于数据质量)

## 技术细节

### 数据增强
- 水平翻转 (p=0.5)
- 亮度调整 (0.8-1.2x, p=0.5)
- 对比度调整 (0.8-1.2x, p=0.5)
- 轻微旋转 (±10度, p=0.3)

### 训练技巧
- BatchNormalization: 加速收敛
- Dropout: 防止过拟合
- Early Stopping: 避免过训练
- ReduceLROnPlateau: 动态调整学习率

## 注意事项

1. **GPU内存**: 标准模型需要~2GB显存
2. **数据平衡**: 确保每个类别样本数相近
3. **数据质量**: 图像清晰,人脸居中效果更好

## 故障排除

### 准确率低
- 增加训练数据
- 使用数据增强
- 调整学习率
- 尝试更多epochs

### 过拟合
- 增加Dropout比率
- 使用更多数据增强
- 减少模型复杂度(使用light model)

### GPU内存不足
- 减小batch_size
- 使用light model
- 释放其他GPU占用
