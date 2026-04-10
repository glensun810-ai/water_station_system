#!/bin/bash
# ============================================================
# AI 产业集群空间服务管理系统 - 统一停止脚本
# 功能：一键停止所有后台服务
# 用法：./stop_all.sh
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 端口配置
PORT_WATER=8000
PORT_GATEWAY=8001
PORT_FRONTEND=8080

# PID 目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="${PROJECT_ROOT}/.pids"

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║   AI 产业集群空间服务管理系统 - 统一停止程序                ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

stop_by_pid() {
    local name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}[STOP]${NC} 停止 $name (PID: $pid)..."
            kill $pid 2>/dev/null || true
            sleep 1
            echo -e "${GREEN}[OK]${NC} $name 已停止"
        else
            echo -e "${YELLOW}[WARN]${NC} $name 未运行 (PID: $pid)"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}[WARN]${NC} $name PID 文件不存在"
    fi
}

stop_by_port() {
    local name=$1
    local port=$2
    
    local pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}[STOP]${NC} 停止 $name (端口 $port, PID: $pid)..."
        kill -9 $pid 2>/dev/null || true
        sleep 1
        echo -e "${GREEN}[OK]${NC} $name 已停止"
    else
        echo -e "${GREEN}[OK]${NC} $name 未运行"
    fi
}

main() {
    print_header
    
    echo ""
    echo "【停止服务】"
    
    # 通过 PID 停止
    stop_by_pid "水站服务" "${PID_DIR}/water.pid"
    stop_by_pid "统一 API 网关" "${PID_DIR}/gateway.pid"
    stop_by_pid "前端静态文件服务器" "${PID_DIR}/frontend.pid"
    
    # 通过端口清理（确保完全停止）
    echo ""
    stop_by_port "水站服务" $PORT_WATER
    stop_by_port "统一 API 网关" $PORT_GATEWAY
    stop_by_port "前端静态文件服务器" $PORT_FRONTEND
    
    # 清理 PID 文件
    rm -rf "${PID_DIR}"
    
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║          ✅ 所有服务已停止                                  ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "【启动服务】"
    echo "  ./start_all.sh"
    echo ""
}

main "$@"
