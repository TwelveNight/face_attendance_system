# 人脸识别考勤系统实施计划

## 项目概述

基于YOLO人脸检测和FaceNet人脸识别的考勤系统，前后端分离架构。

**训练模块状态**: ✅ 已完成
- YOLO人脸检测训练
- FaceNet人脸识别训练

**待实现**: 后端API + 前端界面

---

## 第一阶段: 后端核心模块 (3-4天)

### 步骤1: 配置与数据库 (0.5天)

#### 1.1 配置管理
- [x] `backend/config/settings.py` - 统一配置
- [ ] `backend/config/.env.example` - 环境变量模板

#### 1.2 数据库模型
- [ ] `backend/database/models.py` - ORM模型
  ```python
  - User: id, username, student_id, created_at, avatar_path
  - Attendance: id, user_id, timestamp, status, image_path
  - SystemLog: id, event_type, message, timestamp
  ```
- [ ] `backend/database/repositories.py` - 数据访问层
- [ ] `backend/database/init_db.py` - 数据库初始化

### 步骤2: 模型推理封装 (1天)

#### 2.1 模型管理器
- [ ] `backend/models/__init__.py`
- [ ] `backend/models/yolo_face_detector.py` - YOLO推理
  - `detect_faces(image) -> List[BoundingBox]`
  - 加载模型: `saved_models/yolov8n-face.pt`
  
- [ ] `backend/models/facenet_recognizer.py` - FaceNet推理
  - `extract_embedding(face_image) -> np.ndarray`
  - `recognize(embedding) -> (user_id, confidence)`
  - 加载模型: `facenet_embeddings.npz`, `facenet_svm.pkl`
  
- [ ] `backend/models/model_manager.py` - 单例管理器
  - 预加载所有模型
  - GPU内存管理

### 步骤3: 业务服务层 (1天)

#### 3.1 人脸服务
- [ ] `backend/services/face_service.py`
  - `detect_and_recognize(frame) -> (user_id, bbox, confidence)`
  - `register_user_face(username, student_id, images) -> success`
  - `update_user_face(user_id, images) -> success`

#### 3.2 用户服务
- [ ] `backend/services/user_service.py`
  - `create_user(username, student_id) -> User`
  - `get_all_users() -> List[User]`
  - `get_user(user_id) -> User`
  - `delete_user(user_id) -> success`
  - `search_users(keyword) -> List[User]`

#### 3.3 考勤服务
- [ ] `backend/services/attendance_service.py`
  - `check_in(user_id, image) -> Attendance`
  - `get_attendance_history(filters) -> List[Attendance]`
  - `get_user_attendance(user_id, date_range) -> List[Attendance]`
  - `get_daily_statistics(date) -> Stats`
  - `export_to_csv(date_range) -> file_path`

### 步骤4: Flask API (1-1.5天)

#### 4.1 应用初始化
- [ ] `backend/api/__init__.py`
- [ ] `backend/api/app.py` - Flask应用
  - CORS配置
  - 错误处理
  - 日志配置
  
- [ ] `backend/api/middleware.py`
  - 请求日志
  - 异常处理
  - 响应格式化

#### 4.2 API路由

**用户管理** - `backend/api/routes/user.py`
- [ ] `POST /api/users/register` - 注册用户(含人脸采集)
- [ ] `GET /api/users` - 获取用户列表(分页、搜索)
- [ ] `GET /api/users/:id` - 获取用户详情
- [ ] `PUT /api/users/:id` - 更新用户信息
- [ ] `DELETE /api/users/:id` - 删除用户
- [ ] `POST /api/users/:id/faces` - 更新用户人脸

**考勤管理** - `backend/api/routes/attendance.py`
- [ ] `POST /api/attendance/check-in` - 打卡(上传图片)
- [ ] `GET /api/attendance/history` - 考勤历史(分页、筛选)
- [ ] `GET /api/attendance/user/:id` - 用户考勤记录
- [ ] `GET /api/attendance/export` - 导出CSV

**统计分析** - `backend/api/routes/statistics.py`
- [ ] `GET /api/statistics/daily` - 每日统计
- [ ] `GET /api/statistics/weekly` - 周统计
- [ ] `GET /api/statistics/monthly` - 月统计
- [ ] `GET /api/statistics/user/:id` - 用户考勤趋势

**视频流** - `backend/api/routes/video.py`
- [ ] `GET /api/video/feed` - 实时视频流(MJPEG)
- [ ] `POST /api/video/snapshot` - 拍照识别

**系统管理** - `backend/api/routes/system.py`
- [ ] `GET /api/system/health` - 健康检查
- [ ] `GET /api/system/models` - 模型状态
- [ ] `GET /api/system/logs` - 系统日志

---

## 第二阶段: 前端界面 (3-4天)

### 步骤5: 项目初始化 (0.5天)

#### 5.1 创建项目
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

#### 5.2 安装依赖
```bash
npm install antd zustand axios dayjs
npm install @ant-design/icons @ant-design/charts
npm install react-router-dom
```

#### 5.3 配置文件
- [ ] `vite.config.ts` - Vite配置(代理、别名)
- [ ] `tsconfig.json` - TypeScript配置
- [ ] `.env.development` - 开发环境变量

### 步骤6: 基础架构 (1天)

#### 6.1 类型定义 - `src/types/`
- [ ] `user.ts` - 用户类型
- [ ] `attendance.ts` - 考勤类型
- [ ] `api.ts` - API响应类型

#### 6.2 API客户端 - `src/api/`
- [ ] `client.ts` - Axios封装(拦截器、错误处理)
- [ ] `user.ts` - 用户API
- [ ] `attendance.ts` - 考勤API
- [ ] `statistics.ts` - 统计API
- [ ] `system.ts` - 系统API

#### 6.3 状态管理 - `src/store/`
- [ ] `userStore.ts` - 用户状态
  ```typescript
  - users: User[]
  - currentUser: User | null
  - fetchUsers, createUser, deleteUser
  ```
  
- [ ] `attendanceStore.ts` - 考勤状态
  ```typescript
  - records: Attendance[]
  - statistics: Stats
  - fetchRecords, checkIn
  ```
  
- [ ] `systemStore.ts` - 系统状态
  ```typescript
  - loading, error, message
  - modelStatus, systemHealth
  ```

### 步骤7: 核心组件 (1.5天)

#### 7.1 布局组件 - `src/components/Layout/`
- [ ] `MainLayout.tsx` - 主布局(侧边栏+顶栏)
- [ ] `Sidebar.tsx` - 侧边导航
- [ ] `Header.tsx` - 顶部栏

#### 7.2 仪表盘 - `src/components/Dashboard/`
- [ ] `Dashboard.tsx` - 仪表盘主页
- [ ] `StatCard.tsx` - 统计卡片
- [ ] `QuickActions.tsx` - 快捷操作

#### 7.3 打卡组件 - `src/components/AttendanceCard/`
- [ ] `AttendanceCard.tsx` - 打卡卡片
- [ ] `VideoStream.tsx` - 摄像头视频流
- [ ] `FaceDetection.tsx` - 人脸检测框显示

### 步骤8: 功能页面 (1天)

#### 8.1 用户管理 - `src/pages/UserManagement/`
- [ ] `UserList.tsx` - 用户列表(表格、搜索)
- [ ] `UserForm.tsx` - 用户表单(新增/编辑)
- [ ] `FaceCapture.tsx` - 人脸采集组件

#### 8.2 考勤历史 - `src/pages/AttendanceHistory/`
- [ ] `AttendanceHistory.tsx` - 历史记录
- [ ] `AttendanceTable.tsx` - 考勤表格(分页、筛选)
- [ ] `AttendanceFilter.tsx` - 筛选器

#### 8.3 统计分析 - `src/pages/Statistics/`
- [ ] `Statistics.tsx` - 统计页面
- [ ] `DailyChart.tsx` - 每日统计图表
- [ ] `TrendChart.tsx` - 趋势图
- [ ] `UserRanking.tsx` - 用户排行

### 步骤9: 路由与集成 (0.5天)

#### 9.1 路由配置
- [ ] `src/router/index.tsx` - 路由配置
  ```
  / - Dashboard
  /attendance - 打卡页面
  /users - 用户管理
  /history - 考勤历史
  /statistics - 统计分析
  /settings - 系统设置
  ```

#### 9.2 主应用
- [ ] `src/App.tsx` - 应用入口
- [ ] `src/main.tsx` - 渲染入口
- [ ] 全局样式配置

---

## 第三阶段: 测试与优化 (1-2天)

### 步骤10: 功能测试
- [ ] 用户注册流程测试
- [ ] 人脸识别准确性测试
- [ ] 考勤打卡流程测试
- [ ] 数据导出功能测试
- [ ] 视频流性能测试

### 步骤11: 优化
- [ ] 前端性能优化(懒加载、代码分割)
- [ ] 后端响应时间优化
- [ ] 错误处理完善
- [ ] 用户体验优化

### 步骤12: 文档
- [ ] API文档
- [ ] 部署文档
- [ ] 用户手册

---

## 技术栈总结

### 后端
- **框架**: Flask 2.3+
- **数据库**: SQLite + SQLAlchemy
- **深度学习**: PyTorch, Ultralytics YOLO, FaceNet
- **图像处理**: OpenCV, Pillow
- **其他**: Flask-CORS, python-dotenv

### 前端
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI库**: Ant Design 5
- **状态管理**: Zustand
- **HTTP**: Axios
- **路由**: React Router v6
- **图表**: Ant Design Charts
- **工具**: dayjs

---

## API设计规范

### 请求格式
```json
{
  "data": { ... }
}
```

### 响应格式
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

---

## 数据库设计

### User表
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    student_id VARCHAR(20) UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    avatar_path VARCHAR(255),
    face_embedding_path VARCHAR(255)
);
```

### Attendance表
```sql
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'present',
    confidence FLOAT,
    image_path VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

### SystemLog表
```sql
CREATE TABLE system_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type VARCHAR(50),
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 开发顺序

1. ✅ **训练模块** (已完成)
2. **后端开发** (当前)
   - 配置 → 数据库 → 模型 → 服务 → API
3. **前端开发**
   - 初始化 → 架构 → 组件 → 页面 → 集成
4. **测试优化**
   - 功能测试 → 性能优化 → 文档

---

## 时间估算

- **后端核心**: 3-4天
- **前端界面**: 3-4天
- **测试优化**: 1-2天
- **总计**: 7-10天

---

**开始日期**: 2025年11月18日
**当前阶段**: 后端开发
**优先级**: 后端API → 前端界面 → 测试优化
