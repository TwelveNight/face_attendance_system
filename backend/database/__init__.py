"""
数据库模块初始化
"""
from .models import db, User, Attendance, SystemLog
from .repositories import UserRepository, AttendanceRepository, SystemLogRepository
from .init_db import init_database

def get_db():
    """获取数据库会话"""
    return db.session

__all__ = [
    'db',
    'get_db',
    'User',
    'Attendance',
    'SystemLog',
    'UserRepository',
    'AttendanceRepository',
    'SystemLogRepository',
    'init_database'
]
