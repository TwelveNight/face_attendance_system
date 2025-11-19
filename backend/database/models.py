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
    - avatar_path: 头像路径 (预留字段，当前未使用)
    - face_embedding_path: 人脸特征文件路径 (预留字段，当前人脸特征存储在facenet_embeddings.npz中)
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
    avatar_path = db.Column(db.String(255))  # 预留：用户头像路径
    face_embedding_path = db.Column(db.String(255))  # 预留：单独的人脸特征文件路径
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
            'avatar_path': self.avatar_path,
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
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    status = db.Column(db.String(20), default='present', nullable=False)  # present, late, absent
    check_type = db.Column(db.String(20), default='checkin')  # V3.0: checkin-上班, checkout-下班
    is_late = db.Column(db.Boolean, default=False)  # V3.0: 是否迟到
    is_early = db.Column(db.Boolean, default=False)  # V3.0: 是否早退
    is_makeup = db.Column(db.Boolean, default=False)  # V3.0: 是否补卡
    makeup_request_id = db.Column(db.Integer, db.ForeignKey('makeup_request.id'))  # V3.0: 补卡申请ID
    rule_id = db.Column(db.Integer, db.ForeignKey('attendance_rule.id'))  # V3.0: 应用的考勤规则ID
    confidence = db.Column(db.Float)  # 识别置信度
    image_path = db.Column(db.String(255))  # 打卡时的照片路径
    notes = db.Column(db.Text)  # 备注
    
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
            'is_makeup': self.is_makeup,
            'makeup_request_id': self.makeup_request_id,
            'rule_id': self.rule_id,
            'rule_name': self.rule.name if self.rule else None,
            'confidence': self.confidence,
            'image_path': self.image_path,
            'notes': self.notes
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
