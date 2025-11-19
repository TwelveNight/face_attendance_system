"""
数据库ORM模型定义
使用SQLAlchemy定义User、Attendance、SystemLog表
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """
    用户表
    
    字段说明:
    - id: 用户唯一标识
    - username: 用户名
    - student_id: 学号
    - password_hash: 用户密码哈希(用于登录)
    - department_id: 所属部门
    - position: 职位
    - email: 邮箱
    - phone: 手机号
    - entry_date: 入职日期
    - last_login_at: 最后登录时间
    - created_at: 创建时间
    - updated_at: 更新时间
    - is_active: 是否激活
    
    注意: 人脸特征实际存储在 backend/saved_models/facenet_embeddings.npz 中，
          该文件包含所有用户的特征向量，通过user_id关联
    """
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True, index=True)
    student_id = db.Column(db.String(20), unique=True, index=True)
    password_hash = db.Column(db.String(255))  # V3.0: 用户登录密码
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))  # V3.0: 所属部门
    position = db.Column(db.String(50))  # V3.0: 职位
    email = db.Column(db.String(100), index=True)  # V3.0: 邮箱
    phone = db.Column(db.String(20), index=True)  # V3.0: 手机号
    entry_date = db.Column(db.Date)  # V3.0: 入职日期
    last_login_at = db.Column(db.DateTime)  # V3.0: 最后登录时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)  # V3.0: 更新时间
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # 关系
    attendances = db.relationship('Attendance', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'username': self.username,
            'student_id': self.student_id,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None,
            'position': self.position,
            'email': self.email,
            'phone': self.phone,
            'entry_date': self.entry_date.isoformat() if self.entry_date else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }
        return data
    
    def __repr__(self):
        return f'<User {self.username}>'


class Attendance(db.Model):
    """考勤记录表"""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)
    status = db.Column(db.String(20), default='present', nullable=False)  # present, late, absent
    check_type = db.Column(db.String(20), default='checkin')  # V3.0: checkin-上班, checkout-下班
    is_late = db.Column(db.Boolean, default=False)  # V3.0: 是否迟到
    is_early = db.Column(db.Boolean, default=False)  # V3.0: 是否早退
    rule_id = db.Column(db.Integer, db.ForeignKey('attendance_rule.id'))  # V3.0: 应用的考勤规则ID
    confidence = db.Column(db.Float)  # 识别置信度
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'student_id': self.user.student_id if self.user else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'status': self.status,
            'check_type': self.check_type,
            'is_late': self.is_late,
            'is_early': self.is_early,
            'rule_id': self.rule_id,
            'rule_name': self.rule.name if self.rule else None,
            'confidence': self.confidence
        }
    
    def __repr__(self):
        return f'<Attendance user_id={self.user_id} at {self.timestamp}>'


class SystemLog(db.Model):
    """系统日志表"""
    __tablename__ = 'system_log'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)  # user_register, check_in, error, etc.
    message = db.Column(db.Text, nullable=False)
    level = db.Column(db.String(20), default='INFO')  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    extra_data = db.Column(db.Text)  # JSON格式的额外数据
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'event_type': self.event_type,
            'message': self.message,
            'level': self.level,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user_id': self.user_id,
            'extra_data': self.extra_data
        }
    
    def __repr__(self):
        return f'<SystemLog {self.event_type} at {self.timestamp}>'


# ============================================
# V3.0 新增模型
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
