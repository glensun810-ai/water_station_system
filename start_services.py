#!/usr/bin/env python3
"""
AI产业集群空间服务系统 - 统一启动脚本 (优化版)
功能：
1. 自动检查端口占用，自动选择可用端口
2. 启动统一后端服务（包含水站、会议室、用餐所有功能）
3. 自动打开浏览器访问Portal首页
4. 显示服务状态和访问地址

架构说明：
- 使用统一后端架构 (Service_WaterManage/backend/main.py)
- 所有前端通过StaticFiles.mount挂载到不同路径
- 单一服务提供完整功能
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


def find_available_port(start_port=8000, max_attempts=100):
    """查找可用端口"""
    for port in range(start_port, start_port + max_attempts):
        if not check_port(port):
            return port
    raise RuntimeError(
        f"无法在 {start_port}-{start_port + max_attempts} 范围内找到可用端口"
    )


def start_service(name, working_dir, script, port, log_file):
    """启动统一后端服务"""
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

        # 等待服务启动并检查健康状态
        max_wait = 15
        health_url = f"http://127.0.0.1:{port}/api/health"

        for i in range(max_wait):
            try:
                import urllib.request

                response = urllib.request.urlopen(health_url, timeout=2)
                if response.getcode() == 200:
                    print(f"✅ {name} 服务启动成功！")
                    print(f"   主页地址: http://127.0.0.1:{port}/portal/index.html")
                    print(f"   API文档: http://127.0.0.1:{port}/docs")
                    return process
            except:
                pass
            time.sleep(1)

        print(f"❌ {name} 服务启动超时（健康检查失败）")
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
    print("AI产业集群空间服务系统 - 统一启动器 v2.0")
    print("=" * 60)

    # 获取项目根目录（脚本所在目录）
    project_root = Path(__file__).parent.resolve()

    # 查找可用端口
    print("\n检查端口占用情况...")
    service_port = find_available_port(8000)
    print(f"✅ 统一服务端口: {service_port}")

    # 配置统一服务
    service_config = {
        "name": "统一服务平台",
        "working_dir": project_root / "Service_WaterManage" / "backend",
        "script": "main.py",
        "port": service_port,
        "log_file": project_root / "logs" / "unified_service.log",
        "urls": {
            "portal": f"http://127.0.0.1:{service_port}/portal/index.html",
            "water_admin": f"http://127.0.0.1:{service_port}/water-admin/index.html",
            "meeting": f"http://127.0.0.1:{service_port}/meeting-frontend/index.html",
            "admin_login": f"http://127.0.0.1:{service_port}/portal/admin/login.html",
            "api_docs": f"http://127.0.0.1:{service_port}/docs",
        },
    }

    # 检查服务目录是否存在
    if not Path(service_config["working_dir"]).exists():
        print(f"\n❌ 服务目录不存在: {service_config['working_dir']}")
        print(
            "请确保项目结构正确，或运行 'git submodule update --init' 如果使用了子模块"
        )
        sys.exit(1)

    # 启动统一服务
    process = start_service(
        service_config["name"],
        service_config["working_dir"],
        service_config["script"],
        service_config["port"],
        service_config["log_file"],
    )

    if not process:
        print("\n❌ 服务启动失败")
        sys.exit(1)

    # 显示启动结果
    print("\n" + "=" * 60)
    print("服务启动完成")
    print("=" * 60)

    print("\n✨ 服务状态：")
    status = "✅ 运行中" if process.poll() is None else "❌ 已停止"
    print(f"{status} - {service_config['name']}")

    # 打开浏览器访问Portal首页
    portal_url = service_config["urls"]["portal"]
    print(f"\n🌐 正在打开浏览器访问Portal首页...")
    webbrowser.open(portal_url)
    print(f"✅ 已打开: {portal_url}")

    # 显示快捷访问链接
    print("\n" + "=" * 60)
    print("🚀 快捷访问链接：")
    print("=" * 60)
    print(f"🏠 Portal首页: {service_config['urls']['portal']}")
    print(f"💧 水站管理: {service_config['urls']['water_admin']}")
    print(f"🏢 会议室: {service_config['urls']['meeting']}")
    print(f"🔑 管理后台: {service_config['urls']['admin_login']}")
    print(f"📚 API文档: {service_config['urls']['api_docs']}")

    print("\n" + "=" * 60)
    print("💡 提示：")
    print("- 所有服务功能都通过统一后端提供")
    print("- 日志文件: logs/unified_service.log")
    print("- 按 Ctrl+C 停止服务")
    print("=" * 60)

    # 等待用户中断
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 正在停止服务...")
        stop_service(process, service_config["name"])
        print("\n✅ 服务已安全停止")


if __name__ == "__main__":
    main()
