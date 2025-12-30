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

> 权限说明：🔓游客(无需登录) | 👤普通用户 | 👑管理员

### 管理员认证 `admin_auth.py` → `/api/admin`
| 接口 | 权限 | 说明 |
|------|------|------|
| `POST /login` | 🔓游客 | 管理员登录 |
| `POST /logout` | 👑管理员 | 管理员登出 |
| `GET /me` | 👑管理员 | 获取当前管理员信息 |
| `PUT /profile` | 👑管理员 | 修改管理员用户名 |
| `PUT /password` | 👑管理员 | 修改管理员密码 |
| `GET /login-logs` | 👑管理员 | 查看登录日志 |

### 用户认证 `user_auth.py` → `/api/auth`
| 接口 | 权限 | 说明 |
|------|------|------|
| `POST /login` | 🔓游客 | 普通用户登录 |
| `POST /logout` | 👤普通用户 | 普通用户登出 |
| `GET /me` | 👤普通用户 | 获取当前用户信息 |
| `PUT /password` | 👤普通用户 | 修改用户密码 |
| `POST /set-password` | 🔓游客 | 首次设置密码(需验证用户名) |
| `POST /check-password` | 🔓游客 | 检查用户是否已设置密码 |

### 用户管理 `user.py` → `/api/users`
| 接口 | 权限 | 说明 |
|------|------|------|
| `GET /` | 🔓游客 | 获取用户列表 |
| `GET /:id` | 🔓游客 | 获取用户详情 |
| `POST /register` | 👑管理员 | 注册新用户(含人脸采集) |
| `PUT /:id` | 👑管理员 | 更新用户信息 |
| `DELETE /:id` | 👑管理员 | 删除用户 |
| `POST /:id/faces` | 👑管理员 | 更新用户人脸数据 |
| `GET /statistics` | 👑管理员 | 获取用户统计 |
| `PUT /profile` | 👤普通用户 | 修改个人信息(手机/邮箱) |

### 考勤管理 `attendance.py` → `/api/attendance`
| 接口 | 权限 | 说明 |
|------|------|------|
| `POST /preview` | 🔓游客 | 人脸识别预览(不记录) |
| `POST /check-in` | 🔓游客 | 考勤打卡 |
| `GET /history` | 🔓游客 | 获取考勤历史 |
| `GET /user/:id` | 👤普通用户 | 获取本人考勤记录 |
| `GET /today` | 🔓游客 | 获取今日考勤 |
| `GET /export` | 🔓游客 | 导出考勤CSV |
| `DELETE /:id` | 🔓游客 | 删除考勤记录 |

### 考勤规则 `attendance_rule.py` → `/api/attendance-rules`
| 接口 | 权限 | 说明 |
|------|------|------|
| `GET /` | 👑管理员 | 获取所有规则 |
| `GET /:id` | 👑管理员 | 获取规则详情 |
| `GET /default` | 🔓游客 | 获取默认规则 |
| `GET /department/:id` | 🔓游客 | 获取部门规则 |
| `GET /user/:id` | 🔓游客 | 获取用户规则 |
| `POST /` | 👑管理员 | 创建规则 |
| `PUT /:id` | 👑管理员 | 更新规则 |
| `DELETE /:id` | 👑管理员 | 删除规则 |
| `GET /conflicts` | 👑管理员 | 检查规则冲突 |
| `POST /check` | 🔓游客 | 检查打卡状态 |

### 部门管理 `department.py` → `/api/departments`
| 接口 | 权限 | 说明 |
|------|------|------|
| `GET /` | 👑管理员 | 获取部门列表(支持树形) |
| `GET /:id` | 👑管理员 | 获取部门详情 |
| `POST /` | 👑管理员 | 创建部门 |
| `PUT /:id` | 👑管理员 | 更新部门 |
| `DELETE /:id` | 👑管理员 | 删除部门 |
| `GET /:id/users` | 👑管理员 | 获取部门成员 |
| `GET /search` | 👑管理员 | 搜索部门 |

### 统计分析 `statistics.py` → `/api/statistics`
| 接口 | 权限 | 说明 |
|------|------|------|
| `GET /daily` | 🔓游客 | 每日统计 |
| `GET /weekly` | 🔓游客 | 每周统计 |
| `GET /monthly` | 🔓游客 | 每月统计 |
| `GET /user/:id` | 🔓游客 | 用户个人统计 |

### 定时任务 `scheduler.py` → `/api/scheduler`
| 接口 | 权限 | 说明 |
|------|------|------|
| `POST /trigger-absence-check` | 👑管理员 | 手动触发缺勤检测 |
| `GET /status` | 👑管理员 | 获取定时任务状态 |
| `POST /config` | 👑管理员 | 更新缺勤检测时间配置 |

### 日志管理 `log.py` → `/api/log`
| 接口 | 权限 | 说明 |
|------|------|------|
| `GET /admin/login-logs` | 👑管理员 | 获取登录日志 |
| `GET /system-logs` | 👑管理员 | 获取系统日志 |
| `GET /login-statistics` | 👑管理员 | 登录统计 |
| `GET /system-log-statistics` | 👑管理员 | 系统日志统计 |
| `POST /cleanup` | 👑管理员 | 清理旧日志 |

### 视频流 `video.py` → `/api/video`
| 接口 | 权限 | 说明 |
|------|------|------|
| `GET /feed` | 🔓游客 | 获取实时视频流 |

### 系统管理 `system.py` → `/api/system`
| 接口 | 权限 | 说明 |
|------|------|------|
| `GET /health` | 🔓游客 | 健康检查 |
| `GET /models` | 🔓游客 | 模型加载状态 |
| `GET /logs` | 🔓游客 | 获取系统日志 |
| `GET /config` | 🔓游客 | 获取系统配置 |

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

## 数据模型（7张表）

| 模型 | 表名 | 说明 |
|------|------|------|
| `User` | `user` | 用户信息 |
| `Admin` | `admin` | 管理员账号 |
| `Department` | `department` | 部门（树形） |
| `AttendanceRule` | `attendance_rule` | 考勤规则 |
| `Attendance` | `attendance` | 打卡记录 |
| `AdminLoginLog` | `admin_login_log` | 登录日志 |
| `SystemLog` | `system_log` | 系统日志 |

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
