"""
API中间件
错误处理、日志、响应格式化
"""
from flask import jsonify, request
from functools import wraps
import traceback
import time


def success_response(data=None, message="success", code=200):
    """成功响应"""
    return jsonify({
        'code': code,
        'message': message,
        'data': data
    }), code


def error_response(message="error", code=400, error=None):
    """错误响应"""
    response = {
        'code': code,
        'message': message
    }
    if error:
        response['error'] = str(error)
    return jsonify(response), code


def handle_errors(app):
    """注册错误处理器"""
    
    @app.errorhandler(400)
    def bad_request(e):
        return error_response("请求参数错误", 400, str(e))
    
    @app.errorhandler(404)
    def not_found(e):
        return error_response("资源不存在", 404, str(e))
    
    @app.errorhandler(500)
    def internal_error(e):
        return error_response("服务器内部错误", 500, str(e))
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"未处理的异常: {str(e)}\n{traceback.format_exc()}")
        return error_response("服务器错误", 500, str(e))


def log_requests(app):
    """请求日志中间件"""
    
    @app.before_request
    def before_request():
        request.start_time = time.time()
        app.logger.info(f"[{request.method}] {request.path}")
    
    @app.after_request
    def after_request(response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            app.logger.info(f"[{request.method}] {request.path} - {response.status_code} ({duration:.3f}s)")
        return response


def require_json(f):
    """要求JSON请求体的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return error_response("Content-Type必须是application/json", 400)
        return f(*args, **kwargs)
    return decorated_function
