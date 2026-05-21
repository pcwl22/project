"""
数据库迁移脚本：为 detection_results 表添加 file_type 字段
"""
from sqlalchemy import create_engine, text
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.config import settings

def migrate():
    """添加 file_type 字段"""
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        try:
            # 检查字段是否已存在
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'detection_results'
                AND COLUMN_NAME = 'file_type'
            """))
            
            exists = result.fetchone()[0] > 0
            
            if exists:
                print("✓ file_type 字段已存在，无需迁移")
                return
            
            # 添加字段
            print("正在添加 file_type 字段...")
            conn.execute(text("""
                ALTER TABLE detection_results
                ADD COLUMN file_type VARCHAR(20) NOT NULL DEFAULT 'image'
                AFTER saved_image_path
            """))
            conn.commit()
            
            print("✓ file_type 字段添加成功")
            print("✓ 数据库迁移完成")
            
        except Exception as e:
            print(f"✗ 迁移失败: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    print("=" * 50)
    print("数据库迁移：添加视频支持")
    print("=" * 50)
    print()
    
    try:
        migrate()
    except Exception as e:
        print(f"\n错误: {e}")
        exit(1)
    
    print()
    print("=" * 50)
    print("迁移完成！现在可以存储视频检测记录了")
    print("=" * 50)
