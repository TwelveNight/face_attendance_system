"""
日志相关的数据库模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database.models import db

class AdminLoginLog(db.Model):
    """管理员登录日志"""
    __tablename__ = 'admin_login_log'
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey('admin.id'), nullable=True, comment='管理员ID')
    username = Column(String(50), comment='尝试登录的用户名')
    login_time = Column(DateTime, default=datetime.now, comment='登录时间')
    login_ip = Column(String(50), comment='登录IP地址')
    user_agent = Column(Text, comment='浏览器信息')
    login_status = Column(String(20), comment='登录状态: success/failed')
    failure_reason = Column(String(255), comment='失败原因')
    
    # 关联管理员（使用字符串避免循环导入）
    # admin = relationship("Admin", backref="login_logs")
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'username': self.username,
            'login_time': self.login_time.strftime('%Y-%m-%d %H:%M:%S') if self.login_time else None,
            'login_ip': self.login_ip,
            'user_agent': self.user_agent,
            'login_status': self.login_status,
            'failure_reason': self.failure_reason
        }


class SystemLog(db.Model):
    """系统操作日志"""
    __tablename__ = 'system_log'
    
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50), nullable=False, comment='事件类型')
    message = Column(Text, nullable=False, comment='日志消息')
    level = Column(String(20), default='INFO', comment='日志级别: DEBUG/INFO/WARNING/ERROR/CRITICAL')
    timestamp = Column(DateTime, default=datetime.now, nullable=False, comment='时间戳')
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True, comment='用户ID')
    admin_id = Column(Integer, ForeignKey('admin.id'), nullable=True, comment='管理员ID')
    module = Column(String(50), comment='模块名称')
    ip_address = Column(String(50), comment='操作IP地址')
    extra_data = Column(Text, comment='额外数据(JSON格式)')
    
    # 关联用户和管理员（使用字符串避免循环导入）
    # user = relationship("User", backref="system_logs")
    # admin = relationship("Admin", backref="system_logs")
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'event_type': self.event_type,
            'message': self.message,
            'level': self.level,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else None,
            'user_id': self.user_id,
            'admin_id': self.admin_id,
            'module': self.module,
            'ip_address': self.ip_address,
            'extra_data': self.extra_data
        }
