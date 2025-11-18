"""
API路由模块
"""
from .user import user_bp
from .attendance import attendance_bp
from .statistics import statistics_bp
from .video import video_bp
from .system import system_bp

__all__ = [
    'user_bp',
    'attendance_bp',
    'statistics_bp',
    'video_bp',
    'system_bp'
]
