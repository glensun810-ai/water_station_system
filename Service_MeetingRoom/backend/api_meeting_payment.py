"""
会议管理支付结算API
完善支付流程、审批交互、记录管理功能
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, timedelta
from decimal import Decimal
import sqlite3
import json
import os

router = APIRouter()

DATABASE_URL = os.path.join(os.path.dirname(__file__), "meeting.db")


def get_db():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    return conn


class PaymentSubmit(BaseModel):
    booking_id: int
    payment_method: str
    payment_evidence: Optional[str] = None
    payment_remark: Optional[str] = None


class PaymentConfirm(BaseModel):
    payment_id: int
    remark: Optional[str] = None


class SettlementCreate(BaseModel):
    office_id: Optional[int] = None
    booking_ids: List[int]
    settlement_period_start: str
    settlement_period_end: str
    remark: Optional[str] = None


class BatchPaymentSubmit(BaseModel):
    booking_ids: List[int]
    payment_method: str
    payment_evidence: Optional[str] = None
    payment_remark: Optional[str] = None


class BookingUpdate(BaseModel):
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    department: Optional[str] = None
    meeting_title: Optional[str] = None
    attendees_count: Optional[int] = None


def log_operation(
    operation_type: str,
    operation_desc: str,
    target_type: str = None,
    target_id: int = None,
    target_no: str = None,
    operator: str = None,
    operator_role: str = None,
    detail: str = None,
    ip_address: str = None,
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO meeting_operation_logs 
        (operation_type, operation_desc, target_type, target_id, target_no, operator, 
         operator_role, detail, ip_address, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            operation_type,
            operation_desc,
            target_type,
            target_id,
            target_no,
            operator,
            operator_role,
            detail,
            ip_address,
            datetime.now(),
        ),
    )
    conn.commit()
    conn.close()


@router.get("/api/meeting/bookings/enhanced")
def get_bookings_enhanced(
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    office_id: Optional[int] = None,
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    is_deleted: int = 0,
    page: int = 1,
    page_size: int = 20,
):
    conn = get_db()
    cursor = conn.cursor()

    conditions = ["is_deleted = ?"]
    params = [is_deleted]

    if status:
        conditions.append("status = ?")
        params.append(status)

    if payment_status:
        conditions.append("payment_status = ?")
        params.append(payment_status)

    if office_id:
        conditions.append("office_id = ?")
        params.append(office_id)

    if user_id:
        conditions.append("user_id = ?")
        params.append(user_id)

    if start_date:
        conditions.append("booking_date >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("booking_date <= ?")
        params.append(end_date)

    where_clause = " AND ".join(conditions)

    offset = (page - 1) * page_size

    count_query = f"SELECT COUNT(*) as total FROM meeting_bookings WHERE {where_clause}"
    cursor.execute(count_query, params)
    total = cursor.fetchone()["total"]

    query = f"""
        SELECT b.*, r.name as room_name, r.location, r.capacity, r.price_per_hour,
               r.member_price_per_hour, r.free_hours_per_month
        FROM meeting_bookings b
        LEFT JOIN meeting_rooms r ON b.room_id = r.id
        WHERE {where_clause}
        ORDER BY b.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    cursor.execute(query, params)
    bookings = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "success": True,
        "data": {
            "bookings": bookings,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }


@router.post("/api/meeting/payment/submit")
def submit_payment(payment: PaymentSubmit, operator: str = "user"):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM meeting_bookings WHERE id = ?", (payment.booking_id,))
    booking = cursor.fetchone()

    if not booking:
        conn.close()
        raise HTTPException(status_code=404, detail="预约记录不存在")

    if booking["payment_status"] not in ["unpaid", "pending"]:
        conn.close()
        raise HTTPException(status_code=400, detail="当前状态不允许提交支付")

    payment_no = f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}{payment.booking_id:04d}"

    cursor.execute(
        """
        INSERT INTO meeting_payment_records
        (payment_no, booking_id, booking_no, user_id, user_name, office_id, office_name,
         amount, payment_method, payment_evidence, payment_remark, status, paid_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            payment_no,
            payment.booking_id,
            booking["booking_no"],
            booking["user_id"],
            booking["user_name"],
            booking["office_id"],
            booking.get("department"),
            booking["actual_fee"],
            payment.payment_method,
            payment.payment_evidence,
            payment.payment_remark,
            "pending",
            datetime.now(),
            datetime.now(),
        ),
    )

    payment_id = cursor.lastrowid

    cursor.execute(
        """
        UPDATE meeting_bookings 
        SET payment_status = 'applied', 
            payment_method = ?,
            payment_evidence = ?,
            payment_remark = ?,
            payment_time = ?,
            updated_at = ?
        WHERE id = ?
    """,
        (
            payment.payment_method,
            payment.payment_evidence,
            payment.payment_remark,
            datetime.now(),
            datetime.now(),
            payment.booking_id,
        ),
    )

    conn.commit()
    conn.close()

    log_operation(
        operation_type="payment_submit",
        operation_desc=f"用户提交支付: {payment_no}",
        target_type="payment",
        target_id=payment_id,
        target_no=payment_no,
        operator=operator,
        detail=json.dumps(payment.dict()),
    )

    return {
        "success": True,
        "message": "支付申请已提交，等待管理员确认",
        "data": {"payment_id": payment_id, "payment_no": payment_no},
    }


@router.post("/api/meeting/payment/confirm")
def confirm_payment(payment: PaymentConfirm, operator: str = "admin"):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM meeting_payment_records WHERE id = ?", (payment.payment_id,)
    )
    payment_record = cursor.fetchone()

    if not payment_record:
        conn.close()
        raise HTTPException(status_code=404, detail="支付记录不存在")

    if payment_record["status"] != "pending":
        conn.close()
        raise HTTPException(status_code=400, detail="当前状态不允许确认")

    cursor.execute(
        """
        UPDATE meeting_payment_records 
        SET status = 'confirmed', 
            confirmed_at = ?,
            confirmed_by = ?,
            updated_at = ?
        WHERE id = ?
    """,
        (datetime.now(), operator, datetime.now(), payment.payment_id),
    )

    cursor.execute(
        """
        UPDATE meeting_bookings 
        SET payment_status = 'paid',
            confirmed_by = ?,
            confirmed_at = ?,
            updated_at = ?
        WHERE id = ?
    """,
        (operator, datetime.now(), datetime.now(), payment_record["booking_id"]),
    )

    conn.commit()
    conn.close()

    log_operation(
        operation_type="payment_confirm",
        operation_desc=f"管理员确认支付: {payment_record['payment_no']}",
        target_type="payment",
        target_id=payment.payment_id,
        target_no=payment_record["payment_no"],
        operator=operator,
        operator_role="admin",
        detail=payment.remark,
    )

    return {"success": True, "message": "支付已确认"}


@router.post("/api/meeting/payment/batch-submit")
def batch_submit_payment(payment: BatchPaymentSubmit, operator: str = "user"):
    conn = get_db()
    cursor = conn.cursor()
    results = []

    for booking_id in payment.booking_ids:
        cursor.execute("SELECT * FROM meeting_bookings WHERE id = ?", (booking_id,))
        booking = cursor.fetchone()

        if not booking or booking["payment_status"] not in ["unpaid", "pending"]:
            results.append(
                {"booking_id": booking_id, "success": False, "message": "状态不允许"}
            )
            continue

        payment_no = f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}{booking_id:04d}"

        cursor.execute(
            """
            INSERT INTO meeting_payment_records
            (payment_no, booking_id, booking_no, user_id, user_name, office_id, office_name,
             amount, payment_method, payment_evidence, payment_remark, status, paid_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                payment_no,
                booking_id,
                booking["booking_no"],
                booking["user_id"],
                booking["user_name"],
                booking["office_id"],
                booking.get("department"),
                booking["actual_fee"],
                payment.payment_method,
                payment.payment_evidence,
                payment.payment_remark,
                "pending",
                datetime.now(),
                datetime.now(),
            ),
        )

        cursor.execute(
            """
            UPDATE meeting_bookings 
            SET payment_status = 'applied', 
                payment_method = ?,
                payment_evidence = ?,
                payment_remark = ?,
                payment_time = ?,
                updated_at = ?
            WHERE id = ?
        """,
            (
                payment.payment_method,
                payment.payment_evidence,
                payment.payment_remark,
                datetime.now(),
                datetime.now(),
                booking_id,
            ),
        )

        results.append(
            {"booking_id": booking_id, "success": True, "payment_no": payment_no}
        )

    conn.commit()
    conn.close()

    log_operation(
        operation_type="batch_payment_submit",
        operation_desc=f"批量提交支付: {len(payment.booking_ids)}条",
        target_type="payment",
        operator=operator,
        detail=json.dumps(payment.dict()),
    )

    return {
        "success": True,
        "message": f"批量提交完成，成功{sum(1 for r in results if r['success'])}条",
        "data": results,
    }


@router.post("/api/meeting/payment/batch-confirm")
def batch_confirm_payment(payment_ids: List[int], operator: str = "admin"):
    conn = get_db()
    cursor = conn.cursor()
    success_count = 0

    for payment_id in payment_ids:
        cursor.execute(
            "SELECT * FROM meeting_payment_records WHERE id = ?", (payment_id,)
        )
        payment_record = cursor.fetchone()

        if not payment_record or payment_record["status"] != "pending":
            continue

        cursor.execute(
            """
            UPDATE meeting_payment_records 
            SET status = 'confirmed', 
                confirmed_at = ?,
                confirmed_by = ?,
                updated_at = ?
            WHERE id = ?
        """,
            (datetime.now(), operator, datetime.now(), payment_id),
        )

        cursor.execute(
            """
            UPDATE meeting_bookings 
            SET payment_status = 'paid',
                confirmed_by = ?,
                confirmed_at = ?,
                updated_at = ?
            WHERE id = ?
        """,
            (operator, datetime.now(), datetime.now(), payment_record["booking_id"]),
        )

        success_count += 1

    conn.commit()
    conn.close()

    log_operation(
        operation_type="batch_payment_confirm",
        operation_desc=f"批量确认支付: {success_count}条",
        target_type="payment",
        operator=operator,
        operator_role="admin",
    )

    return {"success": True, "message": f"成功确认{success_count}条支付记录"}


@router.get("/api/meeting/payments")
def get_payment_records(
    status: Optional[str] = None,
    office_id: Optional[int] = None,
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    conn = get_db()
    cursor = conn.cursor()

    conditions = []
    params = []

    if status:
        conditions.append("pr.status = ?")
        params.append(status)

    if office_id:
        conditions.append("pr.office_id = ?")
        params.append(office_id)

    if user_id:
        conditions.append("pr.user_id = ?")
        params.append(user_id)

    if start_date:
        conditions.append("DATE(pr.paid_at) >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("DATE(pr.paid_at) <= ?")
        params.append(end_date)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    offset = (page - 1) * page_size

    count_query = (
        f"SELECT COUNT(*) as total FROM meeting_payment_records pr WHERE {where_clause}"
    )
    cursor.execute(count_query, params)
    total = cursor.fetchone()["total"]

    query = f"""
        SELECT pr.*, b.room_name, b.booking_date, b.start_time, b.end_time, b.duration
        FROM meeting_payment_records pr
        LEFT JOIN meeting_bookings b ON pr.booking_id = b.id
        WHERE {where_clause}
        ORDER BY pr.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    cursor.execute(query, params)
    payments = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "success": True,
        "data": {
            "payments": payments,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.post("/api/meeting/settlement/create")
def create_settlement(settlement: SettlementCreate, operator: str = "admin"):
    conn = get_db()
    cursor = conn.cursor()

    batch_no = f"SET{datetime.now().strftime('%Y%m%d%H%M%S')}"

    placeholders = ",".join(["?" for _ in settlement.booking_ids])
    cursor.execute(
        f"""
        SELECT b.*, r.name as room_name, r.price_per_hour, r.member_price_per_hour
        FROM meeting_bookings b
        LEFT JOIN meeting_rooms r ON b.room_id = r.id
        WHERE b.id IN ({placeholders})
    """,
        settlement.booking_ids,
    )
    bookings = cursor.fetchall()

    if not bookings:
        conn.close()
        raise HTTPException(status_code=400, detail="没有有效的预约记录")

    total_bookings = len(bookings)
    total_hours = sum(float(b["duration"] or 0) for b in bookings)
    total_amount = sum(float(b["total_fee"] or 0) for b in bookings)
    paid_amount = sum(float(b["actual_fee"] or 0) for b in bookings)
    free_hours = sum(float(b["free_hours_used"] or 0) for b in bookings)
    discount_amount = sum(float(b["discount_amount"] or 0) for b in bookings)

    office_id = settlement.office_id or bookings[0]["office_id"]
    office_name = bookings[0].get("department") if not settlement.office_id else None

    cursor.execute(
        """
        INSERT INTO meeting_settlement_batches
        (batch_no, office_id, office_name, user_id, user_name, total_bookings,
         total_hours, total_amount, paid_amount, free_hours, discount_amount,
         status, settlement_period_start, settlement_period_end, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            batch_no,
            office_id,
            office_name,
            bookings[0]["user_id"],
            bookings[0]["user_name"],
            total_bookings,
            total_hours,
            total_amount,
            paid_amount,
            free_hours,
            discount_amount,
            "pending",
            settlement.settlement_period_start,
            settlement.settlement_period_end,
            datetime.now(),
        ),
    )

    batch_id = cursor.lastrowid

    for booking in bookings:
        cursor.execute(
            """
            INSERT INTO meeting_settlement_details
            (batch_id, booking_id, booking_no, room_name, booking_date, start_time,
             end_time, duration, total_fee, actual_fee, discount_amount, is_free,
             free_hours_used, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                batch_id,
                booking["id"],
                booking["booking_no"],
                booking["room_name"],
                booking["booking_date"],
                booking["start_time"],
                booking["end_time"],
                booking["duration"],
                booking["total_fee"],
                booking["actual_fee"],
                booking["discount_amount"],
                booking["is_free"],
                booking["free_hours_used"],
                datetime.now(),
            ),
        )

    conn.commit()
    conn.close()

    log_operation(
        operation_type="settlement_create",
        operation_desc=f"创建结算批次: {batch_no}",
        target_type="settlement",
        target_id=batch_id,
        target_no=batch_no,
        operator=operator,
        operator_role="admin",
        detail=json.dumps(settlement.dict()),
    )

    return {
        "success": True,
        "message": "结算批次创建成功",
        "data": {
            "batch_id": batch_id,
            "batch_no": batch_no,
            "total_bookings": total_bookings,
            "total_amount": total_amount,
        },
    }


@router.get("/api/meeting/settlements")
def get_settlements(
    status: Optional[str] = None,
    office_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    conn = get_db()
    cursor = conn.cursor()

    conditions = []
    params = []

    if status:
        conditions.append("status = ?")
        params.append(status)

    if office_id:
        conditions.append("office_id = ?")
        params.append(office_id)

    if start_date:
        conditions.append("settlement_period_start >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("settlement_period_end <= ?")
        params.append(end_date)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    offset = (page - 1) * page_size

    count_query = (
        f"SELECT COUNT(*) as total FROM meeting_settlement_batches WHERE {where_clause}"
    )
    cursor.execute(count_query, params)
    total = cursor.fetchone()["total"]

    query = f"""
        SELECT * FROM meeting_settlement_batches
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    cursor.execute(query, params)
    settlements = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "success": True,
        "data": {
            "settlements": settlements,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/api/meeting/settlement/{batch_id}")
def get_settlement_detail(batch_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM meeting_settlement_batches WHERE id = ?", (batch_id,))
    settlement = cursor.fetchone()

    if not settlement:
        conn.close()
        raise HTTPException(status_code=404, detail="结算批次不存在")

    cursor.execute(
        """
        SELECT sd.*, b.meeting_title, b.attendees_count, b.status as booking_status
        FROM meeting_settlement_details sd
        LEFT JOIN meeting_bookings b ON sd.booking_id = b.id
        WHERE sd.batch_id = ?
        ORDER BY sd.booking_date, sd.start_time
    """,
        (batch_id,),
    )
    details = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "success": True,
        "data": {"settlement": dict(settlement), "details": details},
    }


@router.delete("/api/meeting/booking/{booking_id}")
def delete_booking(
    booking_id: int, operator: str = "admin", reason: Optional[str] = None
):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM meeting_bookings WHERE id = ?", (booking_id,))
    booking = cursor.fetchone()

    if not booking:
        conn.close()
        raise HTTPException(status_code=404, detail="预约记录不存在")

    cursor.execute(
        """
        UPDATE meeting_bookings 
        SET is_deleted = 1,
            deleted_at = ?,
            deleted_by = ?,
            delete_reason = ?,
            updated_at = ?
        WHERE id = ?
    """,
        (datetime.now(), operator, reason, datetime.now(), booking_id),
    )

    conn.commit()
    conn.close()

    log_operation(
        operation_type="booking_delete",
        operation_desc=f"删除预约记录: {booking['booking_no']}",
        target_type="booking",
        target_id=booking_id,
        target_no=booking["booking_no"],
        operator=operator,
        operator_role="admin",
        detail=reason,
    )

    return {"success": True, "message": "预约记录已删除"}


@router.post("/api/meeting/bookings/batch-delete")
def batch_delete_bookings(
    booking_ids: List[int], operator: str = "admin", reason: Optional[str] = None
):
    conn = get_db()
    cursor = conn.cursor()
    success_count = 0

    for booking_id in booking_ids:
        cursor.execute(
            "SELECT * FROM meeting_bookings WHERE id = ? AND is_deleted = 0",
            (booking_id,),
        )
        booking = cursor.fetchone()

        if not booking:
            continue

        cursor.execute(
            """
            UPDATE meeting_bookings 
            SET is_deleted = 1,
                deleted_at = ?,
                deleted_by = ?,
                delete_reason = ?,
                updated_at = ?
            WHERE id = ?
        """,
            (datetime.now(), operator, reason, datetime.now(), booking_id),
        )

        success_count += 1

    conn.commit()
    conn.close()

    log_operation(
        operation_type="batch_booking_delete",
        operation_desc=f"批量删除预约记录: {success_count}条",
        target_type="booking",
        operator=operator,
        operator_role="admin",
        detail=reason,
    )

    return {"success": True, "message": f"成功删除{success_count}条预约记录"}


@router.get("/api/meeting/statistics/enhanced")
def get_enhanced_statistics(
    start_date: Optional[str] = None, end_date: Optional[str] = None
):
    conn = get_db()
    cursor = conn.cursor()

    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    cursor.execute(
        """
        SELECT 
            COUNT(*) as total_bookings,
            SUM(duration) as total_hours,
            SUM(total_fee) as total_revenue,
            SUM(CASE WHEN payment_status = 'paid' THEN 1 ELSE 0 END) as paid_bookings,
            SUM(CASE WHEN payment_status = 'unpaid' THEN 1 ELSE 0 END) as unpaid_bookings,
            SUM(CASE WHEN payment_status = 'applied' THEN 1 ELSE 0 END) as pending_payment_bookings,
            SUM(CASE WHEN is_free = 1 THEN 1 ELSE 0 END) as free_bookings,
            SUM(CASE WHEN user_type = 'internal' THEN 1 ELSE 0 END) as internal_bookings,
            SUM(CASE WHEN user_type = 'external' THEN 1 ELSE 0 END) as external_bookings,
            SUM(actual_fee) as actual_revenue,
            SUM(discount_amount) as total_discount,
            SUM(free_hours_used) as total_free_hours
        FROM meeting_bookings
        WHERE booking_date BETWEEN ? AND ?
        AND is_deleted = 0
    """,
        (start_date, end_date),
    )

    stats = dict(cursor.fetchone())

    cursor.execute(
        """
        SELECT 
            room_id,
            room_name,
            COUNT(*) as booking_count,
            SUM(duration) as total_hours,
            SUM(total_fee) as total_revenue,
            AVG(duration) as avg_duration
        FROM meeting_bookings
        WHERE booking_date BETWEEN ? AND ?
        AND is_deleted = 0
        GROUP BY room_id
        ORDER BY booking_count DESC
    """,
        (start_date, end_date),
    )

    room_stats = [dict(row) for row in cursor.fetchall()]

    cursor.execute(
        """
        SELECT 
            DATE(booking_date) as date,
            COUNT(*) as booking_count,
            SUM(duration) as total_hours,
            SUM(total_fee) as daily_revenue
        FROM meeting_bookings
        WHERE booking_date BETWEEN ? AND ?
        AND is_deleted = 0
        GROUP BY DATE(booking_date)
        ORDER BY date
    """,
        (start_date, end_date),
    )

    daily_stats = [dict(row) for row in cursor.fetchall()]

    cursor.execute(
        """
        SELECT 
            office_id,
            department as office_name,
            COUNT(*) as booking_count,
            SUM(duration) as total_hours,
            SUM(total_fee) as total_fee,
            SUM(actual_fee) as actual_fee
        FROM meeting_bookings
        WHERE booking_date BETWEEN ? AND ?
        AND is_deleted = 0
        AND office_id IS NOT NULL
        GROUP BY office_id
        ORDER BY total_fee DESC
    """,
        (start_date, end_date),
    )

    office_stats = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "success": True,
        "data": {
            "overview": stats,
            "room_statistics": room_stats,
            "daily_statistics": daily_stats,
            "office_statistics": office_stats,
            "period": {"start_date": start_date, "end_date": end_date},
        },
    }


@router.get("/api/meeting/operation-logs")
def get_operation_logs(
    operation_type: Optional[str] = None,
    target_type: Optional[str] = None,
    operator: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
):
    conn = get_db()
    cursor = conn.cursor()

    conditions = []
    params = []

    if operation_type:
        conditions.append("operation_type = ?")
        params.append(operation_type)

    if target_type:
        conditions.append("target_type = ?")
        params.append(target_type)

    if operator:
        conditions.append("operator LIKE ?")
        params.append(f"%{operator}%")

    if start_date:
        conditions.append("DATE(created_at) >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("DATE(created_at) <= ?")
        params.append(end_date)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    offset = (page - 1) * page_size

    count_query = (
        f"SELECT COUNT(*) as total FROM meeting_operation_logs WHERE {where_clause}"
    )
    cursor.execute(count_query, params)
    total = cursor.fetchone()["total"]

    query = f"""
        SELECT * FROM meeting_operation_logs
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    cursor.execute(query, params)
    logs = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "success": True,
        "data": {"logs": logs, "total": total, "page": page, "page_size": page_size},
    }
