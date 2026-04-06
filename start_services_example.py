#!/usr/bin/env python3
"""
启动器使用示例
演示如何启动和管理服务
"""

import start_services


def example_start():
    """示例：启动所有服务"""
    print("\n示例：启动所有服务")
    start_services.main()


def example_single_service():
    """示例：启动单个服务"""
    print("\n示例：启动单个服务")
    port = start_services.find_available_port(8000)
    process = start_services.start_service(
        name="水站管理",
        working_dir="Service_WaterManage/backend",
        script="main.py",
        port=port,
        log_file="logs/water_service.log",
    )
    return process


def example_check_port():
    """示例：检查端口"""
    print("\n示例：检查端口")
    for port in [8000, 8001, 8002]:
        occupied = start_services.check_port(port)
        status = "占用" if occupied else "可用"
        print(f"端口 {port}: {status}")


if __name__ == "__main__":
    # 取消注释以下示例来运行：
    # example_check_port()
    # example_single_service()
    example_start()
