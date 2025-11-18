"""
API服务器启动脚本
"""
import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

from api.app import create_app
from config.settings import Config

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
