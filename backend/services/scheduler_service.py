"""
定时任务服务
用于自动检测缺勤、生成统计报表等定时任务
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, date, timedelta
from database.models import db, Attendance, User
from database.models_v3 import AttendanceRule
from services.attendance_rule_service import AttendanceRuleService
import logging

logger = logging.getLogger(__name__)


class SchedulerService:
    """定时任务服务"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        logger.info("定时任务调度器已启动")
    
    def start_all_jobs(self):
        """启动所有定时任务"""
        # 每天23:00检查缺勤
        self.scheduler.add_job(
            func=self.check_daily_absence,
            trigger=CronTrigger(hour=23, minute=0),
            id='check_daily_absence',
            name='每日缺勤检查',
            replace_existing=True
        )
        logger.info("已添加定时任务: 每日缺勤检查 (23:00)")
        
        # 可以添加更多定时任务
        # self.scheduler.add_job(...)
    
    def check_daily_absence(self):
        """
        检查今天的缺勤情况
        为没有打卡记录的用户自动创建缺勤记录
        """
        try:
            logger.info("="*70)
            logger.info("开始执行每日缺勤检查")
            logger.info(f"检查日期: {date.today()}")
            
            today = date.today()
            weekday = datetime.now().isoweekday()  # 1-7 (Monday-Sunday)
            
            # 获取所有启用的考勤规则
            rules = AttendanceRule.query.filter_by(is_active=True).all()
            
            absence_count = 0
            checked_users = set()
            
            for rule in rules:
                # 检查今天是否为工作日
                work_days = [int(d) for d in rule.work_days.split(',') if d.strip()]
                if weekday not in work_days:
                    logger.info(f"规则 [{rule.name}] 今天不是工作日，跳过")
                    continue
                
                # 开放模式不记录缺勤
                if rule.is_open_mode:
                    logger.info(f"规则 [{rule.name}] 是开放模式，跳过缺勤检查")
                    continue
                
                # 获取应用此规则的用户
                if rule.department_id:
                    # 部门规则
                    users = User.query.filter_by(department_id=rule.department_id).all()
                elif rule.is_default:
                    # 默认规则：没有专属规则的用户
                    all_users = User.query.all()
                    dept_rule_depts = [r.department_id for r in rules if r.department_id and r.is_active]
                    users = [u for u in all_users if u.department_id not in dept_rule_depts]
                else:
                    users = []
                
                for user in users:
                    # 避免重复检查
                    if user.id in checked_users:
                        continue
                    checked_users.add(user.id)
                    
                    # 检查今天是否有打卡记录
                    attendance_records = Attendance.query.filter(
                        Attendance.user_id == user.id,
                        db.func.date(Attendance.timestamp) == today
                    ).all()
                    
                    if not attendance_records:
                        # 没有任何打卡记录，创建缺勤记录
                        # 上班缺勤
                        checkin_absence = Attendance(
                            user_id=user.id,
                            timestamp=datetime.combine(today, rule.work_start_time),
                            status='absent',
                            check_type='checkin',
                            is_late=False,
                            is_early=False,
                            rule_id=rule.id,
                            notes='系统自动标记：未打卡'
                        )
                        db.session.add(checkin_absence)
                        
                        # 下班缺勤
                        checkout_absence = Attendance(
                            user_id=user.id,
                            timestamp=datetime.combine(today, rule.work_end_time),
                            status='absent',
                            check_type='checkout',
                            is_late=False,
                            is_early=False,
                            rule_id=rule.id,
                            notes='系统自动标记：未打卡'
                        )
                        db.session.add(checkout_absence)
                        
                        absence_count += 2
                        logger.info(f"用户 [{user.username}] 今天未打卡，已标记缺勤")
                    else:
                        # 检查是否缺少上班或下班打卡
                        has_checkin = any(r.check_type == 'checkin' for r in attendance_records)
                        has_checkout = any(r.check_type == 'checkout' for r in attendance_records)
                        
                        if not has_checkin:
                            # 缺少上班打卡
                            checkin_absence = Attendance(
                                user_id=user.id,
                                timestamp=datetime.combine(today, rule.work_start_time),
                                status='absent',
                                check_type='checkin',
                                is_late=False,
                                is_early=False,
                                rule_id=rule.id,
                                notes='系统自动标记：未上班打卡'
                            )
                            db.session.add(checkin_absence)
                            absence_count += 1
                            logger.info(f"用户 [{user.username}] 今天未上班打卡，已标记缺勤")
                        
                        if not has_checkout:
                            # 缺少下班打卡
                            checkout_absence = Attendance(
                                user_id=user.id,
                                timestamp=datetime.combine(today, rule.work_end_time),
                                status='absent',
                                check_type='checkout',
                                is_late=False,
                                is_early=False,
                                rule_id=rule.id,
                                notes='系统自动标记：未下班打卡'
                            )
                            db.session.add(checkout_absence)
                            absence_count += 1
                            logger.info(f"用户 [{user.username}] 今天未下班打卡，已标记缺勤")
            
            # 提交所有缺勤记录
            db.session.commit()
            
            logger.info(f"每日缺勤检查完成")
            logger.info(f"检查用户数: {len(checked_users)}")
            logger.info(f"创建缺勤记录: {absence_count} 条")
            logger.info("="*70)
            
        except Exception as e:
            logger.error(f"每日缺勤检查失败: {str(e)}")
            db.session.rollback()
    
    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()
        logger.info("定时任务调度器已关闭")


# 全局调度器实例
scheduler_service = None


def init_scheduler(app):
    """初始化定时任务调度器"""
    global scheduler_service
    
    with app.app_context():
        scheduler_service = SchedulerService()
        scheduler_service.start_all_jobs()
        logger.info("定时任务系统初始化完成")
    
    return scheduler_service


def get_scheduler():
    """获取调度器实例"""
    return scheduler_service
