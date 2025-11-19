"""
管理员认证API路由
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from database.models import db
from database.models_v3 import Admin, AdminLoginLog
from utils.auth import AuthUtils, admin_required
from api.middleware import success_response, error_response

admin_auth_bp = Blueprint('admin_auth', __name__, url_prefix='/api/admin')


@admin_auth_bp.route('/login', methods=['POST'])
def admin_login():
    """
    管理员登录
    
    请求体:
    {
        "username": "admin",
        "password": "admin123"
    }
    
    返回:
    {
        "success": true,
        "data": {
            "token": "jwt_token",
            "admin": {...}
        }
    }
    """
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # 验证必填字段
        if not username or not password:
            return error_response('用户名和密码不能为空', 400)
        
        # 查询管理员
        admin = Admin.query.filter_by(username=username).first()
        
        if not admin:
            # 记录失败日志
            log_login_attempt(None, request, 'failed', '用户不存在')
            return error_response('用户名或密码错误', 401)
        
        # 检查是否启用
        if not admin.is_active:
            log_login_attempt(admin.id, request, 'failed', '账号已禁用')
            return error_response('账号已禁用', 403)
        
        # 验证密码
        if not AuthUtils.verify_password(password, admin.password_hash):
            log_login_attempt(admin.id, request, 'failed', '密码错误')
            return error_response('用户名或密码错误', 401)
        
        # 生成Token
        token = AuthUtils.generate_token(
            user_id=admin.id,
            user_type='admin',
            username=admin.username,
            is_super=admin.is_super
        )
        
        # 更新最后登录信息
        admin.last_login_at = datetime.utcnow()
        admin.last_login_ip = request.remote_addr
        db.session.commit()
        
        # 记录成功日志
        log_login_attempt(admin.id, request, 'success', None)
        
        return success_response({
            'token': token,
            'admin': admin.to_dict()
        }, '登录成功')
        
    except Exception as e:
        return error_response(f'登录失败: {str(e)}', 500)


@admin_auth_bp.route('/logout', methods=['POST'])
@admin_required
def admin_logout(current_admin):
    """
    管理员登出
    
    请求头:
    Authorization: Bearer <token>
    
    返回:
    {
        "success": true,
        "message": "登出成功"
    }
    """
    try:
        # JWT是无状态的，登出只需要前端删除Token
        # 这里可以记录登出日志
        return success_response(None, '登出成功')
        
    except Exception as e:
        return error_response(f'登出失败: {str(e)}', 500)


@admin_auth_bp.route('/me', methods=['GET'])
@admin_required
def get_current_admin(current_admin):
    """
    获取当前登录的管理员信息
    
    请求头:
    Authorization: Bearer <token>
    
    返回:
    {
        "success": true,
        "data": {
            "id": 1,
            "username": "admin",
            ...
        }
    }
    """
    try:
        admin_id = current_admin['user_id']
        admin = Admin.query.get(admin_id)
        
        if not admin:
            return error_response('管理员不存在', 404)
        
        return success_response(admin.to_dict(), '获取成功')
        
    except Exception as e:
        return error_response(f'获取失败: {str(e)}', 500)


@admin_auth_bp.route('/password', methods=['PUT'])
@admin_required
def change_password(current_admin):
    """
    修改管理员密码
    
    请求头:
    Authorization: Bearer <token>
    
    请求体:
    {
        "old_password": "admin123",
        "new_password": "newpassword123"
    }
    
    返回:
    {
        "success": true,
        "message": "密码修改成功"
    }
    """
    try:
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        # 验证必填字段
        if not old_password or not new_password:
            return error_response('旧密码和新密码不能为空', 400)
        
        # 验证新密码长度
        if len(new_password) < 6:
            return error_response('新密码长度不能少于6位', 400)
        
        admin_id = current_admin['user_id']
        admin = Admin.query.get(admin_id)
        
        if not admin:
            return error_response('管理员不存在', 404)
        
        # 验证旧密码
        if not AuthUtils.verify_password(old_password, admin.password_hash):
            return error_response('旧密码错误', 401)
        
        # 更新密码
        admin.password_hash = AuthUtils.hash_password(new_password)
        admin.updated_at = datetime.utcnow()
        db.session.commit()
        
        return success_response(None, '密码修改成功')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'密码修改失败: {str(e)}', 500)


@admin_auth_bp.route('/login-logs', methods=['GET'])
@admin_required
def get_login_logs(current_admin):
    """
    获取管理员登录日志
    
    请求头:
    Authorization: Bearer <token>
    
    查询参数:
    - page: 页码（默认1）
    - per_page: 每页数量（默认20）
    - admin_id: 管理员ID（可选，超级管理员可查看所有）
    
    返回:
    {
        "success": true,
        "data": {
            "logs": [...],
            "total": 100,
            "page": 1,
            "per_page": 20
        }
    }
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        admin_id = request.args.get('admin_id', type=int)
        
        # 构建查询
        query = AdminLoginLog.query
        
        # 非超级管理员只能查看自己的日志
        if not current_admin.get('is_super'):
            query = query.filter_by(admin_id=current_admin['user_id'])
        elif admin_id:
            query = query.filter_by(admin_id=admin_id)
        
        # 按时间倒序
        query = query.order_by(AdminLoginLog.login_time.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        logs = [log.to_dict() for log in pagination.items]
        
        return success_response({
            'logs': logs,
            'total': pagination.total,
            'page': page,
            'per_page': per_page
        }, '获取成功')
        
    except Exception as e:
        return error_response(f'获取失败: {str(e)}', 500)


def log_login_attempt(admin_id, request, status, reason=None):
    """
    记录登录尝试
    
    Args:
        admin_id: 管理员ID（可能为None）
        request: Flask request对象
        status: 登录状态 ('success' 或 'failed')
        reason: 失败原因
    """
    try:
        log = AdminLoginLog(
            admin_id=admin_id,
            login_time=datetime.utcnow(),
            login_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            login_status=status,
            failure_reason=reason
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"记录登录日志失败: {str(e)}")
        db.session.rollback()
