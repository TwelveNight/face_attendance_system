-- ============================================
-- 人脸识别考勤系统 V3.0 数据库迁移脚本
-- 创建时间: 2025-11-19
-- 说明: 添加管理员认证、部门管理、考勤规则等功能
-- ============================================

-- ============================================
-- 1. 创建管理员表
-- ============================================
CREATE TABLE IF NOT EXISTS admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '管理员用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希(bcrypt)',
    real_name VARCHAR(50) COMMENT '真实姓名',
    email VARCHAR(100) UNIQUE COMMENT '邮箱',
    phone VARCHAR(20) COMMENT '手机号',
    is_super TINYINT(1) DEFAULT 0 COMMENT '是否超级管理员',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    last_login_at DATETIME COMMENT '最后登录时间',
    last_login_ip VARCHAR(50) COMMENT '最后登录IP',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理员表';

-- 插入默认管理员账号（用户名: admin, 密码: admin123）
INSERT INTO admin (username, password_hash, real_name, is_super, is_active, created_at) 
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7TLKkkVppe', '系统管理员', 1, 1, NOW());

-- ============================================
-- 2. 创建管理员登录日志表
-- ============================================
CREATE TABLE IF NOT EXISTS admin_login_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL COMMENT '管理员ID',
    login_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '登录时间',
    login_ip VARCHAR(50) COMMENT '登录IP',
    user_agent TEXT COMMENT '浏览器信息',
    login_status VARCHAR(20) DEFAULT 'success' COMMENT '登录状态(success/failed)',
    failure_reason VARCHAR(255) COMMENT '失败原因',
    FOREIGN KEY (admin_id) REFERENCES admin(id) ON DELETE CASCADE,
    INDEX idx_admin_id (admin_id),
    INDEX idx_login_time (login_time),
    INDEX idx_login_status (login_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理员登录日志表';

-- ============================================
-- 3. 创建部门表
-- ============================================
CREATE TABLE IF NOT EXISTS department (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '部门名称',
    code VARCHAR(50) UNIQUE COMMENT '部门代码',
    parent_id INT COMMENT '父部门ID',
    manager_id INT COMMENT '部门负责人用户ID',
    description TEXT COMMENT '部门描述',
    level INT DEFAULT 1 COMMENT '部门层级',
    sort_order INT DEFAULT 0 COMMENT '排序',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES department(id) ON DELETE SET NULL,
    FOREIGN KEY (manager_id) REFERENCES user(id) ON DELETE SET NULL,
    INDEX idx_parent_id (parent_id),
    INDEX idx_code (code),
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='部门表';

-- ============================================
-- 4. 创建考勤规则表
-- ============================================
CREATE TABLE IF NOT EXISTS attendance_rule (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '规则名称',
    work_start_time TIME NOT NULL COMMENT '上班时间',
    work_end_time TIME NOT NULL COMMENT '下班时间',
    late_threshold INT DEFAULT 0 COMMENT '迟到阈值(分钟)',
    early_threshold INT DEFAULT 0 COMMENT '早退阈值(分钟)',
    work_days VARCHAR(20) DEFAULT '1,2,3,4,5' COMMENT '工作日(1-7,周一到周日)',
    department_id INT COMMENT '适用部门(NULL表示默认规则)',
    is_default TINYINT(1) DEFAULT 0 COMMENT '是否默认规则',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    is_open_mode TINYINT(1) DEFAULT 0 COMMENT '是否开放模式(不限制打卡时间)',
    description TEXT COMMENT '规则描述',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES department(id) ON DELETE SET NULL,
    INDEX idx_department_id (department_id),
    INDEX idx_is_default (is_default),
    INDEX idx_is_open_mode (is_open_mode)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='考勤规则表';

-- 插入默认规则：9:00-18:00，迟到15分钟，早退15分钟
INSERT INTO attendance_rule (name, work_start_time, work_end_time, late_threshold, early_threshold, work_days, is_default, is_active, is_open_mode, created_at)
VALUES ('默认考勤规则', '09:00:00', '18:00:00', 15, 15, '1,2,3,4,5', 1, 1, 0, NOW());

-- 插入测试规则：开放模式，不限制打卡时间
INSERT INTO attendance_rule (name, work_start_time, work_end_time, late_threshold, early_threshold, work_days, is_default, is_active, is_open_mode, description, created_at)
VALUES ('测试模式(开放打卡)', '00:00:00', '23:59:59', 0, 0, '1,2,3,4,5,6,7', 0, 0, 1, '测试用开放打卡模式，任何时间都可以打卡，不判定迟到早退', NOW());

-- ============================================
-- 5. 创建节假日表
-- ============================================
CREATE TABLE IF NOT EXISTS holiday (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '节假日名称',
    date DATE NOT NULL UNIQUE COMMENT '日期',
    type VARCHAR(20) DEFAULT 'holiday' COMMENT '类型(holiday-节假日,workday-调休工作日)',
    is_workday TINYINT(1) DEFAULT 0 COMMENT '是否工作日(调休)',
    description TEXT COMMENT '描述',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date (date),
    INDEX idx_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='节假日表';

-- 插入2025年部分节假日示例
INSERT INTO holiday (name, date, type, is_workday, created_at) VALUES
('元旦', '2025-01-01', 'holiday', 0, NOW()),
('春节', '2025-01-28', 'holiday', 0, NOW()),
('春节', '2025-01-29', 'holiday', 0, NOW()),
('春节', '2025-01-30', 'holiday', 0, NOW()),
('春节', '2025-01-31', 'holiday', 0, NOW()),
('春节', '2025-02-01', 'holiday', 0, NOW()),
('春节', '2025-02-02', 'holiday', 0, NOW()),
('春节', '2025-02-03', 'holiday', 0, NOW()),
('清明节', '2025-04-04', 'holiday', 0, NOW()),
('清明节', '2025-04-05', 'holiday', 0, NOW()),
('清明节', '2025-04-06', 'holiday', 0, NOW()),
('劳动节', '2025-05-01', 'holiday', 0, NOW()),
('劳动节', '2025-05-02', 'holiday', 0, NOW()),
('劳动节', '2025-05-03', 'holiday', 0, NOW()),
('端午节', '2025-05-31', 'holiday', 0, NOW()),
('端午节', '2025-06-01', 'holiday', 0, NOW()),
('端午节', '2025-06-02', 'holiday', 0, NOW()),
('中秋节', '2025-10-06', 'holiday', 0, NOW()),
('中秋节', '2025-10-07', 'holiday', 0, NOW()),
('中秋节', '2025-10-08', 'holiday', 0, NOW()),
('国庆节', '2025-10-01', 'holiday', 0, NOW()),
('国庆节', '2025-10-02', 'holiday', 0, NOW()),
('国庆节', '2025-10-03', 'holiday', 0, NOW()),
('国庆节', '2025-10-04', 'holiday', 0, NOW()),
('国庆节', '2025-10-05', 'holiday', 0, NOW());

-- ============================================
-- 6. 创建请假申请表
-- ============================================
CREATE TABLE IF NOT EXISTS leave_request (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '申请人ID',
    leave_type VARCHAR(20) NOT NULL COMMENT '请假类型(sick-病假,personal-事假,annual-年假,other-其他)',
    start_time DATETIME NOT NULL COMMENT '开始时间',
    end_time DATETIME NOT NULL COMMENT '结束时间',
    duration FLOAT NOT NULL COMMENT '请假时长(天)',
    reason TEXT NOT NULL COMMENT '请假原因',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态(pending-待审批,approved-已批准,rejected-已拒绝,cancelled-已取消)',
    approver_id INT COMMENT '审批人管理员ID',
    approved_at DATETIME COMMENT '审批时间',
    approval_notes TEXT COMMENT '审批备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (approver_id) REFERENCES admin(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_start_time (start_time),
    INDEX idx_leave_type (leave_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='请假申请表';

-- ============================================
-- 7. 创建补卡申请表
-- ============================================
CREATE TABLE IF NOT EXISTS makeup_request (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '申请人ID',
    makeup_date DATE NOT NULL COMMENT '补卡日期',
    makeup_time TIME NOT NULL COMMENT '补卡时间',
    type VARCHAR(20) NOT NULL COMMENT '补卡类型(checkin-上班,checkout-下班)',
    reason TEXT NOT NULL COMMENT '补卡原因',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态(pending-待审批,approved-已批准,rejected-已拒绝)',
    approver_id INT COMMENT '审批人管理员ID',
    approved_at DATETIME COMMENT '审批时间',
    approval_notes TEXT COMMENT '审批备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (approver_id) REFERENCES admin(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_makeup_date (makeup_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='补卡申请表';

-- ============================================
-- 8. 创建系统配置表
-- ============================================
CREATE TABLE IF NOT EXISTS system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
    config_value TEXT NOT NULL COMMENT '配置值',
    config_type VARCHAR(20) DEFAULT 'string' COMMENT '值类型(string,int,float,bool,json)',
    category VARCHAR(50) COMMENT '配置分类(system-系统,attendance-考勤,recognition-识别)',
    description TEXT COMMENT '配置描述',
    is_public TINYINT(1) DEFAULT 0 COMMENT '是否公开(前端可见)',
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_config_key (config_key),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';

-- 插入默认系统配置
INSERT INTO system_config (config_key, config_value, config_type, category, description, is_public, created_at) VALUES
('face_recognition_threshold', '0.7', 'float', 'recognition', '人脸识别阈值(0.0-1.0)', 0, NOW()),
('required_face_samples', '10', 'int', 'recognition', '人脸采集数量', 0, NOW()),
('enable_quality_check', 'true', 'bool', 'recognition', '是否启用质量检测', 0, NOW()),
('enable_data_augmentation', 'true', 'bool', 'recognition', '是否启用数据增强', 0, NOW()),
('system_name', '人脸识别考勤系统', 'string', 'system', '系统名称', 1, NOW()),
('company_name', 'XX公司', 'string', 'system', '公司名称', 1, NOW()),
('enable_auto_checkout', 'false', 'bool', 'attendance', '是否启用自动下班打卡', 0, NOW()),
('max_checkin_per_day', '1', 'int', 'attendance', '每天最多上班打卡次数', 0, NOW()),
('max_checkout_per_day', '1', 'int', 'attendance', '每天最多下班打卡次数', 0, NOW()),
('session_timeout', '7200', 'int', 'system', '会话超时时间(秒)', 0, NOW()),
('min_password_length', '6', 'int', 'system', '最小密码长度', 0, NOW());

-- ============================================
-- 9. 修改现有的 user 表
-- ============================================
-- 添加用户登录和部门相关字段
ALTER TABLE user 
ADD COLUMN password_hash VARCHAR(255) COMMENT '用户密码哈希(用于登录)' AFTER student_id,
ADD COLUMN department_id INT COMMENT '所属部门' AFTER password_hash,
ADD COLUMN position VARCHAR(50) COMMENT '职位' AFTER department_id,
ADD COLUMN email VARCHAR(100) COMMENT '邮箱' AFTER position,
ADD COLUMN phone VARCHAR(20) COMMENT '手机号' AFTER email,
ADD COLUMN entry_date DATE COMMENT '入职日期' AFTER phone,
ADD COLUMN last_login_at DATETIME COMMENT '最后登录时间' AFTER entry_date,
ADD COLUMN updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间' AFTER last_login_at,
ADD CONSTRAINT fk_user_department FOREIGN KEY (department_id) REFERENCES department(id) ON DELETE SET NULL;

-- 创建索引
CREATE INDEX idx_user_email ON user(email);
CREATE INDEX idx_user_phone ON user(phone);
CREATE INDEX idx_user_department ON user(department_id);

-- ============================================
-- 10. 修改现有的 attendance 表
-- ============================================
-- 添加考勤判定相关字段
ALTER TABLE attendance
ADD COLUMN check_type VARCHAR(20) DEFAULT 'checkin' COMMENT '打卡类型(checkin-上班,checkout-下班)' AFTER status,
ADD COLUMN is_late TINYINT(1) DEFAULT 0 COMMENT '是否迟到' AFTER check_type,
ADD COLUMN is_early TINYINT(1) DEFAULT 0 COMMENT '是否早退' AFTER is_late,
ADD COLUMN is_makeup TINYINT(1) DEFAULT 0 COMMENT '是否补卡' AFTER is_early,
ADD COLUMN makeup_request_id INT COMMENT '补卡申请ID' AFTER is_makeup,
ADD COLUMN rule_id INT COMMENT '应用的考勤规则ID' AFTER makeup_request_id,
ADD CONSTRAINT fk_attendance_makeup FOREIGN KEY (makeup_request_id) REFERENCES makeup_request(id) ON DELETE SET NULL,
ADD CONSTRAINT fk_attendance_rule FOREIGN KEY (rule_id) REFERENCES attendance_rule(id) ON DELETE SET NULL;

-- 创建索引
CREATE INDEX idx_attendance_check_type ON attendance(check_type);
CREATE INDEX idx_attendance_is_late ON attendance(is_late);
CREATE INDEX idx_attendance_is_early ON attendance(is_early);
CREATE INDEX idx_attendance_date ON attendance((DATE(`timestamp`)));

-- ============================================
-- 数据库迁移完成
-- ============================================
-- 新增表: 8张
-- 1. admin - 管理员表
-- 2. admin_login_log - 管理员登录日志
-- 3. department - 部门表
-- 4. attendance_rule - 考勤规则表
-- 5. holiday - 节假日表
-- 6. leave_request - 请假申请表
-- 7. makeup_request - 补卡申请表
-- 8. system_config - 系统配置表
--
-- 修改表: 2张
-- 1. user - 添加登录和部门字段
-- 2. attendance - 添加考勤判定字段
-- ============================================
