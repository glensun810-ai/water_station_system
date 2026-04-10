#!/bin/bash
# AI产业集群空间服务系统 - 数据库统一执行脚本

set -e  # 遇到错误立即退出

echo "🚀 Starting Database Unification Process (Phase 2)"

# 检查必要工具
echo "🔍 Checking required tools..."
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed"; exit 1; }
command -v psql >/dev/null 2>&1 || { echo "⚠️  PostgreSQL client (psql) not found, will skip database initialization"; }

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 创建必要的目录
mkdir -p docs

echo "🔐 Creating database backups..."
python3 infra/database/migration-manager.py

echo "🔧 Updating application configurations..."
python3 infra/database/update-config.py

echo "📊 Running data migration..."
cd infra/database
python3 migration-manager.py
cd ../..

echo "✅ Database unification completed successfully!"

echo ""
echo "📋 Next steps:"
echo "1. Start PostgreSQL server if not running"
echo "2. Verify the migrated data in PostgreSQL"
echo "3. Update application environment variables"
echo "4. Test the application with new database"

echo ""
echo "📁 Generated files:"
echo "- docs/数据库迁移报告.md"
echo "- infra/database/water_migration.log"  
echo "- infra/database/meeting_migration.log"
echo "- Updated configuration files in apps/*/backend/"

echo ""
echo "🎉 Phase 2: Database Unification - COMPLETED!"