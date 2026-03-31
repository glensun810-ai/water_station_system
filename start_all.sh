#!/bin/bash
# ============================================================
# AI 产业集群空间服务管理系统 - 统一启动脚本
# 功能：一键启动所有后台服务
# 用法：./start_all.sh
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python"
LOG_DIR="${PROJECT_ROOT}/logs"

# 端口配置
PORT_WATER=8000
PORT_GATEWAY=8001
PORT_FRONTEND=8080

# PID 文件
PID_DIR="${PROJECT_ROOT}/.pids"

# 日志文件
mkdir -p "${LOG_DIR}"
WATER_LOG="${LOG_DIR}/waterms.log"
GATEWAY_LOG="${LOG_DIR}/gateway.log"
FRONTEND_LOG="${LOG_DIR}/frontend.log"

# ============================================================
# 函数定义
# ============================================================

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║   AI 产业集群空间服务管理系统 - 统一启动程序                ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_status() {
    local status=$1
    local message=$2
    case $status in
        "info")    echo -e "${BLUE}[INFO]${NC} $message" ;;
        "success") echo -e "${GREEN}[OK]${NC} $message" ;;
        "warning") echo -e "${YELLOW}[WARN]${NC} $message" ;;
        "error")   echo -e "${RED}[ERROR]${NC} $message" ;;
    esac
}

check_python() {
    if [ ! -f "${VENV_PYTHON}" ]; then
        print_status "error" "虚拟环境不存在，请先创建：python3 -m venv .venv"
        exit 1
    fi
    print_status "success" "Python 虚拟环境检查通过"
}

kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        print_status "warning" "端口 $port 被占用 (PID: $pid)，正在清理..."
        kill -9 $pid 2>/dev/null || true
        sleep 1
    fi
}

cleanup_ports() {
    print_status "info" "检查并清理端口..."
    kill_port $PORT_WATER
    kill_port $PORT_GATEWAY
    kill_port $PORT_FRONTEND
    print_status "success" "端口清理完成"
}

start_water_service() {
    print_status "info" "启动水站服务 (端口 $PORT_WATER)..."
    cd "${PROJECT_ROOT}/Service_WaterManage/backend"
    nohup "${VENV_PYTHON}" main.py > "${WATER_LOG}" 2>&1 &
    echo $! > "${PID_DIR}/water.pid"
    
    sleep 2
    if lsof -i:${PORT_WATER} > /dev/null 2>&1; then
        print_status "success" "水站服务已启动 (PID: $(cat ${PID_DIR}/water.pid))"
        return 0
    else
        print_status "error" "水站服务启动失败，查看日志：${WATER_LOG}"
        tail -10 "${WATER_LOG}"
        return 1
    fi
}

start_gateway_service() {
    print_status "info" "启动统一 API 网关 (端口 $PORT_GATEWAY)..."
    cd "${PROJECT_ROOT}"
    nohup "${VENV_PYTHON}" main.py > "${GATEWAY_LOG}" 2>&1 &
    echo $! > "${PID_DIR}/gateway.pid"
    
    sleep 2
    if lsof -i:${PORT_GATEWAY} > /dev/null 2>&1; then
        print_status "success" "统一 API 网关已启动 (PID: $(cat ${PID_DIR}/gateway.pid))"
        return 0
    else
        print_status "error" "统一 API 网关启动失败，查看日志：${GATEWAY_LOG}"
        tail -10 "${GATEWAY_LOG}"
        return 1
    fi
}

start_frontend_service() {
    print_status "info" "启动前端静态文件服务器 (端口 $PORT_FRONTEND)..."
    cd "${PROJECT_ROOT}"
    nohup python3 -m http.server ${PORT_FRONTEND} > "${FRONTEND_LOG}" 2>&1 &
    echo $! > "${PID_DIR}/frontend.pid"
    
    sleep 2
    if lsof -i:${PORT_FRONTEND} > /dev/null 2>&1; then
        print_status "success" "前端静态文件服务器已启动 (PID: $(cat ${PID_DIR}/frontend.pid))"
        return 0
    else
        print_status "error" "前端静态文件服务器启动失败，查看日志：${FRONTEND_LOG}"
        tail -10 "${FRONTEND_LOG}"
        return 1
    fi
}

show_access_info() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║          ✅ 所有服务已启动成功                              ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}【访问地址】${NC}"
    echo "  🏠 统一门户首页："
    echo "     http://localhost:${PORT_FRONTEND}/portal/index.html"
    echo ""
    echo "  💧 水站管理："
    echo "     http://localhost:${PORT_FRONTEND}/Service_WaterManage/frontend/index.html"
    echo ""
    echo "  🏛️ 会议室预定："
    echo "     http://localhost:${PORT_FRONTEND}/Service_MeetingRoom/frontend/index.html"
    echo ""
    echo "  🍽️ 餐厅茶室："
    echo "     http://localhost:${PORT_FRONTEND}/Service_Dining/frontend/index.html"
    echo ""
    echo "  🏢 办公空间："
    echo "     http://localhost:${PORT_FRONTEND}/Service_Office/frontend/index.html"
    echo ""
    echo "  📺 前台大屏："
    echo "     http://localhost:${PORT_FRONTEND}/Service_Screen/frontend/index.html"
    echo ""
    echo -e "${BLUE}【管理后台】${NC}"
    echo "  水站：http://localhost:${PORT_FRONTEND}/Service_WaterManage/frontend/admin.html"
    echo "  会议室：http://localhost:${PORT_FRONTEND}/Service_MeetingRoom/frontend/admin.html"
    echo "  餐厅：http://localhost:${PORT_FRONTEND}/Service_Dining/frontend/admin.html"
    echo "  大屏：http://localhost:${PORT_FRONTEND}/Service_Screen/frontend/admin.html"
    echo ""
    echo -e "${BLUE}【测试账号】${NC}"
    echo "  用户名：admin"
    echo "  密码：admin123"
    echo ""
    echo -e "${YELLOW}【停止服务】${NC}"
    echo "  ./stop_all.sh"
    echo ""
}

save_startup_info() {
    cat > "${PID_DIR}/startup_info.txt" << INFO
启动时间：$(date '+%Y-%m-%d %H:%M:%S')
水站服务 PID: $(cat ${PID_DIR}/water.pid 2>/dev/null || echo "N/A")
网关服务 PID: $(cat ${PID_DIR}/gateway.pid 2>/dev/null || echo "N/A")
前端服务 PID: $(cat ${PID_DIR}/frontend.pid 2>/dev/null || echo "N/A")
INFO
}

# ============================================================
# 主程序
# ============================================================

main() {
    print_header
    
    # 创建 PID 目录
    mkdir -p "${PID_DIR}"
    
    # 检查 Python
    check_python
    
    # 清理端口
    cleanup_ports
    
    # 启动服务
    echo ""
    start_water_service
    WATER_STATUS=$?
    
    start_gateway_service
    GATEWAY_STATUS=$?
    
    start_frontend_service
    FRONTEND_STATUS=$?
    
    # 显示访问信息
    show_access_info
    
    # 保存启动信息
    save_startup_info
    
    # 返回状态
    if [ $WATER_STATUS -eq 0 ] && [ $GATEWAY_STATUS -eq 0 ] && [ $FRONTEND_STATUS -eq 0 ]; then
        print_status "success" "所有服务启动成功！"
        exit 0
    else
        print_status "error" "部分服务启动失败"
        exit 1
    fi
}

# 运行主程序
main "$@"
