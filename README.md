# 人脸识别考勤系统

基于 YOLO + FaceNet 的智能考勤系统，支持人脸识别打卡、考勤规则管理、自动缺勤检测、统计分析。

## 快速开始

```bash
# 后端 (Python 3.10+ / MySQL 5.7+ / CUDA 12.1可选)
cd backend
pip install -r requirements.txt
python run.py                    # http://localhost:8088

# 前端 (Node.js 16+)
cd frontend
npm install && npm start         # http://localhost:3000
```

**默认账号**: 管理员 `admin / admin123` | 用户需先注册

## 技术栈

### 前端
- **框架**: React 18 + TypeScript
- **UI组件**: Ant Design 5
- **状态管理**: Zustand
- **HTTP客户端**: Axios
- **路由**: React Router 6

### 后端
- **框架**: Flask 2.x
- **ORM**: SQLAlchemy
- **认证**: JWT (flask-jwt-extended)
- **定时任务**: APScheduler
- **密码加密**: bcrypt

### AI模型
- **人脸检测**: YOLO v8 (yolov8n-face.pt)
- **人脸识别**: FaceNet (InceptionResnetV1)
- **深度学习**: PyTorch 2.x
- **图像处理**: OpenCV 4.x

### 数据库
- **类型**: MySQL 5.7+
- **字符集**: UTF8MB4
- **数据表**: 8张

## 项目结构

```
face_attendance_system/
├── backend/                    # 后端服务
│   ├── run.py                 # 启动入口
│   ├── api/routes/            # API路由
│   │   ├── admin_auth.py      # 管理员认证
│   │   ├── user_auth.py       # 用户认证
│   │   ├── attendance.py      # 考勤打卡
│   │   ├── attendance_rule.py # 考勤规则
│   │   ├── department.py      # 部门管理
│   │   ├── statistics.py      # 统计分析
│   │   └── scheduler.py       # 定时任务
│   ├── services/              # 业务逻辑层
│   ├── database/              # 数据模型 & 仓库
│   ├── models/                # AI模型 (YOLO/FaceNet)
│   ├── config/                # 配置 (.env)
│   └── saved_models/          # 训练好的模型文件
│
├── frontend/src/              # 前端应用
│   ├── pages/                 # 页面组件
│   │   ├── AdminLogin/        # 管理员登录
│   │   ├── UserLogin/         # 用户登录
│   │   ├── Dashboard/         # 仪表盘
│   │   ├── Attendance/        # 人脸打卡
│   │   ├── MyAttendance/      # 我的考勤
│   │   ├── History/           # 考勤历史
│   │   ├── Statistics/        # 统计分析
│   │   ├── Users/             # 用户管理
│   │   ├── Departments/       # 部门管理
│   │   ├── AttendanceRules/   # 考勤规则
│   │   ├── SystemLog/         # 系统日志
│   │   └── Profile/           # 个人中心
│   ├── api/                   # API客户端 (Axios)
│   ├── store/                 # 状态管理 (Zustand)
│   └── components/            # 公共组件
```

## 核心功能

| 功能 | 说明 |
|------|------|
| 人脸识别打卡 | 实时检测识别，自动判断上班/下班 |
| 考勤规则管理 | 部门规则、默认规则、开放模式、打卡时间窗口 |
| 自动缺勤检测 | 定时任务（每天23:00），区分上班/下班缺勤 |
| 统计分析 | 16个指标，多维度筛选，可视化展示 |
| 报表导出 | 个人月报、全员考勤、统计报表（CSV） |
| 部门管理 | 树形结构，多级嵌套 |
| 权限控制 | 管理员/用户双端，JWT认证 |

## 数据库

`user` · `admin` · `department` · `attendance_rule` · `attendance` · `admin_login_log` · `system_log`

---

**版本**: v3.0 | **状态**: ✅ 已完成
