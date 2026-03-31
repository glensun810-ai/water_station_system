#!/bin/bash
# 生产环境备份脚本
# 使用方法：./backup_production.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BACKUP_DIR="/backup/waterms"
DATE=$(date +%Y%m%d_%H%M%S)
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          生产环境备份脚本                                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查是否为生产环境
if [ -f "/etc/production_environment" ]; then
    echo -e "${YELLOW}⚠️  检测到生产环境，需要确认${NC}"
    read -p "确认要备份生产环境吗？(yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo -e "${RED}❌ 操作已取消${NC}"
        exit 1
    fi
fi

# 创建备份目录
echo "📁 创建备份目录..."
mkdir -p $BACKUP_DIR/{database,code,config,logs}

# 备份数据库
echo "💾 备份数据库..."
if [ -f "Service_WaterManage/backend/waterms.db" ]; then
    cp Service_WaterManage/backend/waterms.db $BACKUP_DIR/database/waterms_${DATE}.db
    echo -e "${GREEN}✅ 数据库备份完成${NC}"
fi

# 备份代码
echo "📦 备份代码..."
cd /Users/sgl/PycharmProjects/AIchanyejiqun
git archive --format=tar --output=$BACKUP_DIR/code/waterms_${DATE}.tar HEAD
echo -e "${GREEN}✅ 代码备份完成${NC}"

# 备份配置文件
echo "⚙️  备份配置文件..."
cp -r Service_WaterManage/backend/*.env* $BACKUP_DIR/config/ 2>/dev/null || true
cp -r .env* $BACKUP_DIR/config/ 2>/dev/null || true
echo -e "${GREEN}✅ 配置文件备份完成${NC}"

# 创建备份清单
cat > $BACKUP_DIR/backup_${DATE}.manifest << MANIFEST
备份时间：$TIMESTAMP
备份类型：完整备份
备份内容:
- 数据库：waterms_${DATE}.db
- 代码：waterms_${DATE}.tar
- 配置文件：*.env*
MANIFEST

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ 备份完成                                                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "备份位置：$BACKUP_DIR"
echo "备份清单：$BACKUP_DIR/backup_${DATE}.manifest"
echo ""

# 清理 30 天前的备份
echo "🧹 清理 30 天前的旧备份..."
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar" -mtime +30 -delete
find $BACKUP_DIR -name "*.manifest" -mtime +30 -delete
echo -e "${GREEN}✅ 清理完成${NC}"
