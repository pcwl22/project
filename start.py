#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
YOLOv8 货架检测系统 - 一键启动脚本

使用方法: python start.py
"""

import subprocess
import platform
import time
import signal
from pathlib import Path

# 项目配置
PROJECT_ROOT = Path(__file__).parent.absolute()
FRONTEND_DIR = PROJECT_ROOT / "frontend"
CONDA_ENV = "yolo"
BACKEND_PORT = 8000
FRONTEND_PORT = 5173


def start_backend():
    """启动后端服务 (端口 8000)"""
    if platform.system() == "Windows":
        cmd = f'cmd /c "conda activate {CONDA_ENV} && uvicorn backend.app.main:app --reload --port {BACKEND_PORT}"'
        return subprocess.Popen(cmd, cwd=PROJECT_ROOT, shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        cmd = f"conda activate {CONDA_ENV} && uvicorn backend.app.main:app --reload --port {BACKEND_PORT}"
        return subprocess.Popen(cmd, cwd=PROJECT_ROOT, shell=True, executable="/bin/bash")


def start_frontend():
    """启动前端服务 (端口 5173)"""
    if platform.system() == "Windows":
        return subprocess.Popen("npm run dev", cwd=FRONTEND_DIR, shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        return subprocess.Popen("npm run dev", cwd=FRONTEND_DIR, shell=True)


def cleanup(processes):
    """关闭所有服务"""
    print("\n正在关闭服务...")
    for process in processes:
        if process and process.poll() is None:
            try:
                if platform.system() == "Windows":
                    process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()


def main():
    """主函数"""
    print("正在启动服务...\n")
    
    processes = []
    
    try:
        # 启动后端
        print(f"[1/2] 启动后端服务 (端口 {BACKEND_PORT})...")
        processes.append(start_backend())
        time.sleep(2)
        
        # 启动前端
        print(f"[2/2] 启动前端服务 (端口 {FRONTEND_PORT})...")
        processes.append(start_frontend())
        time.sleep(2)
        
        # 显示访问地址
        print("\n" + "="*50)
        print("✓ 所有服务已启动!")
        print("="*50)
        print(f"\n访问地址:")
        print(f"  前端:     http://localhost:{FRONTEND_PORT}")
        print(f"  后端:     http://localhost:{BACKEND_PORT}")
        print(f"  API文档:  http://localhost:{BACKEND_PORT}/docs")
        print(f"\n按 Ctrl+C 关闭所有服务\n")
        
        # 保持运行
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        cleanup(processes)
        print("✓ 所有服务已关闭\n")


if __name__ == "__main__":
    main()

