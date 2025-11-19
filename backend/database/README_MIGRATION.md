# 数据库迁移指南 V3.0

## 📋 迁移概述

本次迁移将为系统添加以下功能：
- ✅ 管理员认证系统
- ✅ 普通用户登录系统
- ✅ 部门管理
- ✅ 考勤规则管理（含开放打卡模式）
- ✅ 节假日管理
- ✅ 请假申请与审批
- ✅ 补卡申请与审批
- ✅ 系统配置管理

## 🗄️ 数据库变更

### 新增表（8张）
1. `admin` - 管理员表
2. `admin_login_log` - 管理员登录日志
3. `department` - 部门表
4. `attendance_rule` - 考勤规则表
5. `holiday` - 节假日表
6. `leave_request` - 请假申请表
7. `makeup_request` - 补卡申请表
8. `system_config` - 系统配置表

### 修改表（2张）
1. `user` - 添加登录密码、部门、职位等字段
2. `attendance` - 添加打卡类型、迟到早退判定等字段

## 🚀 执行迁移

### 方法一：使用Python脚本（推荐）

```bash
# 进入backend目录
cd backend

# 执行迁移脚本
python database/migrate.py
```

### 方法二：手动执行SQL

```bash
# 使用MySQL客户端
mysql -u your_username -p your_database < database/migration_v3.sql

# 或使用MySQL Workbench等图形化工具导入SQL文件
```

## ⚠️ 注意事项

### 1. 备份数据库
**在执行迁移前，请务必备份数据库！**

```bash
# MySQL备份命令
mysqldump -u your_username -p your_database > backup_before_v3.sql
```

### 2. 检查数据库类型

- **MySQL**: 完全支持，推荐使用
- **SQLite**: 部分支持，某些ALTER TABLE语句可能失败

如果使用SQLite，建议：
1. 导出现有数据
2. 删除旧数据库文件
3. 使用SQLAlchemy重新创建所有表
4. 导入数据

### 3. 外键约束

迁移脚本会创建外键约束，确保：
- 数据库引擎为InnoDB（MySQL）
- 外键引用的表已存在

### 4. 默认数据

迁移脚本会自动插入：
- 默认管理员账号（用户名: admin, 密码: admin123）
- 默认考勤规则（9:00-18:00）
- 测试考勤规则（开放打卡模式）
- 2025年节假日数据
- 默认系统配置

## ✅ 验证迁移

### 1. 检查表是否创建成功

```sql
-- 查看所有表
SHOW TABLES;

-- 应该包含以下新表:
-- admin
-- admin_login_log
-- department
-- attendance_rule
-- holiday
-- leave_request
-- makeup_request
-- system_config
```

### 2. 检查user表新字段

```sql
DESC user;

-- 应该包含以下新字段:
-- password_hash
-- department_id
-- position
-- email
-- phone
-- entry_date
-- last_login_at
-- updated_at
```

### 3. 检查attendance表新字段

```sql
DESC attendance;

-- 应该包含以下新字段:
-- check_type
-- is_late
-- is_early
-- is_makeup
-- makeup_request_id
-- rule_id
```

### 4. 检查默认数据

```sql
-- 检查默认管理员
SELECT * FROM admin;

-- 检查默认考勤规则
SELECT * FROM attendance_rule;

-- 检查节假日数据
SELECT COUNT(*) FROM holiday;

-- 检查系统配置
SELECT * FROM system_config;
```

## 🔧 常见问题

### 问题1: 表已存在错误
```
Error 1050: Table 'xxx' already exists
```

**解决方案**: 这是正常的，脚本会自动跳过已存在的表。

### 问题2: 字段已存在错误
```
Error 1060: Duplicate column name 'xxx'
```

**解决方案**: 这是正常的，说明该字段已经存在，脚本会自动跳过。

### 问题3: 外键约束失败
```
Error 1215: Cannot add foreign key constraint
```

**解决方案**: 
1. 确保引用的表已存在
2. 确保引用的字段类型匹配
3. 确保使用InnoDB引擎

### 问题4: 数据已存在错误
```
Error 1062: Duplicate entry 'xxx'
```

**解决方案**: 这是正常的，说明默认数据已经插入过了。

## 📝 迁移后的任务

### 1. 更新ORM模型

确保以下文件已更新：
- `backend/database/models.py` - 更新User和Attendance模型
- `backend/database/models_v3.py` - 新增的模型定义

### 2. 为现有用户设置密码

```python
# 可以创建一个脚本为现有用户设置默认密码
import bcrypt

# 为所有用户设置默认密码（例如: user123）
default_password = "user123"
password_hash = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt())

# 更新数据库
UPDATE user SET password_hash = password_hash WHERE password_hash IS NULL;
```

### 3. 测试管理员登录

```bash
# 默认管理员账号
用户名: admin
密码: admin123
```

### 4. 配置考勤规则

- 检查默认考勤规则是否符合需求
- 如需测试，可以启用"测试模式(开放打卡)"规则

## 🎯 下一步

数据库迁移完成后，继续进行：

1. **阶段二**: 实现双重认证系统（管理员+用户登录）
2. **阶段三**: 实现部门管理功能
3. **阶段四**: 实现考勤规则管理
4. **阶段五**: 实现请假与补卡管理
5. **阶段六**: 实现高级统计与系统配置

## 📞 支持

如果遇到问题，请检查：
1. 数据库连接配置是否正确
2. 数据库用户是否有足够的权限
3. 数据库版本是否支持（MySQL 5.7+）
4. 查看详细的错误日志

---

**重要提示**: 
- 在生产环境执行迁移前，请务必在测试环境中先测试
- 保留好数据库备份，以便出现问题时可以回滚
- 迁移过程中不要中断，确保所有SQL语句执行完成
