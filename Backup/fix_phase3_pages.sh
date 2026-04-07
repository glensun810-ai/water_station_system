#!/bin/bash

# Phase 3 前端页面修复脚本
# 移除GlobalHeader组件依赖，简化页面结构

echo "开始修复Phase 3前端页面..."

# 需要修复的页面列表
pages=(
    "payment.html"
    "orders.html"
    "invoice-apply.html"
    "invoices.html"
)

# 备份目录
backup_dir="backups_phase3_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"

# 修复每个页面
for page in "${pages[@]}"; do
    if [ -f "$page" ]; then
        echo "处理页面: $page"
        
        # 备份原文件
        cp "$page" "$backup_dir/${page}.backup"
        
        # 移除GlobalHeader相关的行
        sed -i '' '/GlobalHeader/d' "$page"
        sed -i '' '/global-header/d' "$page"
        sed -i '' 's/components: {[^}]*},//' "$page"
        
        echo "✓ 已修复: $page"
    else
        echo "⚠ 文件不存在: $page"
    fi
done

echo ""
echo "修复完成！"
echo "备份文件位于: $backup_dir"
echo ""
echo "请刷新浏览器测试以下页面："
for page in "${pages[@]}"; do
    echo "  - http://localhost:8000/portal/$page"
done