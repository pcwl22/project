"""
初始化检测结果存储目录
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.config import settings

def init_directories():
    """创建所需的目录结构"""
    
    directories = [
        ("基础目录", settings.output_dir),
        ("照片检测", settings.image_output_dir),
        ("视频检测", settings.video_output_dir),
        ("摄像头检测", settings.camera_output_dir),
    ]
    
    print("=" * 50)
    print("初始化检测结果存储目录")
    print("=" * 50)
    print()
    
    created_count = 0
    existing_count = 0
    
    for name, path in directories:
        if os.path.exists(path):
            print(f"✓ {name}: {path}")
            print(f"  状态: 已存在")
            existing_count += 1
        else:
            try:
                os.makedirs(path, exist_ok=True)
                print(f"✓ {name}: {path}")
                print(f"  状态: 已创建")
                created_count += 1
            except Exception as e:
                print(f"✗ {name}: {path}")
                print(f"  错误: {e}")
        print()
    
    print("=" * 50)
    print(f"总结: {created_count} 个新建, {existing_count} 个已存在")
    print("=" * 50)
    print()
    
    # 显示目录结构
    print("目录结构:")
    print(f"{settings.output_dir}/")
    print(f"├── 照片/     (图片检测结果)")
    print(f"├── 视频/     (视频检测结果)")
    print(f"└── 摄像头/   (摄像头检测结果)")
    print()
    
    return created_count + existing_count == len(directories)

if __name__ == "__main__":
    success = init_directories()
    
    if success:
        print("✓ 目录初始化完成！")
    else:
        print("✗ 部分目录创建失败")
        sys.exit(1)
    
    input("\n按 Enter 键退出...")
