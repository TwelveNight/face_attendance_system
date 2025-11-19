"""
考勤规则管理服务
提供考勤规则的CRUD操作和规则应用逻辑
"""
from typing import List, Dict, Optional
from datetime import datetime, time
from database.models_v3 import AttendanceRule, db


class AttendanceRuleService:
    """考勤规则服务类"""
    
    @staticmethod
    def get_all_rules(include_inactive: bool = False) -> List[AttendanceRule]:
        """
        获取所有考勤规则
        
        Args:
            include_inactive: 是否包含未启用的规则
            
        Returns:
            规则列表
        """
        query = AttendanceRule.query
        if not include_inactive:
            query = query.filter_by(is_active=True)
        return query.order_by(AttendanceRule.id).all()
    
    @staticmethod
    def get_rule_by_id(rule_id: int) -> Optional[AttendanceRule]:
        """
        根据ID获取规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            规则对象或None
        """
        return AttendanceRule.query.get(rule_id)
    
    @staticmethod
    def get_default_rule() -> Optional[AttendanceRule]:
        """
        获取默认规则
        
        Returns:
            默认规则对象或None
        """
        return AttendanceRule.query.filter_by(is_default=True, is_active=True).first()
    
    @staticmethod
    def get_rule_by_department(department_id: int) -> Optional[AttendanceRule]:
        """
        获取部门的考勤规则
        如果部门没有专属规则，向上查找父部门规则，最后返回默认规则
        
        优先级：
        1. 部门专属规则（按ID降序，最新的优先）
        2. 父部门规则（逐级向上查找）
        3. 默认规则
        
        Args:
            department_id: 部门ID
            
        Returns:
            规则对象或None
        """
        from database.models_v3 import Department
        
        # 先查找部门专属规则（按ID降序，最新创建的优先）
        rule = AttendanceRule.query.filter_by(
            department_id=department_id,
            is_active=True
        ).order_by(AttendanceRule.id.desc()).first()
        
        # 如果没有专属规则，向上查找父部门规则
        if not rule:
            dept = Department.query.get(department_id)
            while dept and dept.parent_id:
                parent_rule = AttendanceRule.query.filter_by(
                    department_id=dept.parent_id,
                    is_active=True
                ).order_by(AttendanceRule.id.desc()).first()
                
                if parent_rule:
                    return parent_rule
                
                # 继续向上查找
                dept = Department.query.get(dept.parent_id)
        
        # 如果还是没有，返回默认规则
        if not rule:
            rule = AttendanceRuleService.get_default_rule()
        
        return rule
    
    @staticmethod
    def get_rule_for_user(user_id: int) -> Optional[AttendanceRule]:
        """
        获取用户的考勤规则
        根据用户所属部门查找规则
        
        Args:
            user_id: 用户ID
            
        Returns:
            规则对象或None
        """
        from database.models import User
        user = User.query.get(user_id)
        
        if not user:
            return None
        
        # 如果用户有部门，查找部门规则
        if user.department_id:
            return AttendanceRuleService.get_rule_by_department(user.department_id)
        
        # 否则返回默认规则
        return AttendanceRuleService.get_default_rule()
    
    @staticmethod
    def create_rule(name: str, work_start_time: time, work_end_time: time,
                   late_threshold: int = 0, early_threshold: int = 0,
                   work_days: str = '1,2,3,4,5', department_id: Optional[int] = None,
                   is_default: bool = False, is_open_mode: bool = False,
                   description: str = None,
                   checkin_before_minutes: int = 0,
                   enable_once_per_day: bool = True) -> AttendanceRule:
        """
        创建考勤规则
        
        Args:
            name: 规则名称
            work_start_time: 上班时间
            work_end_time: 下班时间
            late_threshold: 迟到阈值（分钟）
            early_threshold: 早退阈值（分钟）
            work_days: 工作日（逗号分隔的数字，1-7）
            department_id: 关联部门ID
            is_default: 是否为默认规则
            is_open_mode: 是否为开放模式
            description: 描述
            checkin_before_minutes: 上班打卡可提前多少分钟(0表示不限制)
            enable_once_per_day: 是否限制每天只能打卡一次
            
        Returns:
            创建的规则对象
        """
        # 如果设置为默认规则，取消其他规则的默认状态
        if is_default:
            AttendanceRule.query.filter_by(is_default=True).update({'is_default': False})
        
        rule = AttendanceRule(
            name=name,
            work_start_time=work_start_time,
            work_end_time=work_end_time,
            late_threshold=late_threshold,
            early_threshold=early_threshold,
            work_days=work_days,
            department_id=department_id,
            is_default=is_default,
            is_open_mode=is_open_mode,
            description=description,
            is_active=True,
            checkin_before_minutes=checkin_before_minutes,
            enable_once_per_day=enable_once_per_day
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return rule
    
    @staticmethod
    def update_rule(rule_id: int, **kwargs) -> Optional[AttendanceRule]:
        """
        更新考勤规则
        
        Args:
            rule_id: 规则ID
            **kwargs: 要更新的字段
            
        Returns:
            更新后的规则对象或None
        """
        rule = AttendanceRule.query.get(rule_id)
        if not rule:
            return None
        
        # 如果设置为默认规则，取消其他规则的默认状态
        if kwargs.get('is_default') and not rule.is_default:
            AttendanceRule.query.filter_by(is_default=True).update({'is_default': False})
        
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        db.session.commit()
        return rule
    
    @staticmethod
    def delete_rule(rule_id: int) -> bool:
        """
        删除考勤规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            是否删除成功
        """
        rule = AttendanceRule.query.get(rule_id)
        if not rule:
            return False
        
        # 不允许删除默认规则
        if rule.is_default:
            raise ValueError("不能删除默认规则")
        
        db.session.delete(rule)
        db.session.commit()
        return True
    
    @staticmethod
    def determine_checkin_type(rule: AttendanceRule, check_time: datetime) -> str:
        """
        根据当前时间自动判断是上班打卡还是下班打卡
        
        Args:
            rule: 考勤规则
            check_time: 打卡时间
            
        Returns:
            'checkin' 或 'checkout'
        """
        check_time_only = check_time.time()
        work_start = rule.work_start_time
        work_end = rule.work_end_time
        
        # 计算上下班时间的中点
        start_minutes = work_start.hour * 60 + work_start.minute
        end_minutes = work_end.hour * 60 + work_end.minute
        check_minutes = check_time_only.hour * 60 + check_time_only.minute
        
        # 如果在中点之前，判断为上班打卡；否则为下班打卡
        midpoint = (start_minutes + end_minutes) / 2
        
        if check_minutes < midpoint:
            return 'checkin'
        else:
            return 'checkout'
    
    @staticmethod
    def check_attendance_status(rule: AttendanceRule, check_time: datetime, 
                               check_type: str = None) -> Dict:
        """
        根据规则检查考勤状态
        
        Args:
            rule: 考勤规则
            check_time: 打卡时间
            check_type: 打卡类型（checkin/checkout），None表示自动判断
            
        Returns:
            状态信息字典 {'status': 'present/late/early', 'is_late': bool, 'is_early': bool, 'minutes': int}
        """
        # 如果未指定打卡类型，自动判断
        if check_type is None:
            check_type = AttendanceRuleService.determine_checkin_type(rule, check_time)
        
        # 开放模式：任何时间打卡都是正常
        if rule.is_open_mode:
            return {
                'status': 'present',
                'is_late': False,
                'is_early': False,
                'minutes': 0,
                'message': '开放模式，打卡成功'
            }
        
        # 检查是否为工作日
        weekday = check_time.isoweekday()  # 1-7 (Monday-Sunday)
        work_days = [int(d) for d in rule.work_days.split(',') if d.strip()]
        
        if weekday not in work_days:
            return {
                'status': 'present',
                'is_late': False,
                'is_early': False,
                'minutes': 0,
                'message': '非工作日打卡'
            }
        
        check_time_only = check_time.time()
        
        if check_type == 'checkin':
            # 上班打卡
            target_time = rule.work_start_time
            threshold = rule.late_threshold
            
            # 计算时间差（分钟）
            time_diff = AttendanceRuleService._time_diff_minutes(check_time_only, target_time)
            
            if time_diff > threshold:
                # 迟到
                return {
                    'status': 'late',
                    'is_late': True,
                    'is_early': False,
                    'minutes': time_diff,
                    'message': f'迟到 {time_diff} 分钟'
                }
            else:
                # 正常
                return {
                    'status': 'present',
                    'is_late': False,
                    'is_early': False,
                    'minutes': 0,
                    'message': '上班打卡成功'
                }
        
        elif check_type == 'checkout':
            # 下班打卡
            target_time = rule.work_end_time
            threshold = rule.early_threshold
            
            # 计算时间差（分钟）
            time_diff = AttendanceRuleService._time_diff_minutes(target_time, check_time_only)
            
            if time_diff > threshold:
                # 早退
                return {
                    'status': 'early',
                    'is_late': False,
                    'is_early': True,
                    'minutes': time_diff,
                    'message': f'早退 {time_diff} 分钟'
                }
            else:
                # 正常
                return {
                    'status': 'present',
                    'is_late': False,
                    'is_early': False,
                    'minutes': 0,
                    'message': '下班打卡成功'
                }
        
        return {
            'status': 'present',
            'is_late': False,
            'is_early': False,
            'minutes': 0,
            'message': '打卡成功'
        }
    
    @staticmethod
    def check_rule_conflicts() -> List[Dict]:
        """
        检查规则冲突
        
        Returns:
            冲突列表，每项包含 {type, message, rules}
        """
        conflicts = []
        
        # 检查1：多个默认规则
        default_rules = AttendanceRule.query.filter_by(is_default=True, is_active=True).all()
        if len(default_rules) > 1:
            conflicts.append({
                'type': 'multiple_defaults',
                'severity': 'error',
                'message': f'存在{len(default_rules)}个启用的默认规则，只应有一个',
                'rules': [r.id for r in default_rules]
            })
        
        # 检查2：同一部门的多个规则
        from sqlalchemy import func
        dept_rule_counts = db.session.query(
            AttendanceRule.department_id,
            func.count(AttendanceRule.id).label('count')
        ).filter(
            AttendanceRule.department_id.isnot(None),
            AttendanceRule.is_active == True
        ).group_by(AttendanceRule.department_id).having(func.count(AttendanceRule.id) > 1).all()
        
        for dept_id, count in dept_rule_counts:
            from database.models_v3 import Department
            dept = Department.query.get(dept_id)
            dept_name = dept.name if dept else f"ID:{dept_id}"
            rules = AttendanceRule.query.filter_by(
                department_id=dept_id,
                is_active=True
            ).all()
            conflicts.append({
                'type': 'department_overlap',
                'severity': 'warning',
                'message': f'部门"{dept_name}"有{count}个启用的规则，将使用最新的规则',
                'rules': [r.id for r in rules],
                'department': dept_name
            })
        
        return conflicts
    
    @staticmethod
    def check_checkin_window(rule: AttendanceRule, user_id: int, check_time: datetime) -> Dict:
        """
        检查打卡时间限制和次数限制
        
        Args:
            rule: 考勤规则
            user_id: 用户ID
            check_time: 打卡时间
            
        Returns:
            检查结果 {'allowed': bool, 'message': str, 'reason': str}
        """
        from database.models import Attendance
        
        # 开放模式不限制
        if rule.is_open_mode:
            return {'allowed': True, 'message': '开放模式，可以打卡'}
        
        check_time_only = check_time.time()
        check_date = check_time.date()
        
        # 检查每天打卡次数限制
        if rule.enable_once_per_day:
            # 判断当前打卡类型
            check_type = AttendanceRuleService.determine_checkin_type(rule, check_time)
            
            # 查询今天同类型的打卡记录（直接使用数据库中的check_type字段）
            existing_record = Attendance.query.filter(
                Attendance.user_id == user_id,
                db.func.date(Attendance.timestamp) == check_date,
                Attendance.check_type == check_type
            ).first()
            
            if existing_record:
                type_name = '上班' if check_type == 'checkin' else '下班'
                return {
                    'allowed': False,
                    'message': f'今天已经{type_name}打过卡了（{existing_record.timestamp.strftime("%H:%M:%S")}），每天只能{type_name}打卡一次',
                    'reason': f'already_{check_type}_today'
                }
        
        # 检查打卡时间限制（只限制最早打卡时间）
        # checkin_before_minutes > 0 表示启用限制
        if rule.checkin_before_minutes > 0:
            work_start = rule.work_start_time
            
            # 计算允许的打卡时间范围
            start_minutes = work_start.hour * 60 + work_start.minute
            check_minutes = check_time_only.hour * 60 + check_time_only.minute
            
            # 最早可打卡时间
            earliest_minutes = start_minutes - rule.checkin_before_minutes
            
            if check_minutes < earliest_minutes:
                earliest_time = f"{earliest_minutes // 60:02d}:{earliest_minutes % 60:02d}"
                return {
                    'allowed': False,
                    'message': f'打卡时间过早，最早可在 {earliest_time} 打卡',
                    'reason': 'too_early'
                }
        
        return {'allowed': True, 'message': '可以打卡'}
    
    @staticmethod
    def _time_diff_minutes(time1: time, time2: time) -> int:
        """
        计算两个时间的差值（分钟）
        time1 - time2
        
        Args:
            time1: 时间1
            time2: 时间2
            
        Returns:
            时间差（分钟），正数表示time1晚于time2
        """
        # 转换为分钟数
        minutes1 = time1.hour * 60 + time1.minute
        minutes2 = time2.hour * 60 + time2.minute
        
        return minutes1 - minutes2
