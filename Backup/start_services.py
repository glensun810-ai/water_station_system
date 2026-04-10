#!/usr/bin/env python3
"""
AI产业集群空间服务系统 - 简洁启动脚本
自动启动服务并在浏览器打开Portal页面
"""

import subprocess
import sys
import os
import webbrowser
import socket
import signal
import time
from pathlib import Path


class ServiceLauncher:
    """服务启动器"""

    def __init__(self):
        self.project_root = Path(__file__).parent.resolve()
        self.port = None
        self.process = None
        self.is_static_mode = False

    def find_port(self):
        """查找可用端口"""
        for port in range(8000, 8100):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                sock.close()
                return port
            sock.close()
        raise RuntimeError("无法找到可用端口")

    def start_static_service(self):
        """启动静态文件服务"""
        print("\n⚠️  数据库未配置，启动静态服务模式...")
        self.is_static_mode = True

        log_file = self.project_root / "logs" / "static_service.log"
        log_file.parent.mkdir(exist_ok=True)

        try:
            with open(log_file, "w") as f:
                self.process = subprocess.Popen(
                    [sys.executable, "-m", "http.server", str(self.port)],
                    cwd=self.project_root,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    preexec_fn=os.setsid if os.name != "nt" else None,
                )

            time.sleep(2)
            if self.process.poll() is None:
                return True
            return False
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            return False

    def start_api_service(self):
        """启动API服务"""
        print("\n启动API网关...")

        log_file = self.project_root / "logs" / "api_service.log"
        log_file.parent.mkdir(exist_ok=True)

        try:
            env = os.environ.copy()
            env["PORT"] = str(self.port)
            env["PYTHONPATH"] = str(self.project_root)

            with open(log_file, "w") as f:
                self.process = subprocess.Popen(
                    [sys.executable, "apps/main.py"],
                    cwd=self.project_root,
                    env=env,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    preexec_fn=os.setsid if os.name != "nt" else None,
                )

            # 等待启动
            print("等待服务启动...")
            for i in range(10):
                time.sleep(1)
                try:
                    import urllib.request

                    response = urllib.request.urlopen(
                        f"http://127.0.0.1:{self.port}/health", timeout=2
                    )
                    if response.getcode() == 200:
                        return True
                except:
                    if self.process.poll() is not None:
                        print(f"❌ 服务进程已退出")
                        return False

            print(f"⚠️  服务启动超时")
            return False

        except Exception as e:
            print(f"❌ 启动失败: {e}")
            return False

    def stop_service(self):
        """停止服务"""
        if self.process and self.process.poll() is None:
            try:
                if os.name != "nt":
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                else:
                    self.process.terminate()
                self.process.wait(timeout=5)
            except:
                pass
        print("✅ 服务已停止")

    def show_info(self):
        """显示服务信息"""
        print("\n" + "=" * 70)
        print("📍 服务访问地址")
        print("=" * 70)
        print(f"Portal首页:   http://127.0.0.1:{self.port}/portal/index.html")
        print(f"水站服务:     http://127.0.0.1:{self.port}/water/index.html")
        print(f"会议室服务:   http://127.0.0.1:{self.port}/meeting-frontend/index.html")
        print(f"管理后台:     http://127.0.0.1:{self.port}/portal/admin/login.html")

        if self.is_static_mode:
            print("\n⚠️  当前为静态服务模式:")
            print("   - 仅提供前端页面预览，无后端API")
            print("   - 数据提交等功能不可用")
            print("\n💡 启用完整API功能:")
            print("   1. 安装数据库: brew install postgresql")
            print("   2. 安装驱动: pip install psycopg2-binary")
            print("   3. 配置数据库: 参考 config/settings.py")
        else:
            print(f"API文档:      http://127.0.0.1:{self.port}/docs")

        print("=" * 70)

    def run(self):
        """启动服务"""
        print("=" * 70)
        print("🚀 AI产业集群空间服务系统")
        print("=" * 70)

        # 查找端口
        self.port = self.find_port()
        print(f"\n✅ 服务端口: {self.port}")

        # 检查数据库驱动
        try:
            import psycopg2

            success = self.start_api_service()
        except ImportError:
            success = self.start_static_service()

        if not success:
            print("\n❌ 启动失败，请检查日志:")
            print(f"   logs/api_service.log 或 logs/static_service.log")
            return

        # 显示信息
        self.show_info()

        # 打开浏览器
        url = f"http://127.0.0.1:{self.port}/portal/index.html"
        print(f"\n🌐 正在打开浏览器...")
        webbrowser.open(url)

        # 等待
        print("\n💡 提示:")
        print("   - 按 Ctrl+C 停止服务")
        print("   - 日志文件: logs/ 目录")

        try:
            while True:
                time.sleep(1)
                if self.process and self.process.poll() is not None:
                    print("\n⚠️  服务进程已退出")
                    break
        except KeyboardInterrupt:
            print("\n\n🛑 正在停止服务...")
            self.stop_service()


def main():
    launcher = ServiceLauncher()
    launcher.run()


if __name__ == "__main__":
    main()
