# 认证系统 API 文档

## 📋 概述

系统实现了双重认证机制：
- **管理员认证**：用于管理系统、审批等功能
- **普通用户认证**：用于查看个人信息、申请请假等功能
- **打卡功能**：无需登录，直接人脸识别

## 🔐 认证流程

### 1. 登录获取Token
```
POST /api/admin/login  (管理员)
POST /api/auth/login   (普通用户)
```

### 2. 使用Token访问受保护的API
```
Authorization: Bearer <token>
```

### 3. Token有效期
- 默认24小时
- 过期后需要重新登录

## 📡 API 接口

### 管理员认证 API

#### 1. 管理员登录
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
  "success": true,
  "message": "登录成功",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "admin": {
      "id": 1,
      "username": "admin",
      "real_name": "系统管理员",
      "email": null,
      "is_super": true,
      "is_active": true,
      "last_login_at": "2025-11-19T10:30:00"
    }
  }
}
```

#### 2. 获取当前管理员信息
```http
GET /api/admin/me
Authorization: Bearer <token>
```

**响应**：
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "admin",
    "real_name": "系统管理员",
    ...
  }
}
```

#### 3. 修改管理员密码
```http
PUT /api/admin/password
Authorization: Bearer <token>
Content-Type: application/json

{
  "old_password": "admin123",
  "new_password": "newpassword123"
}
```

#### 4. 管理员登出
```http
POST /api/admin/logout
Authorization: Bearer <token>
```

#### 5. 获取登录日志
```http
GET /api/admin/login-logs?page=1&per_page=20
Authorization: Bearer <token>
```

---

### 普通用户认证 API

#### 1. 用户登录
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "zhangsan",  // 或使用student_id
  "password": "password123"
}
```

**响应**：
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
      "id": 1,
      "username": "zhangsan",
      "student_id": "20210001",
      "department_id": null,
      "position": null,
      ...
    }
  }
}
```

#### 2. 获取当前用户信息
```http
GET /api/auth/me
Authorization: Bearer <token>
```

#### 3. 修改用户密码
```http
PUT /api/auth/password
Authorization: Bearer <token>
Content-Type: application/json

{
  "old_password": "oldpassword",
  "new_password": "newpassword123"
}
```

#### 4. 首次设置密码
```http
POST /api/auth/set-password
Content-Type: application/json

{
  "username": "zhangsan",
  "student_id": "20210001",  // 用于验证身份
  "new_password": "password123"
}
```

**说明**：新注册的用户默认没有密码，需要先设置密码才能登录

#### 5. 检查密码状态
```http
POST /api/auth/check-password
Content-Type: application/json

{
  "username": "zhangsan"
}
```

**响应**：
```json
{
  "success": true,
  "data": {
    "has_password": true,
    "username": "zhangsan",
    "student_id": "20210001"
  }
}
```

#### 6. 用户登出
```http
POST /api/auth/logout
Authorization: Bearer <token>
```

---

## 🛡️ 权限装饰器

### 1. @admin_required
只有管理员可以访问

```python
from utils.auth import admin_required

@app.route('/api/admin/users')
@admin_required
def get_all_users(current_admin):
    # current_admin 包含管理员信息
    admin_id = current_admin['user_id']
    is_super = current_admin['is_super']
    ...
```

### 2. @user_required
需要登录（管理员或普通用户）

```python
from utils.auth import user_required

@app.route('/api/profile')
@user_required
def get_profile(current_user):
    # current_user 包含用户信息
    user_id = current_user['user_id']
    user_type = current_user['user_type']  # 'admin' 或 'user'
    ...
```

### 3. @optional_auth
可选认证（如打卡功能）

```python
from utils.auth import optional_auth

@app.route('/api/attendance/checkin')
@optional_auth
def checkin(current_user):
    # current_user 可能为 None（未登录）或包含用户信息
    if current_user:
        user_id = current_user['user_id']
    ...
```

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

## ⚠️ 错误处理

### 常见错误码

| 状态码 | 说明 | 处理方式 |
|--------|------|----------|
| 400 | 请求参数错误 | 检查请求体格式 |
| 401 | 未授权/Token无效 | 重新登录获取Token |
| 403 | 权限不足 | 检查用户权限 |
| 404 | 资源不存在 | 检查用户是否存在 |
| 500 | 服务器错误 | 查看服务器日志 |

### 错误响应格式

```json
{
  "success": false,
  "message": "用户名或密码错误",
  "error": "详细错误信息"
}
```

---

## 🔒 安全建议

1. **HTTPS**: 生产环境必须使用HTTPS
2. **密码强度**: 建议密码至少8位，包含大小写字母和数字
3. **Token存储**: 前端使用localStorage或sessionStorage存储Token
4. **Token刷新**: Token过期前自动刷新（可选）
5. **登出清理**: 登出时清除本地存储的Token

---

## 🧪 测试

运行测试脚本：
```bash
python backend/test_auth.py
```

测试内容：
- ✅ 管理员登录
- ✅ 获取管理员信息
- ✅ 检查用户密码状态
- ✅ 未授权访问（应返回401）
- ✅ 错误密码（应返回401）

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

## 🔄 迁移现有用户

如果系统中已有用户但没有密码，可以：

1. **方式一**：用户自己设置
   - 调用 `/api/auth/set-password` 接口
   - 提供用户名和学号验证身份

2. **方式二**：管理员批量设置
   ```python
   from utils.auth import AuthUtils
   from database.models import db, User
   
   # 为所有用户设置默认密码
   users = User.query.filter_by(password_hash=None).all()
   for user in users:
       user.password_hash = AuthUtils.hash_password('default123')
   db.session.commit()
   ```

---

## 📚 相关文件

- `backend/utils/auth.py` - 认证工具类
- `backend/api/routes/admin_auth.py` - 管理员认证API
- `backend/api/routes/user_auth.py` - 普通用户认证API
- `backend/test_auth.py` - 认证测试脚本
