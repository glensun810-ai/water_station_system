#!/bin/bash

# 空间服务模块部署脚本
# 用于生产环境部署和启动

set -e

echo "========================================="
echo "空间服务预约管理系统部署脚本"
echo "========================================="
echo ""

PROJECT_ROOT="/Users/sgl/PycharmProjects/AIchanyejiqun"
DATA_DIR="$PROJECT_ROOT/data"
LOGS_DIR="$PROJECT_ROOT/logs"

echo "[Step 1] 检查项目结构..."
if [ ! -d "$PROJECT_ROOT" ]; then
    echo "❌ 项目目录不存在"
    exit 1
fi
echo "✅ 项目目录存在"

if [ ! -d "$DATA_DIR" ]; then
    mkdir -p "$DATA_DIR"
    echo "✅ 创建数据目录"
else
    echo "✅ 数据目录存在"
fi

if [ ! -d "$LOGS_DIR" ]; then
    mkdir -p "$LOGS_DIR"
    echo "✅ 创建日志目录"
else
    echo "✅ 日志目录存在"
fi

echo ""
echo "[Step 2] 检查数据库..."
DB_FILE="$DATA_DIR/space.db"
if [ ! -f "$DB_FILE" ]; then
    echo "⚠️ 空间服务数据库不存在，需要执行迁移..."
    
    if [ -f "$PROJECT_ROOT/infra/database/migrate_to_space.py" ]; then
        echo "执行数据迁移脚本..."
        cd "$PROJECT_ROOT"
        python infra/database/migrate_to_space.py
        
        if [ -f "$DB_FILE" ]; then
            echo "✅ 数据迁移成功"
        else
            echo "❌ 数据迁移失败"
            exit 1
        fi
    else
        echo "❌ 迁移脚本不存在"
        exit 1
    fi
else
    echo "✅ 数据库已存在: $DB_FILE"
fi

echo ""
echo "[Step 3] 检查依赖..."
cd "$PROJECT_ROOT"

if [ ! -d ".venv" ]; then
    echo "⚠️ Python虚拟环境不存在"
    echo "建议运行: python -m venv .venv && source .venv/bin/activate"
    echo "然后运行: pip install -r requirements.txt"
else
    echo "✅ Python虚拟环境存在"
fi

if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt 存在"
else
    echo "❌ requirements.txt 不存在"
    exit 1
fi

echo ""
echo "[Step 4] 检查API服务..."
API_FILES=(
    "apps/api/v2/space_types.py"
    "apps/api/v2/space_resources.py"
    "apps/api/v2/space_bookings.py"
    "apps/api/v2/space_approvals.py"
    "apps/api/v2/space_payments.py"
    "apps/api/v2/space_statistics.py"
)

for api_file in "${API_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$api_file" ]; then
        echo "✅ $api_file 存在"
    else
        echo "❌ $api_file 不存在"
        exit 1
    fi
done

echo ""
echo "[Step 5] 检查前端页面..."
FRONTEND_FILES=(
    "space-frontend/index.html"
    "space-frontend/booking.html"
    "space-frontend/login.html"
    "portal/admin/space/approvals.html"
)

for frontend_file in "${FRONTEND_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$frontend_file" ]; then
        echo "✅ $frontend_file 存在"
    else
        echo "❌ $frontend_file 不存在"
        exit 1
    fi
done

echo ""
echo "[Step 6] 检查配置文件..."
CONFIG_FILES=(
    "config/database.py"
    "depends/auth.py"
)

for config_file in "${CONFIG_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$config_file" ]; then
        echo "✅ $config_file 存在"
    else
        echo "❌ $config_file 不存在"
        exit 1
    fi
done

echo ""
echo "[Step 7] 创建系统健康检查脚本..."
HEALTH_CHECK_SCRIPT="$PROJECT_ROOT/scripts/health_check.sh"
cat > "$HEALTH_CHECK_SCRIPT" << 'EOF'
#!/bin/bash

echo "空间服务系统健康检查"
echo "====================="

check_api_health() {
    echo "检查API服务..."
    curl -s http://localhost:8000/api/v2/space/types | grep -q "200 OK"
    if [ $? -eq 0 ]; then
        echo "✅ API服务正常"
    else
        echo "⚠️ API服务未响应"
    fi
}

check_database_health() {
    echo "检查数据库..."
    if [ -f "data/space.db" ]; then
        echo "✅ 数据库文件存在"
        sqlite3 data/space.db "SELECT COUNT(*) FROM space_types;" > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo "✅ 数据库可访问"
        else
            echo "⚠️ 数据库访问异常"
        fi
    else
        echo "❌ 数据库文件不存在"
    fi
}

check_logs() {
    echo "检查日志..."
    if [ -d "logs" ]; then
        latest_log=$(ls -t logs/*.log 2>/dev/null | head -1)
        if [ ! -z "$latest_log" ]; then
            echo "✅ 最新日志: $latest_log"
            errors=$(grep -c "ERROR" "$latest_log" 2>/dev/null || echo "0")
            if [ "$errors" -gt "0" ]; then
                echo "⚠️ 发现 $errors 个错误日志"
            else
                echo "✅ 无错误日志"
            fi
        fi
    else
        echo "⚠️ 日志目录不存在"
    fi
}

check_api_health
check_database_health
check_logs

echo ""
echo "健康检查完成"
EOF

chmod +x "$HEALTH_CHECK_SCRIPT"
echo "✅ 健康检查脚本创建完成"

echo ""
echo "[Step 8] 数据库备份..."
BACKUP_DIR="$PROJECT_ROOT/Backup/space_service"
BACKUP_FILE="$BACKUP_DIR/space_db_backup_$(date +%Y%m%d_%H%M%S).db"

if [ -f "$DB_FILE" ]; then
    mkdir -p "$BACKUP_DIR"
    cp "$DB_FILE" "$BACKUP_FILE"
    echo "✅ 数据库已备份到: $BACKUP_FILE"
else
    echo "⚠️ 数据库不存在，跳过备份"
fi

echo ""
echo "[Step 9] 验证系统完整性..."
cd "$PROJECT_ROOT"

echo "运行验收测试..."
python tests/test_phase4_acceptance.py

echo ""
echo "========================================="
echo "部署准备工作完成"
echo "========================================="
echo ""
echo "下一步操作："
echo "1. 启动API服务: python run.py"
echo "2. 访问前端页面: http://localhost:8000/space-frontend/index.html"
echo "3. 管理后台: http://localhost:8000/portal/admin/space/approvals.html"
echo "4. 健康检查: ./scripts/health_check.sh"
echo ""
echo "部署脚本执行完成 ✅"