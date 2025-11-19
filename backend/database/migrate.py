"""
数据库迁移脚本
执行 migration_v3.sql 中的所有SQL语句
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'backend'))

from config.settings import Config
from database.models import db
from flask import Flask
import pymysql


def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


def execute_migration():
    """执行数据库迁移"""
    print("=" * 60)
    print("开始执行数据库迁移 V3.0")
    print("=" * 60)
    
    # 读取SQL文件
    sql_file = Path(__file__).parent / 'migration_v3.sql'
    if not sql_file.exists():
        print(f"❌ 错误: 找不到迁移文件 {sql_file}")
        return False
    
    print(f"\n📄 读取迁移文件: {sql_file}")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 解析数据库连接信息
    db_uri = Config.DATABASE_URI
    # 格式: mysql+pymysql://user:password@host:port/database
    
    if 'sqlite' in db_uri.lower():
        print("\n⚠️  检测到SQLite数据库")
        print("SQLite不完全支持ALTER TABLE语句，建议使用MySQL")
        print("\n正在尝试使用SQLAlchemy进行迁移...")
        return migrate_with_sqlalchemy()
    
    # MySQL迁移
    try:
        # 解析连接信息
        import re
        pattern = r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)'
        match = re.match(pattern, db_uri)
        
        if not match:
            print(f"❌ 无法解析数据库URI: {db_uri}")
            return False
        
        user, password, host, port, database = match.groups()
        
        print(f"\n🔗 连接数据库:")
        print(f"   主机: {host}:{port}")
        print(f"   数据库: {database}")
        print(f"   用户: {user}")
        
        # 连接数据库
        connection = pymysql.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # 分割SQL语句（按分号分割，但忽略注释中的分号）
        statements = []
        current_statement = []
        in_comment = False
        
        for line in sql_content.split('\n'):
            stripped = line.strip()
            
            # 跳过空行
            if not stripped:
                continue
            
            # 跳过注释行
            if stripped.startswith('--'):
                continue
            
            current_statement.append(line)
            
            # 检查是否是语句结束
            if stripped.endswith(';'):
                statement = '\n'.join(current_statement)
                if statement.strip():
                    statements.append(statement)
                current_statement = []
        
        print(f"\n📊 共 {len(statements)} 条SQL语句")
        print("\n开始执行...")
        
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(statements, 1):
            try:
                # 显示正在执行的语句（简化）
                first_line = statement.split('\n')[0][:80]
                print(f"\n[{i}/{len(statements)}] {first_line}...")
                
                cursor.execute(statement)
                connection.commit()
                success_count += 1
                print(f"✓ 成功")
                
            except pymysql.err.OperationalError as e:
                error_code = e.args[0]
                error_msg = e.args[1]
                
                # 忽略已存在的错误
                if error_code == 1050:  # Table already exists
                    print(f"⚠️  表已存在，跳过")
                    success_count += 1
                elif error_code == 1060:  # Duplicate column name
                    print(f"⚠️  字段已存在，跳过")
                    success_count += 1
                elif error_code == 1061:  # Duplicate key name
                    print(f"⚠️  索引已存在，跳过")
                    success_count += 1
                elif error_code == 1062:  # Duplicate entry
                    print(f"⚠️  数据已存在，跳过")
                    success_count += 1
                else:
                    print(f"❌ 错误: {error_msg}")
                    error_count += 1
                    
            except Exception as e:
                print(f"❌ 错误: {str(e)}")
                error_count += 1
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 60)
        print("数据库迁移完成")
        print("=" * 60)
        print(f"✓ 成功: {success_count} 条")
        print(f"✗ 失败: {error_count} 条")
        print("=" * 60)
        
        return error_count == 0
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def migrate_with_sqlalchemy():
    """使用SQLAlchemy进行迁移（SQLite）"""
    print("\n使用SQLAlchemy创建所有表...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # 导入所有模型
            from database.models import (
                Admin, AdminLoginLog, Department, AttendanceRule
            )
            
            # 创建所有表
            db.create_all()
            
            print("✓ 所有表创建成功")
            return True
            
        except Exception as e:
            print(f"❌ 创建表失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    success = execute_migration()
    
    if success:
        print("\n✅ 数据库迁移成功！")
        print("\n下一步:")
        print("1. 检查数据库表是否正确创建")
        print("2. 更新后端ORM模型")
        print("3. 开始实现认证系统")
    else:
        print("\n❌ 数据库迁移失败，请检查错误信息")
        sys.exit(1)
