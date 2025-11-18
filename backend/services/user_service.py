"""
用户服务
处理用户管理的业务逻辑
"""
import numpy as np
from typing import List, Optional, Dict
from pathlib import Path
import shutil

from database.repositories import UserRepository, SystemLogRepository
from database.models import User
from config.settings import Config
from .face_service import FaceService


class UserService:
    """用户管理服务"""
    
    def __init__(self):
        """初始化用户服务"""
        self.user_repo = UserRepository
        self.log_repo = SystemLogRepository
        self.face_service = FaceService()
    
    def create_user(self, username: str, student_id: Optional[str] = None,
                   face_images: Optional[List[np.ndarray]] = None) -> Optional[User]:
        """
        创建用户
        
        Args:
            username: 用户名
            student_id: 学号
            face_images: 人脸图像列表(可选)
            
        Returns:
            创建的用户对象 or None
        """
        try:
            # 检查用户名是否已存在
            existing_user = self.user_repo.get_by_username(username)
            if existing_user:
                print(f"用户名已存在: {username}")
                return None
            
            # 检查学号是否已存在
            if student_id:
                existing_student = self.user_repo.get_by_student_id(student_id)
                if existing_student:
                    print(f"学号已存在: {student_id}")
                    return None
            
            # 创建用户
            user = self.user_repo.create(username=username, student_id=student_id)
            
            # 如果提供了人脸图像,注册人脸
            if face_images and len(face_images) > 0:
                success = self.face_service.register_user_faces(user.id, face_images)
                if not success:
                    print("⚠️  用户创建成功,但人脸注册失败")
            
            # 记录日志
            self.log_repo.create(
                event_type='user_created',
                message=f"创建用户: {username}",
                user_id=user.id
            )
            
            print(f"✓ 用户创建成功: {username} (ID: {user.id})")
            return user
        
        except Exception as e:
            print(f"✗ 创建用户失败: {e}")
            return None
    
    def get_user(self, user_id: int) -> Optional[User]:
        """获取用户"""
        return self.user_repo.get_by_id(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.user_repo.get_by_username(username)
    
    def get_user_by_student_id(self, student_id: str) -> Optional[User]:
        """根据学号获取用户"""
        return self.user_repo.get_by_student_id(student_id)
    
    def get_all_users(self, active_only: bool = True) -> List[User]:
        """获取所有用户"""
        return self.user_repo.get_all(active_only=active_only)
    
    def search_users(self, keyword: str, active_only: bool = True) -> List[User]:
        """搜索用户"""
        return self.user_repo.search(keyword, active_only=active_only)
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            **kwargs: 要更新的字段
            
        Returns:
            更新后的用户 or None
        """
        try:
            user = self.user_repo.update(user_id, **kwargs)
            
            if user:
                self.log_repo.create(
                    event_type='user_updated',
                    message=f"更新用户: {user.username}",
                    user_id=user_id
                )
                print(f"✓ 用户更新成功: {user.username}")
            
            return user
        
        except Exception as e:
            print(f"✗ 更新用户失败: {e}")
            return None
    
    def update_user_faces(self, user_id: int, face_images: List[np.ndarray]) -> bool:
        """
        更新用户人脸
        
        Args:
            user_id: 用户ID
            face_images: 新的人脸图像列表
            
        Returns:
            是否成功
        """
        try:
            success = self.face_service.update_user_faces(user_id, face_images)
            
            if success:
                self.log_repo.create(
                    event_type='user_faces_updated',
                    message=f"更新用户人脸数据",
                    user_id=user_id
                )
            
            return success
        
        except Exception as e:
            print(f"✗ 更新用户人脸失败: {e}")
            return False
    
    def delete_user(self, user_id: int, hard_delete: bool = False) -> bool:
        """
        删除用户
        
        Args:
            user_id: 用户ID
            hard_delete: 是否硬删除(物理删除)
            
        Returns:
            是否成功
        """
        try:
            user = self.user_repo.get_by_id(user_id)
            if not user:
                print(f"用户不存在: {user_id}")
                return False
            
            # 删除人脸数据
            self.face_service.remove_user_faces(user_id)
            
            # 删除用户
            if hard_delete:
                success = self.user_repo.hard_delete(user_id)
            else:
                success = self.user_repo.delete(user_id)
            
            if success:
                self.log_repo.create(
                    event_type='user_deleted',
                    message=f"删除用户: {user.username}",
                    user_id=user_id
                )
                print(f"✓ 用户删除成功: {user.username}")
            
            return success
        
        except Exception as e:
            print(f"✗ 删除用户失败: {e}")
            return False
    
    def get_user_count(self, active_only: bool = True) -> int:
        """获取用户数量"""
        return self.user_repo.count(active_only=active_only)
    
    def get_user_statistics(self) -> Dict:
        """获取用户统计信息"""
        total = self.user_repo.count(active_only=False)
        active = self.user_repo.count(active_only=True)
        registered_faces = self.face_service.get_registered_user_count()
        
        return {
            'total': total,
            'active': active,
            'inactive': total - active,
            'registered_faces': registered_faces
        }


if __name__ == '__main__':
    # 测试用户服务
    from database.init_db import create_app
    from database.models import db
    
    app = create_app()
    with app.app_context():
        service = UserService()
        
        # 获取所有用户
        users = service.get_all_users()
        print(f"\n用户列表 ({len(users)}):")
        for user in users:
            print(f"  {user.id}: {user.username} ({user.student_id})")
        
        # 统计信息
        stats = service.get_user_statistics()
        print(f"\n用户统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
