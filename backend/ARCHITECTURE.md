# 后端架构文档

## 目录结构

```
backend/
├── run.py                 # 启动入口
├── requirements.txt       # Python依赖
│
├── api/                   # API层
│   ├── app.py            # Flask应用工厂
│   ├── middleware.py     # 中间件（响应格式、错误处理）
│   └── routes/           # 路由模块
│
├── services/              # 业务逻辑层
├── database/              # 数据访问层
├── models/                # AI模型层
├── utils/                 # 工具函数
├── config/                # 配置管理
├── saved_models/          # 模型文件
└── logs/                  # 日志文件
```

---

## API层 (`api/`)

### 应用入口 (`app.py`)
- Flask应用工厂模式 `create_app()`
- 初始化：数据库、JWT、CORS、定时任务
- 注册所有路由蓝图

### 中间件 (`middleware.py`)
- `success_response()` - 统一成功响应格式
- `error_response()` - 统一错误响应格式
- `@require_json` - JSON请求验证装饰器

### 路由模块 (`routes/`)

| 文件 | 路由前缀 | 功能 |
|------|----------|------|
| `admin_auth.py` | `/api/admin` | 管理员登录、信息、修改密码 |
| `user_auth.py` | `/api/auth` | 用户登录、注册、信息、修改密码 |
| `user.py` | `/api/users` | 用户CRUD、人脸采集、头像上传 |
| `attendance.py` | `/api/attendance` | 打卡、预览、历史、导出 |
| `attendance_rule.py` | `/api/attendance-rules` | 考勤规则CRUD、状态检查 |
| `department.py` | `/api/departments` | 部门CRUD、树形结构、统计 |
| `statistics.py` | `/api/statistics` | 考勤统计、报表导出 |
| `scheduler.py` | `/api/scheduler` | 定时任务状态、手动触发 |
| `log.py` | `/api/log` | 系统日志查询 |
| `video.py` | `/api/video` | 实时视频流 |
| `system.py` | `/api/system` | 健康检查、模型状态 |

---

## 业务逻辑层 (`services/`)

| 文件 | 类 | 职责 |
|------|------|------|
| `face_service.py` | `FaceService` | 人脸检测、识别、特征提取、注册 |
| `user_service.py` | `UserService` | 用户管理、密码处理、头像管理 |
| `attendance_service.py` | `AttendanceService` | 打卡处理、历史查询、CSV导出 |
| `attendance_rule_service.py` | `AttendanceRuleService` | 规则管理、迟到/早退判定、打卡类型判断 |
| `department_service.py` | `DepartmentService` | 部门CRUD、树形构建、人数统计 |
| `scheduler_service.py` | `SchedulerService` | 定时任务（缺勤检测）、APScheduler管理 |
| `log_service.py` | `LogService` | 系统日志记录、数据库写入 |
| `log_service_simple.py` | `SimpleLogService` | 简化日志服务 |

### 关键业务流程

#### 打卡流程 (`AttendanceService.check_in`)
```
1. 接收图像 → 2. YOLO检测人脸 → 3. FaceNet识别用户
4. 获取用户考勤规则 → 5. 判断打卡类型（上班/下班）
6. 检查打卡限制 → 7. 判定迟到/早退 → 8. 保存记录
```

#### 缺勤检测流程 (`SchedulerService`)
```
每天23:00执行:
1. 获取所有启用用户 → 2. 遍历用户考勤规则
3. 检查是否工作日 → 4. 检查上班打卡记录
5. 检查下班打卡记录 → 6. 生成缺勤记录
```

---

## 数据访问层 (`database/`)

### 数据模型 (`models.py`)

| 模型 | 表名 | 说明 |
|------|------|------|
| `User` | `user` | 用户信息、密码、部门关联 |
| `Admin` | `admin` | 管理员账号 |
| `Department` | `department` | 部门（树形结构，自引用） |
| `AttendanceRule` | `attendance_rule` | 考勤规则配置 |
| `Attendance` | `attendance` | 考勤打卡记录 |
| `AdminLoginLog` | `admin_login_log` | 管理员登录日志 |
| `SystemLog` | `system_log` | 系统操作日志 |
| `Holiday` | `holiday` | 节假日配置 |

### 数据仓库 (`repositories.py`)

| 仓库 | 方法 |
|------|------|
| `UserRepository` | `get_all()`, `get_by_id()`, `get_by_username()`, `create()`, `update()`, `delete()` |
| `AttendanceRepository` | `create()`, `get_by_user()`, `get_today()`, `get_history()` |
| `DepartmentRepository` | `get_all()`, `get_tree()`, `create()`, `update()`, `delete()` |

### 日志模型 (`log_models.py`)
- 独立的日志数据库模型定义

---

## AI模型层 (`models/`)

### YOLO人脸检测 (`yolo_face_detector.py`)

```python
class YOLOFaceDetector:
    def detect_faces(image) -> List[Dict]
    # 返回: [{"bbox": [x1,y1,x2,y2], "confidence": 0.95}, ...]
```

- 模型文件: `saved_models/yolov8n-face.pt`
- 置信度阈值: 0.5

### FaceNet人脸识别 (`facenet_recognizer.py`)

```python
class FaceNetRecognizer:
    def get_embedding(face_image) -> np.ndarray      # 提取512维特征
    def register_face(user_id, embeddings)           # 注册人脸
    def recognize(embedding) -> (user_id, confidence) # 识别人脸
    def delete_user(user_id)                         # 删除用户特征
```

- 模型: InceptionResnetV1 (pretrained='vggface2')
- 特征文件: `saved_models/facenet_embeddings.npz`
- 分类器: `saved_models/facenet_svm.pkl`
- 识别阈值: 0.6

### 模型管理器 (`model_manager.py`)

```python
class ModelManager:  # 单例模式
    yolo_detector: YOLOFaceDetector
    facenet_recognizer: FaceNetRecognizer
```

- 统一管理模型加载
- 避免重复加载模型
- GPU/CPU自动选择

---

## 工具层 (`utils/`)

### 认证工具 (`auth.py`)

| 装饰器/函数 | 说明 |
|-------------|------|
| `@admin_required` | 需要管理员JWT认证 |
| `@user_required` | 需要用户JWT认证 |
| `@login_required` | 需要任意JWT认证 |
| `get_current_admin()` | 获取当前管理员 |
| `get_current_user()` | 获取当前用户 |

### 日志工具 (`log_helper.py`)
- 系统日志记录辅助函数

---

## 配置层 (`config/`)

### 配置文件 (`settings.py`)

```python
class Config:
    # 数据库
    DATABASE_URI = "mysql+pymysql://..."
    
    # JWT
    SECRET_KEY = "..."
    
    # CORS
    CORS_ORIGINS = ["http://localhost:3000"]
    
    # AI模型
    YOLO_THRESHOLD = 0.5
    FACE_RECOGNITION_THRESHOLD = 0.6
    REGISTER_FACE_COUNT = 10
    
    # GPU
    USE_CUDA = True
```

### 环境变量 (`.env`)
- 敏感配置通过 `.env` 文件管理
- 模板文件: `.env.template`

---

## 定时任务

### 缺勤检测任务
- **触发时间**: 每天 23:00
- **任务ID**: `absence_check`
- **逻辑**: 检查当天未打卡的用户，生成缺勤记录

### 手动触发
```
POST /api/scheduler/trigger-absence-check
```

---

## 启动流程

```
python run.py
    │
    ├── create_app()
    │   ├── 初始化Flask
    │   ├── 配置数据库 (SQLAlchemy)
    │   ├── 配置JWT (flask-jwt-extended)
    │   ├── 配置CORS
    │   ├── 注册路由蓝图
    │   └── 初始化定时任务 (APScheduler)
    │
    └── app.run(host, port)
        └── 监听 http://0.0.0.0:8088
```

---

## 请求响应格式

### 成功响应
```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

### 错误响应
```json
{
  "code": 400,
  "message": "错误信息",
  "error": "详细错误"
}
```

### 分页响应
```json
{
  "code": 200,
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "per_page": 20,
    "pages": 5
  }
}
```

---

## 依赖关系图

```
routes/ ──→ services/ ──→ database/repositories.py
   │            │                    │
   │            ▼                    ▼
   │       models/ ◄──────── database/models.py
   │            │
   ▼            ▼
middleware ◄── utils/auth.py
```

**调用顺序**: 路由 → 服务 → 仓库 → 数据库
