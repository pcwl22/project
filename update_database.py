#!/usr/bin/env python3
"""
数据库表结构更新脚本
添加安全问题相关字段
"""
import pymysql
import sys

def update_database():
    """更新数据库表结构"""
    print("=" * 60)
    print("数据库表结构更新工具")
    print("=" * 60)
    
    # 数据库连接配置
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '202217',
        'database': 'ultralytics_auth',
        'charset': 'utf8mb4'
    }
    
    try:
        # 连接数据库
        print("\n1. 连接数据库...")
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()
        print("   ✅ 数据库连接成功")
        
        # 检查表是否存在
        print("\n2. 检查 users 表...")
        cursor.execute("SHOW TABLES LIKE 'users'")
        if not cursor.fetchone():
            print("   ❌ users 表不存在")
            return False
        print("   ✅ users 表存在")
        
        # 检查现有字段
        print("\n3. 检查现有字段...")
        cursor.execute("DESCRIBE users")
        existing_columns = {row[0] for row in cursor.fetchall()}
        print(f"   现有字段: {', '.join(existing_columns)}")
        
        # 需要添加的字段
        fields_to_add = []
        
        if 'email' not in existing_columns:
            fields_to_add.append(('email', 'VARCHAR(255) NULL', '邮箱'))
        
        if 'security_question' not in existing_columns:
            fields_to_add.append(('security_question', 'VARCHAR(255) NULL', '安全问题'))
        
        if 'security_answer' not in existing_columns:
            fields_to_add.append(('security_answer', 'VARCHAR(255) NULL', '安全答案'))
        
        if not fields_to_add:
            print("\n   ✅ 所有字段已存在，无需更新")
            return True
        
        # 添加字段
        print(f"\n4. 添加新字段 ({len(fields_to_add)} 个)...")
        for field_name, field_type, field_desc in fields_to_add:
            try:
                sql = f"ALTER TABLE users ADD COLUMN {field_name} {field_type}"
                cursor.execute(sql)
                print(f"   ✅ 添加字段: {field_name} ({field_desc})")
            except pymysql.err.OperationalError as e:
                if "Duplicate column name" in str(e):
                    print(f"   ⚠️  字段已存在: {field_name}")
                else:
                    raise
        
        # 提交更改
        connection.commit()
        print("\n5. 提交更改...")
        print("   ✅ 数据库更新成功")
        
        # 显示更新后的表结构
        print("\n6. 更新后的表结构:")
        cursor.execute("DESCRIBE users")
        rows = cursor.fetchall()
        print("\n   字段名              类型                  允许NULL  键      默认值")
        print("   " + "-" * 70)
        for row in rows:
            field = row[0].ljust(20)
            type_ = row[1].ljust(20)
            null = row[2].ljust(8)
            key = row[3].ljust(8)
            default = str(row[4] or '').ljust(10)
            print(f"   {field}{type_}{null}{key}{default}")
        
        # 检查现有用户的安全问题设置情况
        print("\n7. 检查现有用户...")
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN security_question IS NOT NULL AND security_question != '' THEN 1 ELSE 0 END) as with_question,
                SUM(CASE WHEN security_question IS NULL OR security_question = '' THEN 1 ELSE 0 END) as without_question
            FROM users
        """)
        stats = cursor.fetchone()
        
        print(f"   总用户数: {stats[0]}")
        print(f"   已设置安全问题: {stats[1]}")
        print(f"   未设置安全问题: {stats[2]}")
        
        if stats[2] > 0:
            print("\n   ⚠️  警告: 有 {} 个用户未设置安全问题".format(stats[2]))
            print("   这些用户将无法使用忘记密码功能")
            print("   建议为这些用户设置默认安全问题或通知他们重新注册")
            
            # 询问是否为现有用户设置默认安全问题
            print("\n   是否为现有用户设置默认安全问题？")
            print("   默认问题: '您的学号是？'")
            print("   默认答案: 用户名")
            choice = input("   输入 y 确认，其他键跳过: ").strip().lower()
            
            if choice == 'y':
                cursor.execute("""
                    UPDATE users 
                    SET security_question = '您的学号是？',
                        security_answer = username
                    WHERE security_question IS NULL OR security_question = ''
                """)
                connection.commit()
                print(f"   ✅ 已为 {stats[2]} 个用户设置默认安全问题")
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 60)
        print("✅ 数据库更新完成！")
        print("=" * 60)
        print("\n📝 后续步骤:")
        print("1. 重启后端服务以应用更改")
        print("2. 测试注册功能（必须填写安全问题）")
        print("3. 测试忘记密码功能")
        print("4. 通知现有用户更新安全问题（如果需要）")
        
        return True
        
    except pymysql.err.OperationalError as e:
        print(f"\n❌ 数据库连接失败: {e}")
        print("\n💡 请检查:")
        print("1. MySQL 服务是否运行: net start MySQL80")
        print("2. 数据库配置是否正确")
        print("3. 用户名密码是否正确")
        return False
        
    except Exception as e:
        print(f"\n❌ 更新失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = update_database()
    sys.exit(0 if success else 1)
