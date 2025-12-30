"""
日志助手模块 - 提供便捷的日志记录功能
"""
from functools import wraps
from typing import Optional, Dict, Any
from flask import request, g, has_request_context
try:
    from flask_jwt_extended import get_jwt_identity
except ImportError:
    # 如果没有安装 flask_jwt_extended，提供一个默认实现
    def get_jwt_identity():
        return None


def _get_client_ip() -> Optional[str]:
    """获取客户端IP地址"""
    try:
        if not has_request_context():
            return None
        if request.environ.get('HTTP_X_FORWARDED_FOR'):
            return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0]
        elif request.environ.get('HTTP_X_REAL_IP'):
            return request.environ.get('HTTP_X_REAL_IP')
        else:
            return request.environ.get('REMOTE_ADDR', '')
    except:
        return None


def log_system_event(event_type: str, message: str, level: str = 'INFO',
                    module: Optional[str] = None, extra_data: Optional[Dict] = None,
                    user_id: Optional[int] = None, admin_id: Optional[int] = None):
    """
    记录系统事件日志（写入数据库）
    
    Args:
        event_type: 事件类型
        message: 日志消息
        level: 日志级别
        module: 模块名称
        extra_data: 额外数据
        user_id: 用户ID
        admin_id: 管理员ID
    """
    try:
        from datetime import datetime
        import json
        
        # 打印到控制台
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level}] [{event_type}] {message}"
        if module:
            log_message += f" (模块: {module})"
        if extra_data:
            log_message += f" | 数据: {json.dumps(extra_data, ensure_ascii=False)}"
        print(log_message)
        
        # 写入数据库
        from database.repositories import SystemLogRepository
        ip_address = _get_client_ip()
        
        SystemLogRepository.create(
            event_type=event_type,
            message=message,
            level=level,
            module=module,
            user_id=user_id,
            admin_id=admin_id,
            ip_address=ip_address,
            extra_data=json.dumps(extra_data, ensure_ascii=False) if extra_data else None
        )
        
    except Exception as e:
        print(f"记录日志失败: {e}")


def log_user_action(action: str, module: str = None):
    """
    装饰器：记录用户操作
    
    Args:
        action: 操作描述
        module: 模块名称
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # 执行原函数
                result = func(*args, **kwargs)
                
                # 记录成功日志
                log_system_event(
                    event_type=f"USER_ACTION_{action.upper()}",
                    message=f"用户执行操作: {action}",
                    level='INFO',
                    module=module
                )
                
                return result
                
            except Exception as e:
                # 记录错误日志
                log_system_event(
                    event_type=f"USER_ACTION_{action.upper()}_ERROR",
                    message=f"用户操作失败: {action}, 错误: {str(e)}",
                    level='ERROR',
                    module=module,
                    extra_data={'error': str(e)}
                )
                raise
        
        return wrapper
    return decorator


def log_admin_action(action: str, module: str = None):
    """
    装饰器：记录管理员操作
    
    Args:
        action: 操作描述
        module: 模块名称
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # 执行原函数
                result = func(*args, **kwargs)
                
                # 记录成功日志
                log_system_event(
                    event_type=f"ADMIN_ACTION_{action.upper()}",
                    message=f"管理员执行操作: {action}",
                    level='INFO',
                    module=module
                )
                
                return result
                
            except Exception as e:
                # 记录错误日志
                log_system_event(
                    event_type=f"ADMIN_ACTION_{action.upper()}_ERROR",
                    message=f"管理员操作失败: {action}, 错误: {str(e)}",
                    level='ERROR',
                    module=module,
                    extra_data={'error': str(e)}
                )
                raise
        
        return wrapper
    return decorator


# 常用事件类型常量
class EventType:
    # 用户相关
    USER_CREATE = 'USER_CREATE'
    USER_UPDATE = 'USER_UPDATE'
    USER_DELETE = 'USER_DELETE'
    USER_LOGIN = 'USER_LOGIN'
    USER_LOGOUT = 'USER_LOGOUT'
    
    # 考勤相关
    ATTENDANCE_CHECK = 'ATTENDANCE_CHECK'
    ATTENDANCE_LATE = 'ATTENDANCE_LATE'
    ATTENDANCE_EARLY = 'ATTENDANCE_EARLY'
    ATTENDANCE_ABSENT = 'ATTENDANCE_ABSENT'
    
    # 部门相关
    DEPARTMENT_CREATE = 'DEPARTMENT_CREATE'
    DEPARTMENT_UPDATE = 'DEPARTMENT_UPDATE'
    DEPARTMENT_DELETE = 'DEPARTMENT_DELETE'
    
    # 规则相关
    RULE_CREATE = 'RULE_CREATE'
    RULE_UPDATE = 'RULE_UPDATE'
    RULE_DELETE = 'RULE_DELETE'
    
    # 系统相关
    SYSTEM_START = 'SYSTEM_START'
    SYSTEM_STOP = 'SYSTEM_STOP'
    SYSTEM_ERROR = 'SYSTEM_ERROR'
    SYSTEM_WARNING = 'SYSTEM_WARNING'
    
    # 定时任务相关
    SCHEDULER_START = 'SCHEDULER_START'
    SCHEDULER_STOP = 'SCHEDULER_STOP'
    SCHEDULER_EXECUTE = 'SCHEDULER_EXECUTE'
    SCHEDULER_ERROR = 'SCHEDULER_ERROR'


# 日志级别常量
class LogLevel:
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'
