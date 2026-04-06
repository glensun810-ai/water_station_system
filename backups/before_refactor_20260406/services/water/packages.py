"""
Package Management API Routes - 套餐管理 API 路由
Phase 3: 套餐组合销售功能

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

try:
    from main import get_db
    from models_unified import Package, PackageItem, PackageOrder
except ImportError:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, declarative_base
    from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey

    Base = declarative_base()

    class Package(Base):
        __tablename__ = "packages"
        id = Column(Integer, primary_key=True, index=True)
        name = Column(String(200), nullable=False)
        description = Column(Text)
        original_price = Column(Float, nullable=False)
        package_price = Column(Float, nullable=False)
        discount_rate = Column(Float, default=100)
        service_types = Column(Text)
        valid_days = Column(Integer, default=30)
        max_usage = Column(Integer, default=0)
        status = Column(String(20), default="active")
        sort_order = Column(Integer, default=0)
        created_at = Column(DateTime, default=datetime.now)
        updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    class PackageItem(Base):
        __tablename__ = "package_items"
        id = Column(Integer, primary_key=True, index=True)
        package_id = Column(Integer, ForeignKey("packages.id"), nullable=False)
        service_type = Column(String(50), nullable=False)
        product_id = Column(Integer)
        product_name = Column(String(200))
        quantity = Column(Float, nullable=False, default=1)
        unit = Column(String(50))
        unit_price = Column(Float)
        subtotal = Column(Float)
        note = Column(Text)
        created_at = Column(DateTime, default=datetime.now)

    class PackageOrder(Base):
        __tablename__ = "package_orders"
        id = Column(Integer, primary_key=True, index=True)
        package_id = Column(Integer, ForeignKey("packages.id"), nullable=False)
        package_name = Column(String(200))
        office_id = Column(Integer, nullable=False)
        office_name = Column(String(200))
        order_user_id = Column(Integer)
        order_user_name = Column(String(200))
        original_price = Column(Float)
        package_price = Column(Float)
        saved_amount = Column(Float)
        status = Column(String(20), default="pending")
        used_count = Column(Integer, default=0)
        total_count = Column(Integer, default=1)
        valid_from = Column(String)
        valid_until = Column(String)
        note = Column(Text)
        created_at = Column(DateTime, default=datetime.now)
        updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

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


router = APIRouter(prefix="/api/packages", tags=["package-management"])


class PackageItemCreate(BaseModel):
    service_type: str
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    quantity: float = 1
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    subtotal: Optional[float] = None
    note: Optional[str] = None


class PackageItemResponse(BaseModel):
    id: int
    package_id: int
    service_type: str
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    quantity: float
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    subtotal: Optional[float] = None
    note: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PackageCreate(BaseModel):
    name: str
    description: Optional[str] = None
    original_price: float
    package_price: float
    discount_rate: Optional[float] = 100
    service_types: Optional[str] = None
    valid_days: Optional[int] = 30
    max_usage: Optional[int] = 0
    status: Optional[str] = "active"
    sort_order: Optional[int] = 0
    items: Optional[List[PackageItemCreate]] = None


class PackageUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    original_price: Optional[float] = None
    package_price: Optional[float] = None
    discount_rate: Optional[float] = None
    service_types: Optional[str] = None
    valid_days: Optional[int] = None
    max_usage: Optional[int] = None
    status: Optional[str] = None
    sort_order: Optional[int] = None
    items: Optional[List[PackageItemCreate]] = None


class PackageResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    original_price: float
    package_price: float
    discount_rate: float
    service_types: Optional[str] = None
    valid_days: int
    max_usage: int
    status: str
    sort_order: int
    created_at: datetime
    updated_at: datetime
    items: Optional[List[PackageItemResponse]] = None

    model_config = ConfigDict(from_attributes=True)


class PackageOrderCreate(BaseModel):
    package_id: int
    office_id: int
    office_name: str
    order_user_id: Optional[int] = None
    order_user_name: Optional[str] = None
    note: Optional[str] = None


class PackageOrderResponse(BaseModel):
    id: int
    package_id: int
    package_name: Optional[str] = None
    office_id: int
    office_name: Optional[str] = None
    order_user_id: Optional[int] = None
    order_user_name: Optional[str] = None
    original_price: Optional[float] = None
    package_price: Optional[float] = None
    saved_amount: Optional[float] = None
    status: str
    used_count: int
    total_count: int
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get("", response_model=List[PackageResponse])
def list_packages(
    status: Optional[str] = Query(
        None, description="Filter by status: active, inactive"
    ),
    db: Session = Depends(get_db),
):
    """
    获取套餐列表

    支持按状态筛选：
    - active: 激活的套餐
    - inactive: 停用的套餐
    """
    query = db.query(Package)

    if status:
        query = query.filter(Package.status == status)

    packages = query.order_by(Package.sort_order, Package.id).all()

    result = []
    for pkg in packages:
        pkg_dict = {
            "id": pkg.id,
            "name": pkg.name,
            "description": pkg.description,
            "original_price": pkg.original_price,
            "package_price": pkg.package_price,
            "discount_rate": pkg.discount_rate,
            "service_types": pkg.service_types,
            "valid_days": pkg.valid_days,
            "max_usage": pkg.max_usage,
            "status": pkg.status,
            "sort_order": pkg.sort_order,
            "created_at": pkg.created_at,
            "updated_at": pkg.updated_at,
            "items": None,
        }

        items = db.query(PackageItem).filter(PackageItem.package_id == pkg.id).all()
        if items:
            pkg_dict["items"] = [
                PackageItemResponse(
                    id=item.id,
                    package_id=item.package_id,
                    service_type=item.service_type,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit=item.unit,
                    unit_price=item.unit_price,
                    subtotal=item.subtotal,
                    note=item.note,
                    created_at=item.created_at,
                )
                for item in items
            ]

        result.append(PackageResponse(**pkg_dict))

    return result


@router.get("/{package_id}", response_model=PackageResponse)
def get_package(package_id: int, db: Session = Depends(get_db)):
    """获取单个套餐详情"""
    pkg = db.query(Package).filter(Package.id == package_id).first()

    if not pkg:
        raise HTTPException(status_code=404, detail="套餐不存在")

    items = db.query(PackageItem).filter(PackageItem.package_id == pkg.id).all()

    return PackageResponse(
        id=pkg.id,
        name=pkg.name,
        description=pkg.description,
        original_price=pkg.original_price,
        package_price=pkg.package_price,
        discount_rate=pkg.discount_rate,
        service_types=pkg.service_types,
        valid_days=pkg.valid_days,
        max_usage=pkg.max_usage,
        status=pkg.status,
        sort_order=pkg.sort_order,
        created_at=pkg.created_at,
        updated_at=pkg.updated_at,
        items=[
            PackageItemResponse(
                id=item.id,
                package_id=item.package_id,
                service_type=item.service_type,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                unit=item.unit,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
                note=item.note,
                created_at=item.created_at,
            )
            for item in items
        ],
    )


@router.post("", response_model=PackageResponse)
def create_package(package_data: PackageCreate, db: Session = Depends(get_db)):
    """创建新套餐"""
    db_package = Package(
        name=package_data.name,
        description=package_data.description,
        original_price=package_data.original_price,
        package_price=package_data.package_price,
        discount_rate=package_data.discount_rate,
        service_types=package_data.service_types,
        valid_days=package_data.valid_days,
        max_usage=package_data.max_usage,
        status=package_data.status,
        sort_order=package_data.sort_order,
    )

    db.add(db_package)
    db.commit()
    db.refresh(db_package)

    if package_data.items:
        for item_data in package_data.items:
            db_item = PackageItem(
                package_id=db_package.id,
                service_type=item_data.service_type,
                product_id=item_data.product_id,
                product_name=item_data.product_name,
                quantity=item_data.quantity,
                unit=item_data.unit,
                unit_price=item_data.unit_price,
                subtotal=item_data.subtotal,
                note=item_data.note,
            )
            db.add(db_item)

        db.commit()

    items = db.query(PackageItem).filter(PackageItem.package_id == db_package.id).all()

    return PackageResponse(
        id=db_package.id,
        name=db_package.name,
        description=db_package.description,
        original_price=db_package.original_price,
        package_price=db_package.package_price,
        discount_rate=db_package.discount_rate,
        service_types=db_package.service_types,
        valid_days=db_package.valid_days,
        max_usage=db_package.max_usage,
        status=db_package.status,
        sort_order=db_package.sort_order,
        created_at=db_package.created_at,
        updated_at=db_package.updated_at,
        items=[
            PackageItemResponse(
                id=item.id,
                package_id=item.package_id,
                service_type=item.service_type,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                unit=item.unit,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
                note=item.note,
                created_at=item.created_at,
            )
            for item in items
        ],
    )


@router.put("/{package_id}", response_model=PackageResponse)
def update_package(
    package_id: int, package_data: PackageUpdate, db: Session = Depends(get_db)
):
    """更新套餐信息"""
    pkg = db.query(Package).filter(Package.id == package_id).first()

    if not pkg:
        raise HTTPException(status_code=404, detail="套餐不存在")

    update_data = package_data.model_dump(exclude_unset=True, exclude={"items"})

    for field, value in update_data.items():
        setattr(pkg, field, value)

    if package_data.items is not None:
        db.query(PackageItem).filter(PackageItem.package_id == package_id).delete()

        for item_data in package_data.items:
            db_item = PackageItem(
                package_id=package_id,
                service_type=item_data.service_type,
                product_id=item_data.product_id,
                product_name=item_data.product_name,
                quantity=item_data.quantity,
                unit=item_data.unit,
                unit_price=item_data.unit_price,
                subtotal=item_data.subtotal,
                note=item_data.note,
            )
            db.add(db_item)

    pkg.updated_at = datetime.now()
    db.commit()
    db.refresh(pkg)

    items = db.query(PackageItem).filter(PackageItem.package_id == pkg.id).all()

    return PackageResponse(
        id=pkg.id,
        name=pkg.name,
        description=pkg.description,
        original_price=pkg.original_price,
        package_price=pkg.package_price,
        discount_rate=pkg.discount_rate,
        service_types=pkg.service_types,
        valid_days=pkg.valid_days,
        max_usage=pkg.max_usage,
        status=pkg.status,
        sort_order=pkg.sort_order,
        created_at=pkg.created_at,
        updated_at=pkg.updated_at,
        items=[
            PackageItemResponse(
                id=item.id,
                package_id=item.package_id,
                service_type=item.service_type,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                unit=item.unit,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
                note=item.note,
                created_at=item.created_at,
            )
            for item in items
        ],
    )


@router.delete("/{package_id}")
def delete_package(package_id: int, db: Session = Depends(get_db)):
    """删除套餐（软删除，改为 inactive 状态）"""
    pkg = db.query(Package).filter(Package.id == package_id).first()

    if not pkg:
        raise HTTPException(status_code=404, detail="套餐不存在")

    pkg.status = "inactive"
    pkg.updated_at = datetime.now()
    db.commit()

    return {"message": "套餐已停用", "package_id": package_id}


@router.post("/{package_id}/order", response_model=PackageOrderResponse)
def create_package_order(
    package_id: int, order_data: PackageOrderCreate, db: Session = Depends(get_db)
):
    """订购套餐"""
    pkg = db.query(Package).filter(Package.id == package_id).first()

    if not pkg:
        raise HTTPException(status_code=404, detail="套餐不存在")

    if pkg.status != "active":
        raise HTTPException(status_code=400, detail="该套餐已停用")

    valid_from = datetime.now().date()
    valid_until = valid_from + timedelta(days=pkg.valid_days)

    saved_amount = pkg.original_price - pkg.package_price

    order = PackageOrder(
        package_id=pkg.id,
        package_name=pkg.name,
        office_id=order_data.office_id,
        office_name=order_data.office_name,
        order_user_id=order_data.order_user_id,
        order_user_name=order_data.order_user_name,
        original_price=pkg.original_price,
        package_price=pkg.package_price,
        saved_amount=saved_amount,
        status="pending",
        used_count=0,
        total_count=1,
        valid_from=valid_from.isoformat(),
        valid_until=valid_until.isoformat(),
        note=order_data.note,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return PackageOrderResponse(
        id=order.id,
        package_id=order.package_id,
        package_name=order.package_name,
        office_id=order.office_id,
        office_name=order.office_name,
        order_user_id=order.order_user_id,
        order_user_name=order.order_user_name,
        original_price=order.original_price,
        package_price=order.package_price,
        saved_amount=order.saved_amount,
        status=order.status,
        used_count=order.used_count,
        total_count=order.total_count,
        valid_from=order.valid_from,
        valid_until=order.valid_until,
        note=order.note,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.get("/orders/list", response_model=List[PackageOrderResponse])
def list_package_orders(
    office_id: Optional[int] = Query(None, description="Filter by office ID"),
    status: Optional[str] = Query(
        None, description="Filter by status: pending, active, completed, expired"
    ),
    db: Session = Depends(get_db),
):
    """获取套餐订单列表"""
    query = db.query(PackageOrder)

    if office_id:
        query = query.filter(PackageOrder.office_id == office_id)

    if status:
        query = query.filter(PackageOrder.status == status)

    orders = query.order_by(PackageOrder.created_at.desc()).all()

    return [
        PackageOrderResponse(
            id=order.id,
            package_id=order.package_id,
            package_name=order.package_name,
            office_id=order.office_id,
            office_name=order.office_name,
            order_user_id=order.order_user_id,
            order_user_name=order.order_user_name,
            original_price=order.original_price,
            package_price=order.package_price,
            saved_amount=order.saved_amount,
            status=order.status,
            used_count=order.used_count,
            total_count=order.total_count,
            valid_from=order.valid_from,
            valid_until=order.valid_until,
            note=order.note,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
        for order in orders
    ]


@router.put("/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    status: str = Query(
        ..., description="New status: pending, active, completed, expired"
    ),
    db: Session = Depends(get_db),
):
    """更新套餐订单状态"""
    order = db.query(PackageOrder).filter(PackageOrder.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    valid_statuses = ["pending", "active", "completed", "expired", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400, detail=f"无效的状态，必须是: {', '.join(valid_statuses)}"
        )

    order.status = status
    order.updated_at = datetime.now()
    db.commit()

    return {"message": "订单状态已更新", "order_id": order_id, "status": status}


@router.get("/stats/summary")
def get_package_stats(db: Session = Depends(get_db)):
    """获取套餐统计信息"""
    total_packages = db.query(func.count(Package.id)).scalar()
    active_packages = (
        db.query(func.count(Package.id)).filter(Package.status == "active").scalar()
    )

    total_orders = db.query(func.count(PackageOrder.id)).scalar()
    pending_orders = (
        db.query(func.count(PackageOrder.id))
        .filter(PackageOrder.status == "pending")
        .scalar()
    )
    active_orders = (
        db.query(func.count(PackageOrder.id))
        .filter(PackageOrder.status == "active")
        .scalar()
    )
    completed_orders = (
        db.query(func.count(PackageOrder.id))
        .filter(PackageOrder.status == "completed")
        .scalar()
    )

    total_revenue = (
        db.query(func.sum(PackageOrder.package_price))
        .filter(PackageOrder.status.in_(["active", "completed"]))
        .scalar()
        or 0
    )

    total_saved = (
        db.query(func.sum(PackageOrder.saved_amount))
        .filter(PackageOrder.status.in_(["active", "completed"]))
        .scalar()
        or 0
    )

    return {
        "packages": {
            "total": total_packages,
            "active": active_packages,
            "inactive": total_packages - active_packages,
        },
        "orders": {
            "total": total_orders,
            "pending": pending_orders,
            "active": active_orders,
            "completed": completed_orders,
        },
        "revenue": {"total": total_revenue, "saved": total_saved},
    }
