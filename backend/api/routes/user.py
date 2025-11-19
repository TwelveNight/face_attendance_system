"""
用户管理API路由
"""
from flask import Blueprint, request
import numpy as np
import cv2
import base64

from services import UserService
from api.middleware import success_response, error_response, require_json
from utils.auth import AuthUtils, admin_required

user_bp = Blueprint('user', __name__)
user_service = UserService()


@user_bp.route('', methods=['GET'])
def get_users():
    """获取用户列表"""
    try:
        keyword = request.args.get('keyword', '')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        if keyword:
            users = user_service.search_users(keyword, active_only)
        else:
            users = user_service.get_all_users(active_only)
        
        return success_response([user.to_dict() for user in users])
    
    except Exception as e:
        return error_response("获取用户列表失败", 500, str(e))


@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """获取用户详情"""
    try:
        user = user_service.get_user(user_id)
        if not user:
            return error_response("用户不存在", 404)
        
        return success_response(user.to_dict())
    
    except Exception as e:
        return error_response("获取用户失败", 500, str(e))


@user_bp.route('/register', methods=['POST'])
@require_json
def register_user():
    """注册用户"""
    try:
        data = request.get_json()
        username = data.get('username')
        student_id = data.get('student_id')
        face_images_base64 = data.get('face_images', [])
        
        if not username:
            return error_response("用户名不能为空", 400)
        
        # 检查用户名是否已存在
        existing_user = user_service.get_user_by_username(username)
        if existing_user:
            return error_response(f"用户名已存在: {username}", 400)
        
        # 检查学号是否已存在
        if student_id:
            existing_student = user_service.get_user_by_student_id(student_id)
            if existing_student:
                return error_response(f"学号已存在: {student_id}", 400)
        
        # 解码人脸图像
        face_images = []
        for img_base64 in face_images_base64:
            try:
                img_data = base64.b64decode(img_base64.split(',')[1] if ',' in img_base64 else img_base64)
                img_array = np.frombuffer(img_data, dtype=np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                if img is not None:
                    face_images.append(img)
            except Exception as e:
                print(f"解码图像失败: {e}")
        
        if face_images_base64 and not face_images:
            return error_response("人脸图像解码失败，请重新拍摄", 400)
        
        # 创建用户
        user = user_service.create_user(username, student_id, face_images)
        
        if not user:
            return error_response("用户创建失败，请稍后重试", 400)
        
        return success_response(user.to_dict(), "用户注册成功", 201)
    
    except Exception as e:
        return error_response("注册失败", 500, str(e))


@user_bp.route('/<int:user_id>', methods=['PUT'])
@require_json
@admin_required
def update_user(user_id, current_admin=None):
    """更新用户信息（需要管理员权限）"""
    try:
        data = request.get_json()
        
        # 移除不允许更新的字段
        data.pop('id', None)
        data.pop('created_at', None)
        
        # 处理密码设置
        if 'password' in data:
            password = data.pop('password')
            if password:
                # 使用bcrypt加密密码
                data['password_hash'] = AuthUtils.hash_password(password)
        
        user = user_service.update_user(user_id, **data)
        
        if not user:
            return error_response("用户不存在", 404)
        
        return success_response(user.to_dict(), "更新成功")
    
    except Exception as e:
        return error_response("更新失败", 500, str(e))


@user_bp.route('/<int:user_id>/faces', methods=['POST'])
@require_json
def update_user_faces(user_id):
    """更新用户人脸"""
    try:
        data = request.get_json()
        face_images_base64 = data.get('face_images', [])
        
        if not face_images_base64:
            return error_response("人脸图像不能为空", 400)
        
        # 解码图像
        face_images = []
        for img_base64 in face_images_base64:
            try:
                img_data = base64.b64decode(img_base64.split(',')[1] if ',' in img_base64 else img_base64)
                img_array = np.frombuffer(img_data, dtype=np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                if img is not None:
                    face_images.append(img)
            except Exception as e:
                print(f"解码图像失败: {e}")
        
        if not face_images:
            return error_response("没有有效的人脸图像", 400)
        
        success = user_service.update_user_faces(user_id, face_images)
        
        if not success:
            return error_response("更新人脸失败", 400)
        
        return success_response(None, "人脸更新成功")
    
    except Exception as e:
        return error_response("更新失败", 500, str(e))


@user_bp.route('/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id, current_admin=None):
    """删除用户（需要管理员权限，默认硬删除）"""
    try:
        # 默认硬删除（物理删除），除非明确指定 hard=false
        hard_delete = request.args.get('hard', 'true').lower() == 'true'
        
        success = user_service.delete_user(user_id, hard_delete)
        
        if not success:
            return error_response("删除失败", 400)
        
        return success_response(None, "删除成功")
    
    except Exception as e:
        return error_response("删除失败", 500, str(e))


@user_bp.route('/statistics', methods=['GET'])
def get_user_statistics():
    """获取用户统计"""
    try:
        stats = user_service.get_user_statistics()
        return success_response(stats)
    
    except Exception as e:
        return error_response("获取统计失败", 500, str(e))
