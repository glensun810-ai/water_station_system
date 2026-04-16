"""
统一结算管理API
聚合水站服务和空间服务的结算数据，提供统一查询接口
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
import io
import csv

from config.database import get_db
from depends.auth import get_current_user, get_admin_user
from models.user import User
from models.pickup import OfficePickup
from shared.models.space.space_booking import SpaceBooking

router = APIRouter(prefix="/unified/settlements", tags=["统一结算管理"])


class SettlementSummary(BaseModel):
    """结算汇总数据"""

    water: dict
    space: dict
    total: dict


class SettlementRecord(BaseModel):
    """结算记录"""

    id: str
    service_type: str
    service_name: str
    service_icon: str
    record_no: str
    payer: str
    department: Optional[str] = None
    amount: float
    status: str
    status_text: str
    status_class: str
    created_at: Optional[str] = None
    settled_at: Optional[str] = None
    detail_url: str


class SettlementRecordList(BaseModel):
    """结算记录列表响应"""

    items: List[SettlementRecord]
    total: int
    summary: dict


@router.get("/summary", response_model=SettlementSummary)
async def get_unified_settlement_summary(
    month: Optional[str] = Query(
        "current", description="月份筛选: current/last/quarter/all"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取跨服务结算汇总统计

    返回水站服务和空间服务的结算汇总数据，包括：
    - 待确认收款金额和笔数
    - 已结算金额和笔数
    - 本月收入统计
    - 累计收入统计
    """
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    if month == "current":
        month_start = datetime(current_year, current_month, 1)
        month_end = now
    elif month == "last":
        if current_month == 1:
            month_start = datetime(current_year - 1, 12, 1)
            month_end = datetime(current_year - 1, 12, 31, 23, 59, 59)
        else:
            month_start = datetime(current_year, current_month - 1, 1)
            month_end = datetime(current_year, current_month, 1) - timedelta(seconds=1)
    elif month == "quarter":
        month_start = (
            datetime(current_year, current_month - 2, 1)
            if current_month >= 3
            else datetime(current_year - 1, current_month + 10, 1)
        )
        month_end = now
    else:
        month_start = None
        month_end = None

    water_summary = {}

    try:
        water_pending_query = db.query(
            func.count(OfficePickup.id).label("count"),
            func.sum(OfficePickup.total_amount).label("amount"),
        ).filter(
            OfficePickup.is_deleted == False,
            OfficePickup.settlement_status.in_(["pending", "paid", "applied"]),
        )

        water_pending_result = water_pending_query.first()
        water_summary["pending_amount"] = float(water_pending_result.amount or 0)
        water_summary["pending_count"] = water_pending_result.count or 0

        water_settled_query = db.query(
            func.count(OfficePickup.id).label("count"),
            func.sum(OfficePickup.total_amount).label("amount"),
        ).filter(
            OfficePickup.is_deleted == False,
            OfficePickup.settlement_status.in_(["confirmed", "settled"]),
        )

        if month_start:
            water_settled_query = water_settled_query.filter(
                OfficePickup.confirmed_time >= month_start,
                OfficePickup.confirmed_time <= month_end,
            )

        water_settled_result = water_settled_query.first()
        water_summary["settled_amount"] = float(water_settled_result.amount or 0)
        water_summary["settled_count"] = water_settled_result.count or 0

        water_monthly_query = db.query(
            func.count(OfficePickup.id).label("count"),
            func.sum(OfficePickup.total_amount).label("amount"),
        ).filter(
            OfficePickup.is_deleted == False,
            OfficePickup.settlement_status.in_(["confirmed", "settled"]),
            OfficePickup.confirmed_time >= datetime(current_year, current_month, 1),
        )

        water_monthly_result = water_monthly_query.first()
        water_summary["monthly_revenue"] = float(water_monthly_result.amount or 0)
        water_summary["monthly_count"] = water_monthly_result.count or 0

    except Exception as e:
        water_summary = {
            "pending_amount": 0,
            "pending_count": 0,
            "settled_amount": 0,
            "settled_count": 0,
            "monthly_revenue": 0,
            "monthly_count": 0,
        }

    space_summary = {}

    try:
        space_pending_query = db.query(
            func.count(SpaceBooking.id).label("count"),
            func.sum(SpaceBooking.total_fee).label("amount"),
        ).filter(SpaceBooking.status == "completed")

        space_pending_result = space_pending_query.first()
        space_summary["pending_amount"] = float(space_pending_result.amount or 0)
        space_summary["pending_count"] = space_pending_result.count or 0

        space_settled_query = db.query(
            func.count(SpaceBooking.id).label("count"),
            func.sum(SpaceBooking.total_fee).label("amount"),
        ).filter(SpaceBooking.status == "settled")

        if month_start:
            space_settled_query = space_settled_query.filter(
                SpaceBooking.settled_at >= month_start,
                SpaceBooking.settled_at <= month_end,
            )

        space_settled_result = space_settled_query.first()
        space_summary["settled_amount"] = float(space_settled_result.amount or 0)
        space_summary["settled_count"] = space_settled_result.count or 0

        space_monthly_query = db.query(
            func.count(SpaceBooking.id).label("count"),
            func.sum(SpaceBooking.total_fee).label("amount"),
        ).filter(
            SpaceBooking.status == "settled",
            SpaceBooking.settled_at >= datetime(current_year, current_month, 1),
        )

        space_monthly_result = space_monthly_query.first()
        space_summary["monthly_revenue"] = float(space_monthly_result.amount or 0)
        space_summary["monthly_count"] = space_monthly_result.count or 0

    except Exception as e:
        space_summary = {
            "pending_amount": 0,
            "pending_count": 0,
            "settled_amount": 0,
            "settled_count": 0,
            "monthly_revenue": 0,
            "monthly_count": 0,
        }

    total_summary = {
        "pending_amount": water_summary["pending_amount"]
        + space_summary["pending_amount"],
        "pending_count": water_summary["pending_count"]
        + space_summary["pending_count"],
        "settled_amount": water_summary["settled_amount"]
        + space_summary["settled_amount"],
        "settled_count": water_summary["settled_count"]
        + space_summary["settled_count"],
        "monthly_revenue": water_summary["monthly_revenue"]
        + space_summary["monthly_revenue"],
        "monthly_count": water_summary["monthly_count"]
        + space_summary["monthly_count"],
        "total_revenue": water_summary["settled_amount"]
        + space_summary["settled_amount"],
        "total_revenue_count": water_summary["settled_count"]
        + space_summary["settled_count"],
    }

    return SettlementSummary(
        water=water_summary, space=space_summary, total=total_summary
    )


@router.get("/records", response_model=SettlementRecordList)
async def get_unified_settlement_records(
    service_type: Optional[str] = Query("all", description="服务类型: all/water/space"),
    status: Optional[str] = Query(
        "all", description="结算状态: all/pending/waiting/settled"
    ),
    month: Optional[str] = Query("all", description="月份: all/current/last/quarter"),
    department: Optional[str] = Query(None, description="部门筛选"),
    search: Optional[str] = Query(None, description="关键词搜索"),
    min_amount: Optional[float] = Query(None, description="最小金额"),
    max_amount: Optional[float] = Query(None, description="最大金额"),
    limit: int = Query(50, description="返回记录数量"),
    offset: int = Query(0, description="偏移量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取跨服务结算记录聚合列表

    支持多维度筛选：
    - 服务类型筛选
    - 结算状态筛选
    - 月份筛选
    - 部门筛选
    - 关键词搜索
    - 金额范围筛选
    """
    records = []

    now = datetime.now()
    current_month = now.month
    current_year = now.year

    if month == "current":
        month_start = datetime(current_year, current_month, 1)
        month_end = now
    elif month == "last":
        if current_month == 1:
            month_start = datetime(current_year - 1, 12, 1)
            month_end = datetime(current_year - 1, 12, 31, 23, 59, 59)
        else:
            month_start = datetime(current_year, current_month - 1, 1)
            month_end = datetime(current_year, current_month, 1) - timedelta(seconds=1)
    elif month == "quarter":
        month_start = datetime(current_year, max(1, current_month - 2), 1)
        month_end = now
    else:
        month_start = None
        month_end = None

    if service_type == "all" or service_type == "water":
        try:
            water_query = db.query(OfficePickup).filter(
                OfficePickup.is_deleted == False
            )

            if status == "pending":
                water_query = water_query.filter(
                    OfficePickup.settlement_status == "pending"
                )
            elif status == "waiting":
                water_query = water_query.filter(
                    OfficePickup.settlement_status.in_(["paid", "applied"])
                )
            elif status == "settled":
                water_query = water_query.filter(
                    OfficePickup.settlement_status.in_(["confirmed", "settled"])
                )

            if search:
                water_query = water_query.filter(
                    or_(
                        OfficePickup.office_name.ilike(f"%{search}%"),
                        OfficePickup.pickup_person.ilike(f"%{search}%"),
                    )
                )

            if min_amount:
                water_query = water_query.filter(
                    OfficePickup.total_amount >= min_amount
                )
            if max_amount:
                water_query = water_query.filter(
                    OfficePickup.total_amount <= max_amount
                )

            water_pickups = (
                water_query.order_by(OfficePickup.pickup_time.desc()).limit(limit).all()
            )

            for pickup in water_pickups:
                pickup_status = pickup.settlement_status
                if pickup_status in ["paid", "applied"]:
                    status_class = "waiting"
                    status_text = "已申请结算"
                elif pickup_status in ["confirmed", "settled"]:
                    status_class = "settled"
                    status_text = "已结算"
                else:
                    status_class = "pending"
                    status_text = "待付款"

                record_time = pickup.pickup_time or pickup.created_at
                if month_start and month_end:
                    if not (
                        month_start <= record_time <= month_end if record_time else True
                    ):
                        continue

                records.append(
                    SettlementRecord(
                        id=f"water_{pickup.id}",
                        service_type="water",
                        service_name="水站服务",
                        service_icon="💧",
                        record_no=str(pickup.id),
                        payer=pickup.office_name or "未知办公室",
                        department=None,
                        amount=float(pickup.total_amount or 0),
                        status=pickup_status,
                        status_text=status_text,
                        status_class=status_class,
                        created_at=record_time.isoformat() if record_time else None,
                        settled_at=pickup.confirmed_time.isoformat()
                        if pickup.confirmed_time
                        else None,
                        detail_url=f"/portal/admin/water/settlement_management.html?id={pickup.id}",
                    )
                )

        except Exception as e:
            pass

    if service_type == "all" or service_type == "space":
        try:
            space_query = db.query(SpaceBooking).filter(
                SpaceBooking.status.in_(["completed", "settled"])
            )

            if status == "pending":
                space_query = space_query.filter(SpaceBooking.status == "completed")
            elif status == "settled":
                space_query = space_query.filter(SpaceBooking.status == "settled")
            elif status == "waiting":
                pass

            if department:
                space_query = space_query.filter(SpaceBooking.department == department)

            if search:
                space_query = space_query.filter(
                    or_(
                        SpaceBooking.user_name.ilike(f"%{search}%"),
                        SpaceBooking.department.ilike(f"%{search}%"),
                        SpaceBooking.booking_no.ilike(f"%{search}%"),
                    )
                )

            if min_amount:
                space_query = space_query.filter(SpaceBooking.total_fee >= min_amount)
            if max_amount:
                space_query = space_query.filter(SpaceBooking.total_fee <= max_amount)

            space_bookings = (
                space_query.order_by(SpaceBooking.created_at.desc()).limit(limit).all()
            )

            for booking in space_bookings:
                booking_status = booking.status
                if booking_status == "settled":
                    status_class = "settled"
                    status_text = "已结算"
                else:
                    status_class = "pending"
                    status_text = "待确认收款"

                record_time = booking.settled_at or booking.created_at
                if month_start and month_end:
                    if not (
                        month_start <= record_time <= month_end if record_time else True
                    ):
                        continue

                records.append(
                    SettlementRecord(
                        id=f"space_{booking.id}",
                        service_type="space",
                        service_name="空间服务",
                        service_icon="🏢",
                        record_no=booking.booking_no or f"BK{booking.id}",
                        payer=booking.user_name or "未知用户",
                        department=booking.department,
                        amount=float(booking.total_fee or booking.actual_fee or 0),
                        status=booking_status,
                        status_text=status_text,
                        status_class=status_class,
                        created_at=booking.created_at.isoformat()
                        if booking.created_at
                        else None,
                        settled_at=booking.settled_at.isoformat()
                        if booking.settled_at
                        else None,
                        detail_url=f"/portal/admin/space/settlements.html?id={booking.id}",
                    )
                )

        except Exception as e:
            pass

    records.sort(key=lambda x: x.created_at or "", reverse=True)

    total_count = len(records)
    paginated_records = records[offset : offset + limit]

    summary = {
        "total_count": total_count,
        "total_amount": sum(r.amount for r in paginated_records),
        "water_count": len([r for r in paginated_records if r.service_type == "water"]),
        "space_count": len([r for r in paginated_records if r.service_type == "space"]),
    }

    return SettlementRecordList(
        items=paginated_records, total=total_count, summary=summary
    )


@router.get("/departments")
async def get_settlement_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取结算记录中的部门列表

    用于部门筛选下拉框的数据源
    """
    departments = []

    try:
        space_departments = (
            db.query(SpaceBooking.department)
            .filter(
                SpaceBooking.status.in_(["completed", "settled"]),
                SpaceBooking.department.isnot(None),
                SpaceBooking.department != "",
            )
            .distinct()
            .all()
        )

        departments = [d[0] for d in space_departments if d[0]]
        departments.sort()

    except Exception as e:
        pass

    return {"code": 200, "data": departments}


@router.get("/export")
async def export_settlement_report(
    service_type: Optional[str] = Query("all"),
    status: Optional[str] = Query("all"),
    month: Optional[str] = Query("all"),
    department: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    format: Optional[str] = Query("csv", description="导出格式: csv/json"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    导出结算报表

    支持CSV和JSON格式导出
    CSV格式可直接下载为文件
    """
    records_data = await get_unified_settlement_records(
        service_type=service_type,
        status=status,
        month=month,
        department=department,
        search=search,
        limit=1000,
        offset=0,
        db=db,
        current_user=current_user,
    )

    if format == "json":
        return {
            "code": 200,
            "data": {
                "records": [r.dict() for r in records_data.items],
                "total": records_data.total,
                "summary": records_data.summary,
            },
            "message": "导出数据获取成功",
        }

    output = io.StringIO()
    writer = csv.writer(output)

    header = [
        "序号",
        "服务类型",
        "记录编号",
        "付款方",
        "部门",
        "金额(元)",
        "状态",
        "创建时间",
        "结算时间",
    ]
    writer.writerow(header)

    for idx, record in enumerate(records_data.items, 1):
        row = [
            idx,
            record.service_name,
            record.record_no,
            record.payer,
            record.department or "-",
            f"{record.amount:.2f}",
            record.status_text,
            record.created_at[:19] if record.created_at else "-",
            record.settled_at[:19] if record.settled_at else "-",
        ]
        writer.writerow(row)

    summary_row = [
        "合计",
        "-",
        "-",
        "-",
        "-",
        f"{sum(r.amount for r in records_data.items):.2f}",
        f"{records_data.total}条",
        "-",
        "-",
    ]
    writer.writerow(summary_row)

    output.seek(0)

    filename = f"结算报表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv;charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/monthly-report")
async def export_monthly_report(
    year: int = Query(..., description="年份"),
    month: int = Query(..., description="月份"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    导出月度结算报表

    生成指定月份的完整结算报表，包含：
    - 水站服务月度明细
    - 空间服务月度明细
    - 月度汇总统计
    """
    month_start = datetime(year, month, 1)
    if month == 12:
        month_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        month_end = datetime(year, month + 1, 1) - timedelta(seconds=1)

    records_data = await get_unified_settlement_records(
        service_type="all",
        status="settled",
        month="all",
        department=None,
        search=None,
        limit=1000,
        offset=0,
        db=db,
        current_user=current_user,
    )

    month_records = [
        r
        for r in records_data.items
        if r.settled_at
        and month_start <= datetime.fromisoformat(r.settled_at) <= month_end
    ]

    output = io.StringIO()
    writer = csv.writer(output)

    report_title = f"AI产业集群 {year}年{month}月 结算报表"
    writer.writerow([report_title])
    writer.writerow([])

    writer.writerow(["生成时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow(["生成人:", current_user.name or current_user.username])
    writer.writerow(["报表范围:", f"{year}年{month}月"])
    writer.writerow([])

    writer.writerow(["一、水站服务结算明细"])
    writer.writerow(
        [
            "序号",
            "记录编号",
            "办公室",
            "产品",
            "数量",
            "金额",
            "结算时间",
        ]
    )

    water_records = [r for r in month_records if r.service_type == "water"]
    water_total = 0

    try:
        water_query = (
            db.query(OfficePickup)
            .filter(
                OfficePickup.is_deleted == False,
                OfficePickup.settlement_status.in_(["confirmed", "settled"]),
                OfficePickup.confirmed_time >= month_start,
                OfficePickup.confirmed_time <= month_end,
            )
            .all()
        )

        for idx, pickup in enumerate(water_query, 1):
            amount = float(pickup.total_amount or 0)
            water_total += amount
            writer.writerow(
                [
                    idx,
                    pickup.id,
                    pickup.office_name or "-",
                    pickup.product_name or "-",
                    pickup.quantity or 0,
                    f"{amount:.2f}",
                    pickup.confirmed_time.strftime("%Y-%m-%d %H:%M")
                    if pickup.confirmed_time
                    else "-",
                ]
            )
    except:
        pass

    writer.writerow(
        ["小计", "", "", "", "", f"{water_total:.2f}", f"{len(water_records)}笔"]
    )
    writer.writerow([])

    writer.writerow(["二、空间服务结算明细"])
    writer.writerow(
        [
            "序号",
            "预约编号",
            "使用者",
            "部门",
            "资源",
            "金额",
            "结算时间",
        ]
    )

    space_records = [r for r in month_records if r.service_type == "space"]
    space_total = 0

    try:
        space_query = (
            db.query(SpaceBooking)
            .filter(
                SpaceBooking.status == "settled",
                SpaceBooking.settled_at >= month_start,
                SpaceBooking.settled_at <= month_end,
            )
            .all()
        )

        for idx, booking in enumerate(space_query, 1):
            amount = float(booking.total_fee or booking.actual_fee or 0)
            space_total += amount
            writer.writerow(
                [
                    idx,
                    booking.booking_no or f"BK{booking.id}",
                    booking.user_name or "-",
                    booking.department or "-",
                    booking.resource_name or "-",
                    f"{amount:.2f}",
                    booking.settled_at.strftime("%Y-%m-%d %H:%M")
                    if booking.settled_at
                    else "-",
                ]
            )
    except:
        pass

    writer.writerow(
        ["小计", "", "", "", "", f"{space_total:.2f}", f"{len(space_records)}笔"]
    )
    writer.writerow([])

    writer.writerow(["三、月度汇总"])
    writer.writerow(["服务类型", "笔数", "金额(元)", "占比"])

    total_amount = water_total + space_total

    if total_amount > 0:
        water_ratio = f"{water_total / total_amount * 100:.1f}%"
        space_ratio = f"{space_total / total_amount * 100:.1f}%"
    else:
        water_ratio = "0%"
        space_ratio = "0%"

    writer.writerow(
        ["💧 水站服务", f"{len(water_records)}笔", f"{water_total:.2f}", water_ratio]
    )
    writer.writerow(
        ["🏢 空间服务", f"{len(space_records)}笔", f"{space_total:.2f}", space_ratio]
    )
    writer.writerow(
        [
            "合计",
            f"{len(water_records) + len(space_records)}笔",
            f"{total_amount:.2f}",
            "100%",
        ]
    )
    writer.writerow([])

    writer.writerow(["--- 报表结束 ---"])

    output.seek(0)

    filename = f"月度结算报表_{year}年{month}月.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv;charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
