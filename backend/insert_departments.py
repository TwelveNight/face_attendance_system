"""
使用Python执行部门数据插入
"""
import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

from database.models import db, Department
from api.app import create_app

app = create_app()

with app.app_context():
    print("=" * 60)
    print("开始插入部门数据...")
    print("=" * 60)
    
    try:
        # 检查是否已有数据
        existing_count = Department.query.count()
        if existing_count > 0:
            print(f"\n⚠️  警告：数据库中已有 {existing_count} 个部门")
            response = input("是否继续添加？这可能导致重复数据 (y/n): ")
            if response.lower() != 'y':
                print("操作已取消")
                sys.exit(0)
        
        # 一级部门（学院）
        print("\n[1/3] 插入一级部门（学院）...")
        colleges = [
            Department(name='计算机学院', code='CS', level=1, sort_order=1, 
                      description='计算机科学与技术相关专业', is_active=True),
            Department(name='电子信息学院', code='EE', level=1, sort_order=2, 
                      description='电子信息工程相关专业', is_active=True),
            Department(name='机械工程学院', code='ME', level=1, sort_order=3, 
                      description='机械工程相关专业', is_active=True),
            Department(name='经济管理学院', code='EM', level=1, sort_order=4, 
                      description='经济管理相关专业', is_active=True),
        ]
        
        for college in colleges:
            db.session.add(college)
        db.session.commit()
        print(f"✓ 成功插入 {len(colleges)} 个学院")
        
        # 获取学院ID
        cs_college = Department.query.filter_by(code='CS').first()
        ee_college = Department.query.filter_by(code='EE').first()
        me_college = Department.query.filter_by(code='ME').first()
        em_college = Department.query.filter_by(code='EM').first()
        
        # 二级部门（专业）
        print("\n[2/3] 插入二级部门（专业）...")
        majors = [
            # 计算机学院
            Department(name='计算机科学与技术', code='CS_CST', parent_id=cs_college.id, 
                      level=2, sort_order=1, description='计算机科学与技术专业', is_active=True),
            Department(name='软件工程', code='CS_SE', parent_id=cs_college.id, 
                      level=2, sort_order=2, description='软件工程专业', is_active=True),
            Department(name='网络工程', code='CS_NE', parent_id=cs_college.id, 
                      level=2, sort_order=3, description='网络工程专业', is_active=True),
            Department(name='人工智能', code='CS_AI', parent_id=cs_college.id, 
                      level=2, sort_order=4, description='人工智能专业', is_active=True),
            
            # 电子信息学院
            Department(name='电子信息工程', code='EE_EIE', parent_id=ee_college.id, 
                      level=2, sort_order=1, description='电子信息工程专业', is_active=True),
            Department(name='通信工程', code='EE_CE', parent_id=ee_college.id, 
                      level=2, sort_order=2, description='通信工程专业', is_active=True),
            Department(name='自动化', code='EE_AUTO', parent_id=ee_college.id, 
                      level=2, sort_order=3, description='自动化专业', is_active=True),
            
            # 机械工程学院
            Department(name='机械设计制造及其自动化', code='ME_MD', parent_id=me_college.id, 
                      level=2, sort_order=1, description='机械设计制造及其自动化专业', is_active=True),
            Department(name='车辆工程', code='ME_VE', parent_id=me_college.id, 
                      level=2, sort_order=2, description='车辆工程专业', is_active=True),
            
            # 经济管理学院
            Department(name='工商管理', code='EM_BA', parent_id=em_college.id, 
                      level=2, sort_order=1, description='工商管理专业', is_active=True),
            Department(name='会计学', code='EM_ACC', parent_id=em_college.id, 
                      level=2, sort_order=2, description='会计学专业', is_active=True),
        ]
        
        for major in majors:
            db.session.add(major)
        db.session.commit()
        print(f"✓ 成功插入 {len(majors)} 个专业")
        
        # 获取专业ID
        cs_cst = Department.query.filter_by(code='CS_CST').first()
        cs_se = Department.query.filter_by(code='CS_SE').first()
        cs_ai = Department.query.filter_by(code='CS_AI').first()
        
        # 三级部门（班级）
        print("\n[3/3] 插入三级部门（班级）...")
        classes = [
            # 计算机科学与技术
            Department(name='计科2021级1班', code='CS_CST_2021_1', parent_id=cs_cst.id, 
                      level=3, sort_order=1, description='计算机科学与技术2021级1班', is_active=True),
            Department(name='计科2021级2班', code='CS_CST_2021_2', parent_id=cs_cst.id, 
                      level=3, sort_order=2, description='计算机科学与技术2021级2班', is_active=True),
            Department(name='计科2022级1班', code='CS_CST_2022_1', parent_id=cs_cst.id, 
                      level=3, sort_order=3, description='计算机科学与技术2022级1班', is_active=True),
            
            # 软件工程
            Department(name='软工2021级1班', code='CS_SE_2021_1', parent_id=cs_se.id, 
                      level=3, sort_order=1, description='软件工程2021级1班', is_active=True),
            Department(name='软工2021级2班', code='CS_SE_2021_2', parent_id=cs_se.id, 
                      level=3, sort_order=2, description='软件工程2021级2班', is_active=True),
            Department(name='软工2022级1班', code='CS_SE_2022_1', parent_id=cs_se.id, 
                      level=3, sort_order=3, description='软件工程2022级1班', is_active=True),
            
            # 人工智能
            Department(name='人工智能2021级1班', code='CS_AI_2021_1', parent_id=cs_ai.id, 
                      level=3, sort_order=1, description='人工智能2021级1班', is_active=True),
            Department(name='人工智能2022级1班', code='CS_AI_2022_1', parent_id=cs_ai.id, 
                      level=3, sort_order=2, description='人工智能2022级1班', is_active=True),
        ]
        
        for cls in classes:
            db.session.add(cls)
        db.session.commit()
        print(f"✓ 成功插入 {len(classes)} 个班级")
        
        # 统计结果
        print("\n" + "=" * 60)
        print("插入完成！")
        print("=" * 60)
        total_count = Department.query.count()
        level1_count = Department.query.filter_by(level=1).count()
        level2_count = Department.query.filter_by(level=2).count()
        level3_count = Department.query.filter_by(level=3).count()
        
        print(f"\n数据库中共有 {total_count} 个部门：")
        print(f"  - 一级部门（学院）: {level1_count} 个")
        print(f"  - 二级部门（专业）: {level2_count} 个")
        print(f"  - 三级部门（班级）: {level3_count} 个")
        
        # 显示部门树
        print("\n部门结构预览：")
        print("-" * 60)
        for college in Department.query.filter_by(level=1).order_by(Department.sort_order).all():
            print(f"📚 {college.name} ({college.code})")
            for major in Department.query.filter_by(parent_id=college.id).order_by(Department.sort_order).all():
                print(f"  └─ 📖 {major.name}")
                for cls in Department.query.filter_by(parent_id=major.id).order_by(Department.sort_order).all():
                    print(f"      └─ 👥 {cls.name}")
        
        print("\n✅ 所有部门数据插入成功！")
        
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ 插入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
