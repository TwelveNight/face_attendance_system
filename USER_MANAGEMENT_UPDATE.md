# 用户管理功能更新

## 📋 更新内容

### 1. 用户信息扩展
在用户管理页面中新增以下字段的编辑功能：

#### 新增字段
- **职位/班级** (`position`) - 例如：计算机科学与技术2021级1班
- **邮箱** (`email`) - 用户邮箱地址
- **手机号** (`phone`) - 联系电话
- **部门ID** (`department_id`) - 关联部门（后续实现）

### 2. 密码管理功能
为解决数据迁移后用户无密码的问题，新增密码设置功能：

#### 功能特性
- ✅ 管理员可以为任何用户设置密码
- ✅ 密码长度至少6位
- ✅ 需要二次确认密码
- ✅ 设置后用户可以使用用户名/学号登录

#### 使用场景
1. **数据迁移后**：为现有用户批量设置初始密码
2. **忘记密码**：管理员帮助用户重置密码
3. **新用户**：管理员创建用户后立即设置密码

### 3. 权限控制优化
- ✅ 只有管理员才能看到"删除"按钮
- ✅ 所有登录用户都可以设置密码（为其他用户）
- ✅ 根据`userType`动态显示操作按钮

---

## 🎨 UI更新

### 用户列表操作列
**更新前**:
```
[采集人脸] [编辑] [删除]
```

**更新后**:
```
[设置密码] [采集人脸] [编辑] [删除]（仅管理员可见）
```

### 编辑用户表单
**更新前**:
- 用户名
- 学号

**更新后**:
- 用户名
- 学号
- 职位/班级
- 邮箱
- 手机号

### 新增：设置密码对话框
- 新密码（至少6位）
- 确认密码
- 提示信息

---

## 💻 代码更新

### 1. 类型定义更新
**文件**: `frontend/src/types/index.ts`

```typescript
export interface User {
  id: number;
  username: string;
  student_id?: string;
  department_id?: number;      // 新增
  position?: string;            // 新增
  email?: string;               // 新增
  phone?: string;               // 新增
  entry_date?: string;          // 新增
  created_at: string;
  avatar_path?: string;
  is_active: boolean;
  password?: string;            // 新增（仅用于更新）
}
```

### 2. 用户管理页面更新
**文件**: `frontend/src/pages/Users/index.tsx`

#### 新增状态
```typescript
const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
const [passwordUserId, setPasswordUserId] = useState<number | null>(null);
const [passwordForm] = Form.useForm();
```

#### 新增函数
```typescript
// 打开设置密码对话框
const handleOpenPasswordModal = (userId: number) => {
  setPasswordUserId(userId);
  setIsPasswordModalOpen(true);
  passwordForm.resetFields();
};

// 设置密码
const handleSetPassword = async () => {
  const values = await passwordForm.validateFields();
  if (values.password !== values.confirmPassword) {
    message.error('两次密码输入不一致');
    return;
  }
  
  await userApi.updateUser(passwordUserId!, { password: values.password });
  message.success('密码设置成功');
  setIsPasswordModalOpen(false);
};
```

---

## 🔧 后端适配

### API更新需求
**端点**: `PUT /api/users/:id`

需要支持以下字段的更新：
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

### 后端处理逻辑
```python
# backend/api/routes/user.py

@user_bp.route('/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    data = request.get_json()
    user = User.query.get_or_404(user_id)
    
    # 更新基本信息
    if 'username' in data:
        user.username = data['username']
    if 'student_id' in data:
        user.student_id = data['student_id']
    if 'department_id' in data:
        user.department_id = data['department_id']
    if 'position' in data:
        user.position = data['position']
    if 'email' in data:
        user.email = data['email']
    if 'phone' in data:
        user.phone = data['phone']
    
    # 设置密码（新增）
    if 'password' in data:
        from utils.auth import AuthUtils
        user.password_hash = AuthUtils.hash_password(data['password'])
    
    db.session.commit()
    return success_response(user.to_dict())
```

---

## 🏫 部门管理规划

### 学校部门结构建议

根据学号字段的存在，系统更适合学校场景。建议的部门结构：

#### 一级部门（学院）
- 计算机学院
- 电子信息学院
- 机械工程学院
- 经济管理学院
- ...

#### 二级部门（专业/年级）
- 计算机科学与技术
- 软件工程
- 网络工程
- ...

#### 三级部门（班级）
- 2021级1班
- 2021级2班
- 2022级1班
- ...

### 部门表设计
```sql
CREATE TABLE department (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL COMMENT '部门名称',
    code VARCHAR(50) UNIQUE COMMENT '部门代码',
    parent_id INT COMMENT '父部门ID',
    level INT DEFAULT 1 COMMENT '部门层级(1=学院,2=专业,3=班级)',
    type VARCHAR(20) COMMENT '部门类型(college/major/class)',
    description TEXT COMMENT '部门描述',
    sort_order INT DEFAULT 0 COMMENT '排序',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES department(id)
);
```

### 示例数据
```sql
-- 学院
INSERT INTO department (name, code, level, type) VALUES
('计算机学院', 'CS', 1, 'college'),
('电子信息学院', 'EE', 1, 'college');

-- 专业
INSERT INTO department (name, code, parent_id, level, type) VALUES
('计算机科学与技术', 'CS_CST', 1, 2, 'major'),
('软件工程', 'CS_SE', 1, 2, 'major');

-- 班级
INSERT INTO department (name, code, parent_id, level, type) VALUES
('2021级1班', 'CS_CST_2021_1', 3, 3, 'class'),
('2021级2班', 'CS_CST_2021_2', 3, 3, 'class');
```

---

## 🧪 测试步骤

### 1. 测试编辑用户信息
1. 管理员登录
2. 进入用户管理
3. 点击某个用户的"编辑"按钮
4. 填写新增字段：
   - 职位/班级：计算机科学与技术2021级1班
   - 邮箱：student@example.com
   - 手机号：13800138000
5. 点击确定
6. **预期**：用户信息更新成功

### 2. 测试设置密码
1. 管理员登录
2. 进入用户管理
3. 点击某个用户的"设置密码"按钮
4. 输入新密码：`password123`
5. 确认密码：`password123`
6. 点击确定
7. **预期**：显示"密码设置成功"

### 3. 测试用户登录
1. 登出管理员
2. 点击"用户登录"
3. 输入刚才设置密码的用户名
4. 输入密码：`password123`
5. 点击登录
6. **预期**：登录成功，跳转到考勤打卡页面

### 4. 测试权限控制
1. 以普通用户身份登录
2. 尝试访问用户管理页面
3. **预期**：自动跳转到登录页

### 5. 测试删除按钮显示
1. 以管理员身份登录
2. 进入用户管理
3. **预期**：可以看到"删除"按钮

4. 以普通用户身份登录
5. 进入用户管理（如果有权限）
6. **预期**：看不到"删除"按钮

---

## 📊 数据迁移方案

### 为现有用户批量设置密码

#### 方案1：统一初始密码
```python
# backend/scripts/set_default_passwords.py

from database.models import db, User
from utils.auth import AuthUtils

# 为所有无密码的用户设置默认密码
default_password = "123456"

users = User.query.filter(User.password_hash == None).all()

for user in users:
    user.password_hash = AuthUtils.hash_password(default_password)
    print(f"为用户 {user.username} 设置密码")

db.session.commit()
print(f"共为 {len(users)} 个用户设置了默认密码")
```

#### 方案2：基于学号生成密码
```python
# 使用学号后6位作为初始密码
for user in users:
    if user.student_id:
        password = user.student_id[-6:]  # 学号后6位
    else:
        password = "123456"  # 默认密码
    
    user.password_hash = AuthUtils.hash_password(password)
```

#### 方案3：随机密码并导出
```python
import random
import string

passwords = {}

for user in users:
    # 生成8位随机密码
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    user.password_hash = AuthUtils.hash_password(password)
    passwords[user.username] = password

# 导出到CSV
import csv
with open('user_passwords.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['用户名', '学号', '初始密码'])
    for username, password in passwords.items():
        user = User.query.filter_by(username=username).first()
        writer.writerow([username, user.student_id or '', password])
```

---

## ✨ 功能亮点

1. **灵活的密码管理**
   - 管理员可随时为用户设置/重置密码
   - 支持用户首次自行设置密码
   - 密码强度验证（至少6位）

2. **完善的用户信息**
   - 支持学校场景（学号、班级）
   - 支持联系方式（邮箱、手机）
   - 为部门管理预留字段

3. **权限控制**
   - 管理员独享删除权限
   - 防止误操作
   - 保护数据安全

4. **用户体验优化**
   - 表单验证友好
   - 操作提示清晰
   - 界面布局合理

---

## 🔄 后续优化

### 待实现功能
- [ ] 批量导入用户
- [ ] 批量设置密码
- [ ] 密码强度检测
- [ ] 密码过期提醒
- [ ] 用户头像上传
- [ ] 用户状态管理（启用/禁用）

### 部门管理功能
- [ ] 部门树形结构展示
- [ ] 部门CRUD操作
- [ ] 用户部门关联
- [ ] 按部门筛选用户
- [ ] 部门考勤统计

---

**更新日期**: 2025-11-19
**版本**: v2.2
**状态**: ✅ 前端已完成，等待后端适配
