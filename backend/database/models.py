"""
数据库ORM模型定义
使用SQLAlchemy定义User、Attendance、SystemLog表
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """用户表"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True, index=True)
    student_id = db.Column(db.String(20), unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    avatar_path = db.Column(db.String(255))
    face_embedding_path = db.Column(db.String(255))  # 存储人脸特征文件路径
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # 关系
    attendances = db.relationship('Attendance', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'student_id': self.student_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'avatar_path': self.avatar_path,
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


class Attendance(db.Model):
    """考勤记录表"""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    status = db.Column(db.String(20), default='present', nullable=False)  # present, late, absent
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
