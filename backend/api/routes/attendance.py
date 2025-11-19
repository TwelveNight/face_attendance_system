"""
考勤管理API路由
"""
from flask import Blueprint, request, send_file
import numpy as np
import cv2
import base64
from datetime import datetime

from services import AttendanceService
from api.middleware import success_response, error_response, require_json

attendance_bp = Blueprint('attendance', __name__)
attendance_service = AttendanceService()


@attendance_bp.route('/preview', methods=['POST'])
@require_json
def preview_recognition():
    """实时人脸识别预览（不保存打卡记录）"""
    try:
        data = request.get_json()
        image_base64 = data.get('image')
        
        if not image_base64:
            return error_response("图像不能为空", 400)
        
        # 解码图像
        try:
            img_data = base64.b64decode(image_base64.split(',')[1] if ',' in image_base64 else image_base64)
            img_array = np.frombuffer(img_data, dtype=np.uint8)
            image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        except Exception as e:
            return error_response("图像解码失败", 400, str(e))
        
        if image is None:
            return error_response("无效的图像", 400)
        
        # 检测并识别人脸（不保存记录）
        from services.face_service import FaceService
        face_service = FaceService()
        result = face_service.detect_largest_face_and_recognize(image)
        
        if result is None:
            return success_response({
                'detected': False,
                'message': '未检测到人脸'
            })
        
        user_id = result['user_id']
        confidence = result['confidence']
        
        if user_id is None:
            return success_response({
                'detected': True,
                'recognized': False,
                'confidence': confidence,
                'message': f'检测到人脸，但未识别到已注册用户（置信度: {confidence:.2f}）'
            })
        
        # 获取用户信息
        from database.repositories import UserRepository
        user = UserRepository.get_by_id(user_id)
        
        if not user:
            return success_response({
                'detected': True,
                'recognized': False,
                'message': '用户不存在'
            })
        
        # 返回识别结果
        return success_response({
            'detected': True,
            'recognized': True,
            'user_id': user_id,
            'username': user.username,
            'student_id': user.student_id,
            'confidence': confidence,
            'message': f'识别到: {user.username}'
        })
    
    except Exception as e:
        return error_response("识别失败", 500, str(e))


@attendance_bp.route('/check-in', methods=['POST'])
@require_json
def check_in():
    """考勤打卡"""
    try:
        data = request.get_json()
        image_base64 = data.get('image')
        status = data.get('status', 'present')
        
        if not image_base64:
            return error_response("图像不能为空", 400)
        
        # 解码图像
        try:
            img_data = base64.b64decode(image_base64.split(',')[1] if ',' in image_base64 else image_base64)
            img_array = np.frombuffer(img_data, dtype=np.uint8)
            image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        except Exception as e:
            return error_response("图像解码失败", 400, str(e))
        
        if image is None:
            return error_response("无效的图像", 400)
        
        # 打卡
        result = attendance_service.check_in(image, status)
        
        if not result['success']:
            # 区分不同的失败原因
            message = result['message']
            
            # 如果是未识别到用户，返回更详细的信息
            if message == '未识别到用户':
                confidence = result.get('confidence', 0)
                detailed_message = f'未识别到已注册用户（置信度: {confidence:.2f}），请确认您已注册'
                return error_response(detailed_message, 400)
            
            # 其他情况（未检测到人脸等）
            return error_response(message, 400)
        
        # 构造响应数据
        response_data = {
            'success': True,
            'user_id': result['user_id'],
            'username': result['username'],
            'student_id': result.get('student_id'),
            'confidence': result['confidence'],
            'timestamp': result['attendance'].timestamp.isoformat()
        }
        
        return success_response(response_data, result['message'])
    
    except Exception as e:
        return error_response("打卡失败", 500, str(e))


@attendance_bp.route('/history', methods=['GET'])
def get_history():
    """获取考勤历史"""
    try:
        # 分页参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 过滤参数
        filters = {}
        
        user_id = request.args.get('user_id')
        if user_id:
            filters['user_id'] = int(user_id)
        
        status = request.args.get('status')
        if status:
            filters['status'] = status
        
        department_id = request.args.get('department_id')
        if department_id:
            filters['department_id'] = int(department_id)
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        if start_date and end_date:
            filters['start_date'] = datetime.fromisoformat(start_date)
            filters['end_date'] = datetime.fromisoformat(end_date)
        
        # 获取数据
        result = attendance_service.get_attendance_history(filters, page, per_page)
        
        return success_response(result)
    
    except Exception as e:
        return error_response("获取历史记录失败", 500, str(e))


@attendance_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_attendance(user_id):
    """获取用户考勤记录"""
    try:
        limit = int(request.args.get('limit', 100))
        
        records = attendance_service.get_user_attendance(user_id, limit)
        
        return success_response([record.to_dict() for record in records])
    
    except Exception as e:
        return error_response("获取用户考勤失败", 500, str(e))


@attendance_bp.route('/today', methods=['GET'])
def get_today():
    """获取今日考勤"""
    try:
        user_id = request.args.get('user_id')
        user_id = int(user_id) if user_id else None
        
        records = attendance_service.get_today_attendance(user_id)
        
        return success_response([record.to_dict() for record in records])
    
    except Exception as e:
        return error_response("获取今日考勤失败", 500, str(e))


@attendance_bp.route('/export', methods=['GET'])
def export_csv():
    """导出考勤记录"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return error_response("开始和结束日期不能为空", 400)
        
        start_date = datetime.fromisoformat(start_date)
        end_date = datetime.fromisoformat(end_date)
        
        filepath = attendance_service.export_to_csv(start_date, end_date)
        
        return send_file(filepath, as_attachment=True, download_name=f'attendance_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv')
    
    except Exception as e:
        return error_response("导出失败", 500, str(e))


@attendance_bp.route('/<int:attendance_id>', methods=['DELETE'])
def delete_attendance(attendance_id):
    """删除考勤记录"""
    try:
        success = attendance_service.delete_attendance(attendance_id)
        
        if not success:
            return error_response("删除失败", 400)
        
        return success_response(None, "删除成功")
    
    except Exception as e:
        return error_response("删除失败", 500, str(e))
