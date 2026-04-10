#!/usr/bin/env python3
"""
AI产业集群空间服务系统 - 新架构统一启动程序

基于新架构设计，简化启动流程：
- 单端口统一API服务（8008）
- 统一Portal入口
- 自动打开浏览器

用法：
    python run.py              # 启动并打开浏览器
    python run.py --no-browser # 启动但不打开浏览器
    python run.py --port 9000  # 使用指定端口
    python run.py stop         # 停止服务
    python run.py status       # 查看服务状态
"""

import subprocess
import sys
import os
import webbrowser
import socket
import signal
import time
import argparse
from pathlib import Path


class UnifiedLauncher:
    """新架构统一启动器"""

    def __init__(self):
        self.project_root = Path(__file__).parent.resolve()
        self.log_dir = self.project_root / "logs"
        self.pid_dir = self.project_root / ".pids"
        self.default_port = 8008
        self.port = self.default_port
        self.process = None
        self.pid_file = self.pid_dir / "api_service.pid"
        self.log_file = self.log_dir / "api_service.log"

        # 确保目录存在
        self.log_dir.mkdir(exist_ok=True)
        self.pid_dir.mkdir(exist_ok=True)

    def print_banner(self):
        """打印启动横幅"""
        print("\n" + "=" * 70)
        print("  🏢 AI产业集群空间服务系统 - 新架构统一启动程序")
        print("=" * 70)
        print("\n  架构特点:")
        print("    ✓ 统一API网关 - 单端口访问")
        print("    ✓ 统一数据库 - 数据一致性保证")
        print("    ✓ 统一前端入口 - Portal集成")
        print("    ✓ 模块化服务 - 水站/会议室/系统管理")
        print("\n  服务端口: {}".format(self.port))
        print("  访问地址: http://127.0.0.1:{}/portal/index.html".format(self.port))
        print("\n" + "=" * 70 + "\n")

    def check_port_available(self, port):
        """检查端口是否可用"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        return result != 0  # 如果连接失败，端口可用

    def find_available_port(self):
        """查找可用端口"""
        for port in range(self.default_port, 9000):
            if self.check_port_available(port):
                return port
        raise RuntimeError("无法找到可用端口（8008-9000范围内）")

    def stop_existing_service(self):
        """停止已存在的服务"""
        if self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text().strip())
                os.kill(pid, signal.SIGTERM)
                time.sleep(2)
                print("  ✓ 已停止旧服务进程 (PID: {})".format(pid))
            except ProcessLookupError:
                print("  ⚠ 旧服务进程已不存在")
            except Exception as e:
                print("  ⚠ 停止旧服务失败: {}".format(str(e)))

        # 检查端口是否被占用
        if not self.check_port_available(self.port):
            print("  ⚠ 端口 {} 已被占用，尝试停止...".format(self.port))
            try:
                if sys.platform == "darwin":  # macOS
                    subprocess.run(
                        "lsof -ti:{} | xargs kill -9".format(self.port),
                        shell=True,
                        capture_output=True,
                    )
                elif sys.platform == "win32":
                    subprocess.run(
                        "netstat -ano | findstr :{} | findstr LISTENING".format(
                            self.port
                        ),
                        shell=True,
                        capture_output=True,
                    )
                time.sleep(2)
                print("  ✓ 已清理端口 {}".format(self.port))
            except Exception as e:
                print("  ✗ 清理端口失败: {}".format(str(e)))

    def start_api_service(self):
        """启动API服务"""
        print("\n  [启动API服务]")

        # 检查端口可用性
        if not self.check_port_available(self.port):
            print("  ✗ 端口 {} 已被占用".format(self.port))
            new_port = self.find_available_port()
            print("  → 使用备用端口: {}".format(new_port))
            self.port = new_port

        # 启动命令
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "apps.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(self.port),
        ]

        print("  启动命令: {}".format(" ".join(cmd)))

        # 启动进程
        try:
            with open(self.log_file, "w") as log_f:
                self.process = subprocess.Popen(
                    cmd, cwd=self.project_root, stdout=log_f, stderr=subprocess.STDOUT
                )

            # 记录PID
            self.pid_file.write_text(str(self.process.pid))

            print("  ✓ API服务已启动 (PID: {})".format(self.process.pid))
            print("  → 日志文件: {}".format(self.log_file))

            # 等待服务就绪
            self.wait_for_service_ready()

            return True

        except Exception as e:
            print("  ✗ 启动失败: {}".format(str(e)))
            return False

    def wait_for_service_ready(self, max_wait=10):
        """等待服务就绪"""
        print("  → 等待服务就绪...")

        for i in range(max_wait):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                if sock.connect_ex(("127.0.0.1", self.port)) == 0:
                    sock.close()
                    print("  ✓ 服务已就绪 (耗时 {} 秒)".format(i + 1))
                    return True
                sock.close()
            except Exception:
                pass

            time.sleep(1)

        print("  ⚠ 服务启动超时，请检查日志")
        return False

    def open_browser(self):
        """打开浏览器"""
        url = "http://127.0.0.1:{}/portal/index.html".format(self.port)

        print("\n  [打开浏览器]")
        print("  → 访问地址: {}".format(url))

        try:
            webbrowser.open(url)
            print("  ✓ 浏览器已打开")
        except Exception as e:
            print("  ⚠ 无法自动打开浏览器: {}".format(str(e)))
            print("  → 请手动访问: {}".format(url))

    def stop_service(self):
        """停止服务"""
        print("\n  [停止服务]")

        if self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text().strip())
                os.kill(pid, signal.SIGTERM)
                time.sleep(2)

                # 检查进程是否已停止
                try:
                    os.kill(pid, 0)  # 检查进程是否存在
                    print("  ⚠ 进程仍在运行，强制终止...")
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

                self.pid_file.unlink(missing_ok=True)
                print("  ✓ 服务已停止 (PID: {})".format(pid))

            except ProcessLookupError:
                print("  ⚠ 服务进程已不存在")
                self.pid_file.unlink(missing_ok=True)
            except Exception as e:
                print("  ✗ 停止失败: {}".format(str(e)))
        else:
            print("  ⚠ 未找到PID文件，服务可能未运行")

        # 清理端口
        if not self.check_port_available(self.port):
            try:
                if sys.platform == "darwin":
                    subprocess.run(
                        "lsof -ti:{} | xargs kill -9".format(self.port),
                        shell=True,
                        capture_output=True,
                    )
                print("  ✓ 端口 {} 已清理".format(self.port))
            except Exception:
                pass

    def show_status(self):
        """显示服务状态"""
        print("\n  [服务状态]")

        if self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text().strip())
                os.kill(pid, 0)  # 检查进程是否存在
                print("  ✓ 服务运行中 (PID: {})".format(pid))

                # 检查健康状态
                import requests

                try:
                    response = requests.get(
                        "http://127.0.0.1:{}/health".format(self.port), timeout=2
                    )
                    if response.status_code == 200:
                        health = response.json()
                        print(
                            "  ✓ 健康状态: {}".format(health.get("status", "unknown"))
                        )
                        print("  → 版本: {}".format(health.get("version", "unknown")))
                except Exception:
                    print("  ⚠ 健康检查失败")

            except ProcessLookupError:
                print("  ✗ 服务进程已停止")
            except Exception as e:
                print("  ⚠ 检查失败: {}".format(str(e)))
        else:
            print("  ✗ 服务未运行")

        print("\n  [数据统计]")

        # 检查数据库
        import sqlite3

        db_path = self.project_root / "data" / "app.db"

        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()

                tables = {
                    "products": "产品",
                    "users": "用户",
                    "office": "办公室",
                    "meeting_rooms": "会议室",
                }

                for table, name in tables.items():
                    cursor.execute("SELECT COUNT(*) FROM {}".format(table))
                    count = cursor.fetchone()[0]
                    print("  → {}: {} 条".format(name, count))

                conn.close()

            except Exception as e:
                print("  ⚠ 数据库查询失败: {}".format(str(e)))
        else:
            print("  ⚠ 数据库文件不存在")

    def run(self, open_browser=True):
        """运行启动流程"""
        self.print_banner()

        # 停止旧服务
        self.stop_existing_service()

        # 启动新服务
        if not self.start_api_service():
            print("\n  ✗ 启动失败，请检查日志文件")
            return False

        # 打开浏览器
        if open_browser:
            self.open_browser()

        # 显示使用说明
        self.show_usage()

        return True

    def show_usage(self):
        """显示使用说明"""
        print("\n" + "=" * 70)
        print("  📌 使用说明")
        print("=" * 70)
        print("\n  服务地址:")
        print(
            "    - Portal首页:  http://127.0.0.1:{}/portal/index.html".format(self.port)
        )
        print("    - API文档:     http://127.0.0.1:{}/docs".format(self.port))
        print("    - 健康检查:    http://127.0.0.1:{}/health".format(self.port))

        print("\n  管理功能:")
        print(
            "    - 水站管理:    http://127.0.0.1:{}/portal/admin/water/dashboard.html".format(
                self.port
            )
        )
        print(
            "    - 会议室管理:  http://127.0.0.1:{}/portal/admin/meeting/rooms.html".format(
                self.port
            )
        )
        print(
            "    - 用户管理:    http://127.0.0.1:{}/portal/admin/users.html".format(
                self.port
            )
        )

        print("\n  登录信息:")
        print("    - 用户名: admin")
        print("    - 密码:   123456")
        print("    - 角色:   超级管理员")

        print("\n  常用命令:")
        print("    python run.py              # 启动服务")
        print("    python run.py stop         # 停止服务")
        print("    python run.py status       # 查看状态")
        print("    python run.py --no-browser # 不打开浏览器")

        print("\n" + "=" * 70)
        print("  🎉 服务启动成功！按 Ctrl+C 可停止服务")
        print("=" * 70 + "\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AI产业集群空间服务系统启动程序")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    parser.add_argument(
        "--port", type=int, default=8008, help="指定API服务端口（默认8008）"
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["stop", "status"],
        help="执行命令：stop（停止）或 status（查看状态）",
    )

    args = parser.parse_args()

    launcher = UnifiedLauncher()
    launcher.port = args.port

    try:
        if args.command == "stop":
            launcher.stop_service()
        elif args.command == "status":
            launcher.show_status()
        else:
            success = launcher.run(open_browser=not args.no_browser)

            if success:
                # 保持运行，等待Ctrl+C
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n\n  ⚠ 收到停止信号...")
                    launcher.stop_service()
                    print("  ✓ 服务已停止\n")

    except Exception as e:
        print("\n  ✗ 执行失败: {}".format(str(e)))
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
