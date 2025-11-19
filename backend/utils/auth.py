"""
认证工具类
提供密码加密、JWT Token生成和验证等功能
"""
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import jwt
from config.settings import Config


class AuthUtils:
    """认证工具类"""
    
    # JWT密钥和配置
    SECRET_KEY = Config.SECRET_KEY
    ALGORITHM = 'HS256'
    ACCESS_TOKEN_EXPIRE_HOURS = 24  # Token有效期24小时
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        密码加密
        
        Args:
            password: 明文密码
            
        Returns:
            加密后的密码哈希
        """
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        验证密码
        
        Args:
            password: 明文密码
            password_hash: 密码哈希
            
        Returns:
            密码是否正确
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    @classmethod
    def generate_token(cls, user_id: int, user_type: str, **extra_data) -> str:
        """
        生成JWT Token
        
        Args:
            user_id: 用户ID
            user_type: 用户类型 ('admin' 或 'user')
            **extra_data: 额外的数据（如username）
            
        Returns:
            JWT Token字符串
        """
        payload = {
            'user_id': user_id,
            'user_type': user_type,
            'exp': datetime.utcnow() + timedelta(hours=cls.ACCESS_TOKEN_EXPIRE_HOURS),
            'iat': datetime.utcnow()
        }
        
        # 添加额外数据
        payload.update(extra_data)
        
        token = jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return token
    
    @classmethod
    def decode_token(cls, token: str) -> dict:
        """
        解码JWT Token
        
        Args:
            token: JWT Token字符串
            
        Returns:
            解码后的payload字典
            
        Raises:
            jwt.ExpiredSignatureError: Token已过期
            jwt.InvalidTokenError: Token无效
        """
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError('Token已过期')
        except jwt.InvalidTokenError:
            raise ValueError('Token无效')
    
    @classmethod
    def get_token_from_request(cls) -> str:
        """
        从请求头中获取Token
        
        Returns:
            Token字符串
            
        Raises:
            ValueError: 未提供Token或格式错误
        """
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            raise ValueError('未提供认证Token')
        
        # 格式: "Bearer <token>"
        parts = auth_header.split()
        
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            raise ValueError('Token格式错误')
        
        return parts[1]
    
    @classmethod
    def get_current_user(cls) -> dict:
        """
        获取当前登录用户信息
        
        Returns:
            用户信息字典 {'user_id': int, 'user_type': str, ...}
            
        Raises:
            ValueError: Token无效或已过期
        """
        token = cls.get_token_from_request()
        payload = cls.decode_token(token)
        return payload


def admin_required(f):
    """
    管理员权限装饰器
    只有管理员可以访问
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user_info = AuthUtils.get_current_user()
            
            if user_info.get('user_type') != 'admin':
                return jsonify({
                    'success': False,
                    'message': '需要管理员权限'
                }), 403
            
            # 将用户信息传递给路由函数
            kwargs['current_admin'] = user_info
            return f(*args, **kwargs)
            
        except ValueError as e:
            print(f"✗ 认证失败 (ValueError): {str(e)}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 401
        except Exception as e:
            print(f"✗ 认证失败 (Exception): {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'认证失败: {str(e)}'
            }), 401
    
    return decorated_function


def user_required(f):
    """
    普通用户权限装饰器
    需要登录（管理员或普通用户）
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user_info = AuthUtils.get_current_user()
            
            # 将用户信息传递给路由函数
            kwargs['current_user'] = user_info
            return f(*args, **kwargs)
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 401
        except Exception as e:
            return jsonify({
                'success': False,
                'message': '认证失败'
            }), 401
    
    return decorated_function


def optional_auth(f):
    """
    可选认证装饰器
    如果提供了Token则验证，否则继续执行
    用于打卡等功能（可以无需登录）
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user_info = AuthUtils.get_current_user()
            kwargs['current_user'] = user_info
        except:
            # 没有Token或Token无效，继续执行
            kwargs['current_user'] = None
        
        return f(*args, **kwargs)
    
    return decorated_function
