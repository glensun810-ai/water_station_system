#!/usr/bin/env python3
"""
Phase 1.3-1.4: 注释main.py中所有剩余的重复路由
"""

from pathlib import Path
import re


def find_function_end(lines, start_idx):
    """找到函数的结束位置"""
    # 找到def行的缩进级别
    def_indent = None
    for i in range(start_idx, len(lines)):
        if lines[i].strip().startswith("def "):
            def_indent = len(lines[i]) - len(lines[i].lstrip())
            break

    if def_indent is None:
        return start_idx + 10  # 默认10行

    # 向下查找，直到遇到同级或更少缩进的非空行
    end_idx = start_idx
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        if line.strip() == "":
            end_idx = i
            continue

        current_indent = len(line) - len(line.lstrip())
        if current_indent <= def_indent:
            # 遇到同级或更少缩进，函数结束
            return end_idx

        end_idx = i

    return end_idx


def comment_out_function(lines, start_idx, end_idx):
    """用三引号注释掉函数"""
    result = ["    # ===== DUPLICATE ROUTE - 已移至模块化文件 ====="]
    result.append('    """')
    for i in range(start_idx, end_idx + 1):
        result.append("    " + lines[i])
    result.append('    """')
    result.append("")
    return result


def main():
    main_py = Path(__file__).parent / "main.py"

    with open(main_py, "r", encoding="utf-8") as f:
        lines = f.readlines()

    original_count = len(lines)

    # 定义要注释的路由（按出现顺序）
    routes_to_comment = [
        # 产品API (约1434-1700行)
        '@app.get("/api/products"',
        '@app.post("/api/products"',
        '@app.get("/api/products/{product_id}"',
        '@app.delete("/api/products/{product_id}"',
        '@app.put("/api/products/{product_id}/toggle"',
        '@app.put("/api/products/{product_id}/protect"',
        '@app.put("/api/products/{product_id}"',  # update_product
        '@app.put("/api/products/{product_id}/stock"',
        '@app.put("/api/products/{product_id}/promo-toggle"',
        # 分类API (约1722-1770行)
        '@app.get("/api/admin/product-categories"',
        '@app.post("/api/admin/product-categories"',
        '@app.put("/api/admin/product-categories/{category_id}"',
        '@app.delete("/api/admin/product-categories/{category_id}"',
        # 领水API (约2384-3430行)
        '@app.post("/api/user/office-pickup"',
        '@app.put("/api/admin/office-pickups/{pickup_id}"',
        '@app.delete("/api/admin/office-pickups/{pickup_id}"',
        '@app.post("/api/admin/settlement/apply"',
        '@app.post("/api/admin/settlement/{pickup_id}/confirm"',
        '@app.post("/api/admin/settlement/{pickup_id}/reject"',
        '@app.post("/api/admin/settlement/batch-confirm"',
        '@app.get("/api/user/office-pickups"',
        '@app.get("/api/admin/office-pickups/trash"',
        '@app.post("/api/admin/office-pickups/trash/restore"',
        '@app.delete("/api/admin/office-pickups/trash/{pickup_id}"',
        # 领水汇总 (约4431-4478行)
        '@app.get("/api/user/office-pickup-summary"',
    ]

    # 查找每个路由的位置
    routes_found = []
    for pattern in routes_to_comment:
        for i, line in enumerate(lines):
            if pattern in line and "@app." in line:
                # 确保不是在注释中
                if not line.strip().startswith("#"):
                    routes_found.append((i, pattern))
                    break

    # 从后往前处理（避免索引变化）
    routes_found.sort(key=lambda x: x[0], reverse=True)

    modified_lines = lines.copy()
    count = 0

    for start_idx, pattern in routes_found:
        # 找到函数结束
        end_idx = find_function_end(modified_lines, start_idx)

        # 注释掉
        commented = comment_out_function(modified_lines, start_idx, end_idx)

        # 替换
        modified_lines = (
            modified_lines[:start_idx] + commented + modified_lines[end_idx + 1 :]
        )

        print(f"✅ 注释: {pattern} (行 {start_idx + 1}-{end_idx + 1})")
        count += 1

    # 写回文件
    with open(main_py, "w", encoding="utf-8") as f:
        f.writelines(modified_lines)

    new_count = len(modified_lines)

    print(f"\n✅ Phase 1.3-1.4 完成！")
    print(f"   共注释 {count} 个重复路由")
    print(
        f"   main.py: {original_count} 行 -> {new_count} 行 (减少 {original_count - new_count} 行)"
    )


if __name__ == "__main__":
    main()
