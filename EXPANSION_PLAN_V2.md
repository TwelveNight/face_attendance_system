# 人脸识别考勤系统扩展计划 V3.0

## 📋 需求调整说明

### 核心理念（最终版）
**双重登录模式**
- 👥 **普通用户**：需要登录，可以查看个人考勤、申请请假/补卡
- 🎯 **每日打卡**：无需登录，人脸识别自动打卡（唯一的游客功能）
- 👨‍💼 **管理员**：需要登录，管理用户、审批、配置系统

### 权限对比
| 功能 | 普通用户 | 管理员 |
|------|---------|--------|
| 每日打卡 | ✅ 无需登录 | ✅ 无需登录 |
| 查看个人考勤 | ✅ 需登录 | ✅ 需登录 |
| 申请请假/补卡 | ✅ 需登录 | ✅ 需登录 |
| 查看所有用户 | ❌ | ✅ |
| 录入/修改/删除用户 | ❌ | ✅ |
| 审批请假/补卡 | ❌ | ✅ |
| 配置考勤规则 | ❌ | ✅ |
| 部门管理 | ❌ | ✅ |
| 系统配置 | ❌ | ✅ |

### 优先级调整
- ✅ **P0（高优先级）**：阶段1-4 必须实现
- ✅ **P1（中优先级）**：阶段5-6 建议实现
- ❌ **暂不实现**：通知系统、移动端

### 测试便利性
- ✅ 管理员可以配置"开放打卡模式"（不限制打卡时间）
- ✅ 管理员可以灵活调整考勤规则用于测试

---

## 🗄️ 数据库设计（8张新表）

### 1. admin - 管理员表
```sql
CREATE TABLE admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '管理员用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    real_name VARCHAR(50) COMMENT '真实姓名',
    email VARCHAR(100) UNIQUE COMMENT '邮箱',
    phone VARCHAR(20) COMMENT '手机号',
    is_super TINYINT(1) DEFAULT 0 COMMENT '是否超级管理员',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    last_login_at DATETIME COMMENT '最后登录时间',
    last_login_ip VARCHAR(50) COMMENT '最后登录IP',
    created_at DATETIME NOT NULL,
    updated_at DATETIME,
    INDEX idx_username (username)
) COMMENT='管理员表';

-- 默认管理员账号（密码: admin123）
INSERT INTO admin (username, password_hash, real_name, is_super, is_active, created_at) 
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7TLKkkVppe', '系统管理员', 1, 1, NOW());
```

### 2. admin_login_log - 管理员登录日志
```sql
CREATE TABLE admin_login_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL,
    login_time DATETIME NOT NULL,
    login_ip VARCHAR(50),
    user_agent TEXT,
    login_status VARCHAR(20) DEFAULT 'success',
    FOREIGN KEY (admin_id) REFERENCES admin(id),
    INDEX idx_admin_id (admin_id)
);
```

### 3. department - 部门表
```sql
CREATE TABLE department (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE,
    parent_id INT,
    manager_id INT,
    level INT DEFAULT 1,
    is_active TINYINT(1) DEFAULT 1,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES department(id),
    FOREIGN KEY (manager_id) REFERENCES user(id)
);
```

### 4. attendance_rule - 考勤规则表
```sql
CREATE TABLE attendance_rule (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '规则名称',
    work_start_time TIME NOT NULL COMMENT '上班时间',
    work_end_time TIME NOT NULL COMMENT '下班时间',
    late_threshold INT DEFAULT 0 COMMENT '迟到阈值(分钟)',
    early_threshold INT DEFAULT 0 COMMENT '早退阈值(分钟)',
    work_days VARCHAR(20) DEFAULT '1,2,3,4,5' COMMENT '工作日(1-7)',
    department_id INT COMMENT '适用部门',
    is_default TINYINT(1) DEFAULT 0 COMMENT '是否默认规则',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    is_open_mode TINYINT(1) DEFAULT 0 COMMENT '是否开放模式(不限制打卡时间)',
    created_at DATETIME NOT NULL,
    updated_at DATETIME,
    FOREIGN KEY (department_id) REFERENCES department(id),
    INDEX idx_is_default (is_default),
    INDEX idx_is_open_mode (is_open_mode)
) COMMENT='考勤规则表';

-- 默认规则：9:00-18:00，迟到15分钟，早退15分钟
INSERT INTO attendance_rule (name, work_start_time, work_end_time, late_threshold, early_threshold, work_days, is_default, is_active, is_open_mode, created_at)
VALUES ('默认考勤规则', '09:00:00', '18:00:00', 15, 15, '1,2,3,4,5', 1, 1, 0, NOW());

-- 测试规则：开放模式，不限制打卡时间
INSERT INTO attendance_rule (name, work_start_time, work_end_time, late_threshold, early_threshold, work_days, is_default, is_active, is_open_mode, created_at)
VALUES ('测试模式(开放打卡)', '00:00:00', '23:59:59', 0, 0, '1,2,3,4,5,6,7', 0, 0, 1, NOW());
```

### 5. holiday - 节假日表
```sql
CREATE TABLE holiday (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    date DATE NOT NULL UNIQUE,
    type VARCHAR(20) DEFAULT 'holiday',
    is_workday TINYINT(1) DEFAULT 0,
    created_at DATETIME NOT NULL,
    INDEX idx_date (date)
);
```

### 6. leave_request - 请假申请表
```sql
CREATE TABLE leave_request (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    leave_type VARCHAR(20) NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    duration FLOAT NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    approver_id INT,
    approved_at DATETIME,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (approver_id) REFERENCES admin(id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);
```

### 7. makeup_request - 补卡申请表
```sql
CREATE TABLE makeup_request (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    makeup_date DATE NOT NULL,
    makeup_time TIME NOT NULL,
    type VARCHAR(20) NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    approver_id INT,
    approved_at DATETIME,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (approver_id) REFERENCES admin(id),
    INDEX idx_user_id (user_id)
);
```

### 8. system_config - 系统配置表
```sql
CREATE TABLE system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    config_type VARCHAR(20) DEFAULT 'string',
    category VARCHAR(50),
    description TEXT,
    updated_at DATETIME,
    INDEX idx_config_key (config_key)
);
```

---

## 🔄 现有表修改

### user 表（添加登录和部门字段）
```sql
ALTER TABLE user 
ADD COLUMN password_hash VARCHAR(255) COMMENT '用户密码哈希(用于登录)',
ADD COLUMN department_id INT COMMENT '所属部门',
ADD COLUMN position VARCHAR(50) COMMENT '职位',
ADD COLUMN email VARCHAR(100) COMMENT '邮箱',
ADD COLUMN phone VARCHAR(20) COMMENT '手机号',
ADD COLUMN entry_date DATE COMMENT '入职日期',
ADD COLUMN last_login_at DATETIME COMMENT '最后登录时间',
ADD COLUMN updated_at DATETIME COMMENT '更新时间',
ADD CONSTRAINT fk_user_department FOREIGN KEY (department_id) REFERENCES department(id);

CREATE INDEX idx_email ON user(email);
CREATE INDEX idx_phone ON user(phone);
```

**说明**：
- `password_hash`：普通用户登录密码（用于查看个人考勤、申请请假等）
- 普通用户登录后可以查看个人信息、申请请假/补卡
- 打卡功能无需登录，直接人脸识别

### attendance 表
```sql
ALTER TABLE attendance
ADD COLUMN check_type VARCHAR(20) DEFAULT 'checkin',
ADD COLUMN is_late TINYINT(1) DEFAULT 0,
ADD COLUMN is_early TINYINT(1) DEFAULT 0,
ADD COLUMN is_makeup TINYINT(1) DEFAULT 0,
ADD COLUMN rule_id INT,
ADD CONSTRAINT fk_attendance_rule FOREIGN KEY (rule_id) REFERENCES attendance_rule(id);
```

---

## 📐 实施步骤（详细版）

### 🔴 阶段一：双重认证系统（3-4天）⭐ 核心
**目标**：实现管理员和普通用户的登录系统

#### 数据库层
1. 创建 `admin` 表（管理员）
2. 创建 `admin_login_log` 表（管理员登录日志）
3. 修改 `user` 表，添加 `password_hash` 字段（普通用户登录）
4. 插入默认管理员账号

#### 后端层
1. **安装依赖**
```bash
pip install Flask-JWT-Extended==4.5.3
pip install bcrypt==4.1.2
```

2. **实现管理员认证**
- `POST /api/admin/login` - 管理员登录
- `POST /api/admin/logout` - 管理员登出
- `GET /api/admin/me` - 获取当前管理员信息
- `PUT /api/admin/password` - 修改管理员密码

3. **实现普通用户认证**
- `POST /api/auth/login` - 普通用户登录
- `POST /api/auth/logout` - 普通用户登出
- `GET /api/auth/me` - 获取当前用户信息
- `PUT /api/auth/password` - 修改用户密码

4. **JWT Token 中间件**
- 管理员权限装饰器 `@admin_required`
- 普通用户权限装饰器 `@user_required`
- 可选登录装饰器 `@optional_auth`（打卡功能）

#### 前端层
1. **新增页面**
- 管理员登录页面 (`/admin/login`)
- 普通用户登录页面 (`/login`)
- 个人中心页面 (`/profile`)

2. **路由守卫**
- 管理员路由守卫（用户管理、审批等）
- 普通用户路由守卫（个人考勤、请假申请等）
- 公开路由（打卡页面）

3. **状态管理**
- 管理员状态（Zustand）
- 普通用户状态（Zustand）
- Token 自动刷新

**交付物**：
- ✅ 管理员可以登录/登出
- ✅ 普通用户可以登录/登出
- ✅ 打卡功能无需登录
- ✅ 权限控制完善

---

### 🔴 阶段二：部门管理（2天）⭐
**目标**：实现部门层级管理

#### 数据库层
1. 创建 `department` 表
2. 修改 `user` 表，添加 `department_id` 字段

#### 后端层
1. **部门管理 API（管理员权限）**
```python
GET    /api/departments          # 获取部门列表（树形）
GET    /api/departments/:id      # 获取部门详情
POST   /api/departments          # 创建部门
PUT    /api/departments/:id      # 更新部门
DELETE /api/departments/:id      # 删除部门
GET    /api/departments/:id/users # 获取部门用户
```

2. **部门树形结构**
- 递归查询子部门
- 部门层级计算

#### 前端层
1. **新增页面**
- 部门管理页面 (`/admin/departments`) - 管理员
- 部门树形展示（Ant Design Tree）

2. **用户管理集成**
- 用户表单添加部门选择
- 用户列表显示部门信息
- 按部门筛选

**交付物**：
- ✅ 部门层级管理
- ✅ 用户归属部门

---

### 🔴 阶段三：考勤规则管理（3-4天）⭐ 核心
**目标**：实现灵活的考勤规则配置，支持测试模式

#### 数据库层
1. 创建 `attendance_rule` 表（包含 `is_open_mode` 字段）
2. 创建 `holiday` 表
3. 修改 `attendance` 表，添加规则相关字段
4. 插入默认规则和测试规则

#### 后端层
1. **考勤规则 API（管理员权限）**
```python
GET    /api/attendance-rules     # 获取规则列表
POST   /api/attendance-rules     # 创建规则
PUT    /api/attendance-rules/:id # 更新规则
DELETE /api/attendance-rules/:id # 删除规则
PUT    /api/attendance-rules/:id/activate   # 激活规则
PUT    /api/attendance-rules/:id/deactivate # 停用规则
```

2. **节假日 API（管理员权限）**
```python
GET    /api/holidays             # 获取节假日列表
POST   /api/holidays             # 添加节假日
DELETE /api/holidays/:id         # 删除节假日
POST   /api/holidays/batch       # 批量导入节假日
```

3. **考勤判定逻辑**
- 修改打卡服务，应用考勤规则
- 检查是否开放模式（`is_open_mode`）
- 如果是开放模式，跳过时间限制
- 否则，自动判定迟到/早退/缺勤
- 节假日识别

#### 前端层
1. **新增页面**
- 考勤规则管理页面 (`/admin/attendance-rules`) - 管理员
- 节假日管理页面 (`/admin/holidays`) - 管理员

2. **规则配置界面**
- 规则表单（时间、阈值、工作日）
- 开放模式开关（用于测试）
- 规则激活/停用
- 默认规则设置

3. **打卡页面增强**
- 显示当前应用的规则
- 显示是否迟到/早退
- 开放模式提示

**交付物**：
- ✅ 考勤规则配置
- ✅ 开放打卡模式（测试用）
- ✅ 自动判定考勤状态
- ✅ 节假日管理

---

### 🔴 阶段四：请假与补卡管理（3天）⭐
**目标**：实现请假和补卡申请审批流程

#### 数据库层
1. 创建 `leave_request` 表
2. 创建 `makeup_request` 表

#### 后端层
1. **请假 API**
```python
# 普通用户
GET    /api/leave-requests/my    # 获取我的请假列表
POST   /api/leave-requests       # 申请请假
DELETE /api/leave-requests/:id   # 取消请假申请

# 管理员
GET    /api/leave-requests       # 获取所有请假列表
PUT    /api/leave-requests/:id/approve  # 批准请假
PUT    /api/leave-requests/:id/reject   # 拒绝请假
```

2. **补卡 API**
```python
# 普通用户
GET    /api/makeup-requests/my   # 获取我的补卡列表
POST   /api/makeup-requests      # 申请补卡

# 管理员
GET    /api/makeup-requests      # 获取所有补卡列表
PUT    /api/makeup-requests/:id/approve # 批准补卡
PUT    /api/makeup-requests/:id/reject  # 拒绝补卡
```

#### 前端层
1. **普通用户页面**
- 请假申请页面 (`/leave-request`)
- 补卡申请页面 (`/makeup-request`)
- 我的申请列表 (`/my-requests`)

2. **管理员页面**
- 审批管理页面 (`/admin/approvals`)
- 待审批列表
- 审批历史

**交付物**：
- ✅ 请假申请功能
- ✅ 补卡申请功能
- ✅ 管理员审批功能
- ✅ 审批通知

---

### 🟡 阶段五：高级统计与报表（3天）
**目标**：多维度统计和数据导出

#### 后端层
1. **统计 API**
```python
# 普通用户
GET /api/statistics/my           # 我的考勤统计

# 管理员
GET /api/statistics/personal/:user_id  # 个人考勤统计
GET /api/statistics/department/:dept_id # 部门考勤统计
GET /api/statistics/monthly      # 月度统计
GET /api/statistics/abnormal     # 异常考勤统计
GET /api/statistics/export       # 导出报表
```

2. **报表导出**
- 安装 `openpyxl`
- 生成考勤月报
- 生成部门汇总表

#### 前端层
1. **统计页面**
- 个人考勤统计（普通用户）
- 全局统计（管理员）
- 部门排名
- 异常考勤列表
- 导出按钮

**交付物**：
- ✅ 多维度统计
- ✅ Excel 导出

---

### 🟡 阶段六：系统配置管理（2天）
**目标**：动态系统配置

#### 数据库层
1. 创建 `system_config` 表

#### 后端层
1. **配置 API（管理员权限）**
```python
GET    /api/system-config       # 获取配置列表
PUT    /api/system-config/:key  # 更新配置
```

#### 前端层
1. **系统设置页面**
- 系统设置页面 (`/admin/settings`) - 管理员
- 人脸识别参数
- 考勤参数
- 系统信息

**交付物**：
- ✅ 系统参数配置

---

## ⏱️ 总时间：16-20天

## 🎯 核心特性总结

### 1. 双重登录模式
- 管理员登录：管理系统
- 普通用户登录：查看个人信息、申请请假
- 打卡无需登录：人脸识别自动打卡

### 2. 灵活的考勤规则
- 正常模式：严格考勤规则
- 开放模式：不限制打卡时间（测试用）
- 管理员可随时切换

### 3. 完整的审批流程
- 请假申请
- 补卡申请
- 管理员审批

---

## ✅ 下一步：请确认后开始实施！

**确认内容**：
1. ✅ 双重登录模式是否符合需求？
2. ✅ 开放打卡模式是否满足测试需求？
3. ✅ 数据表设计是否合理？
4. ✅ 实施步骤是否可行？
