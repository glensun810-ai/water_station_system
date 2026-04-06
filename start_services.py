#!/usr/bin/env python3
"""
AI产业集群空间服务系统 - 统一启动脚本
功能：
1. 自动检查端口占用，自动选择可用端口
2. 启动水站、会议室、用餐三个服务
3. 自动打开浏览器访问系统首页
4. 显示服务状态和访问地址
"""

import subprocess
import time
import sys
import os
import webbrowser
from pathlib import Path
import socket
import signal


def check_port(port):
    """检查端口是否被占用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(("127.0.0.1", port))
    sock.close()
    return result == 0


def find_available_port(start_port=8000, max_attempts=100, exclude_ports=None):
    """查找可用端口"""
    if exclude_ports is None:
        exclude_ports = set()

    for port in range(start_port, start_port + max_attempts):
        if port not in exclude_ports and not check_port(port):
            return port
    raise RuntimeError(
        f"无法在 {start_port}-{start_port + max_attempts} 范围内找到可用端口"
    )


def start_service(name, working_dir, script, port, log_file):
    """启动服务"""
    print(f"\n{'=' * 60}")
    print(f"启动 {name} 服务...")
    print(f"{'=' * 60}")
    print(f"工作目录: {working_dir}")
    print(f"端口: {port}")
    print(f"日志文件: {log_file}")
    print()

    # 确保日志目录存在
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # 启动服务
    env = os.environ.copy()
    env["PORT"] = str(port)

    try:
        with open(log_file, "w") as f:
            process = subprocess.Popen(
                [sys.executable, script],
                cwd=working_dir,
                env=env,
                stdout=f,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid if os.name != "nt" else None,
            )

        # 等待服务启动
        max_wait = 10
        for i in range(max_wait):
            if check_port(port):
                print(f"✅ {name} 服务启动成功！")
                print(f"   访问地址: http://127.0.0.1:{port}")
                print(f"   API文档: http://127.0.0.1:{port}/docs")
                return process
            time.sleep(1)

        print(f"❌ {name} 服务启动超时")
        return None

    except Exception as e:
        print(f"❌ {name} 服务启动失败: {e}")
        return None


def stop_service(process, name):
    """停止服务"""
    if process:
        print(f"\n停止 {name} 服务...")
        if os.name == "nt":
            process.terminate()
        else:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        process.wait()
        print(f"✅ {name} 服务已停止")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("AI产业集群空间服务系统 - 启动器")
    print("=" * 60)

    # 获取项目根目录（脚本所在目录）
    project_root = Path(__file__).parent.resolve()

    # 查找可用端口
    print("\n检查端口占用情况...")

    # 分配端口，确保不重复
    water_port = find_available_port(8000)
    print(f"✅ 水站服务端口: {water_port}")

    meeting_port = find_available_port(8000, exclude_ports={water_port})
    print(f"✅ 会议室服务端口: {meeting_port}")

    dining_port = find_available_port(8000, exclude_ports={water_port, meeting_port})
    print(f"✅ 用餐服务端口: {dining_port}")

    # 配置服务路径
    services = [
        {
            "name": "水站管理",
            "working_dir": project_root / "Service_WaterManage" / "backend",
            "script": "main.py",
            "port": water_port,
            "log_file": project_root / "logs" / "water_service.log",
            "url": f"http://127.0.0.1:{water_port}/portal/index.html",
        },
        {
            "name": "会议室预定",
            "working_dir": project_root / "Service_MeetingRoom" / "backend",
            "script": "main.py",
            "port": meeting_port,
            "log_file": project_root / "logs" / "meeting_service.log",
            "url": f"http://127.0.0.1:{water_port}/meeting-frontend/index.html",
        },
        {
            "name": "用餐服务",
            "working_dir": project_root / "Service_Dining" / "backend",
            "script": "main.py",
            "port": dining_port,
            "log_file": project_root / "logs" / "dining_service.log",
            "url": f"http://127.0.0.1:{dining_port}",
        },
    ]

    # 启动所有服务
    processes = []
    primary_url = None

    for service in services:
        if not Path(service["working_dir"]).exists():
            print(f"\n⚠️ {service['name']} 服务目录不存在，跳过")
            continue

        process = start_service(
            service["name"],
            service["working_dir"],
            service["script"],
            service["port"],
            service["log_file"],
        )

        if process:
            processes.append((process, service))
            if not primary_url:
                primary_url = service["url"]

    # 显示启动结果
    print("\n" + "=" * 60)
    print("服务启动完成")
    print("=" * 60)

    if processes:
        print("\n服务状态：")
        for process, service in processes:
            status = "✅ 运行中" if process.poll() is None else "❌ 已停止"
            print(f"{status} - {service['name']}: {service['url']}")

        # 打开浏览器
        if primary_url:
            print("\n正在打开浏览器...")
            webbrowser.open(primary_url)
            print(f"✅ 已打开: {primary_url}")

        # 显示快捷访问链接
        print("\n" + "=" * 60)
        print("快捷访问链接：")
        print("=" * 60)
        print(f"🏠 首页: {services[0]['url']}")
        print(f"💧 水站管理: http://127.0.0.1:{water_port}/water-admin/index.html")
        print(f"🏢 会议室: http://127.0.0.1:{water_port}/meeting-frontend/index.html")
        print(f"🍽️ 用餐管理: http://127.0.0.1:{water_port}/portal/admin/dining.html")
        print(f"📊 API文档: http://127.0.0.1:{water_port}/docs")

        print("\n" + "=" * 60)
        print("按 Ctrl+C 停止所有服务")
        print("=" * 60)

        # 等待用户中断
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n正在停止所有服务...")
            for process, service in reversed(processes):
                stop_service(process, service["name"])

            print("\n✅ 所有服务已停止")
    else:
        print("\n❌ 没有服务成功启动")
        sys.exit(1)


if __name__ == "__main__":
    main()
