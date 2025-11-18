# 情绪考勤系统 - 后端

基于PyTorch的情绪考勤系统后端,提供人脸检测、识别和情绪分析功能。

## 技术栈

- **深度学习框架**: PyTorch (统一)
- **Web框架**: Flask
- **数据库**: SQLite + SQLAlchemy
- **人脸检测**: YOLOv8
- **人脸识别**: FaceNet (facenet-pytorch)
- **情绪识别**: PyTorch CNN / Sklearn SVM + MediaPipe

## 项目结构

```
backend/
├── config/              # 配置管理
├── train/               # 训练脚本
│   ├── common/          # 共享工具
│   ├── train_yolo/      # YOLO人脸检测训练
│   ├── train_facenet/   # FaceNet人脸识别训练
│   ├── train_emotion_pytorch/  # PyTorch情绪识别训练
│   └── train_emotion_sklearn/  # Sklearn情绪识别训练
├── models/              # 模型管理(推理)
├── services/            # 业务逻辑
├── database/            # 数据库
├── api/                 # Flask API
├── saved_models/        # 训练好的模型
├── data/                # 运行时数据
└── logs/                # 日志
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp config/.env.example .env
# 编辑 .env 文件,根据实际情况修改配置
```

### 3. 训练模型

```bash
# 训练YOLO人脸检测模型
cd train/train_yolo
python train.py

# 训练FaceNet人脸识别模型
cd train/train_facenet
python collect_faces.py  # 采集人脸数据
python train.py          # 训练模型

# 训练PyTorch情绪识别模型
cd train/train_emotion_pytorch
python train.py

# 训练Sklearn情绪识别模型
cd train/train_emotion_sklearn
python data.py   # 准备数据
python train.py  # 训练模型
```

### 4. 启动API服务

```bash
cd api
python app.py
```

服务将在 http://localhost:8088 启动

## API文档

### 用户管理

- `POST /api/users/register` - 注册新用户
- `GET /api/users` - 获取用户列表
- `DELETE /api/users/:id` - 删除用户

### 考勤管理

- `POST /api/attendance/check-in` - 打卡
- `GET /api/attendance/history` - 查询历史记录
- `GET /api/attendance/export` - 导出数据

### 统计分析

- `GET /api/statistics/daily` - 每日统计
- `GET /api/statistics/emotion-distribution` - 情绪分布
- `GET /api/statistics/user-trend/:id` - 用户趋势

### 视频流

- `GET /api/video/feed` - 实时视频流

### 系统

- `GET /api/system/health` - 健康检查
- `GET /api/system/model-status` - 模型状态

## 配置说明

主要配置项在 `config/settings.py`:

- `YOLO_CONFIDENCE_THRESHOLD`: YOLO检测阈值(默认0.5)
- `DEFAULT_EMOTION_MODEL`: 默认情绪模型(pytorch/sklearn/deepface)
- `REGISTER_FACE_COUNT`: 注册时采集人脸数量(默认10)
- `USE_CUDA`: 是否使用GPU加速
- `EMOTION_CLASSES`: 情绪类别

## 开发指南

### 添加新的情绪类别

1. 准备训练数据
2. 修改 `config/settings.py` 中的 `EMOTION_CLASSES`
3. 重新训练情绪识别模型

### 自定义模型

1. 在 `models/` 目录下创建新的模型类
2. 在 `model_manager.py` 中注册
3. 在服务层调用

## 许可证

MIT
