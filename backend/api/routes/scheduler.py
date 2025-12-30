"""
定时任务管理路由
"""
from flask import Blueprint, jsonify, request
from utils.auth import admin_required
from services.scheduler_service import get_scheduler
from api.middleware import success_response, error_response

scheduler_bp = Blueprint('scheduler', __name__)

# 存储当前配置的检测时间
_absence_check_time = {'hour': 23, 'minute': 0}


@scheduler_bp.route('/trigger-absence-check', methods=['POST'])
@admin_required
def trigger_absence_check(current_admin=None):
    """手动触发缺勤检查（管理员功能，用于测试）"""
    try:
        scheduler = get_scheduler()
        if not scheduler:
            return error_response("定时任务服务未启动", 500)
        
        # 手动执行缺勤检查
        scheduler.check_daily_absence()
        
        return success_response({
            'message': '缺勤检查已执行'
        })
    
    except Exception as e:
        return error_response("执行失败", 500, str(e))


@scheduler_bp.route('/status', methods=['GET'])
@admin_required
def get_scheduler_status(current_admin=None):
    """获取定时任务状态"""
    try:
        scheduler = get_scheduler()
        if not scheduler:
            return success_response({
                'running': False,
                'jobs': [],
                'absence_check_time': _absence_check_time
            })
        
        jobs = []
        for job in scheduler.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
            })
        
        return success_response({
            'running': True,
            'jobs': jobs,
            'absence_check_time': _absence_check_time
        })
    
    except Exception as e:
        return error_response("获取状态失败", 500, str(e))


@scheduler_bp.route('/config', methods=['POST'])
@admin_required
def update_scheduler_config(current_admin=None):
    """更新定时任务配置（修改缺勤检测时间）"""
    global _absence_check_time
    try:
        data = request.get_json()
        hour = data.get('hour', 23)
        minute = data.get('minute', 0)
        
        # 验证时间范围
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return error_response("时间格式无效", 400)
        
        scheduler = get_scheduler()
        if not scheduler:
            return error_response("定时任务服务未启动", 500)
        
        # 更新定时任务
        from apscheduler.triggers.cron import CronTrigger
        scheduler.scheduler.reschedule_job(
            'check_daily_absence',
            trigger=CronTrigger(hour=hour, minute=minute)
        )
        
        # 保存配置
        _absence_check_time = {'hour': hour, 'minute': minute}
        
        return success_response({
            'message': f'缺勤检测时间已更新为 {hour:02d}:{minute:02d}',
            'absence_check_time': _absence_check_time
        })
    
    except Exception as e:
        return error_response("更新配置失败", 500, str(e))
