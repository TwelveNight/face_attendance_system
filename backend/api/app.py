"""
Flask应用入口
"""
import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask
from flask_cors import CORS
import logging

from config.settings import Config
from database.models import db
from models.model_manager import model_manager
from api.middleware import handle_errors, log_requests


def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 配置
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Config.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    
    # 初始化数据库
    db.init_app(app)
    
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
    
    # 原有路由
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
    app.register_blueprint(statistics_bp, url_prefix='/api/statistics')
    app.register_blueprint(video_bp, url_prefix='/api/video')
    app.register_blueprint(system_bp, url_prefix='/api/system')
    
    # V3.0 新增：认证路由
    app.register_blueprint(admin_auth_bp)  # /api/admin/*
    app.register_blueprint(user_auth_bp)   # /api/auth/*
    
    # V3.0 新增：部门管理路由
    app.register_blueprint(department_bp)  # /api/departments/*
    
    # V3.0 新增：考勤规则路由
    app.register_blueprint(attendance_rule_bp, url_prefix='/api/attendance-rules')
    
    app.logger.info("路由注册完成")


if __name__ == '__main__':
    app = create_app()
    
    print("=" * 60)
    print("人脸识别考勤系统 API 服务器")
    print("=" * 60)
    print(f"地址: http://{Config.API_HOST}:{Config.API_PORT}")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    app.run(
        host=Config.API_HOST,
        port=Config.API_PORT,
        debug=Config.API_DEBUG
    )
