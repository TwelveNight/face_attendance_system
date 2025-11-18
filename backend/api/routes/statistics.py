"""
统计分析API路由
"""
from flask import Blueprint, request
from datetime import datetime

from services import AttendanceService
from api.middleware import success_response, error_response

statistics_bp = Blueprint('statistics', __name__)
attendance_service = AttendanceService()


@statistics_bp.route('/daily', methods=['GET'])
def get_daily():
    """每日统计"""
    try:
        date_str = request.args.get('date')
        
        if date_str:
            date = datetime.fromisoformat(date_str)
        else:
            date = None
        
        stats = attendance_service.get_daily_statistics(date)
        
        return success_response(stats)
    
    except Exception as e:
        return error_response("获取每日统计失败", 500, str(e))


@statistics_bp.route('/weekly', methods=['GET'])
def get_weekly():
    """周统计"""
    try:
        start_date_str = request.args.get('start_date')
        
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str)
        else:
            start_date = None
        
        stats = attendance_service.get_weekly_statistics(start_date)
        
        return success_response(stats)
    
    except Exception as e:
        return error_response("获取周统计失败", 500, str(e))


@statistics_bp.route('/monthly', methods=['GET'])
def get_monthly():
    """月统计"""
    try:
        year = request.args.get('year')
        month = request.args.get('month')
        
        year = int(year) if year else None
        month = int(month) if month else None
        
        stats = attendance_service.get_monthly_statistics(year, month)
        
        return success_response(stats)
    
    except Exception as e:
        return error_response("获取月统计失败", 500, str(e))


@statistics_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_stats(user_id):
    """用户统计"""
    try:
        days = int(request.args.get('days', 30))
        
        stats = attendance_service.get_user_statistics(user_id, days)
        
        return success_response(stats)
    
    except Exception as e:
        return error_response("获取用户统计失败", 500, str(e))
