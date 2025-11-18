"""
数据库初始化脚本
创建所有表并可选地插入测试数据
"""
import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask
from config.settings import Config
from database.models import db, User, Attendance, SystemLog
from database.repositories import SystemLogRepository


def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Config.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['SQLALCHEMY_ECHO'] = Config.SQLALCHEMY_ECHO
    
    db.init_app(app)
    return app


def init_database(drop_existing=False, create_sample_data=False):
    """
    初始化数据库
    
    Args:
        drop_existing: 是否删除现有表
        create_sample_data: 是否创建示例数据
    """
    app = create_app()
    
    with app.app_context():
        if drop_existing:
            print("删除现有表...")
            db.drop_all()
        
        print("创建数据库表...")
        db.create_all()
        print("✓ 数据库表创建成功")
        
        # 记录系统日志
        SystemLogRepository.create(
            event_type='system_init',
            message='数据库初始化完成',
            level='INFO'
        )
        
        if create_sample_data:
            print("\n创建示例数据...")
            create_sample_users()
            print("✓ 示例数据创建成功")
        
        print(f"\n数据库位置: {Config.DATABASE_PATH}")
        print("初始化完成!")


def create_sample_users():
    """创建示例用户"""
    from database.repositories import UserRepository
    
    sample_users = [
        {'username': '张三', 'student_id': '2021001'},
        {'username': '李四', 'student_id': '2021002'},
        {'username': '王五', 'student_id': '2021003'},
    ]
    
    for user_data in sample_users:
        try:
            user = UserRepository.create(**user_data)
            print(f"  创建用户: {user.username} ({user.student_id})")
        except Exception as e:
            print(f"  创建用户失败: {user_data['username']} - {e}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='初始化数据库')
    parser.add_argument('--drop', action='store_true', help='删除现有表')
    parser.add_argument('--sample', action='store_true', help='创建示例数据')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("数据库初始化")
    print("=" * 60)
    
    if args.drop:
        confirm = input("⚠️  警告: 这将删除所有现有数据! 确认? (yes/no): ")
        if confirm.lower() != 'yes':
            print("已取消")
            sys.exit(0)
    
    init_database(drop_existing=args.drop, create_sample_data=args.sample)
