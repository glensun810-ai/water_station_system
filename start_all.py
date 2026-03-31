#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 产业集群空间服务管理系统 - 统一启动程序
跨平台版本（Windows/Mac/Linux），支持自动打开浏览器

用法：
    python start_all.py              # 启动并打开浏览器
    python start_all.py --no-browser # 启动但不打开浏览器
    python start_all.py stop         # 停止所有服务
"""

import os
import sys
import time
import signal
import subprocess
import socket
import webbrowser
import argparse
from pathlib import Path

# 颜色定义
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

# 配置
PROJECT_ROOT = Path(__file__).parent.resolve()
LOG_DIR = PROJECT_ROOT / "logs"
PID_DIR = PROJECT_ROOT / ".pids"

PORT_WATER = 8000
PORT_GATEWAY = 8001
PORT_FRONTEND = 8080
HOME_PAGE = f"http://localhost:{PORT_FRONTEND}/portal/index.html"

def c(text, color):
    """彩色文本"""
    return f"{color}{text}{Colors.NC}"

def print_header():
    print(c("╔════════════════════════════════════════════════════════════╗", Colors.BLUE))
    print(c("║   AI 产业集群空间服务管理系统 - 统一启动程序                ║", Colors.BLUE))
    print(c("╚════════════════════════════════════════════════════════════╝", Colors.BLUE))
    print()

def print_status(status, message):
    icons = {
        "info": c("[INFO]", Colors.BLUE),
        "success": c("[OK]", Colors.GREEN),
        "warning": c("[WARN]", Colors.YELLOW),
        "error": c("[ERROR]", Colors.RED)
    }
    print(f"{icons.get(status, '[?]')} {message}")

def check_port(port):
    """检查端口是否被占用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def kill_port(port):
    """杀死占用端口的进程"""
    try:
        if sys.platform == 'win32':
            # Windows
            result = subprocess.run(
                f"netstat -ano | findstr :{port}",
                shell=True, capture_output=True, text=True
            )
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    parts = line.split()
                    if len(parts) > 0:
                        pid = parts[-1]
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
        else:
            # Mac/Linux
            subprocess.run(f"lsof -ti:{port} | xargs kill -9", shell=True, capture_output=True)
        time.sleep(1)
    except Exception as e:
        print_status("warning", f"清理端口 {port} 失败：{e}")

def check_python():
    """检查 Python 虚拟环境"""
    # Mac/Linux
    venv_python = PROJECT_ROOT / ".venv" / "bin" / "python"
    if venv_python.exists():
        return venv_python
    # Windows
    venv_python_win = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    if venv_python_win.exists():
        return venv_python_win
    # 使用系统 Python
    print_status("warning", "虚拟环境不存在，使用系统 Python")
    return sys.executable

def start_service(name, cmd, port, log_file, pid_file, cwd=None):
    """启动服务"""
    print_status("info", f"启动 {name} (端口 {port})...")
    
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        PID_DIR.mkdir(parents=True, exist_ok=True)
        
        log_fp = open(log_file, 'w')
        cmd_str = [str(c) for c in cmd]
        
        process = subprocess.Popen(
            cmd_str,
            stdout=log_fp,
            stderr=subprocess.STDOUT,
            cwd=str(cwd) if cwd else str(PROJECT_ROOT)
        )
        
        pid_file.write_text(str(process.pid))
        time.sleep(2)
        
        if check_port(port):
            print_status("success", f"{name} 已启动 (PID: {process.pid})")
            return True
        else:
            print_status("error", f"{name} 启动失败，查看日志：{log_file}")
            return False
            
    except Exception as e:
        print_status("error", f"{name} 启动异常：{e}")
        return False

def open_browser():
    """打开浏览器访问系统首页"""
    print()
    print_status("info", f"正在打开浏览器：{HOME_PAGE}")
    
    try:
        # 使用系统默认浏览器打开
        webbrowser.open(HOME_PAGE)
        print_status("success", "浏览器已打开")
        return True
    except Exception as e:
        print_status("warning", f"无法自动打开浏览器：{e}")
        print_status("info", "请手动访问：http://localhost:8080/portal/index.html")
        return False

def show_access_info():
    """显示访问信息"""
    print()
    print(c("╔════════════════════════════════════════════════════════════╗", Colors.GREEN))
    print(c("║          ✅ 所有服务已启动成功                              ║", Colors.GREEN))
    print(c("╚════════════════════════════════════════════════════════════╝", Colors.GREEN))
    print()
    print(c("【访问地址】", Colors.BLUE))
    print(f"  🏠 统一门户首页：")
    print(f"     {HOME_PAGE}")
    print()
    print(f"  💧 水站管理：")
    print(f"     http://localhost:{PORT_FRONTEND}/Service_WaterManage/frontend/index.html")
    print()
    print(f"  🏛️ 会议室预定：")
    print(f"     http://localhost:{PORT_FRONTEND}/Service_MeetingRoom/frontend/index.html")
    print()
    print(f"  🍽️ 餐厅茶室：")
    print(f"     http://localhost:{PORT_FRONTEND}/Service_Dining/frontend/index.html")
    print()
    print(f"  🏢 办公空间：")
    print(f"     http://localhost:{PORT_FRONTEND}/Service_Office/frontend/index.html")
    print()
    print(f"  📺 前台大屏：")
    print(f"     http://localhost:{PORT_FRONTEND}/Service_Screen/frontend/index.html")
    print()
    print(c("【管理后台】", Colors.BLUE))
    print(f"  水站：http://localhost:{PORT_FRONTEND}/Service_WaterManage/frontend/admin.html")
    print(f"  会议室：http://localhost:{PORT_FRONTEND}/Service_MeetingRoom/frontend/admin.html")
    print(f"  餐厅：http://localhost:{PORT_FRONTEND}/Service_Dining/frontend/admin.html")
    print(f"  大屏：http://localhost:{PORT_FRONTEND}/Service_Screen/frontend/admin.html")
    print()
    print(c("【测试账号】", Colors.YELLOW))
    print("  用户名：admin")
    print("  密码：admin123")
    print()
    print(c("【停止服务】", Colors.YELLOW))
    print("  python start_all.py stop")
    print("  或：./stop_all.sh")
    print()

def stop_services():
    """停止所有服务"""
    print_header()
    print_status("info", "正在停止所有服务...")
    print()
    
    services = [
        ("水站服务", PORT_WATER, PID_DIR / "water.pid"),
        ("统一 API 网关", PORT_GATEWAY, PID_DIR / "gateway.pid"),
        ("前端静态文件服务器", PORT_FRONTEND, PID_DIR / "frontend.pid")
    ]
    
    for name, port, pid_file in services:
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text())
                os.kill(pid, signal.SIGTERM)
                print_status("success", f"{name} 已停止 (PID: {pid})")
            except:
                pass
            pid_file.unlink()
        
        if check_port(port):
            kill_port(port)
            print_status("success", f"{name} (端口 {port}) 已停止")
        else:
            print_status("success", f"{name} 未运行")
        print()
    
    if PID_DIR.exists():
        import shutil
        shutil.rmtree(PID_DIR)
    
    print(c("╔════════════════════════════════════════════════════════════╗", Colors.GREEN))
    print(c("║          ✅ 所有服务已停止                                  ║", Colors.GREEN))
    print(c("╚════════════════════════════════════════════════════════════╝", Colors.GREEN))
    print()
    print("【启动服务】")
    print("  python start_all.py")
    print("  或：./start_all.sh")
    print()

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='AI 产业集群空间服务管理系统 - 统一启动程序')
    parser.add_argument('--no-browser', action='store_true', help='启动但不自动打开浏览器')
    parser.add_argument('action', nargs='?', default='start', choices=['start', 'stop'], help='操作：start(启动) 或 stop(停止)')
    args = parser.parse_args()
    
    # 处理停止命令
    if args.action == 'stop':
        stop_services()
        return
    
    print_header()
    
    python = check_python()
    print_status("success", f"Python: {python}")
    
    print()
    print_status("info", "检查并清理端口...")
    for port in [PORT_WATER, PORT_GATEWAY, PORT_FRONTEND]:
        if check_port(port):
            print_status("warning", f"端口 {port} 被占用，正在清理...")
            kill_port(port)
    print_status("success", "端口清理完成")
    
    print()
    
    # 1. 水站服务
    water_cmd = [python, "main.py"]
    water_status = start_service(
        "水站服务",
        water_cmd,
        PORT_WATER,
        LOG_DIR / "waterms.log",
        PID_DIR / "water.pid",
        cwd=PROJECT_ROOT / "Service_WaterManage" / "backend"
    )
    
    # 2. 统一 API 网关
    gateway_cmd = [python, "main.py"]
    gateway_status = start_service(
        "统一 API 网关",
        gateway_cmd,
        PORT_GATEWAY,
        LOG_DIR / "gateway.log",
        PID_DIR / "gateway.pid",
        cwd=PROJECT_ROOT
    )
    
    # 3. 前端静态文件服务器
    frontend_cmd = [sys.executable, "-m", "http.server", str(PORT_FRONTEND)]
    frontend_status = start_service(
        "前端静态文件服务器",
        frontend_cmd,
        PORT_FRONTEND,
        LOG_DIR / "frontend.log",
        PID_DIR / "frontend.pid",
        cwd=PROJECT_ROOT
    )
    
    # 显示访问信息
    show_access_info()
    
    # 自动打开浏览器（除非指定了 --no-browser）
    if not args.no_browser:
        time.sleep(1)  # 等待服务完全启动
        open_browser()
    
    # 保存启动信息
    if PID_DIR.exists():
        with open(PID_DIR / "startup_info.txt", 'w', encoding='utf-8') as f:
            f.write(f"启动时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    if water_status and gateway_status and frontend_status:
        print_status("success", "所有服务启动成功！")
        sys.exit(0)
    else:
        print_status("error", "部分服务启动失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
