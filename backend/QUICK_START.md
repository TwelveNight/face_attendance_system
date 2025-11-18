# 快速开始指南

## 1️⃣ 环境配置 (5分钟)

### 创建环境
```powershell
conda create -n emotion_attendance python=3.10 -y
conda activate emotion_attendance
```

### 安装依赖 (按顺序执行)
```powershell
# 1. PyTorch (CUDA 12.1) - 必须先安装
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 2. facenet-pytorch (不降级PyTorch)
pip install facenet-pytorch --no-deps

# 3. 其他核心库
conda install numpy pandas scikit-learn pillow -c conda-forge -y
pip install opencv-python ultralytics mediapipe

# 4. Web框架
pip install Flask Flask-CORS flask-sqlalchemy SQLAlchemy python-dotenv

# 5. 工具
pip install tqdm openpyxl
```

### 验证安装
```powershell
python -c "import torch; print('CUDA:', torch.cuda.is_available())"
python -c "from facenet_pytorch import InceptionResnetV1; print('✓ 环境配置成功')"
```

---

## 2️⃣ 项目结构

```
emotion_attendance_v2/
└── backend/
    ├── config/              # 配置管理
    │   └── settings.py
    ├── train/               # 训练模块
    │   ├── common/          # 共享工具
    │   ├── train_yolo/      # YOLO人脸检测训练
    │   ├── train_facenet/   # 人脸识别训练
    │   ├── train_emotion_pytorch/  # PyTorch情感识别
    │   └── train_emotion_sklearn/  # Sklearn情感识别
    ├── models/              # (待创建) 推理模型
    ├── services/            # (待创建) 业务逻辑
    ├── database/            # (待创建) 数据库
    └── api/                 # (待创建) API接口
```

---

## 3️⃣ 测试配置

```powershell
cd e:\school\sophomore\python\emotion_attendence_system\final\emotion_attendance_v2\backend

# 测试配置系统
python config/settings.py
```

预期输出:
```
✓ 配置系统正常
YOLO模型路径: ...
数据库路径: ...
CUDA可用: True
```

---

## 4️⃣ 训练流程

### Step 1: YOLO人脸检测 (可选)

如果已有YOLO模型,可跳过此步骤。

```powershell
cd train/train_yolo

# 准备数据 (参考data.yaml配置)
# 训练
python train.py

# 测试
python test.py
```

### Step 2: FaceNet人脸识别

```powershell
cd train/train_facenet

# 1. 采集人脸数据
python collect_faces.py --interactive

# 2. 训练模型
python train.py

# 3. 测试
python test.py
```

### Step 3: 情感识别训练

#### 选项A: PyTorch CNN (推荐,准确率高)

```powershell
cd train/train_emotion_pytorch

# 准备数据 (data/train/ 目录)
# 训练
python train.py

# 测试
python test.py
```

#### 选项B: Sklearn + MediaPipe (快速,轻量)

```powershell
cd train/train_emotion_sklearn

# 1. 提取特征
python data.py --data_dir data/train

# 2. 训练
python train.py --features_file emotion_features.npz

# 3. 测试
python test.py
```

---

## 5️⃣ 数据准备

### 人脸识别数据

使用采集脚本:
```powershell
cd train/train_facenet
python collect_faces.py --user zhangsan --num 10
```

或手动准备:
```
train_facenet/dataset/
├── user1/
│   ├── user1_1.jpg
│   └── user1_2.jpg
└── user2/
    └── ...
```

### 情感识别数据

```
train_emotion_pytorch/data/train/
├── happy/
│   ├── img1.jpg
│   └── ...
├── sad/
│   └── ...
└── surprised/
    └── ...
```

---

## 6️⃣ 常用命令

### 激活环境
```powershell
conda activate emotion_attendance
```

### 查看已安装包
```powershell
conda list
pip list
```

### 检查GPU
```powershell
nvidia-smi
python -c "import torch; print(torch.cuda.get_device_name(0))"
```

---

## 7️⃣ 下一步计划

- [ ] 完成所有训练模块的训练
- [ ] 创建后端推理模块 (models/, services/)
- [ ] 创建数据库模块 (database/)
- [ ] 创建Flask API (api/)
- [ ] 创建前端界面 (frontend/)

---

## 📚 详细文档

- **环境配置问题**: 参考 `ENV_SETUP.md`
- **训练说明**: 参考各模块的 `README.md`
- **配置参数**: 查看 `config/settings.py`

---

## ⚠️ 注意事项

1. **必须先安装PyTorch (cu121)** 再安装facenet-pytorch
2. **使用`--no-deps`** 安装facenet-pytorch避免降级
3. **训练前确认CUDA可用** 否则速度会很慢
4. **数据格式** 按照各模块README要求准备

---

**环境配置完成时间**: 约5-10分钟  
**完整训练时间**: 视数据量而定,通常1-2小时  
**推荐配置**: GTX 1060 6GB以上 / RTX 30系列
