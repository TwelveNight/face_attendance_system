# YOLO人脸检测训练

训练YOLOv8人脸检测模型。

## 数据准备

如果您已有训练数据,请将数据复制到此目录:

```
train_yolo/data/
├── train/
│   ├── images/
│   │   ├── img1.jpg
│   │   └── ...
│   └── labels/
│       ├── img1.txt
│       └── ...
└── val/
    ├── images/
    └── labels/
```

**或者从旧项目复制:**

```bash
# 复制数据
cp -r ../../../emotion_attendance_system/train/train_yolo_face_detection/data ./
```

标签格式(YOLO格式):
```
class_id x_center y_center width height
```
所有值归一化到[0, 1]

## 训练

```bash
python train.py
```

训练完成后,最佳模型会自动保存到 `../../saved_models/yolov8n-face.pt`

## 测试

```bash
# 实时测试
python test.py --mode realtime

# 测试单张图像
python test.py --mode image --image path/to/image.jpg

# 自定义参数
python test.py --threshold 0.6 --camera 0
```

## 自定义参数

在 `train.py` 中修改:

```python
EPOCHS = 50          # 训练轮数
BATCH_SIZE = 16      # 批次大小
IMG_SIZE = 640       # 图像大小
```

## 注意事项

1. 确保数据集路径在 `data.yaml` 中正确配置
2. GPU训练需要CUDA支持
3. 训练过程会生成图表在 `runs/detect/train/` 目录
