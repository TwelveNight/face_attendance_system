"""
部门管理服务
提供部门的CRUD操作和树形结构查询
"""
from typing import List, Dict, Optional
from database.models_v3 import Department, db
from sqlalchemy import or_


class DepartmentService:
    """部门服务类"""
    
    @staticmethod
    def get_all_departments(include_inactive=False) -> List[Department]:
        """
        获取所有部门列表
        
        Args:
            include_inactive: 是否包含未启用的部门
            
        Returns:
            部门列表
        """
        query = Department.query
        if not include_inactive:
            query = query.filter_by(is_active=True)
        return query.order_by(Department.sort_order, Department.id).all()
    
    @staticmethod
    def get_department_tree(parent_id: Optional[int] = None, include_inactive=False) -> List[Dict]:
        """
        获取部门树形结构
        
        Args:
            parent_id: 父部门ID，None表示获取根部门
            include_inactive: 是否包含未启用的部门
            
        Returns:
            树形结构的部门列表
        """
        query = Department.query.filter_by(parent_id=parent_id)
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
        departments = query.order_by(Department.sort_order, Department.id).all()
        
        result = []
        for dept in departments:
            dept_dict = dept.to_dict()
            # 递归获取子部门
            children = DepartmentService.get_department_tree(dept.id, include_inactive)
            if children:
                dept_dict['children'] = children
            result.append(dept_dict)
        
        return result
    
    @staticmethod
    def get_department_by_id(dept_id: int) -> Optional[Department]:
        """
        根据ID获取部门
        
        Args:
            dept_id: 部门ID
            
        Returns:
            部门对象，不存在返回None
        """
        return Department.query.get(dept_id)
    
    @staticmethod
    def get_department_by_code(code: str) -> Optional[Department]:
        """
        根据代码获取部门
        
        Args:
            code: 部门代码
            
        Returns:
            部门对象，不存在返回None
        """
        return Department.query.filter_by(code=code).first()
    
    @staticmethod
    def create_department(name: str, code: Optional[str] = None, 
                         parent_id: Optional[int] = None, **kwargs) -> Department:
        """
        创建部门
        
        Args:
            name: 部门名称
            code: 部门代码
            parent_id: 父部门ID
            **kwargs: 其他字段
            
        Returns:
            创建的部门对象
            
        Raises:
            ValueError: 参数验证失败
        """
        # 验证父部门是否存在
        if parent_id is not None:
            parent = Department.query.get(parent_id)
            if not parent:
                raise ValueError(f"父部门不存在: {parent_id}")
            level = parent.level + 1
        else:
            level = 1
        
        # 验证部门代码是否重复
        if code and Department.query.filter_by(code=code).first():
            raise ValueError(f"部门代码已存在: {code}")
        
        # 创建部门
        department = Department(
            name=name,
            code=code,
            parent_id=parent_id,
            level=level,
            **kwargs
        )
        
        db.session.add(department)
        db.session.commit()
        
        return department
    
    @staticmethod
    def update_department(dept_id: int, **kwargs) -> Optional[Department]:
        """
        更新部门信息
        
        Args:
            dept_id: 部门ID
            **kwargs: 要更新的字段
            
        Returns:
            更新后的部门对象，不存在返回None
            
        Raises:
            ValueError: 参数验证失败
        """
        department = Department.query.get(dept_id)
        if not department:
            return None
        
        # 如果更新父部门，需要验证
        if 'parent_id' in kwargs:
            new_parent_id = kwargs['parent_id']
            if new_parent_id is not None:
                # 不能将部门设置为自己的子部门
                if new_parent_id == dept_id:
                    raise ValueError("不能将部门设置为自己的父部门")
                
                # 检查是否会形成循环引用
                if DepartmentService._is_descendant(dept_id, new_parent_id):
                    raise ValueError("不能将部门移动到自己的子部门下")
                
                # 更新层级
                parent = Department.query.get(new_parent_id)
                if not parent:
                    raise ValueError(f"父部门不存在: {new_parent_id}")
                kwargs['level'] = parent.level + 1
            else:
                kwargs['level'] = 1
        
        # 如果更新部门代码，需要验证唯一性
        if 'code' in kwargs and kwargs['code'] != department.code:
            if Department.query.filter_by(code=kwargs['code']).first():
                raise ValueError(f"部门代码已存在: {kwargs['code']}")
        
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(department, key):
                setattr(department, key, value)
        
        db.session.commit()
        
        return department
    
    @staticmethod
    def delete_department(dept_id: int, force: bool = False) -> bool:
        """
        删除部门
        
        Args:
            dept_id: 部门ID
            force: 是否强制删除（即使有子部门或用户）
            
        Returns:
            是否删除成功
            
        Raises:
            ValueError: 删除条件不满足
        """
        department = Department.query.get(dept_id)
        if not department:
            return False
        
        # 检查是否有子部门
        if department.children.count() > 0:
            if not force:
                raise ValueError("该部门下有子部门，无法删除")
            # 强制删除时，将子部门的parent_id设为None
            for child in department.children:
                child.parent_id = None
        
        # 检查是否有用户
        if department.users.count() > 0:
            if not force:
                raise ValueError("该部门下有用户，无法删除")
            # 强制删除时，将用户的department_id设为None
            for user in department.users:
                user.department_id = None
        
        db.session.delete(department)
        db.session.commit()
        
        return True
    
    @staticmethod
    def _is_descendant(ancestor_id: int, descendant_id: int) -> bool:
        """
        检查一个部门是否是另一个部门的后代
        
        Args:
            ancestor_id: 祖先部门ID
            descendant_id: 后代部门ID
            
        Returns:
            是否是后代关系
        """
        current = Department.query.get(descendant_id)
        while current and current.parent_id:
            if current.parent_id == ancestor_id:
                return True
            current = Department.query.get(current.parent_id)
        return False
    
    @staticmethod
    def get_department_users(dept_id: int, include_children: bool = False):
        """
        获取部门下的用户
        
        Args:
            dept_id: 部门ID
            include_children: 是否包含子部门的用户
            
        Returns:
            用户列表
        """
        department = Department.query.get(dept_id)
        if not department:
            return []
        
        if not include_children:
            return list(department.users)
        
        # 包含子部门用户
        dept_ids = [dept_id]
        dept_ids.extend(DepartmentService._get_all_child_ids(dept_id))
        
        from database.models import User
        return User.query.filter(User.department_id.in_(dept_ids)).all()
    
    @staticmethod
    def _get_all_child_ids(dept_id: int) -> List[int]:
        """
        递归获取所有子部门ID
        
        Args:
            dept_id: 部门ID
            
        Returns:
            子部门ID列表
        """
        children = Department.query.filter_by(parent_id=dept_id).all()
        result = []
        for child in children:
            result.append(child.id)
            result.extend(DepartmentService._get_all_child_ids(child.id))
        return result
    
    @staticmethod
    def search_departments(keyword: str) -> List[Department]:
        """
        搜索部门
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的部门列表
        """
        return Department.query.filter(
            or_(
                Department.name.like(f'%{keyword}%'),
                Department.code.like(f'%{keyword}%'),
                Department.description.like(f'%{keyword}%')
            )
        ).all()
