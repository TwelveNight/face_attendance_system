# 人脸识别考勤系统 API 文档

## 📋 概述

本文档描述了人脸识别考勤系统的所有后端API接口。

**基础URL**: `http://localhost:8088`

**认证方式**: JWT Token (Bearer)

**响应格式**: JSON

---

## 🔐 认证系统

### 双重认证机制
- **管理员认证**：用于管理系统、审批等功能
- **普通用户认证**：用于查看个人信息、修改联系方式等功能
- **打卡功能**：无需登录，直接人脸识别

### Token使用
```http
Authorization: Bearer <token>
```

### Token有效期
- 默认24小时
- 过期后需要重新登录

---

## 📡 API 接口列表

### 1. 管理员认证 (`/api/admin`)

#### 1.1 管理员登录
```http
POST /api/admin/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**响应**：
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "admin": {
      "id": 1,
      "username": "admin",
      "real_name": "系统管理员",
      "email": null,
      "is_super": true,
      "is_active": true
    }
  }
}
```

#### 1.2 获取当前管理员信息
```http
GET /api/admin/me
Authorization: Bearer <token>
```

#### 1.3 修改管理员密码
```http
PUT /api/admin/password
Authorization: Bearer <token>
Content-Type: application/json

{
  "old_password": "admin123",
  "new_password": "newpassword123"
}
```

#### 1.4 管理员登出
```http
POST /api/admin/logout
Authorization: Bearer <token>
```

#### 1.5 获取登录日志
```http
GET /api/admin/login-logs?page=1&per_page=20
Authorization: Bearer <token>
```

---

### 2. 普通用户认证 (`/api/auth`)

#### 2.1 用户登录
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "zhangsan",
  "password": "password123"
}
```

#### 2.2 获取当前用户信息
```http
GET /api/auth/me
Authorization: Bearer <token>
```

#### 2.3 修改用户密码
```http
PUT /api/auth/password
Authorization: Bearer <token>
Content-Type: application/json

{
  "old_password": "oldpassword",
  "new_password": "newpassword123"
}
```

#### 2.4 首次设置密码
```http
POST /api/auth/set-password
Content-Type: application/json

{
  "username": "zhangsan",
  "student_id": "20210001",
  "new_password": "password123"
}
```

#### 2.5 检查密码状态
```http
POST /api/auth/check-password
Content-Type: application/json

{
  "username": "zhangsan"
}
```

#### 2.6 用户登出
```http
POST /api/auth/logout
Authorization: Bearer <token>
```

---

### 3. 用户管理 (`/api/users`)

#### 3.1 获取用户列表
```http
GET /api/users?keyword=&active_only=true
```

#### 3.2 获取用户详情
```http
GET /api/users/{user_id}
```

#### 3.3 注册用户
```http
POST /api/users/register
Content-Type: application/json

{
  "username": "zhangsan",
  "student_id": "20210001",
  "face_images": ["base64_image1", "base64_image2", ...]
}
```

#### 3.4 更新用户信息（管理员）
```http
PUT /api/users/{user_id}
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "department_id": 1,
  "position": "员工",
  "email": "user@example.com",
  "phone": "13800138000",
  "password": "newpassword"
}
```

#### 3.5 更新个人信息（普通用户）
```http
PUT /api/users/profile
Authorization: Bearer <user_token>
Content-Type: application/json

{
  "phone": "13800138000",
  "email": "user@example.com"
}
```

#### 3.6 更新用户人脸
```http
POST /api/users/{user_id}/faces
Content-Type: application/json

{
  "face_images": ["base64_image1", "base64_image2", ...]
}
```

#### 3.7 删除用户
```http
DELETE /api/users/{user_id}?hard=true
Authorization: Bearer <admin_token>
```

#### 3.8 用户统计
```http
GET /api/users/statistics
```

---

### 4. 考勤管理 (`/api/attendance`)

#### 4.1 实时识别预览（不保存）
```http
POST /api/attendance/preview
Content-Type: application/json

{
  "image": "base64_encoded_image"
}
```

#### 4.2 人脸打卡
```http
POST /api/attendance/checkin
Content-Type: application/json

{
  "image": "base64_encoded_image",
  "check_type": "checkin"  // 或 "checkout"
}
```

#### 4.3 获取考勤历史
```http
GET /api/attendance/history?start_date=2025-12-01&end_date=2025-12-31&user_id=1&page=1&per_page=20
```

#### 4.4 获取考勤详情
```http
GET /api/attendance/{attendance_id}
```

#### 4.5 更新考勤记录（管理员）
```http
PUT /api/attendance/{attendance_id}
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "status": "present",
  "notes": "备注信息"
}
```

#### 4.6 删除考勤记录（管理员）
```http
DELETE /api/attendance/{attendance_id}
Authorization: Bearer <admin_token>
```

#### 4.7 批量导出考勤记录
```http
POST /api/attendance/export
Content-Type: application/json

{
  "start_date": "2025-12-01",
  "end_date": "2025-12-31",
  "user_ids": [1, 2, 3]
}
```

---

### 5. 考勤规则 (`/api/attendance-rules`)

#### 5.1 获取规则列表
```http
GET /api/attendance-rules?include_inactive=false
```

#### 5.2 获取规则详情
```http
GET /api/attendance-rules/{rule_id}
```

#### 5.3 获取用户的考勤规则
```http
GET /api/attendance-rules/user/{user_id}
```

#### 5.4 创建考勤规则（管理员）
```http
POST /api/attendance-rules
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "标准工作日",
  "work_start_time": "09:00:00",
  "work_end_time": "18:00:00",
  "late_threshold": 15,
  "early_threshold": 15,
  "work_days": "0,1,2,3,4",
  "department_id": 1,
  "is_default": false,
  "is_open_mode": false
}
```

#### 5.5 更新考勤规则（管理员）
```http
PUT /api/attendance-rules/{rule_id}
Authorization: Bearer <admin_token>
Content-Type: application/json
```

#### 5.6 删除考勤规则（管理员）
```http
DELETE /api/attendance-rules/{rule_id}
Authorization: Bearer <admin_token>
```

#### 5.7 设置默认规则（管理员）
```http
POST /api/attendance-rules/{rule_id}/set-default
Authorization: Bearer <admin_token>
```

#### 5.8 批量分配规则（管理员）
```http
POST /api/attendance-rules/{rule_id}/assign
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "user_ids": [1, 2, 3]
}
```

#### 5.9 获取规则统计
```http
GET /api/attendance-rules/{rule_id}/statistics
```

---

### 6. 部门管理 (`/api/departments`)

#### 6.1 获取部门列表
```http
GET /api/departments?tree=true&include_inactive=false
```

#### 6.2 获取部门详情
```http
GET /api/departments/{dept_id}
```

#### 6.3 创建部门（管理员）
```http
POST /api/departments
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "技术部",
  "parent_id": null,
  "description": "技术研发部门"
}
```

#### 6.4 更新部门（管理员）
```http
PUT /api/departments/{dept_id}
Authorization: Bearer <admin_token>
Content-Type: application/json
```

#### 6.5 删除部门（管理员）
```http
DELETE /api/departments/{dept_id}
Authorization: Bearer <admin_token>
```

#### 6.6 获取部门成员
```http
GET /api/departments/{dept_id}/members
```

#### 6.7 获取部门统计
```http
GET /api/departments/{dept_id}/statistics
```

---

### 7. 统计分析 (`/api/statistics`)

#### 7.1 每日统计
```http
GET /api/statistics/daily?date=2025-12-30&department_id=1
```

**响应**：
```json
{
  "code": 200,
  "data": {
    "total": 10,
    "unique_users": 5,
    "total_users": 6,
    "attendance_rate": 83.3,
    "status_distribution": {
      "present": 8,
      "late": 2,
      "absent": 3
    }
  }
}
```

#### 7.2 每周统计
```http
GET /api/statistics/weekly?start_date=2025-12-23&department_id=1
```

#### 7.3 每月统计
```http
GET /api/statistics/monthly?year=2025&month=12&department_id=1
```

#### 7.4 用户统计
```http
GET /api/statistics/user/{user_id}?start_date=2025-12-01&end_date=2025-12-31
```

---

### 8. 系统日志 (`/api/logs`)

#### 8.1 获取操作日志
```http
GET /api/logs/operations?page=1&per_page=20&user_id=1&action=&start_date=2025-12-01
Authorization: Bearer <admin_token>
```

#### 8.2 获取系统日志
```http
GET /api/logs/system?page=1&per_page=20&level=ERROR
Authorization: Bearer <admin_token>
```

#### 8.3 获取登录日志
```http
GET /api/logs/login?page=1&per_page=20&user_id=1
Authorization: Bearer <admin_token>
```

#### 8.4 清理日志（管理员）
```http
DELETE /api/logs/clean?days=30
Authorization: Bearer <admin_token>
```

#### 8.5 导出日志
```http
POST /api/logs/export
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "log_type": "operation",
  "start_date": "2025-12-01",
  "end_date": "2025-12-31"
}
```

---

### 9. 定时任务 (`/api/scheduler`)

#### 9.1 获取任务配置
```http
GET /api/scheduler/config
Authorization: Bearer <admin_token>
```

#### 9.2 更新任务配置
```http
PUT /api/scheduler/config
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "absence_check_time": "23:00"
}
```

#### 9.3 手动触发缺勤检测
```http
POST /api/scheduler/trigger-absence-check
Authorization: Bearer <admin_token>
```

---

### 10. 系统信息 (`/api/system`)

#### 10.1 获取系统信息
```http
GET /api/system/info
```

**响应**：
```json
{
  "code": 200,
  "data": {
    "version": "3.0.0",
    "models_loaded": true,
    "database_connected": true,
    "gpu_available": true
  }
}
```

#### 10.2 健康检查
```http
GET /api/system/health
```

#### 10.3 获取GPU状态
```http
GET /api/system/gpu
```

#### 10.4 重载模型（管理员）
```http
POST /api/system/reload-models
Authorization: Bearer <admin_token>
```

---

### 11. 视频流 (`/api/video`)

#### 11.1 获取视频流
```http
GET /api/video/stream
```

返回MJPEG视频流，用于实时人脸识别预览。

---

## 🛡️ 权限装饰器

### @admin_required
只有管理员可以访问

```python
from utils.auth import admin_required

@app.route('/api/admin/users')
@admin_required
def get_all_users(current_admin):
    admin_id = current_admin['user_id']
    is_super = current_admin['is_super']
    ...
```

### @user_required
需要登录（管理员或普通用户）

```python
from utils.auth import user_required

@app.route('/api/profile')
@user_required
def get_profile(current_user):
    user_id = current_user['user_id']
    user_type = current_user['user_type']
    ...
```

### @optional_auth
可选认证（如打卡功能）

```python
from utils.auth import optional_auth

@app.route('/api/attendance/checkin')
@optional_auth
def checkin(current_user):
    if current_user:
        user_id = current_user['user_id']
    ...
```

---

## 📦 响应格式

### 成功响应
```json
{
  "code": 200,
  "message": "success",
  "data": {...}
}
```

### 错误响应
```json
{
  "code": 400,
  "message": "错误信息",
  "error": "详细错误信息"
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

## ⚠️ 错误码

| 状态码 | 说明 | 处理方式 |
|--------|------|----------|
| 200 | 成功 | - |
| 400 | 请求参数错误 | 检查请求体格式 |
| 401 | 未授权/Token无效 | 重新登录获取Token |
| 403 | 权限不足 | 检查用户权限 |
| 404 | 资源不存在 | 检查资源ID |
| 500 | 服务器错误 | 查看服务器日志 |

---

## 🔒 安全建议

1. **HTTPS**: 生产环境必须使用HTTPS
2. **密码强度**: 建议密码至少6位
3. **Token存储**: 前端使用localStorage或sessionStorage存储Token
4. **Token刷新**: Token过期前自动刷新（可选）
5. **登出清理**: 登出时清除本地存储的Token
6. **CORS配置**: 正确配置跨域资源共享

---

## 🔧 使用示例

### Python (requests)

```python
import requests

BASE_URL = 'http://localhost:8088'

# 1. 管理员登录
response = requests.post(f'{BASE_URL}/api/admin/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = response.json()['data']['token']

# 2. 使用Token访问受保护的API
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(f'{BASE_URL}/api/admin/me', headers=headers)
admin_info = response.json()['data']
```

### JavaScript (Axios)

```javascript
import axios from 'axios';

const BASE_URL = 'http://localhost:8088';

// 1. 管理员登录
const loginResponse = await axios.post(`${BASE_URL}/api/admin/login`, {
  username: 'admin',
  password: 'admin123'
});
const token = loginResponse.data.data.token;

// 2. 设置默认请求头
axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

// 3. 使用Token访问受保护的API
const meResponse = await axios.get(`${BASE_URL}/api/admin/me`);
const adminInfo = meResponse.data.data;
```

---

## 📝 默认账号

### 管理员
- 用户名: `admin`
- 密码: `admin123`

### 普通用户
- 新注册的用户默认没有密码
- 需要先调用 `/api/auth/set-password` 设置密码
- 或由管理员在用户管理界面设置

---

## 📚 相关文件

- `backend/api/routes/` - 所有API路由定义
- `backend/utils/auth.py` - 认证工具类
- `backend/services/` - 业务逻辑层
- `backend/database/` - 数据库模型和仓库

---

## 📞 技术支持

如有问题，请查看：
- 后端日志：`backend/logs/`
- 系统信息：`GET /api/system/info`
- 健康检查：`GET /api/system/health`
