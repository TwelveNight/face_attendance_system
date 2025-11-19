"""
部门管理API路由
提供部门的CRUD操作接口
"""
from flask import Blueprint, request, jsonify
from services.department_service import DepartmentService
from utils.auth import admin_required
from api.middleware import success_response, error_response, require_json


department_bp = Blueprint('department', __name__, url_prefix='/api/departments')


@department_bp.route('', methods=['GET'])
@admin_required
def get_departments(current_admin=None):
    """
    获取部门列表
    
    Query参数:
        tree: 是否返回树形结构 (true/false)
        include_inactive: 是否包含未启用的部门 (true/false)
    """
    try:
        tree = request.args.get('tree', 'false').lower() == 'true'
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        
        if tree:
            # 返回树形结构
            departments = DepartmentService.get_department_tree(
                parent_id=None,
                include_inactive=include_inactive
            )
        else:
            # 返回平铺列表
            departments = DepartmentService.get_all_departments(include_inactive)
            departments = [dept.to_dict() for dept in departments]
        
        return success_response(departments, "获取成功")
    
    except Exception as e:
        return error_response("获取失败", 500, str(e))


@department_bp.route('/<int:dept_id>', methods=['GET'])
@admin_required
def get_department(dept_id, current_admin=None):
    """获取部门详情"""
    try:
        department = DepartmentService.get_department_by_id(dept_id)
        
        if not department:
            return error_response("部门不存在", 404)
        
        return success_response(department.to_dict(include_children=True), "获取成功")
    
    except Exception as e:
        return error_response("获取失败", 500, str(e))


@department_bp.route('', methods=['POST'])
@require_json
@admin_required
def create_department(current_admin=None):
    """
    创建部门
    
    Body参数:
        name: 部门名称 (必填)
        code: 部门代码 (可选)
        parent_id: 父部门ID (可选)
        manager_id: 部门负责人ID (可选)
        description: 部门描述 (可选)
        sort_order: 排序 (可选)
    """
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name'):
            return error_response("部门名称不能为空", 400)
        
        # 创建部门
        department = DepartmentService.create_department(
            name=data['name'],
            code=data.get('code'),
            parent_id=data.get('parent_id'),
            manager_id=data.get('manager_id'),
            description=data.get('description'),
            sort_order=data.get('sort_order', 0)
        )
        
        return success_response(department.to_dict(), "创建成功", 201)
    
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("创建失败", 500, str(e))


@department_bp.route('/<int:dept_id>', methods=['PUT'])
@require_json
@admin_required
def update_department(dept_id, current_admin=None):
    """
    更新部门信息
    
    Body参数:
        name: 部门名称
        code: 部门代码
        parent_id: 父部门ID
        manager_id: 部门负责人ID
        description: 部门描述
        sort_order: 排序
        is_active: 是否启用
    """
    try:
        data = request.get_json()
        
        # 移除不允许更新的字段
        data.pop('id', None)
        data.pop('created_at', None)
        data.pop('level', None)  # level由系统自动计算
        
        department = DepartmentService.update_department(dept_id, **data)
        
        if not department:
            return error_response("部门不存在", 404)
        
        return success_response(department.to_dict(), "更新成功")
    
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("更新失败", 500, str(e))


@department_bp.route('/<int:dept_id>', methods=['DELETE'])
@admin_required
def delete_department(dept_id, current_admin=None):
    """
    删除部门
    
    Query参数:
        force: 是否强制删除 (true/false)，默认false
    """
    try:
        force = request.args.get('force', 'false').lower() == 'true'
        
        success = DepartmentService.delete_department(dept_id, force=force)
        
        if not success:
            return error_response("部门不存在", 404)
        
        return success_response(None, "删除成功")
    
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response("删除失败", 500, str(e))


@department_bp.route('/<int:dept_id>/users', methods=['GET'])
@admin_required
def get_department_users(dept_id, current_admin=None):
    """
    获取部门下的用户
    
    Query参数:
        include_children: 是否包含子部门的用户 (true/false)
    """
    try:
        include_children = request.args.get('include_children', 'false').lower() == 'true'
        
        users = DepartmentService.get_department_users(dept_id, include_children)
        users_data = [user.to_dict() for user in users]
        
        return success_response(users_data, "获取成功")
    
    except Exception as e:
        return error_response("获取失败", 500, str(e))


@department_bp.route('/search', methods=['GET'])
@admin_required
def search_departments(current_admin=None):
    """
    搜索部门
    
    Query参数:
        keyword: 搜索关键词
    """
    try:
        keyword = request.args.get('keyword', '').strip()
        
        if not keyword:
            return error_response("搜索关键词不能为空", 400)
        
        departments = DepartmentService.search_departments(keyword)
        departments_data = [dept.to_dict() for dept in departments]
        
        return success_response(departments_data, "搜索成功")
    
    except Exception as e:
        return error_response("搜索失败", 500, str(e))
