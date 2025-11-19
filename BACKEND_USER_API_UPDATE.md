# 后端用户管理API更新

## 📋 更新内容

### 1. 密码设置功能
在用户更新API中添加密码设置支持。

#### 更新的API
**端点**: `PUT /api/users/:id`

**权限**: 需要管理员权限 (`@admin_required`)

**支持的字段**:
```json
{
  "username": "string",
  "student_id": "string",
  "department_id": "number",
  "position": "string",
  "email": "string",
  "phone": "string",
  "password": "string"  // 新增：设置密码
}
```

### 2. 权限控制增强
为用户管理API添加权限装饰器。

#### 更新的端点
- `PUT /api/users/:id` - 添加 `@admin_required`
- `DELETE /api/users/:id` - 添加 `@admin_required`

---

## 💻 代码更新

### 文件: `backend/api/routes/user.py`

#### 1. 导入认证工具
```python
from utils.auth import AuthUtils, admin_required
```

#### 2. 更新用户信息API
```python
@user_bp.route('/<int:user_id>', methods=['PUT'])
@require_json
@admin_required  # 新增：需要管理员权限
def update_user(user_id):
    """更新用户信息（需要管理员权限）"""
    try:
        data = request.get_json()
        
        # 移除不允许更新的字段
        data.pop('id', None)
        data.pop('created_at', None)
        
        # 处理密码设置（新增）
        if 'password' in data:
            password = data.pop('password')
            if password:
                # 使用bcrypt加密密码
                data['password_hash'] = AuthUtils.hash_password(password)
        
        user = user_service.update_user(user_id, **data)
        
        if not user:
            return error_response("用户不存在", 404)
        
        return success_response(user.to_dict(), "更新成功")
    
    except Exception as e:
        return error_response("更新失败", 500, str(e))
```

#### 3. 删除用户API
```python
@user_bp.route('/<int:user_id>', methods=['DELETE'])
@admin_required  # 新增：需要管理员权限
def delete_user(user_id):
    """删除用户（需要管理员权限，默认硬删除）"""
    # ... 原有代码
```

---

## 🔐 密码处理流程

### 1. 前端发送请求
```javascript
await userApi.updateUser(userId, {
  password: 'newPassword123'
});
```

### 2. 后端处理
```python
# 1. 接收密码
password = data.pop('password')

# 2. 使用bcrypt加密
password_hash = AuthUtils.hash_password(password)

# 3. 存储到数据库
data['password_hash'] = password_hash
user = user_service.update_user(user_id, **data)
```

### 3. 数据库存储
```
password_hash: $2b$12$KIXqLc3yE8rGxZ8vH5F3/.rJ8OqP7jKp5vYx3mXqZ8VqH5F3/.rJ8O
```

---

## 🧪 测试

### 测试脚本
**文件**: `backend/test_user_password.py`

**功能**:
1. ✅ 管理员登录
2. ✅ 获取用户列表
3. ✅ 为用户设置密码
4. ✅ 更新用户其他信息
5. ✅ 测试用户登录
6. ✅ 测试权限控制

### 运行测试
```bash
cd backend
conda activate emotion_attendance
python test_user_password.py
```

### 预期输出
```
============================================================
测试用户密码管理功能
============================================================

1. 管理员登录...
✓ 管理员登录成功
  Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

2. 获取用户列表...
✓ 获取到 3 个用户
  测试用户: ID=1, 用户名=test_user

3. 为用户 test_user 设置密码...
✓ 密码设置成功

4. 更新用户 test_user 的其他信息...
✓ 信息更新成功
  职位/班级: 计算机科学与技术2021级1班
  邮箱: student@example.com
  手机号: 13800138000

5. 测试用户 test_user 登录...
✓ 用户登录成功
  Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

6. 测试未授权删除用户...
✓ 权限控制正常：未授权访问被拒绝

============================================================
测试完成！
============================================================
```

---

## 📊 API权限矩阵

| 端点 | 方法 | 权限要求 | 说明 |
|------|------|----------|------|
| `/api/users` | GET | 无 | 获取用户列表 |
| `/api/users/:id` | GET | 无 | 获取用户详情 |
| `/api/users/register` | POST | 无 | 注册用户 |
| `/api/users/:id` | PUT | **管理员** | 更新用户信息 |
| `/api/users/:id/faces` | POST | 无 | 更新用户人脸 |
| `/api/users/:id` | DELETE | **管理员** | 删除用户 |
| `/api/users/statistics` | GET | 无 | 用户统计 |

---

## 🔒 安全特性

### 1. 密码加密
- ✅ 使用bcrypt算法
- ✅ 每个密码独立的盐
- ✅ 不可逆加密
- ✅ 密码不在日志中显示

### 2. 权限控制
- ✅ 只有管理员可以更新用户
- ✅ 只有管理员可以删除用户
- ✅ Token验证
- ✅ 401/403错误响应

### 3. 数据验证
- ✅ 移除不允许更新的字段（id, created_at）
- ✅ 密码长度验证（前端）
- ✅ 用户存在性检查

---

## 📝 使用示例

### 1. 为用户设置密码
```bash
curl -X PUT http://localhost:8088/api/users/1 \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "newPassword123"
  }'
```

### 2. 更新用户完整信息
```bash
curl -X PUT http://localhost:8088/api/users/1 \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "张三",
    "student_id": "20210001",
    "position": "计算机科学与技术2021级1班",
    "email": "zhangsan@example.com",
    "phone": "13800138000",
    "password": "newPassword123"
  }'
```

### 3. 测试用户登录
```bash
curl -X POST http://localhost:8088/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "张三",
    "password": "newPassword123"
  }'
```

---

## 🔄 完整流程

### 管理员为用户设置密码
```
1. 管理员登录
   POST /api/admin/login
   ↓
2. 获取Token
   token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ↓
3. 为用户设置密码
   PUT /api/users/1
   Headers: Authorization: Bearer <token>
   Body: { "password": "newPassword123" }
   ↓
4. 后端加密密码
   password_hash = bcrypt.hashpw(password, salt)
   ↓
5. 存储到数据库
   UPDATE user SET password_hash = '...' WHERE id = 1
   ↓
6. 返回成功响应
   { "code": 200, "message": "更新成功" }
```

### 用户登录
```
1. 用户输入用户名和密码
   username: 张三
   password: newPassword123
   ↓
2. 发送登录请求
   POST /api/auth/login
   ↓
3. 后端验证密码
   bcrypt.checkpw(password, user.password_hash)
   ↓
4. 生成Token
   token = jwt.encode({...})
   ↓
5. 返回Token
   { "token": "...", "user": {...} }
```

---

## 🐛 常见问题

### 问题1: 401 Unauthorized
**原因**: 未提供Token或Token无效

**解决方案**:
1. 确保管理员已登录
2. 检查Token是否正确
3. 检查Token是否过期

### 问题2: 403 Forbidden
**原因**: 权限不足（非管理员）

**解决方案**:
1. 使用管理员账号登录
2. 检查userType是否为'admin'

### 问题3: 密码设置后无法登录
**原因**: 密码加密问题

**解决方案**:
1. 检查bcrypt是否正确安装
2. 检查密码哈希是否正确存储
3. 查看后端日志

---

## ✨ 功能亮点

1. **安全的密码管理**
   - bcrypt加密
   - 盐值随机生成
   - 不可逆加密

2. **完善的权限控制**
   - 装饰器模式
   - Token验证
   - 角色检查

3. **灵活的API设计**
   - 支持部分更新
   - 字段自动过滤
   - 错误处理完善

4. **易于测试**
   - 提供测试脚本
   - 清晰的测试步骤
   - 详细的日志输出

---

## 📚 相关文档

- [用户管理更新文档](USER_MANAGEMENT_UPDATE.md)
- [认证API文档](backend/api/routes/README_AUTH.md)
- [权限控制系统](PERMISSION_CONTROL.md)

---

**更新日期**: 2025-11-19
**版本**: v2.2
**状态**: ✅ 已完成并测试
