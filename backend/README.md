# 后端服务

## 快速开始

```powershell
# 1. 创建环境
conda create -n face_attendance python=3.10 -y
conda activate face_attendance

# 2. 安装依赖
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install facenet-pytorch --no-deps
pip install -r requirements.txt

# 3. 配置数据库
cp config/.env.template config/.env
# 编辑 .env 配置MySQL连接

# 4. 启动服务
python run.py  # http://localhost:8088
```

---

## 目录结构

```
backend/
├── run.py                 # 启动入口
├── requirements.txt       # Python依赖
├── api/                   # API层
│   ├── app.py            # Flask应用工厂
│   ├── middleware.py     # 中间件（响应格式、错误处理）
│   └── routes/           # 路由模块（11个）
├── services/              # 业务逻辑层（8个服务）
├── database/              # 数据访问层
│   ├── models.py         # ORM模型（8张表）
│   └── repositories.py   # 数据仓库
├── models/                # AI模型层
│   ├── yolo_face_detector.py    # YOLO人脸检测
│   ├── facenet_recognizer.py    # FaceNet人脸识别
│   └── model_manager.py         # 模型管理器（单例）
├── utils/                 # 工具函数
│   └── auth.py           # JWT认证装饰器
├── config/                # 配置
│   ├── settings.py       # 配置类
│   └── .env              # 环境变量
├── saved_models/          # 模型文件
└── logs/                  # 日志
```

---

## API路由

| 文件 | 路由前缀 | 功能 |
|------|----------|------|
| `admin_auth.py` | `/api/admin` | 管理员登录、信息、修改密码 |
| `user_auth.py` | `/api/auth` | 用户登录、注册、修改密码 |
| `user.py` | `/api/users` | 用户CRUD、人脸采集 |
| `attendance.py` | `/api/attendance` | 打卡、预览、历史、导出 |
| `attendance_rule.py` | `/api/attendance-rules` | 考勤规则CRUD |
| `department.py` | `/api/departments` | 部门CRUD、树形结构 |
| `statistics.py` | `/api/statistics` | 考勤统计、报表导出 |
| `scheduler.py` | `/api/scheduler` | 定时任务管理 |
| `log.py` | `/api/log` | 系统日志查询 |
| `video.py` | `/api/video` | 实时视频流 |
| `system.py` | `/api/system` | 健康检查、模型状态 |

---

## 业务服务层

| 服务 | 职责 |
|------|------|
| `FaceService` | 人脸检测、识别、特征提取、注册 |
| `UserService` | 用户管理、密码处理 |
| `AttendanceService` | 打卡处理、历史查询、CSV导出 |
| `AttendanceRuleService` | 规则管理、迟到/早退判定 |
| `DepartmentService` | 部门CRUD、树形构建 |
| `SchedulerService` | 定时任务（缺勤检测） |
| `LogService` | 系统日志记录 |

---

## 数据模型（8张表）

| 模型 | 表名 | 说明 |
|------|------|------|
| `User` | `user` | 用户信息 |
| `Admin` | `admin` | 管理员账号 |
| `Department` | `department` | 部门（树形） |
| `AttendanceRule` | `attendance_rule` | 考勤规则 |
| `Attendance` | `attendance` | 打卡记录 |
| `AdminLoginLog` | `admin_login_log` | 管理员登录日志 |
| `SystemLog` | `system_log` | 系统日志 |
| `Holiday` | `holiday` | 节假日 |

---

## AI模型

### YOLO人脸检测
- 模型: `saved_models/yolov8n-face.pt`
- 阈值: 0.5

### FaceNet人脸识别
- 模型: InceptionResnetV1 (vggface2)
- 特征: `saved_models/facenet_embeddings.npz`
- 分类器: `saved_models/facenet_svm.pkl`
- 阈值: 0.6

---

## 关键流程

### 打卡流程
```
图像 → YOLO检测 → FaceNet识别 → 获取规则 → 判断类型 → 检查限制 → 判定状态 → 保存
```

### 缺勤检测（每天23:00）
```
获取用户 → 遍历规则 → 检查工作日 → 检查打卡 → 生成缺勤记录
```

---

## 请求响应格式

```json
// 成功
{"code": 200, "message": "success", "data": {...}}

// 错误
{"code": 400, "message": "错误信息", "error": "详情"}

// 分页
{"code": 200, "data": {"items": [], "total": 100, "page": 1, "pages": 5}}
```

---

## 认证

| 装饰器 | 说明 |
|--------|------|
| `@admin_required` | 需要管理员JWT |
| `@user_required` | 需要用户JWT |
| `@login_required` | 需要任意JWT |

---

## 常见问题

**PyTorch被降级?**
```powershell
pip uninstall torch torchvision -y
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install facenet-pytorch --no-deps
```

**验证CUDA:**
```powershell
python -c "import torch; print('CUDA:', torch.cuda.is_available())"
```
