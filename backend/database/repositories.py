"""
数据访问层 (Repository Pattern)
封装数据库CRUD操作
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from .models import db, User, Attendance, SystemLog


class UserRepository:
    """用户数据访问"""
    
    @staticmethod
    def create(username: str, student_id: Optional[str] = None, **kwargs) -> User:
        """创建用户"""
        user = User(username=username, student_id=student_id, **kwargs)
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return User.query.get(user_id)
    
    @staticmethod
    def get_by_username(username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def get_by_student_id(student_id: str) -> Optional[User]:
        """根据学号获取用户"""
        return User.query.filter_by(student_id=student_id).first()
    
    @staticmethod
    def get_all(active_only: bool = True) -> List[User]:
        """获取所有用户"""
        query = User.query
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(User.created_at.desc()).all()
    
    @staticmethod
    def search(keyword: str, active_only: bool = True) -> List[User]:
        """搜索用户"""
        query = User.query.filter(
            or_(
                User.username.like(f'%{keyword}%'),
                User.student_id.like(f'%{keyword}%')
            )
        )
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(User.created_at.desc()).all()
    
    @staticmethod
    def update(user_id: int, **kwargs) -> Optional[User]:
        """更新用户"""
        user = User.query.get(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            db.session.commit()
        return user
    
    @staticmethod
    def delete(user_id: int) -> bool:
        """删除用户(软删除)"""
        user = User.query.get(user_id)
        if user:
            user.is_active = False
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def hard_delete(user_id: int) -> bool:
        """硬删除用户（级联删除关联记录）"""
        user = User.query.get(user_id)
        if user:
            # 先删除关联的系统日志（避免外键约束错误）
            SystemLog.query.filter_by(user_id=user_id).delete()
            
            # 删除用户（attendance会通过cascade自动删除）
            db.session.delete(user)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def count(active_only: bool = True) -> int:
        """统计用户数量"""
        query = User.query
        if active_only:
            query = query.filter_by(is_active=True)
        return query.count()


class AttendanceRepository:
    """考勤数据访问"""
    
    @staticmethod
    def create(user_id: int, status: str = 'present', **kwargs) -> Attendance:
        """创建考勤记录"""
        attendance = Attendance(user_id=user_id, status=status, **kwargs)
        db.session.add(attendance)
        db.session.commit()
        return attendance
    
    @staticmethod
    def get_by_id(attendance_id: int) -> Optional[Attendance]:
        """根据ID获取考勤记录"""
        return Attendance.query.get(attendance_id)
    
    @staticmethod
    def get_by_user(user_id: int, limit: int = 100) -> List[Attendance]:
        """获取用户的考勤记录"""
        return Attendance.query.filter_by(user_id=user_id)\
            .order_by(Attendance.timestamp.desc())\
            .limit(limit).all()
    
    @staticmethod
    def get_by_date_range(start_date: datetime, end_date: datetime, 
                          user_id: Optional[int] = None) -> List[Attendance]:
        """获取日期范围内的考勤记录"""
        query = Attendance.query.filter(
            and_(
                Attendance.timestamp >= start_date,
                Attendance.timestamp <= end_date
            )
        )
        if user_id:
            query = query.filter_by(user_id=user_id)
        return query.order_by(Attendance.timestamp.desc()).all()
    
    @staticmethod
    def get_today(user_id: Optional[int] = None) -> List[Attendance]:
        """获取今天的考勤记录"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        return AttendanceRepository.get_by_date_range(today_start, today_end, user_id)
    
    @staticmethod
    def check_today_attendance(user_id: int) -> bool:
        """检查用户今天是否已打卡"""
        today_records = AttendanceRepository.get_today(user_id)
        return len(today_records) > 0
    
    @staticmethod
    def get_paginated(page: int = 1, per_page: int = 20, 
                     filters: Optional[Dict[str, Any]] = None) -> Dict:
        """分页获取考勤记录"""
        query = Attendance.query
        
        # 应用过滤器
        if filters:
            if 'user_id' in filters:
                query = query.filter_by(user_id=filters['user_id'])
            if 'status' in filters:
                query = query.filter_by(status=filters['status'])
            if 'check_type' in filters:
                query = query.filter_by(check_type=filters['check_type'])
            if 'department_id' in filters:
                # 筛选指定部门及其所有子部门的用户
                from database.models import Department
                dept = Department.query.get(filters['department_id'])
                if dept:
                    # 获取该部门及所有子部门的ID
                    dept_ids = [dept.id]
                    def get_child_ids(parent_id):
                        children = Department.query.filter_by(parent_id=parent_id).all()
                        for child in children:
                            dept_ids.append(child.id)
                            get_child_ids(child.id)
                    get_child_ids(dept.id)
                    
                    # 筛选这些部门的用户
                    query = query.join(User).filter(User.department_id.in_(dept_ids))
            if 'start_date' in filters and 'end_date' in filters:
                query = query.filter(
                    and_(
                        Attendance.timestamp >= filters['start_date'],
                        Attendance.timestamp <= filters['end_date']
                    )
                )
        
        # 分页
        pagination = query.order_by(Attendance.timestamp.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'items': [item.to_dict() for item in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    
    @staticmethod
    def get_statistics(start_date: datetime, end_date: datetime, department_id: Optional[int] = None) -> Dict:
        """获取统计数据"""
        query = Attendance.query.filter(
            and_(
                Attendance.timestamp >= start_date,
                Attendance.timestamp < end_date
            )
        )
        
        # 如果指定了部门，筛选该部门及其子部门的用户
        if department_id:
            from database.models import Department
            dept = Department.query.get(department_id)
            if dept:
                # 获取该部门及所有子部门的ID
                dept_ids = [dept.id]
                def get_child_ids(parent_id):
                    children = Department.query.filter_by(parent_id=parent_id).all()
                    for child in children:
                        dept_ids.append(child.id)
                        get_child_ids(child.id)
                get_child_ids(dept.id)
                
                # 筛选这些部门的用户
                query = query.join(User).filter(User.department_id.in_(dept_ids))
        
        records = query.all()
        
        total = len(records)
        status_count = {}
        user_count = {}
        
        for record in records:
            # 统计状态
            status = record.status
            status_count[status] = status_count.get(status, 0) + 1
            
            # 统计用户
            user_id = record.user_id
            user_count[user_id] = user_count.get(user_id, 0) + 1
        
        return {
            'total': total,
            'status_distribution': status_count,
            'unique_users': len(user_count),
            'user_attendance': user_count
        }
    
    @staticmethod
    def delete(attendance_id: int) -> bool:
        """删除考勤记录"""
        attendance = Attendance.query.get(attendance_id)
        if attendance:
            db.session.delete(attendance)
            db.session.commit()
            return True
        return False


class SystemLogRepository:
    """系统日志数据访问"""
    
    @staticmethod
    def create(event_type: str, message: str, level: str = 'INFO', **kwargs) -> SystemLog:
        """创建日志"""
        log = SystemLog(event_type=event_type, message=message, level=level, **kwargs)
        db.session.add(log)
        db.session.commit()
        return log
    
    @staticmethod
    def get_recent(limit: int = 100, level: Optional[str] = None) -> List[SystemLog]:
        """获取最近的日志"""
        query = SystemLog.query
        if level:
            query = query.filter_by(level=level)
        return query.order_by(SystemLog.timestamp.desc()).limit(limit).all()
    
    @staticmethod
    def get_by_event_type(event_type: str, limit: int = 100) -> List[SystemLog]:
        """根据事件类型获取日志"""
        return SystemLog.query.filter_by(event_type=event_type)\
            .order_by(SystemLog.timestamp.desc())\
            .limit(limit).all()
    
    @staticmethod
    def get_by_user(user_id: int, limit: int = 100) -> List[SystemLog]:
        """获取用户相关日志"""
        return SystemLog.query.filter_by(user_id=user_id)\
            .order_by(SystemLog.timestamp.desc())\
            .limit(limit).all()
    
    @staticmethod
    def cleanup_old_logs(days: int = 30) -> int:
        """清理旧日志"""
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted = SystemLog.query.filter(SystemLog.timestamp < cutoff_date).delete()
        db.session.commit()
        return deleted
