"""
Flask应用入口
"""
import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import logging

from config.settings import Config
from database.models import db
from models.model_manager import model_manager
from api.middleware import handle_errors, log_requests
from services.scheduler_service import init_scheduler


def init_scheduler_service(app):
    """初始化定时任务服务"""
    try:
        init_scheduler(app)
        app.logger.info("定时任务服务初始化成功")
    except Exception as e:
        app.logger.error(f"定时任务服务初始化失败: {e}")


def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 配置
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Config.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    
    # JWT配置
    app.config['JWT_SECRET_KEY'] = Config.SECRET_KEY
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # 设置token不过期
    
    # 初始化数据库
    db.init_app(app)
    
    # 初始化JWT
    jwt = JWTManager(app)
    
    # CORS
    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)
    
    # 日志配置
    setup_logging(app)
    
    # 中间件
    handle_errors(app)
    log_requests(app)
    
    # 注册路由
    register_blueprints(app)
    
    # 加载模型
    with app.app_context():
        try:
            model_manager.load_models()
        except Exception as e:
            app.logger.warning(f"模型加载失败: {e}")
    
    # 初始化定时任务
    init_scheduler_service(app)
    
    return app


def setup_logging(app):
    """配置日志"""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format=Config.LOG_FORMAT,
        handlers=[
            logging.FileHandler(Config.LOG_FILE),
            logging.StreamHandler()
        ]
    )
    app.logger.setLevel(getattr(logging, Config.LOG_LEVEL))


def register_blueprints(app):
    """注册蓝图"""
    from api.routes import user_bp, attendance_bp, statistics_bp, video_bp, system_bp
    from api.routes.admin_auth import admin_auth_bp
    from api.routes.user_auth import user_auth_bp
    from api.routes.department import department_bp
    from api.routes.attendance_rule import attendance_rule_bp
    from api.routes.scheduler import scheduler_bp
    from api.routes.log import log_bp
    
    # ==================== 认证模块 ====================
    # 管理员认证：登录、登出、密码修改
    app.register_blueprint(admin_auth_bp)
    # 用户认证：登录、登出、密码设置与修改
    app.register_blueprint(user_auth_bp)
    
    # ==================== 核心业务模块 ====================
    # 用户管理：注册、查询、更新、删除用户及人脸数据
    app.register_blueprint(user_bp, url_prefix='/api/users')
    # 考勤管理：人脸打卡、考勤记录查询、导出
    app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
    # 考勤规则：规则配置、分配、统计
    app.register_blueprint(attendance_rule_bp, url_prefix='/api/attendance-rules')
    # 部门管理：部门增删改查、成员管理
    app.register_blueprint(department_bp)
    
    # ==================== 数据分析模块 ====================
    # 统计分析：每日/每周/每月考勤统计
    app.register_blueprint(statistics_bp, url_prefix='/api/statistics')
    # 日志管理：操作日志、系统日志、登录日志
    app.register_blueprint(log_bp, url_prefix='/api/log')
    
    # ==================== 系统功能模块 ====================
    # 视频流：实时摄像头视频流
    app.register_blueprint(video_bp, url_prefix='/api/video')
    # 系统信息：健康检查、GPU状态、模型重载
    app.register_blueprint(system_bp, url_prefix='/api/system')
    # 定时任务：缺勤检测配置与手动触发
    app.register_blueprint(scheduler_bp, url_prefix='/api/scheduler')
    
    app.logger.info("路由注册完成")
