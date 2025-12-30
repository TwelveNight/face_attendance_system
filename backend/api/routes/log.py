"""
日志管理路由
"""
from flask import Blueprint, request, jsonify
from database import get_db
from services.log_service import LogService
from utils.auth import admin_required
from datetime import datetime

log_bp = Blueprint('log', __name__)

@log_bp.route('/admin/login-logs', methods=['GET'])
@admin_required
def get_login_logs(current_admin):
    """获取管理员登录日志"""
    try:
        # 获取查询参数
        admin_id = request.args.get('admin_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        
        # 转换日期
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 查询日志
        db = get_db()
        log_service = LogService(db)
        result = log_service.get_admin_login_logs(
            admin_id=admin_id,
            start_date=start_date,
            end_date=end_date,
            status=status,
            page=page,
            size=size
        )
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取登录日志失败: {str(e)}'
        }), 500


@log_bp.route('/system-logs', methods=['GET'])
@admin_required
def get_system_logs(current_admin):
    """获取系统日志"""
    try:
        print(f"获取系统日志，管理员: {current_admin}")
        # 获取查询参数
        event_type = request.args.get('event_type')
        level = request.args.get('level')
        module = request.args.get('module')
        user_id = request.args.get('user_id', type=int)
        admin_id = request.args.get('admin_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        
        # 转换日期
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 查询日志
        db = get_db()
        log_service = LogService(db)
        result = log_service.get_system_logs(
            event_type=event_type,
            level=level,
            module=module,
            user_id=user_id,
            admin_id=admin_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            size=size
        )
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"获取系统日志失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取系统日志失败: {str(e)}'
        }), 500


@log_bp.route('/login-statistics', methods=['GET'])
@admin_required
def get_login_statistics(current_admin):
    """获取登录统计"""
    try:
        days = request.args.get('days', 7, type=int)
        
        db = get_db()
        log_service = LogService(db)
        result = log_service.get_login_statistics(days=days)
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取登录统计失败: {str(e)}'
        }), 500


@log_bp.route('/system-log-statistics', methods=['GET'])
@admin_required
def get_system_log_statistics(current_admin):
    """获取系统日志统计"""
    try:
        days = request.args.get('days', 7, type=int)
        
        db = get_db()
        log_service = LogService(db)
        result = log_service.get_system_log_statistics(days=days)
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取系统日志统计失败: {str(e)}'
        }), 500


@log_bp.route('/system-logs/<int:log_id>', methods=['DELETE'])
@admin_required
def delete_system_log(current_admin, log_id):
    """删除单条系统日志"""
    try:
        db = get_db()
        log_service = LogService(db)
        
        if log_service.delete_system_log(log_id):
            return jsonify({
                'success': True,
                'message': '删除成功'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '日志不存在或删除失败'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


@log_bp.route('/admin/login-logs/<int:log_id>', methods=['DELETE'])
@admin_required
def delete_login_log(current_admin, log_id):
    """删除单条登录日志"""
    try:
        db = get_db()
        log_service = LogService(db)
        
        if log_service.delete_login_log(log_id):
            return jsonify({
                'success': True,
                'message': '删除成功'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '日志不存在或删除失败'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


@log_bp.route('/cleanup', methods=['POST'])
@admin_required
def cleanup_logs(current_admin):
    """清理旧日志"""
    try:
        print(f"清理日志请求，管理员: {current_admin}")
        # 管理员权限已经通过装饰器验证
        
        days = request.json.get('days', 90)
        
        db = get_db()
        log_service = LogService(db)
        deleted_count = log_service.cleanup_old_logs(days=days)
        
        # 记录清理操作
        log_service.log_system_event(
            event_type='LOG_CLEANUP',
            message=f'清理了{deleted_count}条超过{days}天的日志',
            level='INFO',
            admin_id=current_admin.get('id'),
            module='日志管理'
        )
        
        return jsonify({
            'success': True,
            'data': {
                'deleted_count': deleted_count,
                'message': f'成功清理{deleted_count}条日志'
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'清理日志失败: {str(e)}'
        }), 500
