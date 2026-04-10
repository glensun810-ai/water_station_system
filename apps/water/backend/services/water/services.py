"""
Service Extension API Routes - 服务扩展 API 路由
Phase 2: 新增服务配置和管理 API（向后兼容）

核心原则：
- 新增 API，不修改现有 API
- 独立文件，不影响 main.py 其他代码
- 仅在 main.py 增加 1 行引入 router
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
import json

# 使用相对导入从 main.py 获取依赖
try:
    from main import get_db, Product, OfficePickup
except ImportError:
    # 独立运行时的备用导入
    from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
    from sqlalchemy.orm import sessionmaker, declarative_base

    Base = declarative_base()

    class Product(Base):
        __tablename__ = "products"
        id = Column(Integer, primary_key=True)
        name = Column(String)
        service_type = Column(String(50), default="water")
        booking_required = Column(Integer, default=0)

    class OfficePickup(Base):
        __tablename__ = "office_pickup"
        id = Column(Integer, primary_key=True)
        service_type = Column(String(50), default="water")
        time_slot = Column(String(100))

    SQLALCHEMY_DATABASE_URL = "sqlite:///./waterms.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()


router = APIRouter(prefix="/api/services", tags=["service-extension"])


# ==================== Pydantic Schemas ====================


class ServiceTypeConfig(BaseModel):
    """服务类型配置"""

    value: str
    label: str
    icon: str
    color: str
    category: str
    units: List[str]
    bookingRequired: bool
    defaultUnit: str
    description: str
    config: Optional[dict] = None


class ServiceConfigResponse(BaseModel):
    """服务配置响应"""

    serviceTypes: List[ServiceTypeConfig]
    units: List[dict]


class ServiceTypeInfo(BaseModel):
    """服务类型信息"""

    type: str
    count: int
    icon: str
    color: str


class AvailabilityRequest(BaseModel):
    """可用性检查请求"""

    service_type: str
    product_id: Optional[int] = None
    time_slot: Optional[str] = None
    date: Optional[str] = None
    duration: Optional[int] = None


class AvailabilityResponse(BaseModel):
    """可用性检查响应"""

    available: bool
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    remaining_slots: Optional[int] = None
    message: str


class ServiceStatsResponse(BaseModel):
    """服务统计响应"""

    total_services: int
    by_type: List[dict]
    active_services: int


# ==================== 服务配置 API ====================

SERVICE_CONFIGS = {
    "water": {
        "value": "water",
        "label": "饮用水",
        "icon": "💧",
        "color": "blue",
        "category": "physical",
        "units": ["桶", "瓶", "件", "提"],
        "bookingRequired": False,
        "defaultUnit": "桶",
        "description": "桶装水、瓶装水等饮用水服务",
        "config": None,
    },
    "meeting_room": {
        "value": "meeting_room",
        "label": "会议室",
        "icon": "🏛️",
        "color": "purple",
        "category": "space",
        "units": ["小时", "半天", "天"],
        "bookingRequired": True,
        "defaultUnit": "小时",
        "description": "各类会议室、洽谈室预订",
        "config": {
            "timeSlots": ["09:00-12:00", "14:00-18:00", "19:00-21:00"],
            "minDuration": 1,
            "maxDuration": 8,
            "advanceDays": 7,
        },
    },
    "dining": {
        "value": "dining",
        "label": "餐厅服务",
        "icon": "🍽️",
        "color": "orange",
        "category": "service",
        "units": ["餐", "桌", "位"],
        "bookingRequired": True,
        "defaultUnit": "餐",
        "description": "VIP餐厅、商务宴请服务",
        "config": {"mealTimes": ["午餐", "晚餐"], "advanceDays": 3},
    },
    "cleaning": {
        "value": "cleaning",
        "label": "保洁服务",
        "icon": "🧹",
        "color": "green",
        "category": "service",
        "units": ["次", "小时", "天"],
        "bookingRequired": False,
        "defaultUnit": "次",
        "description": "办公室清洁、保洁服务",
        "config": None,
    },
    "tea_break": {
        "value": "tea_break",
        "label": "茶歇服务",
        "icon": "☕",
        "color": "brown",
        "category": "service",
        "units": ["份", "套", "人"],
        "bookingRequired": True,
        "defaultUnit": "份",
        "description": "会议茶歇、商务接待茶点",
        "config": {"packages": ["标准套餐", "精品套餐", "定制套餐"], "advanceDays": 2},
    },
}

UNIT_CONFIGS = [
    {"value": "桶", "label": "桶", "category": "physical"},
    {"value": "瓶", "label": "瓶", "category": "physical"},
    {"value": "件", "label": "件", "category": "physical"},
    {"value": "小时", "label": "小时", "category": "time"},
    {"value": "半天", "label": "半天", "category": "time"},
    {"value": "天", "label": "天", "category": "time"},
    {"value": "餐", "label": "餐", "category": "service"},
    {"value": "次", "label": "次", "category": "service"},
    {"value": "份", "label": "份", "category": "service"},
]


@router.get("/config", response_model=ServiceConfigResponse)
def get_service_config():
    """
    获取服务配置（类型、单位、规则等）

    返回所有支持的服务类型配置，包括：
    - 服务类型列表（icon、color、units等）
    - 单位列表（physical/time/service分类）

    向后兼容：不影响现有 API
    """
    service_types = [ServiceTypeConfig(**config) for config in SERVICE_CONFIGS.values()]

    return ServiceConfigResponse(serviceTypes=service_types, units=UNIT_CONFIGS)


@router.get("/types")
def get_service_types(db: Session = Depends(get_db)):
    """
    获取服务类型列表（从数据库）

    返回数据库中实际存在的服务类型，
    包含每种类型的数量统计

    向后兼容：不影响现有 API
    """
    # 查询产品表中的服务类型分布
    type_stats = (
        db.query(Product.service_type, func.count(Product.id).label("count"))
        .filter(Product.is_active == 1)
        .group_by(Product.service_type)
        .all()
    )

    result = []
    for stat in type_stats:
        type_name = stat.service_type or "water"
        config = SERVICE_CONFIGS.get(type_name, {"icon": "📦", "color": "gray"})

        result.append(
            {
                "type": type_name,
                "count": stat.count,
                "icon": config.get("icon", "📦"),
                "color": config.get("color", "gray"),
                "label": config.get("label", type_name),
            }
        )

    return result


@router.get("/types/{service_type}")
def get_service_type_detail(service_type: str, db: Session = Depends(get_db)):
    """
    获取特定服务类型的详细信息

    Args:
        service_type: 服务类型（water/meeting_room/dining等）

    Returns:
        服务类型配置和该类型的产品列表

    向后兼容：不影响现有 API
    """
    config = SERVICE_CONFIGS.get(service_type)

    if not config:
        raise HTTPException(status_code=404, detail=f"服务类型 '{service_type}' 不存在")

    # 查询该类型的产品
    products = (
        db.query(Product)
        .filter(Product.service_type == service_type, Product.is_active == 1)
        .all()
    )

    return {
        "config": config,
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "unit": p.unit,
                "stock": p.stock,
                "booking_required": p.booking_required,
            }
            for p in products
        ],
    }


@router.post("/check-availability", response_model=AvailabilityResponse)
def check_service_availability(
    request: AvailabilityRequest, db: Session = Depends(get_db)
):
    """
    检查服务资源可用性

    用于预约类服务（会议室、餐厅等）检查资源是否可用

    Args:
        request: 可用性检查请求

    Returns:
        可用性状态和剩余资源信息

    向后兼容：不影响现有 API
    """
    # 如果指定了产品ID，检查特定产品
    if request.product_id:
        product = db.query(Product).filter(Product.id == request.product_id).first()

        if not product:
            raise HTTPException(
                status_code=404, detail=f"产品 ID {request.product_id} 不存在"
            )

        # 检查库存/容量
        if product.service_type == "water":
            # 水服务检查库存
            available = product.stock > 0
            remaining = product.stock
            message = f"库存剩余 {remaining} {product.unit}"
        elif product.booking_required == 1:
            # 预约类服务检查已预订情况
            # 简化实现：检查是否有冲突的预订记录
            if request.time_slot and request.date:
                # 查询同时间段的其他预订
                conflicting = (
                    db.query(OfficePickup)
                    .filter(
                        OfficePickup.product_id == request.product_id,
                        OfficePickup.time_slot == request.time_slot,
                        OfficePickup.service_type == product.service_type,
                    )
                    .count()
                )

                max_capacity = product.max_capacity or 10
                available = conflicting < max_capacity
                remaining = max_capacity - conflicting
                message = f"{request.date} {request.time_slot} 可用: {remaining} 个时段"
            else:
                # 未指定时间段，返回可用状态
                available = True
                remaining = product.max_capacity or 10
                message = "请指定具体时间段"
        else:
            # 其他服务类型
            available = True
            remaining = product.stock
            message = f"资源可用"

        return AvailabilityResponse(
            available=available,
            product_id=product.id,
            product_name=product.name,
            remaining_slots=remaining,
            message=message,
        )

    # 未指定产品ID，按服务类型检查
    else:
        products = (
            db.query(Product)
            .filter(
                Product.service_type == request.service_type, Product.is_active == 1
            )
            .all()
        )

        if not products:
            raise HTTPException(
                status_code=404, detail=f"服务类型 '{request.service_type}' 无可用产品"
            )

        # 返回第一个可用产品
        available_product = products[0]

        return AvailabilityResponse(
            available=True,
            product_id=available_product.id,
            product_name=available_product.name,
            remaining_slots=available_product.stock,
            message=f"服务类型 '{request.service_type}' 有 {len(products)} 个可用产品",
        )


@router.get("/stats", response_model=ServiceStatsResponse)
def get_service_stats(db: Session = Depends(get_db)):
    """
    获取服务统计信息

    返回：
    - 总服务数量
    - 各类型服务数量
    - 活跃服务数量

    向后兼容：不影响现有 API
    """
    # 总服务数量
    total = db.query(func.count(Product.id)).filter(Product.is_active == 1).scalar()

    # 按类型统计
    by_type = (
        db.query(Product.service_type, func.count(Product.id).label("count"))
        .filter(Product.is_active == 1)
        .group_by(Product.service_type)
        .all()
    )

    type_stats = [
        {
            "type": stat.service_type or "water",
            "count": stat.count,
            "label": SERVICE_CONFIGS.get(stat.service_type or "water", {}).get(
                "label", "其他"
            ),
        }
        for stat in by_type
    ]

    # 活跃服务数量
    active = total

    return ServiceStatsResponse(
        total_services=total or 0, by_type=type_stats, active_services=active or 0
    )


@router.get("/health")
def services_health_check():
    """
    服务扩展 API 健康检查

    向后兼容：不影响现有 API
    """
    return {
        "status": "ok",
        "module": "service-extension",
        "phase": "phase-2",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "/api/services/config",
            "/api/services/types",
            "/api/services/types/{service_type}",
            "/api/services/check-availability",
            "/api/services/stats",
            "/api/services/health",
        ],
    }


# ==================== 注册路由说明 ====================
"""
在 main.py 中引入此 router（仅增加 1 行）：

from api_services import router as services_router
app.include_router(services_router)

向后兼容保证：
- 所有 API 以 /api/services/ 开头，不与现有 API 冲突
- 独立文件，不影响 main.py 其他代码
- 新增功能，不修改任何现有功能
"""
