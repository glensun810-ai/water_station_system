#!/usr/bin/env python3
"""
步骤3: 安全删除main.py中的重复路由
"""

import re
from pathlib import Path


def find_function_end(lines, start_idx):
    """
    找到函数的结束位置

    策略：
    1. 找到def行的缩进级别
    2. 向下查找，直到遇到同级或更少缩进的非空行
    """
    # 跳过装饰器
    func_start = start_idx
    for i in range(start_idx, min(start_idx + 10, len(lines))):
        if lines[i].strip().startswith("def "):
            func_start = i
            break

    # 获取函数缩进级别
    func_indent = len(lines[func_start]) - len(lines[func_start].lstrip())

    # 向下查找函数结束
    end_idx = func_start
    for i in range(func_start + 1, len(lines)):
        line = lines[i]

        # 空行继续
        if not line.strip():
            end_idx = i
            continue

        current_indent = len(line) - len(line.lstrip())

        # 遇到同级或更少缩进，且是def或@装饰器，函数结束
        if current_indent <= func_indent:
            if line.strip().startswith("def ") or line.strip().startswith("@"):
                return end_idx

        end_idx = i

    return end_idx


def main():
    main_py = Path(__file__).parent / "main.py"

    with open(main_py, "r", encoding="utf-8") as f:
        lines = f.readlines()

    original_count = len(lines)

    # 需要删除的路由（按倒序排列，从后往前删除）
    routes_to_delete = [
        (r'@app\.get\("/api/user/office-pickup-summary"', "领水汇总"),
        (
            r'@app\.delete\("/api/admin/office-pickups/trash/\{pickup_id\}"',
            "回收站删除",
        ),
        (r'@app\.post\("/api/admin/office-pickups/trash/restore"', "回收站恢复"),
        (r'@app\.get\("/api/admin/office-pickups/trash"', "回收站列表"),
        (r'@app\.get\("/api/user/office-pickups"', "领水记录"),
        (r'@app\.post\("/api/admin/settlement/batch-confirm"', "批量确认结算"),
        (r'@app\.post\("/api/admin/settlement/\{pickup_id\}/reject"', "拒绝结算"),
        (r'@app\.post\("/api/admin/settlement/\{pickup_id\}/confirm"', "确认结算"),
        (r'@app\.post\("/api/admin/settlement/apply"', "申请结算"),
        (r'@app\.delete\("/api/admin/office-pickups/\{pickup_id\}"\)', "删除领水"),
        (r'@app\.put\("/api/admin/office-pickups/\{pickup_id\}"', "更新领水"),
        (r'@app\.post\("/api/user/office-pickup"', "创建领水"),
        (r'@app\.delete\("/api/admin/product-categories/\{category_id\}"', "删除分类"),
        (r'@app\.put\("/api/admin/product-categories/\{category_id\}"', "更新分类"),
        (r'@app\.post\("/api/admin/product-categories"', "创建分类"),
        (r'@app\.get\("/api/admin/product-categories"', "分类列表"),
        (r'@app\.put\("/api/products/\{product_id\}/promo-toggle"', "切换优惠"),
        (r'@app\.put\("/api/products/\{product_id\}/stock"', "更新库存"),
        (r'@app\.put\("/api/products/\{product_id\}"\)', "更新产品"),
        (r'@app\.put\("/api/products/\{product_id\}/protect"', "切换保护"),
        (r'@app\.put\("/api/products/\{product_id\}/toggle"', "切换状态"),
        (r'@app\.delete\("/api/products/\{product_id\}"\)', "删除产品"),
        (r'@app\.get\("/api/products/\{product_id\}"\)', "获取产品"),
        (r'@app\.post\("/api/products"', "创建产品"),
        (r'@app\.get\("/api/products"', "产品列表"),
        (r'@app\.get\("/api/user/offices"', "办公室列表"),
        (r'@app\.post\("/api/auth/change-password"', "修改密码"),
        (r'@app\.get\("/api/auth/me"', "当前用户"),
        (r'@app\.post\("/api/auth/login"', "登录"),
    ]

    # 找到所有路由位置（从后往前）
    deletions = []
    for pattern, desc in routes_to_delete:
        for i, line in enumerate(lines):
            if re.search(pattern, line) and line.strip().startswith("@app."):
                end = find_function_end(lines, i)
                deletions.append((i, end, desc))
                break

    # 按行号倒序排序（从后往前删除）
    deletions.sort(key=lambda x: x[0], reverse=True)

    # 执行删除
    modified_lines = lines.copy()
    total_deleted = 0

    for start, end, desc in deletions:
        # 删除函数
        deleted_count = end - start + 1
        modified_lines = modified_lines[:start] + modified_lines[end + 1 :]
        total_deleted += deleted_count
        print(f"✅ 删除: {desc} (行 {start + 1}-{end + 1}, {deleted_count}行)")

    # 写回文件
    with open(main_py, "w", encoding="utf-8") as f:
        f.writelines(modified_lines)

    new_count = len(modified_lines)

    print(f"\n✅ Phase 1 删除完成！")
    print(f"   删除了 {len(deletions)} 个重复路由")
    print(f"   共删除 {total_deleted} 行代码")
    print(f"   main.py: {original_count} 行 -> {new_count} 行")


if __name__ == "__main__":
    main()
