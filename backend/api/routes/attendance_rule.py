"""
考勤规则管理API路由
提供考勤规则的CRUD操作接口
"""
from flask import Blueprint, request
from datetime import datetime, time

from services.attendance_rule_service import AttendanceRuleService
from api.middleware import success_response, error_response, require_json
from utils.auth import admin_required

attendance_rule_bp = Blueprint('attendance_rule', __name__)
rule_service = AttendanceRuleService()


@attendance_rule_bp.route('', methods=['GET'])
@admin_required
def get_all_rules(current_admin=None):
    """获取所有考勤规则（需要管理员权限）"""
    try:
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        
        rules = rule_service.get_all_rules(include_inactive)
        
        return success_response([rule.to_dict() for rule in rules])
    
    except Exception as e:
        return error_response("获取规则列表失败", 500, str(e))


@attendance_rule_bp.route('/<int:rule_id>', methods=['GET'])
@admin_required
def get_rule(rule_id, current_admin=None):
    """获取规则详情（需要管理员权限）"""
    try:
        rule = rule_service.get_rule_by_id(rule_id)
        
        if not rule:
            return error_response("规则不存在", 404)
        
        return success_response(rule.to_dict())
    
    except Exception as e:
        return error_response("获取规则详情失败", 500, str(e))


@attendance_rule_bp.route('/default', methods=['GET'])
def get_default_rule():
    """获取默认规则（公开接口）"""
    try:
        rule = rule_service.get_default_rule()
        
        if not rule:
            return error_response("未设置默认规则", 404)
        
        return success_response(rule.to_dict())
    
    except Exception as e:
        return error_response("获取默认规则失败", 500, str(e))


@attendance_rule_bp.route('/department/<int:department_id>', methods=['GET'])
def get_department_rule(department_id):
    """获取部门的考勤规则（公开接口）"""
    try:
        rule = rule_service.get_rule_by_department(department_id)
        
        if not rule:
            return error_response("未找到适用的规则", 404)
        
        return success_response(rule.to_dict())
    
    except Exception as e:
        return error_response("获取部门规则失败", 500, str(e))


@attendance_rule_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_rule(user_id):
    """获取用户的考勤规则（公开接口）"""
    try:
        rule = rule_service.get_rule_for_user(user_id)
        
        if not rule:
            return error_response("未找到适用的规则", 404)
        
        return success_response(rule.to_dict())
    
    except Exception as e:
        return error_response("获取用户规则失败", 500, str(e))


@attendance_rule_bp.route('', methods=['POST'])
@require_json
@admin_required
def create_rule(current_admin=None):
    """创建考勤规则（需要管理员权限）"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['name', 'work_start_time', 'work_end_time']
        for field in required_fields:
            if field not in data:
                return error_response(f"缺少必填字段: {field}", 400)
        
        # 解析时间
        try:
            work_start_time = datetime.strptime(data['work_start_time'], '%H:%M:%S').time()
            work_end_time = datetime.strptime(data['work_end_time'], '%H:%M:%S').time()
        except ValueError:
            return error_response("时间格式错误，应为 HH:MM:SS", 400)
        
        # 创建规则
        rule = rule_service.create_rule(
            name=data['name'],
            work_start_time=work_start_time,
            work_end_time=work_end_time,
            late_threshold=data.get('late_threshold', 0),
            early_threshold=data.get('early_threshold', 0),
            work_days=data.get('work_days', '1,2,3,4,5'),
            department_id=data.get('department_id'),
            is_default=data.get('is_default', False),
            is_open_mode=data.get('is_open_mode', False),
            description=data.get('description')
        )
        
        return success_response(rule.to_dict(), "创建成功")
    
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("创建失败", 500, str(e))


@attendance_rule_bp.route('/<int:rule_id>', methods=['PUT'])
@require_json
@admin_required
def update_rule(rule_id, current_admin=None):
    """更新考勤规则（需要管理员权限）"""
    try:
        data = request.get_json()
        
        # 解析时间字段（如果提供）
        if 'work_start_time' in data:
            try:
                data['work_start_time'] = datetime.strptime(data['work_start_time'], '%H:%M:%S').time()
            except ValueError:
                return error_response("上班时间格式错误，应为 HH:MM:SS", 400)
        
        if 'work_end_time' in data:
            try:
                data['work_end_time'] = datetime.strptime(data['work_end_time'], '%H:%M:%S').time()
            except ValueError:
                return error_response("下班时间格式错误，应为 HH:MM:SS", 400)
        
        # 移除不允许更新的字段
        data.pop('id', None)
        data.pop('created_at', None)
        data.pop('updated_at', None)
        
        rule = rule_service.update_rule(rule_id, **data)
        
        if not rule:
            return error_response("规则不存在", 404)
        
        return success_response(rule.to_dict(), "更新成功")
    
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("更新失败", 500, str(e))


@attendance_rule_bp.route('/<int:rule_id>', methods=['DELETE'])
@admin_required
def delete_rule(rule_id, current_admin=None):
    """删除考勤规则（需要管理员权限）"""
    try:
        success = rule_service.delete_rule(rule_id)
        
        if not success:
            return error_response("规则不存在", 404)
        
        return success_response(None, "删除成功")
    
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("删除失败", 500, str(e))


@attendance_rule_bp.route('/check', methods=['POST'])
@require_json
def check_status():
    """
    检查打卡状态（公开接口）
    用于前端预览打卡结果
    """
    try:
        data = request.get_json()
        
        # 验证必填字段
        if 'rule_id' not in data:
            return error_response("缺少规则ID", 400)
        
        rule = rule_service.get_rule_by_id(data['rule_id'])
        if not rule:
            return error_response("规则不存在", 404)
        
        # 获取打卡时间（默认当前时间）
        check_time_str = data.get('check_time')
        if check_time_str:
            try:
                check_time = datetime.fromisoformat(check_time_str)
            except ValueError:
                return error_response("时间格式错误", 400)
        else:
            check_time = datetime.now()
        
        check_type = data.get('check_type', 'checkin')
        
        # 检查状态
        result = rule_service.check_attendance_status(rule, check_time, check_type)
        
        return success_response(result)
    
    except Exception as e:
        return error_response("检查失败", 500, str(e))
