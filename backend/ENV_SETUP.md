# 环境配置说明

## 系统要求

- **操作系统**: Windows 10/11
- **Python**: 3.10
- **CUDA**: 12.1 (根据显卡驱动版本)
- **包管理器**: Conda + Pip

---

## 快速安装步骤

### 1. 创建Conda环境

```powershell
# 创建Python 3.10环境
conda create -n emotion_attendance python=3.10 -y

# 激活环境
conda activate emotion_attendance
```

### 2. 安装PyTorch (CUDA 12.1)

⚠️ **重要**: Windows系统需要根据CUDA版本安装对应的PyTorch

```powershell
# 安装CUDA 12.1版本的PyTorch
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

**验证PyTorch安装:**
```powershell
python -c "import torch; print('PyTorch版本:', torch.__version__); print('CUDA可用:', torch.cuda.is_available()); print('CUDA版本:', torch.version.cuda)"
```

预期输出:
```
PyTorch版本: 2.x.x+cu121
CUDA可用: True
CUDA版本: 12.1
```

### 3. 安装facenet-pytorch

⚠️ **已知问题**: 直接安装`facenet-pytorch`可能会降级PyTorch版本

**解决方案:**

```powershell
# 方法1: 指定不降级依赖 (推荐)
pip install facenet-pytorch --no-deps
pip install requests  # facenet-pytorch需要的依赖

# 如果PyTorch已被降级,重新安装正确版本
pip uninstall torch torchvision -y
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install facenet-pytorch --no-deps
```

**验证facenet-pytorch:**
```powershell
python -c "from facenet_pytorch import InceptionResnetV1; print('✓ facenet-pytorch安装成功')"
```

### 4. 安装其他核心依赖

```powershell
# 使用conda安装基础包(速度更快)
conda install numpy pandas scikit-learn pillow -c conda-forge -y

# 使用pip安装其余依赖
pip install opencv-python>=4.8.0
pip install ultralytics>=8.0.0
pip install mediapipe>=0.10.0
pip install Flask>=3.0.0
pip install Flask-CORS>=4.0.0
pip install flask-sqlalchemy>=3.0.0
pip install SQLAlchemy>=2.0.0
pip install python-dotenv>=1.0.0
pip install openpyxl>=3.1.0
pip install tqdm
```

### 5. 完整验证

```powershell
# 验证所有核心依赖
python -c "import torch; import cv2; import numpy; import sklearn; import flask; from facenet_pytorch import InceptionResnetV1; from ultralytics import YOLO; import mediapipe; print('✓ 所有依赖安装成功!')"
```

---

## 常见问题与解决方案

### ❌ 问题1: PyTorch被facenet-pytorch降级

**现象:**
```
安装facenet-pytorch后,torch版本从2.x.x+cu121降级为2.x.x+cpu
```

**解决:**
```powershell
# 1. 卸载现有PyTorch
pip uninstall torch torchvision torchaudio -y

# 2. 重新安装CUDA 12.1版本
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 3. 安装facenet-pytorch时不安装依赖
pip install facenet-pytorch --no-deps
```

### ❌ 问题2: CUDA版本不匹配

**检查你的CUDA版本:**
```powershell
nvidia-smi
```

根据输出选择对应版本:
- CUDA 11.8: `https://download.pytorch.org/whl/cu118`
- CUDA 12.1: `https://download.pytorch.org/whl/cu121`
- 仅CPU: `pip install torch torchvision`

### ❌ 问题3: opencv-python安装失败

```powershell
# 尝试安装headless版本
pip install opencv-python-headless
```

### ❌ 问题4: mediapipe安装失败

```powershell
# 确保Python版本在3.8-3.11之间
python --version

# 升级pip
python -m pip install --upgrade pip

# 重试安装
pip install mediapipe --upgrade
```

### ❌ 问题5: ultralytics依赖冲突

```powershell
# 先安装ultralytics需要的核心依赖
pip install pyyaml>=5.3.1
pip install matplotlib>=3.3.0
pip install ultralytics
```

---

## 环境测试

### 测试1: PyTorch GPU加速

```powershell
python -c "import torch; x = torch.rand(5, 3).cuda(); print('GPU测试通过:', x.device)"
```

### 测试2: 配置系统

```powershell
cd e:\school\sophomore\python\emotion_attendence_system\final\emotion_attendance_v2\backend
python config/settings.py
```

### 测试3: YOLO检测

```powershell
cd train/train_yolo
python -c "from ultralytics import YOLO; model = YOLO('yolov8n.pt'); print('✓ YOLO加载成功')"
```

### 测试4: FaceNet

```powershell
python -c "from facenet_pytorch import InceptionResnetV1; model = InceptionResnetV1(pretrained='vggface2'); print('✓ FaceNet加载成功')"
```

### 测试5: MediaPipe

```powershell
python -c "import mediapipe as mp; face_mesh = mp.solutions.face_mesh; print('✓ MediaPipe加载成功')"
```

---

## 完整依赖清单

### 深度学习框架
- ✅ torch>=2.0.0+cu121
- ✅ torchvision>=0.15.0+cu121
- ✅ facenet-pytorch>=2.5.3
- ✅ ultralytics>=8.0.0

### 机器学习
- ✅ scikit-learn>=1.3.0
- ✅ numpy>=1.24.0
- ✅ pandas>=2.0.0

### 图像处理
- ✅ opencv-python>=4.8.0
- ✅ Pillow>=10.0.0
- ✅ mediapipe>=0.10.0

### Web框架
- ✅ Flask>=3.0.0
- ✅ Flask-CORS>=4.0.0
- ✅ flask-sqlalchemy>=3.0.0
- ✅ SQLAlchemy>=2.0.0

### 工具库
- ✅ python-dotenv>=1.0.0
- ✅ openpyxl>=3.1.0
- ✅ tqdm

---

## 环境管理

### 导出环境配置

```powershell
# 导出pip依赖
pip freeze > requirements_installed.txt

# 导出conda环境
conda env export > environment_installed.yml
```

### 在其他机器复现环境

```powershell
# 创建环境
conda create -n emotion_attendance python=3.10 -y
conda activate emotion_attendance

# 安装PyTorch (CUDA 12.1)
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 安装facenet-pytorch (不降级)
pip install facenet-pytorch --no-deps

# 安装其他依赖
pip install -r requirements.txt
```

### 删除环境

```powershell
conda deactivate
conda remove -n emotion_attendance --all -y
```

---

## 性能优化建议

### 1. 使用国内镜像源 (可选)

**Pip镜像 (清华源):**
```powershell
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

**Conda镜像:**
```powershell
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free
conda config --set show_channel_urls yes
```

### 2. CUDA优化

确保安装了最新的NVIDIA驱动:
```powershell
nvidia-smi
```

### 3. 内存优化

如果GPU内存不足,可以在训练时减小batch_size:
- YOLO训练: `batch_size=8` 或 `batch_size=4`
- PyTorch情感训练: `batch_size=16`

---

## 下一步

环境配置完成后,可以开始:

1. **测试配置**: `python config/settings.py`
2. **查看训练指南**: 参考各模块的`README.md`
3. **准备数据**: 收集人脸和情感数据
4. **开始训练**: 按YOLO → FaceNet → 情感识别的顺序

---

## 技术支持

遇到问题时:

1. 检查Python版本: `python --version`
2. 检查PyTorch版本: `python -c "import torch; print(torch.__version__)"`
3. 检查CUDA: `python -c "import torch; print(torch.cuda.is_available())"`
4. 查看错误日志并根据上述常见问题排查

---

**最后更新**: 2025年11月18日  
**测试环境**: Windows 11, Python 3.10, CUDA 12.1
