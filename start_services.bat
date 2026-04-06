@echo off
chcp 65001 >nul
title AI产业集群空间服务系统 - 启动器

echo ============================================================
echo AI产业集群空间服务系统 - 启动器
echo ============================================================
echo.

cd /d "%~dp0"

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

:: 运行启动脚本
echo 正在启动服务...
python start_services.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ 服务启动失败
    pause
    exit /b 1
)

pause