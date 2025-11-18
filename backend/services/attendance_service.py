"""
考勤服务
处理考勤打卡和统计的业务逻辑
"""
import numpy as np
import cv2
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import csv

from database.repositories import AttendanceRepository, UserRepository, SystemLogRepository
from database.models import Attendance
from config.settings import Config
from .face_service import FaceService


class AttendanceService:
    """考勤管理服务"""
    
    def __init__(self):
        """初始化考勤服务"""
        self.attendance_repo = AttendanceRepository
        self.user_repo = UserRepository
        self.log_repo = SystemLogRepository
        self.face_service = FaceService()
    
    def check_in(self, image: np.ndarray, status: str = 'present') -> Optional[Dict]:
        """
        考勤打卡
        
        Args:
            image: 打卡图像
            status: 考勤状态 (present, late, absent)
            
        Returns:
            {
                'success': bool,
                'user_id': int,
                'username': str,
                'confidence': float,
                'message': str,
                'attendance': Attendance
            } or None
        """
        try:
            # 检测并识别人脸
            result = self.face_service.detect_largest_face_and_recognize(image)
            
            if result is None:
                return {
                    'success': False,
                    'message': '未检测到人脸'
                }
            
            user_id = result['user_id']
            confidence = result['confidence']
            
            if user_id is None:
                return {
                    'success': False,
                    'message': '未识别到用户',
                    'confidence': confidence
                }
            
            # 获取用户信息
            user = self.user_repo.get_by_id(user_id)
            if not user:
                return {
                    'success': False,
                    'message': '用户不存在'
                }
            
            # 检查今天是否已打卡 (测试模式：已禁用)
            # if self.attendance_repo.check_today_attendance(user_id):
            #     return {
            #         'success': False,
            #         'user_id': user_id,
            #         'username': user.username,
            #         'message': '今天已打卡'
            #     }
            
            # 保存打卡图像(可选)
            image_path = None
            # TODO: 实现图像保存逻辑
            
            # 创建考勤记录
            attendance = self.attendance_repo.create(
                user_id=user_id,
                status=status,
                confidence=confidence,
                image_path=image_path
            )
            
            # 记录日志
            self.log_repo.create(
                event_type='check_in',
                message=f"用户 {user.username} 打卡成功",
                user_id=user_id
            )
            
            print(f"✓ 打卡成功: {user.username} (置信度: {confidence:.2f})")
            
            return {
                'success': True,
                'user_id': user_id,
                'username': user.username,
                'student_id': user.student_id,
                'confidence': confidence,
                'message': '打卡成功',
                'attendance': attendance
            }
        
        except Exception as e:
            print(f"✗ 打卡失败: {e}")
            return {
                'success': False,
                'message': f'打卡失败: {str(e)}'
            }
    
    def get_attendance_history(self, filters: Optional[Dict] = None, 
                              page: int = 1, per_page: int = 20) -> Dict:
        """
        获取考勤历史
        
        Args:
            filters: 过滤条件 {'user_id', 'status', 'start_date', 'end_date'}
            page: 页码
            per_page: 每页数量
            
        Returns:
            分页数据
        """
        return self.attendance_repo.get_paginated(page, per_page, filters)
    
    def get_user_attendance(self, user_id: int, limit: int = 100) -> List[Attendance]:
        """获取用户的考勤记录"""
        return self.attendance_repo.get_by_user(user_id, limit)
    
    def get_today_attendance(self, user_id: Optional[int] = None) -> List[Attendance]:
        """获取今天的考勤记录"""
        return self.attendance_repo.get_today(user_id)
    
    def get_date_range_attendance(self, start_date: datetime, end_date: datetime,
                                  user_id: Optional[int] = None) -> List[Attendance]:
        """获取日期范围内的考勤记录"""
        return self.attendance_repo.get_by_date_range(start_date, end_date, user_id)
    
    def get_daily_statistics(self, date: Optional[datetime] = None) -> Dict:
        """
        获取每日统计
        
        Args:
            date: 日期(默认今天)
            
        Returns:
            统计数据
        """
        if date is None:
            date = datetime.now()
        
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        stats = self.attendance_repo.get_statistics(start_date, end_date)
        
        # 添加额外信息
        total_users = self.user_repo.count(active_only=True)
        stats['total_users'] = total_users
        stats['attendance_rate'] = (stats['unique_users'] / total_users * 100) if total_users > 0 else 0
        stats['date'] = start_date.strftime('%Y-%m-%d')
        
        return stats
    
    def get_weekly_statistics(self, start_date: Optional[datetime] = None) -> Dict:
        """
        获取周统计
        
        Args:
            start_date: 周开始日期(默认本周一)
            
        Returns:
            统计数据
        """
        if start_date is None:
            today = datetime.now()
            start_date = today - timedelta(days=today.weekday())
        
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=7)
        
        stats = self.attendance_repo.get_statistics(start_date, end_date)
        
        # 按天统计
        daily_stats = []
        for i in range(7):
            day = start_date + timedelta(days=i)
            day_stats = self.get_daily_statistics(day)
            daily_stats.append(day_stats)
        
        stats['daily_breakdown'] = daily_stats
        stats['start_date'] = start_date.strftime('%Y-%m-%d')
        stats['end_date'] = end_date.strftime('%Y-%m-%d')
        
        return stats
    
    def get_monthly_statistics(self, year: Optional[int] = None, 
                               month: Optional[int] = None) -> Dict:
        """
        获取月统计
        
        Args:
            year: 年份(默认今年)
            month: 月份(默认本月)
            
        Returns:
            统计数据
        """
        if year is None or month is None:
            now = datetime.now()
            year = year or now.year
            month = month or now.month
        
        start_date = datetime(year, month, 1)
        
        # 计算月末
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        stats = self.attendance_repo.get_statistics(start_date, end_date)
        stats['year'] = year
        stats['month'] = month
        
        return stats
    
    def get_user_statistics(self, user_id: int, days: int = 30) -> Dict:
        """
        获取用户统计
        
        Args:
            user_id: 用户ID
            days: 统计天数
            
        Returns:
            用户统计数据
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        records = self.get_date_range_attendance(start_date, end_date, user_id)
        
        total = len(records)
        status_count = {}
        
        for record in records:
            status = record.status
            status_count[status] = status_count.get(status, 0) + 1
        
        # 计算出勤率
        attendance_rate = (status_count.get('present', 0) / days * 100) if days > 0 else 0
        
        return {
            'user_id': user_id,
            'total_records': total,
            'status_distribution': status_count,
            'attendance_rate': attendance_rate,
            'days': days
        }
    
    def export_to_csv(self, start_date: datetime, end_date: datetime, 
                     filepath: Optional[str] = None) -> str:
        """
        导出考勤记录到CSV
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            filepath: 文件路径(可选)
            
        Returns:
            文件路径
        """
        if filepath is None:
            filename = f"attendance_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
            filepath = Config.DATA_DIR / filename
        
        records = self.get_date_range_attendance(start_date, end_date)
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            # 写入表头
            writer.writerow(['ID', '用户ID', '用户名', '学号', '时间', '状态', '置信度'])
            
            # 写入数据
            for record in records:
                writer.writerow([
                    record.id,
                    record.user_id,
                    record.user.username if record.user else '',
                    record.user.student_id if record.user else '',
                    record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    record.status,
                    f"{record.confidence:.2f}" if record.confidence else ''
                ])
        
        print(f"✓ 导出成功: {filepath}")
        return str(filepath)
    
    def delete_attendance(self, attendance_id: int) -> bool:
        """删除考勤记录"""
        return self.attendance_repo.delete(attendance_id)


if __name__ == '__main__':
    # 测试考勤服务
    from database.init_db import create_app
    
    app = create_app()
    with app.app_context():
        service = AttendanceService()
        
        # 今日统计
        stats = service.get_daily_statistics()
        print("\n今日考勤统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # 获取今日记录
        today_records = service.get_today_attendance()
        print(f"\n今日打卡记录 ({len(today_records)}):")
        for record in today_records[:5]:
            print(f"  {record.user.username}: {record.timestamp.strftime('%H:%M:%S')}")
