"""
数据库ORM模型定义 V3.0
包含所有新增的表模型
"""
from datetime import datetime
from database.models import db


# ============================================
# 新增模型
# ============================================

class Admin(db.Model):
    """管理员表"""
    __tablename__ = 'admin'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True, index=True)
    phone = db.Column(db.String(20))
    is_super = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # 关系
    login_logs = db.relationship('AdminLoginLog', backref='admin', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'username': self.username,
            'real_name': self.real_name,
            'email': self.email,
            'phone': self.phone,
            'is_super': self.is_super,
            'is_active': self.is_active,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_sensitive:
            data['last_login_ip'] = self.last_login_ip
        return data
    
    def __repr__(self):
        return f'<Admin {self.username}>'


class AdminLoginLog(db.Model):
    """管理员登录日志表"""
    __tablename__ = 'admin_login_log'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False, index=True)
    login_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    login_ip = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    login_status = db.Column(db.String(20), default='success', index=True)
    failure_reason = db.Column(db.String(255))
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'admin_username': self.admin.username if self.admin else None,
            'login_time': self.login_time.isoformat() if self.login_time else None,
            'login_ip': self.login_ip,
            'user_agent': self.user_agent,
            'login_status': self.login_status,
            'failure_reason': self.failure_reason
        }
    
    def __repr__(self):
        return f'<AdminLoginLog admin_id={self.admin_id} at {self.login_time}>'


class Department(db.Model):
    """部门表"""
    __tablename__ = 'department'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('department.id'), index=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    description = db.Column(db.Text)
    level = db.Column(db.Integer, default=1)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # 关系
    children = db.relationship('Department', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    users = db.relationship('User', backref='department', lazy='dynamic', foreign_keys='User.department_id')
    manager = db.relationship('User', foreign_keys=[manager_id], uselist=False)
    rules = db.relationship('AttendanceRule', backref='department', lazy='dynamic')
    
    def get_total_user_count(self):
        """
        获取部门总人数（包含所有子部门）
        递归统计本部门及所有子部门的用户数
        """
        count = self.users.count()  # 本部门的用户数
        # 递归统计所有子部门的用户数
        for child in self.children:
            count += child.get_total_user_count()
        return count
    
    def to_dict(self, include_children=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'parent_id': self.parent_id,
            'manager_id': self.manager_id,
            'manager_name': self.manager.username if self.manager else None,
            'description': self.description,
            'level': self.level,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'user_count': self.get_total_user_count(),  # 使用递归统计
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_children:
            data['children'] = [child.to_dict() for child in self.children]
        return data
    
    def __repr__(self):
        return f'<Department {self.name}>'


class AttendanceRule(db.Model):
    """考勤规则表"""
    __tablename__ = 'attendance_rule'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    work_start_time = db.Column(db.Time, nullable=False)
    work_end_time = db.Column(db.Time, nullable=False)
    late_threshold = db.Column(db.Integer, default=0)
    early_threshold = db.Column(db.Integer, default=0)
    work_days = db.Column(db.String(20), default='1,2,3,4,5')
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), index=True)
    is_default = db.Column(db.Boolean, default=False, index=True)
    is_active = db.Column(db.Boolean, default=True)
    is_open_mode = db.Column(db.Boolean, default=False, index=True)
    description = db.Column(db.Text)
    
    # 打卡时间限制
    checkin_before_minutes = db.Column(db.Integer, default=0)  # 上班打卡可提前多少分钟(0表示不限制)
    enable_once_per_day = db.Column(db.Boolean, default=True)  # 是否限制每天只能打卡一次
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # 关系
    attendances = db.relationship('Attendance', backref='rule', lazy='dynamic', foreign_keys='Attendance.rule_id')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'work_start_time': self.work_start_time.strftime('%H:%M:%S') if self.work_start_time else None,
            'work_end_time': self.work_end_time.strftime('%H:%M:%S') if self.work_end_time else None,
            'late_threshold': self.late_threshold,
            'early_threshold': self.early_threshold,
            'work_days': self.work_days,
            'work_days_list': self.work_days.split(',') if self.work_days else [],
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'is_open_mode': self.is_open_mode,
            'description': self.description,
            'checkin_before_minutes': self.checkin_before_minutes,
            'enable_once_per_day': self.enable_once_per_day,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<AttendanceRule {self.name}>'


class Holiday(db.Model):
    """节假日表"""
    __tablename__ = 'holiday'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False, unique=True, index=True)
    type = db.Column(db.String(20), default='holiday', index=True)
    is_workday = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'date': self.date.isoformat() if self.date else None,
            'type': self.type,
            'is_workday': self.is_workday,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Holiday {self.name} on {self.date}>'


class LeaveRequest(db.Model):
    """请假申请表"""
    __tablename__ = 'leave_request'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    leave_type = db.Column(db.String(20), nullable=False, index=True)
    start_time = db.Column(db.DateTime, nullable=False, index=True)
    end_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending', index=True)
    approver_id = db.Column(db.Integer, db.ForeignKey('admin.id'))
    approved_at = db.Column(db.DateTime)
    approval_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # 关系
    user = db.relationship('User', backref='leave_requests', foreign_keys=[user_id])
    approver = db.relationship('Admin', backref='approved_leaves', foreign_keys=[approver_id])
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'leave_type': self.leave_type,
            'leave_type_name': self.get_leave_type_name(),
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'reason': self.reason,
            'status': self.status,
            'status_name': self.get_status_name(),
            'approver_id': self.approver_id,
            'approver_name': self.approver.real_name if self.approver else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approval_notes': self.approval_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_leave_type_name(self):
        """获取请假类型名称"""
        types = {
            'sick': '病假',
            'personal': '事假',
            'annual': '年假',
            'other': '其他'
        }
        return types.get(self.leave_type, self.leave_type)
    
    def get_status_name(self):
        """获取状态名称"""
        statuses = {
            'pending': '待审批',
            'approved': '已批准',
            'rejected': '已拒绝',
            'cancelled': '已取消'
        }
        return statuses.get(self.status, self.status)
    
    def __repr__(self):
        return f'<LeaveRequest user_id={self.user_id} {self.leave_type}>'


class MakeupRequest(db.Model):
    """补卡申请表"""
    __tablename__ = 'makeup_request'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    makeup_date = db.Column(db.Date, nullable=False, index=True)
    makeup_time = db.Column(db.Time, nullable=False)
    type = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending', index=True)
    approver_id = db.Column(db.Integer, db.ForeignKey('admin.id'))
    approved_at = db.Column(db.DateTime)
    approval_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # 关系
    user = db.relationship('User', backref='makeup_requests', foreign_keys=[user_id])
    approver = db.relationship('Admin', backref='approved_makeups', foreign_keys=[approver_id])
    attendances = db.relationship('Attendance', backref='makeup_request', lazy='dynamic', foreign_keys='Attendance.makeup_request_id')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'makeup_date': self.makeup_date.isoformat() if self.makeup_date else None,
            'makeup_time': self.makeup_time.strftime('%H:%M:%S') if self.makeup_time else None,
            'type': self.type,
            'type_name': '上班打卡' if self.type == 'checkin' else '下班打卡',
            'reason': self.reason,
            'status': self.status,
            'status_name': self.get_status_name(),
            'approver_id': self.approver_id,
            'approver_name': self.approver.real_name if self.approver else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approval_notes': self.approval_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_status_name(self):
        """获取状态名称"""
        statuses = {
            'pending': '待审批',
            'approved': '已批准',
            'rejected': '已拒绝'
        }
        return statuses.get(self.status, self.status)
    
    def __repr__(self):
        return f'<MakeupRequest user_id={self.user_id} on {self.makeup_date}>'


class SystemConfig(db.Model):
    """系统配置表"""
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    config_key = db.Column(db.String(100), nullable=False, unique=True, index=True)
    config_value = db.Column(db.Text, nullable=False)
    config_type = db.Column(db.String(20), default='string')
    category = db.Column(db.String(50), index=True)
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'config_key': self.config_key,
            'config_value': self.get_typed_value(),
            'config_type': self.config_type,
            'category': self.category,
            'description': self.description,
            'is_public': self.is_public,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_typed_value(self):
        """根据类型返回值"""
        if self.config_type == 'int':
            return int(self.config_value)
        elif self.config_type == 'float':
            return float(self.config_value)
        elif self.config_type == 'bool':
            return self.config_value.lower() in ('true', '1', 'yes')
        elif self.config_type == 'json':
            import json
            return json.loads(self.config_value)
        else:
            return self.config_value
    
    def __repr__(self):
        return f'<SystemConfig {self.config_key}={self.config_value}>'
