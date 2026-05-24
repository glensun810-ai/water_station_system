"""办公室领水管理 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from config.database import get_db
from models.user import User
from models.office import Office
from models.product import Product
from models.pickup import OfficePickup
from depends.auth import get_current_user, get_admin_user

router = APIRouter(prefix="/office-pickup", tags=["办公室领水管理"])


@router.get("s")
def get_office_pickups(
    office_id: Optional[int] = Query(None),
    limit: int = Query(100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取领水记录列表"""
    db.expire_all()
    query = db.query(OfficePickup).filter(OfficePickup.is_deleted == False)
    if office_id is not None:
        query = query.filter(OfficePickup.office_id == office_id)
    pickups = query.order_by(OfficePickup.pickup_time.desc()).limit(limit).all()
    return [serialize_pickup(p) for p in pickups]


def serialize_pickup(p: OfficePickup) -> dict:
    return {
        "id": p.id,
        "office_id": p.office_id,
        "office_name": getattr(p, "office_name", ""),
        "product_id": p.product_id,
        "quantity": p.quantity,
        "pickup_person": p.pickup_person,
        "pickup_person_id": p.pickup_person_id,
        "pickup_time": p.pickup_time.isoformat() if p.pickup_time else None,
        "settlement_status": p.settlement_status,
        "payment_method": getattr(p, "payment_method", ""),
        "payment_time": p.payment_time.isoformat() if p.payment_time else None,
        "confirmed_by": p.confirmed_by,
        "is_deleted": p.is_deleted,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@router.put("/{pickup_id}")
def update_office_pickup(
    pickup_id: int,
    pickup_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """更新领水记录"""
    pickup = db.query(OfficePickup).filter(
        OfficePickup.id == pickup_id, OfficePickup.is_deleted == False
    ).first()
    if not pickup:
        raise HTTPException(status_code=404, detail="领水记录不存在")

    for key in ["quantity", "pickup_person", "settlement_status", "payment_method"]:
        if key in pickup_data:
            setattr(pickup, key, pickup_data[key])

    db.commit()
    return {"message": "更新成功", "pickup_id": pickup_id}


@router.post("/{pickup_id}/confirm")
def confirm_office_pickup(
    pickup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """管理员确认收款"""
    pickup = db.query(OfficePickup).filter(
        OfficePickup.id == pickup_id, OfficePickup.is_deleted == False
    ).first()
    if not pickup:
        raise HTTPException(status_code=404, detail="领水记录不存在")
    if pickup.settlement_status != "paid":
        raise HTTPException(status_code=400, detail="只能确认'已付款'状态的记录")

    pickup.settlement_status = "settled"
    pickup.confirmed_by = current_user.id
    pickup.confirmed_time = datetime.now()
    db.commit()
    return {"message": "已确认收款", "pickup_id": pickup_id}


@router.post("/{pickup_id}/revert")
def revert_office_pickup(
    pickup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """回退领水记录状态"""
    pickup = db.query(OfficePickup).filter(
        OfficePickup.id == pickup_id, OfficePickup.is_deleted == False
    ).first()
    if not pickup:
        raise HTTPException(status_code=404, detail="领水记录不存在")
    if pickup.settlement_status not in ("settled", "paid"):
        raise HTTPException(status_code=400, detail="只能回退'已结清'或'已付款'状态的记录")

    pickup.settlement_status = "pending"
    pickup.confirmed_by = None
    db.commit()
    return {"message": "已回退为待付款", "pickup_id": pickup_id}


@router.post("/{pickup_id}/remind")
def remind_office_pickup(
    pickup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """发送催缴提醒（需配置通知服务后生效）"""
    pickup = db.query(OfficePickup).filter(
        OfficePickup.id == pickup_id, OfficePickup.is_deleted == False
    ).first()
    if not pickup:
        raise HTTPException(status_code=404, detail="领水记录不存在")
    # 通知服务尚未接入，返回明确提示
    return {
        "message": f"催缴提醒已记录（通知服务未接入，请通过其他渠道联系 {pickup.pickup_person}）",
        "warning": "通知服务尚未配置，催缴消息不会实际发送",
    }


@router.post("/batch-confirm")
def batch_confirm_pickups(
    pickup_ids: list[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """批量确认收款"""
    confirmed = []
    for pid in pickup_ids:
        pickup = db.query(OfficePickup).filter(
            OfficePickup.id == pid, OfficePickup.is_deleted == False
        ).first()
        if pickup and pickup.settlement_status == "paid":
            pickup.settlement_status = "settled"
            pickup.confirmed_by = current_user.id
            pickup.confirmed_time = datetime.now()
            confirmed.append(pid)
    db.commit()
    return {"message": f"已确认 {len(confirmed)} 条记录", "confirmed_ids": confirmed}


@router.post("/batch-delete")
def batch_delete_pickups(
    pickup_ids: list[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """批量删除领水记录（软删除）"""
    deleted = []
    for pid in pickup_ids:
        pickup = db.query(OfficePickup).filter(
            OfficePickup.id == pid, OfficePickup.is_deleted == False
        ).first()
        if pickup:
            pickup.is_deleted = True
            pickup.deleted_at = datetime.now()
            deleted.append(pid)
    db.commit()
    return {"message": f"已删除 {len(deleted)} 条记录", "deleted_ids": deleted}


@router.delete("/{pickup_id}")
def delete_office_pickup(
    pickup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """删除领水记录（软删除）"""
    pickup = db.query(OfficePickup).filter(
        OfficePickup.id == pickup_id, OfficePickup.is_deleted == False
    ).first()
    if not pickup:
        raise HTTPException(status_code=404, detail="领水记录不存在")
    pickup.is_deleted = True
    pickup.deleted_at = datetime.now()
    db.commit()
    return {"message": "已删除", "pickup_id": pickup_id}


# ==================== 办公室结算管理 ====================

admin_settlement_router = APIRouter(prefix="/admin/office-settlements", tags=["办公室结算"])


@admin_settlement_router.get("")
def get_admin_settlements(
    limit: int = Query(100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """管理员获取办公室结算列表"""
    pickups = db.query(OfficePickup).filter(
        OfficePickup.is_deleted == False,
        OfficePickup.settlement_status == "settled",
    ).order_by(OfficePickup.pickup_time.desc()).limit(limit).all()

    # 按办公室分组
    office_data = {}
    for p in pickups:
        key = p.office_id
        if key not in office_data:
            office_data[key] = {
                "office_id": p.office_id,
                "office_name": getattr(p, "office_name", ""),
                "total_amount": 0.0,
                "pickup_count": 0,
                "pickups": [],
            }
        office_data[key]["total_amount"] += float(p.total_amount or 0)
        office_data[key]["pickup_count"] += 1
        office_data[key]["pickups"].append(serialize_pickup(p))

    return list(office_data.values())


office_settlement_router = APIRouter(prefix="/office-settlements", tags=["办公室结算操作"])


@office_settlement_router.post("/auto-generate-monthly")
def auto_generate_monthly_settlement(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """自动生成月度结算单（已升级为正式结算流程，创建 MonthlySettlement 记录）"""
    from models.settlement_v2 import MonthlySettlement
    from datetime import date

    pickups = db.query(OfficePickup).filter(
        OfficePickup.is_deleted == False,
        OfficePickup.settlement_status == "settled",
    ).all()

    if not pickups:
        return {"message": "没有需要结算的记录", "settlement_count": 0}

    # 按办公室分组
    office_groups = {}
    for p in pickups:
        oid = p.office_id
        if oid not in office_groups:
            office_groups[oid] = {"pickups": [], "total_amount": 0.0}
        office_groups[oid]["pickups"].append(p)
        office_groups[oid]["total_amount"] += float(p.total_amount or 0)

    today = date.today()
    period = today.strftime("%Y-%m")
    settlements_created = 0

    for idx, (oid, group) in enumerate(office_groups.items(), 1):
        # 生成结算单号
        seq = db.query(MonthlySettlement).count() + idx
        settlement_no = f"MS{today.strftime('%Y%m')}{seq:04d}"

        # 创建正式的月度结算单
        settlement = MonthlySettlement(
            settlement_no=settlement_no,
            office_id=oid,
            office_name=group["pickups"][0].office_name or f"办公室{oid}",
            settlement_period=period,
            start_date=today.replace(day=1),
            end_date=today,
            record_count=len(group["pickups"]),
            total_amount=group["total_amount"],
            status="approved",
            approved_at=datetime.now(),
            approved_by=current_user.id,
            approved_by_name=current_user.name,
            note=f"由 {current_user.name} 自动生成",
        )
        db.add(settlement)
        db.flush()

        # 更新对应 pickup 记录为已结算
        for p in group["pickups"]:
            p.settlement_status = "settled"

        settlements_created += 1

    db.commit()

    return {
        "message": f"已生成 {settlements_created} 份月度结算单，共结算 {len(pickups)} 条记录",
        "settlement_count": settlements_created,
        "record_count": len(pickups),
    }
