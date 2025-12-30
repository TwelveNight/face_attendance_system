# 人脸识别考勤系统 - 后端

## 技术栈

- **框架**: Flask + SQLAlchemy
- **数据库**: MySQL
- **人脸检测**: YOLOv8
- **人脸识别**: FaceNet (facenet-pytorch)
- **运行环境**: Python 3.10 + CUDA 12.1

## 项目结构

```
backend/
├── api/                 # Flask API (入口: run.py)
├── config/              # 配置 (.env)
├── database/            # 数据库模型
├── models/              # AI模型推理
├── services/            # 业务逻辑
├── train/               # 模型训练脚本
├── saved_models/        # 训练好的模型
└── logs/                # 日志
```

## 快速开始

### 1. 环境配置

```powershell
# 创建环境
conda create -n face_attendance python=3.10 -y
conda activate face_attendance

# 安装PyTorch (CUDA 12.1)
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 安装facenet-pytorch (不降级PyTorch)
pip install facenet-pytorch --no-deps

# 安装其他依赖
pip install -r requirements.txt
```

### 2. 配置数据库

```powershell
# 复制配置模板
cp config/.env.template config/.env

# 编辑 .env，配置MySQL连接信息
```

### 3. 启动服务

```powershell
python run.py
```

服务地址: http://localhost:8088

## 主要API

| 模块 | 接口 | 说明 |
|------|------|------|
| 认证 | `POST /api/auth/login` | 用户登录 |
| 用户 | `POST /api/users/register` | 注册用户 |
| 考勤 | `POST /api/attendance/check-in` | 人脸打卡 |
| 考勤 | `GET /api/attendance/history` | 考勤记录 |
| 规则 | `GET /api/attendance-rules` | 考勤规则 |
| 部门 | `GET /api/departments` | 部门管理 |
| 系统 | `GET /api/system/health` | 健康检查 |

## 模型文件

确保 `saved_models/` 目录包含:
- `yolov8n-face.pt` - YOLO人脸检测
- `facenet_embeddings.npz` - FaceNet特征
- `facenet_svm.pkl` - SVM分类器

## 常见问题

**PyTorch被降级?**
```powershell
pip uninstall torch torchvision -y
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install facenet-pytorch --no-deps
```

**验证环境:**
```powershell
python -c "import torch; print('CUDA:', torch.cuda.is_available())"
```
