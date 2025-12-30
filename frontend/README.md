# 前端应用

## 快速开始

```powershell
# 安装依赖
npm install

# 启动开发服务器
npm run dev  # http://localhost:3000

# 生产构建
npm run build
```

---

## 目录结构

```
frontend/
├── index.html             # HTML入口
├── vite.config.ts         # Vite配置
├── package.json           # 依赖配置
├── tsconfig.json          # TypeScript配置
│
└── src/
    ├── main.tsx           # 应用入口
    ├── App.tsx            # 根组件（路由配置）
    ├── App.css            # 全局样式
    │
    ├── pages/             # 页面组件（14个）
    ├── components/        # 公共组件
    ├── api/               # API客户端
    ├── store/             # 状态管理（Zustand）
    ├── types/             # TypeScript类型定义
    └── utils/             # 工具函数
```

---

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 框架 | React | 19.x |
| 语言 | TypeScript | 5.x |
| 构建工具 | Vite | 7.x |
| UI组件库 | Ant Design | 5.x |
| 状态管理 | Zustand | 5.x |
| HTTP客户端 | Axios | 1.x |
| 路由 | React Router | 7.x |
| 日期处理 | Day.js | 1.x |
| 图标 | @ant-design/icons | 6.x |

---

## 页面组件

### 登录页面（独立路由）

| 页面 | 路由 | 说明 |
|------|------|------|
| `AdminLogin` | `/admin/login` | 管理员登录 |
| `UserLogin` | `/login` | 用户登录 |
| `SetPassword` | `/set-password` | 首次设置密码 |

### 公开页面

| 页面 | 路由 | 说明 |
|------|------|------|
| `Attendance` | `/attendance` | 人脸打卡（摄像头实时检测） |

### 用户页面（需用户登录）

| 页面 | 路由 | 说明 |
|------|------|------|
| `MyAttendance` | `/my-attendance` | 我的考勤记录、个人月报导出 |
| `Profile` | `/profile` | 个人信息、修改密码 |

### 管理员页面（需管理员登录）

| 页面 | 路由 | 说明 |
|------|------|------|
| `Dashboard` | `/dashboard` | 仪表盘（统计概览） |
| `Users` | `/users` | 用户管理（CRUD、人脸采集） |
| `Departments` | `/departments` | 部门管理（树形结构） |
| `AttendanceRules` | `/attendance-rules` | 考勤规则配置 |
| `History` | `/history` | 考勤历史查询、导出 |
| `Statistics` | `/statistics` | 统计分析、报表导出 |
| `SystemLog` | `/system-log` | 系统日志查询 |

---

## 公共组件

| 组件 | 路径 | 说明 |
|------|------|------|
| `MainLayout` | `components/Layout/` | 主布局（侧边栏、头部、内容区） |
| `PrivateRoute` | `components/PrivateRoute.tsx` | 路由守卫（AdminRoute、UserRoute） |
| `FaceCapture` | `components/FaceCapture/` | 人脸采集组件 |

---

## 状态管理（Zustand）

| Store | 文件 | 状态 |
|-------|------|------|
| `authStore` | `store/authStore.ts` | 认证状态（token、用户信息、登录/登出） |
| `userStore` | `store/userStore.ts` | 用户列表管理 |
| `attendanceStore` | `store/attendanceStore.ts` | 考勤记录管理 |

### authStore 主要方法

```typescript
interface AuthStore {
  token: string | null;
  userType: 'admin' | 'user' | null;
  currentUser: User | null;
  currentAdmin: Admin | null;
  
  adminLogin(username, password): Promise<void>;
  userLogin(username, password): Promise<void>;
  logout(): void;
  isAdmin(): boolean;
  isUser(): boolean;
}
```

---

## API客户端

### 文件结构

| 文件 | 说明 |
|------|------|
| `api/client.ts` | Axios封装、所有API接口定义 |
| `api/log.ts` | 日志相关API |

### API模块

```typescript
// client.ts 导出的API对象
export const authApi = { ... }           // 用户认证
export const adminAuthApi = { ... }      // 管理员认证
export const userApi = { ... }           // 用户管理
export const attendanceApi = { ... }     // 考勤打卡
export const attendanceRuleApi = { ... } // 考勤规则
export const departmentApi = { ... }     // 部门管理
export const statisticsApi = { ... }     // 统计分析
export const systemApi = { ... }         // 系统接口
```

### 请求拦截器

- 自动添加 `Authorization: Bearer <token>` 头
- 401响应自动跳转登录页

---

## 类型定义

### 主要类型 (`types/index.ts`)

```typescript
interface User {
  id: number;
  username: string;
  student_id: string;
  department_id?: number;
  is_active: boolean;
}

interface Attendance {
  id: number;
  user_id: number;
  timestamp: string;
  status: 'present' | 'late' | 'absent';
  check_type: 'checkin' | 'checkout';
  is_late: boolean;
  is_early: boolean;
}

interface AttendanceRule {
  id: number;
  name: string;
  work_start_time: string;
  work_end_time: string;
  late_threshold: number;
  is_open_mode: boolean;
}

interface Department {
  id: number;
  name: string;
  parent_id?: number;
  children?: Department[];
}
```

---

## 路由守卫

### AdminRoute
- 检查 `authStore.isAdmin()`
- 未登录或非管理员 → 跳转 `/admin/login`

### UserRoute
- 检查 `authStore.isUser()` 或 `authStore.isAdmin()`
- 未登录 → 跳转 `/login`

---

## 关键功能实现

### 人脸打卡 (`Attendance/index.tsx`)

```
1. 开启摄像头 → 获取视频流
2. 实时预览 → 每500ms调用 /api/attendance/preview
3. 显示识别结果 → 用户名、置信度、预计状态
4. 点击打卡 → 调用 /api/attendance/check-in
5. 显示打卡结果 → 成功/失败/迟到/早退
```

### 用户注册 (`Users/index.tsx`)

```
1. 填写用户信息 → 用户名、学号、部门
2. 开启摄像头 → 采集人脸
3. 采集10张人脸图像 → 调用 /api/users/register
4. 后端训练FaceNet → 注册完成
```

### 统计分析 (`Statistics/index.tsx`)

```
1. 选择日期范围、部门 → 筛选条件
2. 调用统计API → 获取16个指标
3. 可视化展示 → Statistic、Progress组件
4. 导出报表 → CSV格式下载
```

---

## 环境配置

### 开发环境 (`.env.development`)

```
VITE_API_BASE_URL=http://localhost:8088
```

### 生产环境

在 `vite.config.ts` 中配置代理或修改环境变量

---

## 常用命令

```powershell
npm run dev      # 启动开发服务器
npm run build    # 生产构建
npm run preview  # 预览生产构建
npm run lint     # ESLint检查
```

---

## 样式说明

- 使用 Ant Design 5 组件库
- 主题色: `#1890ff`
- 中文语言包: `antd/locale/zh_CN`
- 响应式布局: Ant Design Grid系统
