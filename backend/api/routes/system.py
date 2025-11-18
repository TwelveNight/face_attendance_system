"""
系统管理API路由
"""
from flask import Blueprint, request
import torch

from models.model_manager import model_manager
from database.repositories import SystemLogRepository
from config.settings import Config
from api.middleware import success_response, error_response

system_bp = Blueprint('system', __name__)


@system_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        health = {
            'status': 'healthy',
            'database': 'connected',
            'models_loaded': model_manager.is_loaded()
        }
        
        return success_response(health)
    
    except Exception as e:
        return error_response("健康检查失败", 500, str(e))


@system_bp.route('/models', methods=['GET'])
def get_model_status():
    """获取模型状态"""
    try:
        status = model_manager.get_status()
        
        return success_response(status)
    
    except Exception as e:
        return error_response("获取模型状态失败", 500, str(e))


@system_bp.route('/logs', methods=['GET'])
def get_logs():
    """获取系统日志"""
    try:
        limit = int(request.args.get('limit', 100))
        level = request.args.get('level')
        
        logs = SystemLogRepository.get_recent(limit, level)
        
        return success_response([log.to_dict() for log in logs])
    
    except Exception as e:
        return error_response("获取日志失败", 500, str(e))


@system_bp.route('/config', methods=['GET'])
def get_config():
    """获取系统配置"""
    try:
        config = {
            'api_host': Config.API_HOST,
            'api_port': Config.API_PORT,
            'database_uri': Config.DATABASE_URI,
            'use_cuda': Config.USE_CUDA,
            'cuda_available': torch.cuda.is_available(),
            'yolo_threshold': Config.YOLO_CONFIDENCE_THRESHOLD,
            'face_recognition_threshold': Config.FACE_RECOGNITION_THRESHOLD
        }
        
        return success_response(config)
    
    except Exception as e:
        return error_response("获取配置失败", 500, str(e))
