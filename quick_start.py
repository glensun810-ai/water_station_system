#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动脚本 - 仅启动核心服务
一键启动水站用户端和管理后台

用法：
    python quick_start.py          # 启动并打开浏览器
    python quick_start.py --admin  # 直接打开管理后台
    python quick_start.py stop     # 停止服务
"""

import os
import sys
import time
import signal
import subprocess
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
LOG_DIR = PROJECT_ROOT / "logs"
PID_DIR = PROJECT_ROOT / ".pids"

PORT_BACKEND = 8000
PORT_FRONTEND = 8080


def print_header():
    print("\n" + "=" * 60)
    print("   🚀 AI产业集群空间服务管理平台 - 快速启动")
    print("=" * 60 + "\n")


def check_port(port):
    """检查端口是否被占用"""
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(("127.0.0.1", port))
    sock.close()
    return result == 0


def kill_port(port):
    """杀死占用端口的进程"""
    try:
        if sys.platform == "win32":
            subprocess.run(
                f"netstat -ano | findstr :{port} | findstr LISTENING",
                shell=True,
                capture_output=True,
            )
        else:
            subprocess.run(
                f"lsof -ti:{port} | xargs kill -9", shell=True, capture_output=True
            )
        time.sleep(1)
    except:
        pass


def start_backend():
    """启动后端服务"""
    print("[1/2] 启动后端服务...")

    # 清理端口
    if check_port(PORT_BACKEND):
        print(f"  ⚠️  端口 {PORT_BACKEND} 被占用，正在清理...")
        kill_port(PORT_BACKEND)

    # 启动服务
    venv_python = PROJECT_ROOT / ".venv" / "bin" / "python"
    if not venv_python.exists():
        venv_python = Path(sys.executable)

    backend_dir = PROJECT_ROOT / "Service_WaterManage" / "backend"
    log_file = LOG_DIR / "backend.log"

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    PID_DIR.mkdir(parents=True, exist_ok=True)

    log_fp = open(log_file, "w")
    process = subprocess.Popen(
        [str(venv_python), "main.py"],
        stdout=log_fp,
        stderr=subprocess.STDOUT,
        cwd=str(backend_dir),
    )

    PID_DIR.joinpath("backend.pid").write_text(str(process.pid))
    time.sleep(2)

    if check_port(PORT_BACKEND):
        print(f"  ✅ 后端服务已启动 (PID: {process.pid}, 端口: {PORT_BACKEND})")
        return True
    else:
        print(f"  ❌ 后端服务启动失败，查看日志: {log_file}")
        return False


def start_frontend():
    """启动前端静态文件服务器"""
    print("[2/2] 启动前端服务器...")

    # 清理端口
    if check_port(PORT_FRONTEND):
        print(f"  ⚠️  端口 {PORT_FRONTEND} 被占用，正在清理...")
        kill_port(PORT_FRONTEND)

    log_file = LOG_DIR / "frontend.log"
    log_fp = open(log_file, "w")
    process = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT_FRONTEND)],
        stdout=log_fp,
        stderr=subprocess.STDOUT,
        cwd=str(PROJECT_ROOT),
    )

    PID_DIR.joinpath("frontend.pid").write_text(str(process.pid))
    time.sleep(1)

    if check_port(PORT_FRONTEND):
        print(f"  ✅ 前端服务器已启动 (PID: {process.pid}, 端口: {PORT_FRONTEND})")
        return True
    else:
        print(f"  ❌ 前端服务器启动失败")
        return False


def open_browser(mode="user"):
    """打开浏览器"""
    if mode == "admin":
        # 直接打开管理后台
        url = (
            f"http://localhost:{PORT_FRONTEND}/Service_WaterManage/frontend/admin.html"
        )
        print(f"\n  🖥️  正在打开管理后台: {url}")
    else:
        # 打开用户端（门户首页）
        url = f"http://localhost:{PORT_FRONTEND}/portal/index.html"
        print(f"\n  🌐 正在打开用户端: {url}")

    try:
        webbrowser.open(url)
        print("  ✅ 浏览器已打开")
    except Exception as e:
        print(f"  ⚠️  无法自动打开浏览器: {e}")
        print(f"  请手动访问: {url}")


def show_info():
    """显示访问信息"""
    print("\n" + "=" * 60)
    print("   ✅ 服务启动成功！")
    print("=" * 60 + "\n")
    print("【访问地址】")
    print(f"  🏠 门户首页: http://localhost:{PORT_FRONTEND}/portal/index.html")
    print(
        f"  💧 水站用户端: http://localhost:{PORT_FRONTEND}/Service_WaterManage/frontend/index.html"
    )
    print(
        f"  🏛️ 会议室预定: http://localhost:{PORT_FRONTEND}/Service_MeetingRoom/frontend/index.html"
    )
    print(
        f"  🍽️ VIP餐厅: http://localhost:{PORT_FRONTEND}/Service_Dining/frontend/index.html"
    )
    print()
    print("【管理后台】")
    print(
        f"  💧 水站管理: http://localhost:{PORT_FRONTEND}/Service_WaterManage/frontend/admin.html"
    )
    print(
        f"  🏛️ 会议室管理: http://localhost:{PORT_FRONTEND}/Service_MeetingRoom/frontend/admin.html"
    )
    print(
        f"  🍽️ 餐厅管理: http://localhost:{PORT_FRONTEND}/Service_Dining/frontend/admin.html"
    )
    print()
    print("【API端点】")
    print(f"  🔗 http://localhost:{PORT_BACKEND}/api")
    print()
    print("【停止服务】")
    print("  python quick_start.py stop")
    print()


def stop_services():
    """停止所有服务"""
    print("\n正在停止服务...")

    # 停止后端
    if PID_DIR.joinpath("backend.pid").exists():
        try:
            pid = int(PID_DIR.joinpath("backend.pid").read_text())
            os.kill(pid, signal.SIGTERM)
            print(f"  ✅ 后端服务已停止 (PID: {pid})")
        except:
            pass

    if check_port(PORT_BACKEND):
        kill_port(PORT_BACKEND)
        print(f"  ✅ 后端端口 {PORT_BACKEND} 已清理")

    # 停止前端
    if PID_DIR.joinpath("frontend.pid").exists():
        try:
            pid = int(PID_DIR.joinpath("frontend.pid").read_text())
            os.kill(pid, signal.SIGTERM)
            print(f"  ✅ 前端服务器已停止 (PID: {pid})")
        except:
            pass

    if check_port(PORT_FRONTEND):
        kill_port(PORT_FRONTEND)
        print(f"  ✅ 前端端口 {PORT_FRONTEND} 已清理")

    # 清理PID目录
    if PID_DIR.exists():
        import shutil

        shutil.rmtree(PID_DIR)

    print("\n✅ 所有服务已停止\n")


def main():
    # 解析参数
    args = sys.argv[1:]
    mode = "user"

    if "stop" in args:
        stop_services()
        return

    if "--admin" in args:
        mode = "admin"

    print_header()

    # 启动服务
    backend_ok = start_backend()
    frontend_ok = start_frontend()

    # 显示信息
    show_info()

    # 打开浏览器
    if backend_ok and frontend_ok:
        time.sleep(1)
        open_browser(mode)
        print("\n🎉 启动完成！按 Ctrl+C 不会停止服务")
        print("   要停止服务请运行: python quick_start.py stop\n")
    else:
        print("\n⚠️  部分服务启动失败，请检查日志\n")


if __name__ == "__main__":
    main()
