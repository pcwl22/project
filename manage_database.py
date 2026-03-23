#!/usr/bin/env python3
"""
数据库管理工具
提供数据库表的创建、更新、查询等功能
"""
import pymysql
import sys

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '202217',
    'database': 'ultralytics_auth',
    'charset': 'utf8mb4'
}

def connect_db():
    """连接数据库"""
    return pymysql.connect(**DB_CONFIG)

def show_users():
    """显示所有用户信息"""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, 
                   CASE WHEN security_question IS NOT NULL AND security_question != '' 
                        THEN '已设置' ELSE '未设置' END as question_status,
                   created_at
            FROM users
            ORDER BY id
        """)
        
        users = cursor.fetchall()
        
        print("\n" + "=" * 80)
        print("用户列表")
        print("=" * 80)
        print(f"{'ID':<5} {'用户名':<20} {'安全问题':<10} {'创建时间':<20}")
        print("-" * 80)
        
        for user in users:
            print(f"{user[0]:<5} {user[1]:<20} {user[2]:<10} {str(user[3]):<20}")
        
        print("-" * 80)
        print(f"总计: {len(users)} 个用户\n")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")

def set_security_question():
    """为用户设置安全问题"""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # 显示用户列表
        cursor.execute("SELECT id, username FROM users ORDER BY id")
        users = cursor.fetchall()
        
        print("\n用户列表:")
        for user in users:
            print(f"  {user[0]}. {user[1]}")
        
        # 选择用户
        user_id = input("\n请输入用户ID: ").strip()
        if not user_id.isdigit():
            print("❌ 无效的用户ID")
            return
        
        # 检查用户是否存在
        cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            print("❌ 用户不存在")
            return
        
        print(f"\n为用户 '{user[0]}' 设置安全问题")
        
        # 显示预设问题
        questions = [
            "您的出生地是？",
            "您母亲的姓名是？",
            "您的小学名称是？",
            "您最喜欢的颜色是？",
            "您的宠物名字是？",
            "您最喜欢的电影是？",
            "您父亲的生日是？",
            "您的学号是？"
        ]
        
        print("\n预设问题:")
        for i, q in enumerate(questions, 1):
            print(f"  {i}. {q}")
        print("  0. 自定义问题")
        
        choice = input("\n选择问题 (0-8): ").strip()
        
        if choice == '0':
            question = input("请输入自定义问题: ").strip()
        elif choice.isdigit() and 1 <= int(choice) <= len(questions):
            question = questions[int(choice) - 1]
        else:
            print("❌ 无效的选择")
            return
        
        answer = input("请输入答案: ").strip()
        
        if not question or not answer:
            print("❌ 问题和答案不能为空")
            return
        
        # 更新数据库
        cursor.execute("""
            UPDATE users 
            SET security_question = %s, security_answer = %s
            WHERE id = %s
        """, (question, answer, user_id))
        
        conn.commit()
        print(f"\n✅ 已为用户 '{user[0]}' 设置安全问题")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 设置失败: {e}")

def reset_password():
    """重置用户密码"""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # 显示用户列表
        cursor.execute("SELECT id, username FROM users ORDER BY id")
        users = cursor.fetchall()
        
        print("\n用户列表:")
        for user in users:
            print(f"  {user[0]}. {user[1]}")
        
        # 选择用户
        user_id = input("\n请输入用户ID: ").strip()
        if not user_id.isdigit():
            print("❌ 无效的用户ID")
            return
        
        # 检查用户是否存在
        cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            print("❌ 用户不存在")
            return
        
        print(f"\n为用户 '{user[0]}' 重置密码")
        new_password = input("请输入新密码: ").strip()
        
        if len(new_password) < 5:
            print("❌ 密码长度不能小于5位")
            return
        
        # 更新密码
        cursor.execute("UPDATE users SET password = %s WHERE id = %s", (new_password, user_id))
        conn.commit()
        
        print(f"\n✅ 密码已重置为: {new_password}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 重置失败: {e}")

def main_menu():
    """主菜单"""
    while True:
        print("\n" + "=" * 60)
        print("数据库管理工具")
        print("=" * 60)
        print("1. 更新数据库表结构（添加安全问题字段）")
        print("2. 查看所有用户")
        print("3. 为用户设置安全问题")
        print("4. 重置用户密码")
        print("5. 退出")
        print("=" * 60)
        
        choice = input("\n请选择操作 (1-5): ").strip()
        
        if choice == '1':
            from update_database import update_database
            update_database()
        elif choice == '2':
            show_users()
        elif choice == '3':
            set_security_question()
        elif choice == '4':
            reset_password()
        elif choice == '5':
            print("\n再见！")
            break
        else:
            print("❌ 无效的选择")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
