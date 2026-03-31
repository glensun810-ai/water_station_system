#!/bin/bash
# ============================================================
# Phase 0 验证脚本 - 准备工作验收
# ============================================================
# 用途：验证 Phase 0 的所有准备工作是否完成
# 验收标准：所有检查项必须通过
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0

check_pass() {
    echo -e "${GREEN}✅ PASS${NC} $1"
    ((PASS_COUNT++))
}

check_fail() {
    echo -e "${RED}❌ FAIL${NC} $1"
    ((FAIL_COUNT++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC} $1"
}

echo "=========================================="
echo "Phase 0 验证 - 准备工作验收"
echo "=========================================="
echo ""

# 1. 检查 Git 分支
echo "1. 检查 Git 分支..."
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" == "feature/service-extension" ]; then
    check_pass "开发分支正确：$CURRENT_BRANCH"
else
    check_fail "当前分支为 $CURRENT_BRANCH，应为 feature/service-extension"
fi
echo ""

# 2. 检查回滚脚本
echo "2. 检查回滚脚本..."
if [ -f "Service_WaterManage/scripts/rollback_phase_1.sh" ]; then
    check_pass "Phase 1 回滚脚本存在"
    if [ -x "Service_WaterManage/scripts/rollback_phase_1.sh" ]; then
        check_pass "Phase 1 回滚脚本可执行"
    else
        check_warn "Phase 1 回滚脚本缺少执行权限"
    fi
else
    check_fail "Phase 1 回滚脚本不存在"
fi

if [ -f "Service_WaterManage/scripts/rollback_phase_2.sh" ]; then
    check_pass "Phase 2 回滚脚本存在"
    if [ -x "Service_WaterManage/scripts/rollback_phase_2.sh" ]; then
        check_pass "Phase 2 回滚脚本可执行"
    else
        check_warn "Phase 2 回滚脚本缺少执行权限"
    fi
else
    check_fail "Phase 2 回滚脚本不存在"
fi
echo ""

# 3. 检查测试数据脚本
echo "3. 检查测试数据..."
if [ -f "Service_WaterManage/tests/fixtures/service_extension_test_data.sql" ]; then
    check_pass "测试数据脚本存在"
    # 检查内容完整性
    if grep -q "INSERT INTO products" "Service_WaterManage/tests/fixtures/service_extension_test_data.sql"; then
        check_pass "测试数据包含产品插入语句"
    else
        check_fail "测试数据缺少产品插入语句"
    fi
    
    if grep -q "INSERT INTO office_pickup" "Service_WaterManage/tests/fixtures/service_extension_test_data.sql"; then
        check_pass "测试数据包含服务记录插入语句"
    else
        check_fail "测试数据缺少服务记录插入语句"
    fi
else
    check_fail "测试数据脚本不存在"
fi
echo ""

# 4. 检查设计文档
echo "4. 检查设计文档..."
DOCS=(
    "Service_WaterManage/Requirements/12_通用服务管理平台扩展方案.md"
    "Service_WaterManage/Requirements/12_扩展方案执行摘要.md"
    "Service_WaterManage/Requirements/13_零风险开发实施计划.md"
    "Service_WaterManage/Requirements/13_开发计划执行摘要.md"
    "Service_WaterManage/frontend/config.js"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        check_pass "文档存在：$(basename "$doc")"
    else
        check_fail "文档缺失：$(basename "$doc")"
    fi
done
echo ""

# 5. 回滚脚本 dry-run 测试
echo "5. 回滚脚本 dry-run 测试..."
if bash Service_WaterManage/scripts/rollback_phase_1.sh --dry-run > /dev/null 2>&1; then
    check_pass "Phase 1 回滚脚本 dry-run 通过"
else
    check_fail "Phase 1 回滚脚本 dry-run 失败"
fi

if bash Service_WaterManage/scripts/rollback_phase_2.sh --dry-run > /dev/null 2>&1; then
    check_pass "Phase 2 回滚脚本 dry-run 通过"
else
    check_fail "Phase 2 回滚脚本 dry-run 失败"
fi
echo ""

# 6. 总结
echo "=========================================="
echo "Phase 0 验证结果"
echo "=========================================="
echo -e "通过：${GREEN}$PASS_COUNT${NC}"
echo -e "失败：${RED}$FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ Phase 0 验收通过！可以开始 Phase 1${NC}"
    echo ""
    echo "下一步："
    echo "  1. 执行 Phase 1 数据库扩展迁移"
    echo "  2. 运行测试数据脚本"
    echo "  3. 验证现有功能正常"
    exit 0
else
    echo -e "${RED}❌ Phase 0 验收失败！请修复上述问题${NC}"
    echo ""
    echo "需要修复的问题数：$FAIL_COUNT"
    exit 1
fi
