# 训练模块

本目录包含所有模型的训练脚本,统一使用PyTorch框架。

## 模块结构

```
train/
├── common/                      # 共享工具
│   ├── yolo_detector.py        # YOLO检测器封装
│   └── data_utils.py           # 数据处理工具
│
├── train_yolo/                 # YOLO人脸检测训练
│   ├── train.py                # 训练脚本
│   ├── test.py                 # 测试脚本
│   ├── data.yaml               # 数据配置
│   └── data/                   # 训练数据
│
├── train_facenet/              # FaceNet人脸识别训练
│   ├── collect_faces.py        # 采集人脸(使用YOLO)
│   ├── train.py                # 训练SVM分类器
│   ├── test.py                 # 测试脚本
│   └── dataset/                # 人脸数据集
│
├── train_emotion_pytorch/      # PyTorch情绪识别训练
│   ├── model.py                # CNN模型定义
│   ├── dataset.py              # 数据集加载
│   ├── train.py                # 训练脚本
│   ├── test.py                 # 测试脚本
│   └── data/                   # 情绪数据
│
└── train_emotion_sklearn/      # Sklearn情绪识别训练
    ├── utils.py                # MediaPipe特征提取
    ├── data.py                 # 数据准备
    ├── train.py                # 训练SVM
    ├── test.py                 # 测试脚本
    └── data/                   # 情绪图像数据
```

## 训练流程

### 1. YOLO人脸检测

```bash
cd train_yolo
python train.py
```

训练完成后,模型保存到 `../../saved_models/yolov8n-face.pt`

### 2. FaceNet人脸识别

```bash
cd train_facenet

# 步骤1: 采集人脸数据
python collect_faces.py

# 步骤2: 训练SVM分类器
python train.py

# 步骤3: 测试
python test.py
```

训练完成后,模型保存到:
- `../../saved_models/facenet_embeddings.npz`
- `../../saved_models/facenet_svm.pkl`

### 3. PyTorch情绪识别

```bash
cd train_emotion_pytorch

# 训练
python train.py

# 测试
python test.py
```

训练完成后,模型保存到 `../../saved_models/emotion_cnn.pth`

### 4. Sklearn情绪识别

```bash
cd train_emotion_sklearn

# 步骤1: 准备数据
python data.py

# 步骤2: 训练
python train.py

# 步骤3: 测试
python test.py
```

训练完成后,模型保存到 `../../saved_models/emotion_svm.pkl`

## 数据准备

### YOLO训练数据

从Roboflow下载人脸检测数据集,解压到 `train_yolo/data/`

### FaceNet训练数据

每个用户创建一个文件夹,包含至少10张不同角度的人脸照片:

```
train_facenet/dataset/
├── user1/
│   ├── 1.jpg
│   ├── 2.jpg
│   └── ...
├── user2/
│   └── ...
```

### 情绪训练数据

按情绪类别组织:

```
train_emotion_*/data/
├── happy/
│   ├── img1.jpg
│   └── ...
├── sad/
│   └── ...
└── surprised/
    └── ...
```

## 注意事项

1. **统一使用YOLO**: 所有需要人脸检测的地方都使用YOLO,移除了MTCNN依赖
2. **统一使用PyTorch**: 情绪识别从TensorFlow迁移到PyTorch
3. **配置引用**: 所有脚本都引用 `config.settings` 中的配置
4. **日志记录**: 训练过程有详细的日志输出
5. **GPU加速**: 自动检测并使用CUDA加速

## 模型评估

每个训练脚本都包含测试功能,运行后会输出:
- 准确率
- 混淆矩阵
- 可视化结果

## 疑难解答

### GPU内存不足

降低batch size或使用CPU训练:
```python
# 在train.py中修改
device = 'cpu'
batch_size = 16  # 减小
```

### 数据集路径问题

确保数据集路径正确,支持中文路径。

### 依赖安装

```bash
pip install -r ../requirements.txt
```
