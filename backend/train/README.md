# 训练模块

本目录包含人脸识别考勤系统的模型训练脚本。

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
└── train_facenet/              # FaceNet人脸识别训练
    ├── collect_faces.py        # 采集人脸(使用YOLO)
    ├── train.py                # 训练SVM分类器
    ├── test.py                 # 测试脚本
    └── dataset/                # 人脸数据集
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

## 注意事项

1. **统一使用YOLO**: 所有人脸检测都使用YOLOv8,确保检测一致性
2. **配置引用**: 所有脚本都引用 `config.settings` 中的配置
3. **日志记录**: 训练过程有详细的日志输出
4. **GPU加速**: 自动检测并使用CUDA加速
5. **数据质量**: 确保训练数据质量,人脸图像清晰、角度多样

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
