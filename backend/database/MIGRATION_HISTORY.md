# 数据库迁移历史

## V3.0 迁移 (2025-11)

**已执行的迁移内容：**

### 新增表 (8张)
- `admin` - 管理员表
- `admin_login_log` - 管理员登录日志
- `department` - 部门表
- `attendance_rule` - 考勤规则表
- `holiday` - 节假日表
- `leave_request` - 请假申请表
- `makeup_request` - 补卡申请表
- `system_config` - 系统配置表

### 修改表 (2张)
- `user` - 添加 password_hash, department_id, position, email, phone, entry_date 等字段
- `attendance` - 添加 check_type, is_late, is_early, is_makeup, rule_id 等字段

### 默认数据
- 默认管理员: admin / admin123
- 默认考勤规则: 9:00-18:00

---

*注：原迁移脚本 (migrate.py, migration_v3.sql 等) 已在 2025-12-30 整理时删除，迁移已完成无需保留。*
