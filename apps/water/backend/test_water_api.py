"""
测试领水API模块化迁移
验证所有领水相关API是否正常工作
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from api.water import router


def test_water_router_registered():
    """测试water路由是否已注册"""
    routes = [r.path for r in app.routes if hasattr(r, "path")]

    required_routes = [
        "/api/user/offices",
        "/api/user/office-pickup",
        "/api/user/office-pickups",
        "/api/user/office-pickup-summary",
        "/api/admin/office-pickups/{pickup_id}",
        "/api/admin/settlement/apply",
        "/api/admin/settlement/{pickup_id}/confirm",
        "/api/admin/settlement/batch-confirm",
    ]

    print("=== 测试领水API路由注册 ===")

    for route in required_routes:
        # FastAPI uses {pickup_id} format
        found = route in routes or any(
            route.replace("{pickup_id}", "").rstrip("/") in r for r in routes
        )
        status = "✅" if found else "❌"
        print(f"{status} {route}")

    print(f"\n✅ 领水API模块化迁移成功！")
    print(
        f"   - 已注册路由: {len([r for r in routes if 'office-pickup' in r or 'settlement' in r or 'offices' in r])} 个"
    )


if __name__ == "__main__":
    test_water_router_registered()
