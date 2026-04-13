"""
空间服务API路由包
"""

from .space_types import router as space_types_router
from .space_resources import router as space_resources_router
from .space_bookings import router as space_bookings_router
from .space_approvals import router as space_approvals_router
from .space_payments import router as space_payments_router
from .space_statistics import router as space_statistics_router

__all__ = [
    "space_types_router",
    "space_resources_router",
    "space_bookings_router",
    "space_approvals_router",
    "space_payments_router",
    "space_statistics_router",
]
