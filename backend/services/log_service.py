"""
日志服务类（简化版本）
处理管理员登录日志和系统操作日志
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from flask import request
import json

class LogService:
    """日志服务类"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def log_admin_login(self, username: str, admin_id: Optional[int], 
                        success: bool, failure_reason: Optional[str] = None) -> Dict:
        """
        记录管理员登录日志
        
        Args:
            username: 尝试登录的用户名
            admin_id: 管理员ID（登录成功时）
            success: 是否登录成功
            failure_reason: 失败原因
        """
        try:
            sql = text("""
                INSERT INTO admin_login_log 
                (admin_id, username, login_time, login_ip, user_agent, login_status, failure_reason)
                VALUES (:admin_id, :username, :login_time, :login_ip, :user_agent, :login_status, :failure_reason)
            """)
            
            self.db.execute(sql, {
                'admin_id': admin_id if success else None,
                'username': username,
                'login_time': datetime.now(),
                'login_ip': self._get_client_ip(),
                'user_agent': request.headers.get('User-Agent', ''),
                'login_status': 'success' if success else 'failed',
                'failure_reason': failure_reason if not success else None
            })
            self.db.commit()
        except Exception as e:
            print(f"记录登录日志失败: {e}")
            self.db.rollback()
        
        return {}
    
    def log_system_event(self, event_type: str, message: str, 
                        level: str = 'INFO',
                        user_id: Optional[int] = None,
                        admin_id: Optional[int] = None,
                        module: Optional[str] = None,
                        extra_data: Optional[Dict] = None) -> Dict:
        """
        记录系统日志
        
        Args:
            event_type: 事件类型（如：USER_CREATE, USER_DELETE, ATTENDANCE_CHECK等）
            message: 日志消息
            level: 日志级别
            user_id: 相关用户ID
            admin_id: 操作的管理员ID
            module: 模块名称
            extra_data: 额外数据
        """
        try:
            sql = text("""
                INSERT INTO system_log 
                (event_type, message, level, timestamp, user_id, admin_id, module, ip_address, extra_data)
                VALUES (:event_type, :message, :level, :timestamp, :user_id, :admin_id, :module, :ip_address, :extra_data)
            """)
            
            self.db.execute(sql, {
                'event_type': event_type,
                'message': message,
                'level': level,
                'timestamp': datetime.now(),
                'user_id': user_id,
                'admin_id': admin_id,
                'module': module,
                'ip_address': self._get_client_ip(),
                'extra_data': json.dumps(extra_data) if extra_data else None
            })
            self.db.commit()
        except Exception as e:
            print(f"记录系统日志失败: {e}")
            self.db.rollback()
        
        return {}
    
    def get_admin_login_logs(self, admin_id: Optional[int] = None,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            status: Optional[str] = None,
                            page: int = 1, 
                            size: int = 20) -> Dict[str, Any]:
        """
        获取管理员登录日志
        
        Args:
            admin_id: 管理员ID（筛选特定管理员）
            start_date: 开始日期
            end_date: 结束日期
            status: 登录状态（success/failed）
            page: 页码
            size: 每页大小
        """
        query = self.db.query(AdminLoginLog)
        
        # 添加筛选条件
        if admin_id:
            query = query.filter(AdminLoginLog.admin_id == admin_id)
        if start_date:
            query = query.filter(AdminLoginLog.login_time >= start_date)
        if end_date:
            query = query.filter(AdminLoginLog.login_time <= end_date)
        if status:
            query = query.filter(AdminLoginLog.login_status == status)
        
        # 按时间倒序排列
        query = query.order_by(desc(AdminLoginLog.login_time))
        
        # 分页
        total = query.count()
        logs = query.offset((page - 1) * size).limit(size).all()
        
        return {
            'total': total,
            'page': page,
            'size': size,
            'logs': [log.to_dict() for log in logs]
        }
    
    def get_system_logs(self, event_type: Optional[str] = None,
                       level: Optional[str] = None,
                       module: Optional[str] = None,
                       user_id: Optional[int] = None,
                       admin_id: Optional[int] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       page: int = 1,
                       size: int = 20) -> Dict[str, Any]:
        """
        获取系统日志
        
        Args:
            event_type: 事件类型
            level: 日志级别
            module: 模块名称
            user_id: 用户ID
            admin_id: 管理员ID
            start_date: 开始日期
            end_date: 结束日期
            page: 页码
            size: 每页大小
        """
        query = self.db.query(SystemLog)
        
        # 添加筛选条件
        if event_type:
            query = query.filter(SystemLog.event_type == event_type)
        if level:
            query = query.filter(SystemLog.level == level)
        if module:
            query = query.filter(SystemLog.module == module)
        if user_id:
            query = query.filter(SystemLog.user_id == user_id)
        if admin_id:
            query = query.filter(SystemLog.admin_id == admin_id)
        if start_date:
            query = query.filter(SystemLog.timestamp >= start_date)
        if end_date:
            query = query.filter(SystemLog.timestamp <= end_date)
        
        # 按时间倒序排列
        query = query.order_by(desc(SystemLog.timestamp))
        
        # 分页
        total = query.count()
        logs = query.offset((page - 1) * size).limit(size).all()
        
        return {
            'total': total,
            'page': page,
            'size': size,
            'logs': [log.to_dict() for log in logs]
        }
    
    def get_login_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        获取登录统计信息
        
        Args:
            days: 统计最近多少天
        """
        start_date = datetime.now() - timedelta(days=days)
        
        # 统计总登录次数
        total_logins = self.db.query(AdminLoginLog).filter(
            AdminLoginLog.login_time >= start_date
        ).count()
        
        # 统计成功登录次数
        success_logins = self.db.query(AdminLoginLog).filter(
            and_(
                AdminLoginLog.login_time >= start_date,
                AdminLoginLog.login_status == 'success'
            )
        ).count()
        
        # 统计失败登录次数
        failed_logins = self.db.query(AdminLoginLog).filter(
            and_(
                AdminLoginLog.login_time >= start_date,
                AdminLoginLog.login_status == 'failed'
            )
        ).count()
        
        # 按日期统计
        daily_stats = []
        for i in range(days):
            date = datetime.now().date() - timedelta(days=i)
            day_start = datetime.combine(date, datetime.min.time())
            day_end = datetime.combine(date, datetime.max.time())
            
            day_count = self.db.query(AdminLoginLog).filter(
                and_(
                    AdminLoginLog.login_time >= day_start,
                    AdminLoginLog.login_time <= day_end
                )
            ).count()
            
            daily_stats.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': day_count
            })
        
        daily_stats.reverse()  # 按日期正序
        
        return {
            'total_logins': total_logins,
            'success_logins': success_logins,
            'failed_logins': failed_logins,
            'success_rate': round(success_logins / total_logins * 100, 2) if total_logins > 0 else 0,
            'daily_stats': daily_stats
        }
    
    def get_system_log_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        获取系统日志统计
        
        Args:
            days: 统计最近多少天
        """
        start_date = datetime.now() - timedelta(days=days)
        
        # 按级别统计
        level_stats = {}
        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            count = self.db.query(SystemLog).filter(
                and_(
                    SystemLog.timestamp >= start_date,
                    SystemLog.level == level
                )
            ).count()
            level_stats[level.lower()] = count
        
        # 按事件类型统计（取前10个）
        from sqlalchemy import func
        event_stats = self.db.query(
            SystemLog.event_type,
            func.count(SystemLog.id).label('count')
        ).filter(
            SystemLog.timestamp >= start_date
        ).group_by(
            SystemLog.event_type
        ).order_by(
            desc('count')
        ).limit(10).all()
        
        # 按模块统计
        module_stats = self.db.query(
            SystemLog.module,
            func.count(SystemLog.id).label('count')
        ).filter(
            SystemLog.timestamp >= start_date
        ).group_by(
            SystemLog.module
        ).order_by(
            desc('count')
        ).all()
        
        return {
            'level_stats': level_stats,
            'event_stats': [
                {'event_type': event, 'count': count}
                for event, count in event_stats
            ],
            'module_stats': [
                {'module': module or '未知模块', 'count': count}
                for module, count in module_stats
            ]
        }
    
    def cleanup_old_logs(self, days: int = 90) -> int:
        """
        清理旧日志
        
        Args:
            days: 保留最近多少天的日志
        
        Returns:
            删除的日志数量
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 删除旧的登录日志
        deleted_login_logs = self.db.query(AdminLoginLog).filter(
            AdminLoginLog.login_time < cutoff_date
        ).delete()
        
        # 删除旧的系统日志
        deleted_system_logs = self.db.query(SystemLog).filter(
            SystemLog.timestamp < cutoff_date
        ).delete()
        
        self.db.commit()
        
        return deleted_login_logs + deleted_system_logs
    
    def _get_client_ip(self) -> str:
        """获取客户端IP地址"""
        if request.environ.get('HTTP_X_FORWARDED_FOR'):
            return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0]
        elif request.environ.get('HTTP_X_REAL_IP'):
            return request.environ.get('HTTP_X_REAL_IP')
        else:
            return request.environ.get('REMOTE_ADDR', '')
