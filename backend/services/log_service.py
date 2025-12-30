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
        """记录管理员登录日志"""
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
        """记录系统日志"""
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
        """获取管理员登录日志"""
        try:
            # 构建查询条件
            conditions = []
            params = {}
            
            if admin_id:
                conditions.append("admin_id = :admin_id")
                params['admin_id'] = admin_id
            if start_date:
                conditions.append("login_time >= :start_date")
                params['start_date'] = start_date
            if end_date:
                conditions.append("login_time <= :end_date")
                params['end_date'] = end_date
            if status:
                conditions.append("login_status = :status")
                params['status'] = status
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # 查询总数
            count_sql = text(f"SELECT COUNT(*) FROM admin_login_log WHERE {where_clause}")
            total = self.db.execute(count_sql, params).scalar()
            
            # 查询数据
            offset = (page - 1) * size
            query_sql = text(f"""
                SELECT * FROM admin_login_log 
                WHERE {where_clause}
                ORDER BY login_time DESC
                LIMIT :limit OFFSET :offset
            """)
            params['limit'] = size
            params['offset'] = offset
            
            result = self.db.execute(query_sql, params)
            logs = []
            for row in result:
                logs.append({
                    'id': row.id,
                    'admin_id': row.admin_id,
                    'username': row.username,
                    'login_time': row.login_time.strftime('%Y-%m-%d %H:%M:%S') if row.login_time else None,
                    'login_ip': row.login_ip,
                    'user_agent': row.user_agent,
                    'login_status': row.login_status,
                    'failure_reason': row.failure_reason
                })
            
            return {
                'total': total,
                'page': page,
                'size': size,
                'logs': logs
            }
        except Exception as e:
            print(f"获取登录日志失败: {e}")
            return {
                'total': 0,
                'page': page,
                'size': size,
                'logs': []
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
        """获取系统日志"""
        try:
            # 构建查询条件
            conditions = []
            params = {}
            
            if event_type:
                conditions.append("event_type = :event_type")
                params['event_type'] = event_type
            if level:
                conditions.append("level = :level")
                params['level'] = level
            if module:
                conditions.append("module = :module")
                params['module'] = module
            if user_id:
                conditions.append("user_id = :user_id")
                params['user_id'] = user_id
            if admin_id:
                conditions.append("admin_id = :admin_id")
                params['admin_id'] = admin_id
            if start_date:
                conditions.append("timestamp >= :start_date")
                params['start_date'] = start_date
            if end_date:
                conditions.append("timestamp <= :end_date")
                params['end_date'] = end_date
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # 查询总数
            count_sql = text(f"SELECT COUNT(*) FROM system_log WHERE {where_clause}")
            total = self.db.execute(count_sql, params).scalar()
            
            # 查询数据
            offset = (page - 1) * size
            query_sql = text(f"""
                SELECT * FROM system_log 
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT :limit OFFSET :offset
            """)
            params['limit'] = size
            params['offset'] = offset
            
            result = self.db.execute(query_sql, params)
            logs = []
            for row in result:
                logs.append({
                    'id': row.id,
                    'event_type': row.event_type,
                    'message': row.message,
                    'level': row.level,
                    'timestamp': row.timestamp.strftime('%Y-%m-%d %H:%M:%S') if row.timestamp else None,
                    'user_id': row.user_id,
                    'admin_id': row.admin_id,
                    'module': row.module,
                    'ip_address': row.ip_address,
                    'extra_data': row.extra_data
                })
            
            return {
                'total': total,
                'page': page,
                'size': size,
                'logs': logs
            }
        except Exception as e:
            print(f"获取系统日志失败: {e}")
            return {
                'total': 0,
                'page': page,
                'size': size,
                'logs': []
            }
    
    def get_login_statistics(self, days: int = 7) -> Dict[str, Any]:
        """获取登录统计信息"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # 统计总登录次数 - 不限制时间范围
            sql = text("SELECT COUNT(*) FROM admin_login_log")
            total_logins = self.db.execute(sql).scalar() or 0
            print(f"总登录次数: {total_logins}")
            
            # 统计成功登录次数
            sql = text("SELECT COUNT(*) FROM admin_login_log WHERE LOWER(login_status) = LOWER('success')")
            success_logins = self.db.execute(sql).scalar() or 0
            print(f"成功登录次数: {success_logins}")
            
            # 统计失败登录次数
            sql = text("SELECT COUNT(*) FROM admin_login_log WHERE LOWER(login_status) = LOWER('failed')")
            failed_logins = self.db.execute(sql).scalar() or 0
            print(f"失败登录次数: {failed_logins}")
            
            # 查看所有登录状态
            debug_sql = text("SELECT DISTINCT login_status FROM admin_login_log")
            statuses = self.db.execute(debug_sql).fetchall()
            print(f"所有登录状态: {[row[0] for row in statuses]}")
            
            # 成功率
            success_rate = (success_logins / total_logins * 100) if total_logins > 0 else 0
            
            # 按日期统计
            daily_stats = []
            for i in range(days):
                date = datetime.now().date() - timedelta(days=i)
                day_start = datetime.combine(date, datetime.min.time())
                day_end = datetime.combine(date, datetime.max.time())
                
                sql = text("""
                    SELECT COUNT(*) FROM admin_login_log 
                    WHERE login_time >= :start AND login_time <= :end
                """)
                day_count = self.db.execute(sql, {'start': day_start, 'end': day_end}).scalar()
                
                daily_stats.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': day_count
                })
            
            return {
                'total_logins': total_logins,
                'success_logins': success_logins,
                'failed_logins': failed_logins,
                'success_rate': round(success_rate, 2),
                'daily_stats': daily_stats
            }
        except Exception as e:
            print(f"获取登录统计失败: {e}")
            return {
                'total_logins': 0,
                'success_logins': 0,
                'failed_logins': 0,
                'success_rate': 0,
                'daily_stats': []
            }
    
    def get_system_log_statistics(self, days: int = 7) -> Dict[str, Any]:
        """获取系统日志统计"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # 按级别统计 - 不限制时间范围，获取所有日志的统计
            level_stats = {}
            for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                sql = text("""
                    SELECT COUNT(*) FROM system_log 
                    WHERE UPPER(level) = UPPER(:level)
                """)
                count = self.db.execute(sql, {'level': level}).scalar() or 0
                level_stats[level.lower()] = count
                print(f"统计 {level} 级别日志: {count} 条")
            
            # 获取总数
            total_sql = text("SELECT COUNT(*) FROM system_log")
            total_count = self.db.execute(total_sql).scalar() or 0
            print(f"系统日志总数: {total_count}")
            
            # 查看所有日志级别
            debug_sql = text("SELECT DISTINCT level FROM system_log")
            levels = self.db.execute(debug_sql).fetchall()
            print(f"所有日志级别: {[row[0] for row in levels]}")
            
            # 按事件类型统计（前10个）
            sql = text("""
                SELECT event_type, COUNT(*) as count 
                FROM system_log 
                WHERE timestamp >= :start_date 
                GROUP BY event_type 
                ORDER BY count DESC 
                LIMIT 10
            """)
            result = self.db.execute(sql, {'start_date': start_date})
            event_stats = [{'event_type': row[0], 'count': row[1]} for row in result]
            
            # 按模块统计（前10个）
            sql = text("""
                SELECT module, COUNT(*) as count 
                FROM system_log 
                WHERE timestamp >= :start_date AND module IS NOT NULL
                GROUP BY module 
                ORDER BY count DESC 
                LIMIT 10
            """)
            result = self.db.execute(sql, {'start_date': start_date})
            module_stats = [{'module': row[0], 'count': row[1]} for row in result]
            
            return {
                'level_stats': level_stats,
                'event_stats': event_stats,
                'module_stats': module_stats
            }
        except Exception as e:
            print(f"获取系统日志统计失败: {e}")
            return {
                'level_stats': {
                    'debug': 0,
                    'info': 0,
                    'warning': 0,
                    'error': 0,
                    'critical': 0
                },
                'event_stats': [],
                'module_stats': []
            }
    
    def cleanup_old_logs(self, days: int = 90) -> int:
        """清理旧日志"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 清理登录日志
            sql = text("DELETE FROM admin_login_log WHERE login_time < :cutoff_date")
            result1 = self.db.execute(sql, {'cutoff_date': cutoff_date})
            
            # 清理系统日志
            sql = text("DELETE FROM system_log WHERE timestamp < :cutoff_date")
            result2 = self.db.execute(sql, {'cutoff_date': cutoff_date})
            
            self.db.commit()
            
            total_deleted = result1.rowcount + result2.rowcount
            print(f"清理了 {total_deleted} 条旧日志")
            return total_deleted
        except Exception as e:
            print(f"清理日志失败: {e}")
            self.db.rollback()
            return 0
    
    def _get_client_ip(self) -> str:
        """获取客户端IP地址"""
        try:
            if request.environ.get('HTTP_X_FORWARDED_FOR'):
                return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0]
            elif request.environ.get('HTTP_X_REAL_IP'):
                return request.environ.get('HTTP_X_REAL_IP')
            else:
                return request.environ.get('REMOTE_ADDR', '')
        except:
            return ''
