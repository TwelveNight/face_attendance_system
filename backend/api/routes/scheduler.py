"""
定时任务管理路由
"""
from flask import Blueprint, jsonify
from utils.auth import admin_required
from services.scheduler_service import get_scheduler
from api.middleware import success_response, error_response

scheduler_bp = Blueprint('scheduler', __name__)


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
                'jobs': []
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
            'jobs': jobs
        })
    
    except Exception as e:
        return error_response("获取状态失败", 500, str(e))
