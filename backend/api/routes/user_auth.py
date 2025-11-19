"""
普通用户认证API路由
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from database.models import db, User
from utils.auth import AuthUtils, user_required
from api.middleware import success_response, error_response

user_auth_bp = Blueprint('user_auth', __name__, url_prefix='/api/auth')


@user_auth_bp.route('/login', methods=['POST'])
def user_login():
    """
    普通用户登录
    
    请求体:
    {
        "username": "zhangsan",  # 或使用student_id
        "password": "password123"
    }
    
    返回:
    {
        "success": true,
        "data": {
            "token": "jwt_token",
            "user": {...}
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
        
        # 查询用户（支持用户名或学号登录）
        user = User.query.filter(
            (User.username == username) | (User.student_id == username)
        ).first()
        
        if not user:
            return error_response('用户名或密码错误', 401)
        
        # 检查是否启用
        if not user.is_active:
            return error_response('账号已禁用', 403)
        
        # 检查是否设置了密码
        if not user.password_hash:
            return error_response('账号未设置密码，请联系管理员', 403)
        
        # 验证密码
        if not AuthUtils.verify_password(password, user.password_hash):
            return error_response('用户名或密码错误', 401)
        
        # 生成Token
        token = AuthUtils.generate_token(
            user_id=user.id,
            user_type='user',
            username=user.username,
            student_id=user.student_id
        )
        
        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        db.session.commit()
        
        return success_response({
            'token': token,
            'user': user.to_dict()
        }, '登录成功')
        
    except Exception as e:
        return error_response(f'登录失败: {str(e)}', 500)


@user_auth_bp.route('/logout', methods=['POST'])
@user_required
def user_logout(current_user):
    """
    普通用户登出
    
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
        return success_response(None, '登出成功')
        
    except Exception as e:
        return error_response(f'登出失败: {str(e)}', 500)


@user_auth_bp.route('/me', methods=['GET'])
@user_required
def get_current_user_info(current_user):
    """
    获取当前登录的用户信息
    
    请求头:
    Authorization: Bearer <token>
    
    返回:
    {
        "success": true,
        "data": {
            "id": 1,
            "username": "zhangsan",
            ...
        }
    }
    """
    try:
        user_id = current_user['user_id']
        user = User.query.get(user_id)
        
        if not user:
            return error_response('用户不存在', 404)
        
        return success_response(user.to_dict(), '获取成功')
        
    except Exception as e:
        return error_response(f'获取失败: {str(e)}', 500)


@user_auth_bp.route('/password', methods=['PUT'])
@user_required
def change_user_password(current_user):
    """
    修改用户密码
    
    请求头:
    Authorization: Bearer <token>
    
    请求体:
    {
        "old_password": "oldpassword",
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
        
        user_id = current_user['user_id']
        user = User.query.get(user_id)
        
        if not user:
            return error_response('用户不存在', 404)
        
        # 如果用户还没有设置密码
        if not user.password_hash:
            return error_response('账号未设置密码，请联系管理员', 403)
        
        # 验证旧密码
        if not AuthUtils.verify_password(old_password, user.password_hash):
            return error_response('旧密码错误', 401)
        
        # 更新密码
        user.password_hash = AuthUtils.hash_password(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return success_response(None, '密码修改成功')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'密码修改失败: {str(e)}', 500)


@user_auth_bp.route('/set-password', methods=['POST'])
def set_initial_password():
    """
    首次设置密码（用于新注册用户）
    
    请求体:
    {
        "username": "zhangsan",  # 或student_id
        "student_id": "20210001",  # 用于验证身份
        "new_password": "password123"
    }
    
    返回:
    {
        "success": true,
        "message": "密码设置成功"
    }
    """
    try:
        data = request.get_json()
        username = data.get('username')
        student_id = data.get('student_id')
        new_password = data.get('new_password')
        
        # 验证必填字段
        if not username or not student_id or not new_password:
            return error_response('用户名、学号和新密码不能为空', 400)
        
        # 验证新密码长度
        if len(new_password) < 6:
            return error_response('密码长度不能少于6位', 400)
        
        # 查询用户（必须同时匹配用户名和学号）
        user = User.query.filter_by(
            username=username,
            student_id=student_id
        ).first()
        
        if not user:
            return error_response('用户信息不匹配', 404)
        
        # 检查是否已经设置过密码
        if user.password_hash:
            return error_response('密码已设置，请使用修改密码功能', 400)
        
        # 设置密码
        user.password_hash = AuthUtils.hash_password(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return success_response(None, '密码设置成功，请使用新密码登录')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'密码设置失败: {str(e)}', 500)


@user_auth_bp.route('/check-password', methods=['POST'])
def check_password_status():
    """
    检查用户是否已设置密码
    
    请求体:
    {
        "username": "zhangsan"  # 或student_id
    }
    
    返回:
    {
        "success": true,
        "data": {
            "has_password": true,
            "username": "zhangsan"
        }
    }
    """
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return error_response('用户名不能为空', 400)
        
        # 查询用户
        user = User.query.filter(
            (User.username == username) | (User.student_id == username)
        ).first()
        
        if not user:
            return error_response('用户不存在', 404)
        
        return success_response({
            'has_password': bool(user.password_hash),
            'username': user.username,
            'student_id': user.student_id
        }, '查询成功')
        
    except Exception as e:
        return error_response(f'查询失败: {str(e)}', 500)
