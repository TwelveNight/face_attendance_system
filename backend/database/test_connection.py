"""
测试数据库连接
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'backend'))

from config.settings import Config


def test_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("测试数据库连接")
    print("=" * 60)
    
    db_uri = Config.DATABASE_URI
    print(f"\n数据库URI: {db_uri}")
    
    # 判断数据库类型
    if 'sqlite' in db_uri.lower():
        print("\n数据库类型: SQLite")
        return test_sqlite(db_uri)
    elif 'mysql' in db_uri.lower():
        print("\n数据库类型: MySQL")
        return test_mysql(db_uri)
    else:
        print("\n❌ 不支持的数据库类型")
        return False


def test_sqlite(db_uri):
    """测试SQLite连接"""
    import sqlite3
    import re
    
    # 提取数据库文件路径
    match = re.search(r'sqlite:///(.+)', db_uri)
    if not match:
        print("❌ 无法解析SQLite路径")
        return False
    
    db_path = match.group(1)
    print(f"数据库文件: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n✓ 连接成功！")
        print(f"\n当前数据库中的表 ({len(tables)} 张):")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ 连接失败: {str(e)}")
        return False


def test_mysql(db_uri):
    """测试MySQL连接"""
    import pymysql
    import re
    
    # 解析连接信息
    pattern = r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)'
    match = re.match(pattern, db_uri)
    
    if not match:
        print(f"❌ 无法解析数据库URI")
        return False
    
    user, password, host, port, database = match.groups()
    
    print(f"主机: {host}:{port}")
    print(f"数据库: {database}")
    print(f"用户: {user}")
    
    try:
        conn = pymysql.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # 查询所有表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print(f"\n✓ 连接成功！")
        print(f"\n当前数据库中的表 ({len(tables)} 张):")
        for table in tables:
            print(f"  - {table[0]}")
        
        # 检查是否需要迁移
        table_names = [table[0] for table in tables]
        new_tables = ['admin', 'admin_login_log', 'department', 'attendance_rule', 
                     'holiday', 'leave_request', 'makeup_request', 'system_config']
        
        missing_tables = [t for t in new_tables if t not in table_names]
        
        if missing_tables:
            print(f"\n⚠️  需要迁移！缺少以下表:")
            for table in missing_tables:
                print(f"  - {table}")
            print(f"\n请运行: python database/migrate.py")
            cursor.close()
            conn.close()
            return False
        else:
            print(f"\n✓ 所有表都已创建，数据库已迁移！")
            cursor.close()
            conn.close()
            return True
        
    except pymysql.err.OperationalError as e:
        error_code = e.args[0]
        error_msg = e.args[1]
        
        if error_code == 1045:
            print(f"\n❌ 认证失败: 用户名或密码错误")
        elif error_code == 1049:
            print(f"\n❌ 数据库不存在: {database}")
            print(f"\n请先创建数据库:")
            print(f"  CREATE DATABASE {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        elif error_code == 2003:
            print(f"\n❌ 无法连接到MySQL服务器: {host}:{port}")
            print(f"  请检查MySQL服务是否启动")
        else:
            print(f"\n❌ 连接失败: {error_msg}")
        
        return False
        
    except Exception as e:
        print(f"\n❌ 连接失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_connection()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ 数据库连接测试通过！")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 数据库连接测试失败！")
        print("=" * 60)
        sys.exit(1)
