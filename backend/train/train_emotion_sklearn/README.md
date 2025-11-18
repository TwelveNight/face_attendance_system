# Sklearn 情感识别训练 (MediaPipe + SVM)

基于MediaPipe面部特征和Sklearn SVM进行情感识别。

## 方法概述

1. 使用MediaPipe提取468个面部关键点 (x, y, z坐标)
2. 将关键点展平为1404维特征向量
3. 归一化特征(平移+缩放)
4. 使用SVM分类器进行训练

## 数据准备

### 创建数据集结构

```
data/
├── train/
│   ├── happy/
│   │   ├── img1.jpg
│   │   └── ...
│   ├── sad/
│   └── surprised/
```

**或从旧项目复制:**
```bash
cp -r ../../../../emotion_attendance_system/train/train_sklearn_emotion/data/* ./data/
```

### 提取特征

```bash
# 从图像提取MediaPipe特征
python data.py --data_dir data/train --output train_features.npz
```

这会生成 `train_features.npz` 文件包含:
- `X`: 特征矩阵 (N, 1404)
- `y`: 标签 (N,)
- `class_names`: 类别名称

## 训练模型

### 基础训练
```bash
python train.py --features_file train_features.npz
```

### 使用网格搜索优化参数
```bash
python train.py --features_file train_features.npz --grid_search
```

网格搜索参数:
- `C`: [0.1, 1, 10, 100]
- `gamma`: ['scale', 'auto', 0.001, 0.01]
- `kernel`: ['rbf', 'linear']

### 直接从图像训练
```bash
python train.py --data_dir data/train
```

模型保存到: `../../saved_models/emotion_sklearn.pkl`

## 测试模型

```bash
python test.py
```

## 技术细节

### MediaPipe面部网格
- 468个3D关键点
- 覆盖整个面部(眼睛、眉毛、嘴巴、轮廓)
- 实时检测(约30-60 FPS)

### 特征归一化
```python
# 1. 平移到原点
landmarks_centered = landmarks - center

# 2. 缩放到[-1, 1]
landmarks_normalized = landmarks_centered / max_distance
```

### SVM配置
- **Kernel**: RBF (默认)
- **C**: 10 (正则化参数)
- **Gamma**: 'scale' (RBF核参数)
- **Probability**: True (输出置信度)

## 性能对比

| 方法 | 特征维度 | 训练时间 | 推理速度 | 预期准确率 |
|------|----------|----------|----------|------------|
| MediaPipe+SVM | 1404 | ~10s | ~30ms | 70-80% |
| PyTorch CNN | 图像 | ~10min | ~20ms | 75-85% |

## 优势

1. **训练快速**: 几秒即可完成
2. **轻量级**: 模型文件小(<1MB)
3. **可解释**: 基于几何特征,更易理解
4. **鲁棒性**: MediaPipe对光照变化较鲁棒

## 劣势

1. **准确率**: 通常低于深度学习方法
2. **依赖检测**: MediaPipe检测失败则无法识别
3. **特征固定**: 无法自动学习特征

## 使用场景

适合:
- 快速原型开发
- 资源受限环境
- 需要可解释性的场景
- 数据量较小时

## 故障排除

### MediaPipe检测失败
- 确保图像清晰
- 人脸占据足够大的区域
- 光照均匀

### 准确率低
- 增加训练数据
- 使用网格搜索优化参数
- 尝试不同的特征归一化方法

### 速度慢
- MediaPipe已经很快了
- 如果还慢,检查CPU性能
- 考虑减少输入图像分辨率
