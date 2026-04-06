"""
会议管理审批API
处理预约取消申请、特殊预约审批等审批流程
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import sqlite3
import os
import json

router = APIRouter()

# 使用环境变量或相对路径，支持本地和云服务器环境
current_dir = os.path.dirname(__file__)

# 尝试多个可能的数据库路径（优先级从高到低）
possible_paths = [
    # 1. 环境变量指定的路径（适用于云服务器）
    os.environ.get("MEETING_DB_PATH"),
    # 2. Service_MeetingRoom模块的标准路径
    os.path.join(current_dir, "../../Service_MeetingRoom/backend/meeting.db"),
    # 3. 当前模块目录下（备选）
    os.path.join(current_dir, "meeting.db"),
]

DATABASE_URL = None
for path in possible_paths:
    if path and os.path.exists(os.path.abspath(path)):
        DATABASE_URL = os.path.abspath(path)
        break

if not DATABASE_URL:
    # 如果都找不到，使用第一个存在的路径
    for path in possible_paths:
        if path:
            DATABASE_URL = os.path.abspath(path)
            print(f"⚠️ 会议数据库未找到，使用配置路径: {DATABASE_URL}")
            break

    if not DATABASE_URL:
        raise RuntimeError("会议室数据库路径未配置，请设置 MEETING_DB_PATH 环境变量")

print(f"✅ 会议审批数据库路径: {DATABASE_URL}")


def get_db():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    return conn


class ApprovalRequest(BaseModel):
    booking_id: int
    approval_type: str
    request_reason: str
    requester_id: Optional[int] = None
    requester_name: Optional[str] = None
    requester_phone: Optional[str] = None


class ApprovalAction(BaseModel):
    approval_id: int
    approval_result: str
    approval_reason: Optional[str] = None
    approver_name: Optional[str] = "管理员"


def log_approval_history(
    approval_id: int,
    action_type: str,
    action_by: str,
    action_reason: str = None,
    previous_status: str = None,
    new_status: str = None,
    detail: str = None,
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO meeting_approval_history
        (approval_id, action_type, action_by, action_time, action_reason, 
         previous_status, new_status, detail)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            approval_id,
            action_type,
            action_by,
            datetime.now(),
            action_reason,
            previous_status,
            new_status,
            detail,
        ),
    )
    conn.commit()
    conn.close()


@router.post("/api/meeting/approval/submit")
def submit_approval_request(request: ApprovalRequest):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM meeting_bookings WHERE id = ?", (request.booking_id,))
    booking = cursor.fetchone()

    if not booking:
        conn.close()
        raise HTTPException(status_code=404, detail="预约记录不存在")

    approval_no = (
        f"APR{datetime.now().strftime('%Y%m%d%H%M%S')}{request.booking_id:04d}"
    )

    cursor.execute(
        """
        INSERT INTO meeting_approval_requests
        (approval_no, approval_type, booking_id, booking_no, requester_id, 
         requester_name, requester_phone, request_reason, request_time, status,
         room_id, room_name, booking_date, start_time, end_time, total_fee, 
         created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            approval_no,
            request.approval_type,
            request.booking_id,
            booking["booking_no"],
            request.requester_id or booking["user_id"],
            request.requester_name or booking["user_name"],
            request.requester_phone or booking["user_phone"],
            request.request_reason,
            datetime.now(),
            "pending",
            booking["room_id"],
            booking.get("room_name"),
            booking["booking_date"],
            booking["start_time"],
            booking["end_time"],
            booking["total_fee"],
            datetime.now(),
            datetime.now(),
        ),
    )

    approval_id = cursor.lastrowid

    log_approval_history(
        approval_id=approval_id,
        action_type="submit",
        action_by=request.requester_name or "用户",
        action_reason=request.request_reason,
        previous_status=None,
        new_status="pending",
        detail=json.dumps(request.dict()),
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "审批申请已提交，请等待管理员审核",
        "data": {"approval_id": approval_id, "approval_no": approval_no},
    }


@router.post("/api/meeting/approval/approve")
def approve_request(action: ApprovalAction):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM meeting_approval_requests WHERE id = ?", (action.approval_id,)
    )
    approval = cursor.fetchone()

    if not approval:
        conn.close()
        raise HTTPException(status_code=404, detail="审批申请不存在")

    if approval["status"] != "pending":
        conn.close()
        raise HTTPException(status_code=400, detail="当前状态不允许审批")

    new_status = action.approval_result

    cursor.execute(
        """
        UPDATE meeting_approval_requests
        SET status = ?,
            approval_result = ?,
            approval_reason = ?,
            approver_name = ?,
            approval_time = ?,
            updated_at = ?
        WHERE id = ?
    """,
        (
            new_status,
            action.approval_result,
            action.approval_reason,
            action.approver_name,
            datetime.now(),
            datetime.now(),
            action.approval_id,
        ),
    )

    if action.approval_result == "approved":
        if approval["approval_type"] == "cancel":
            cursor.execute(
                """
                UPDATE meeting_bookings
                SET status = 'cancelled',
                    cancel_reason = ?,
                    cancelled_at = ?,
                    cancelled_by = ?,
                    updated_at = ?
                WHERE id = ?
            """,
                (
                    action.approval_reason,
                    datetime.now(),
                    action.approver_name,
                    datetime.now(),
                    approval["booking_id"],
                ),
            )

    log_approval_history(
        approval_id=action.approval_id,
        action_type="approve",
        action_by=action.approver_name,
        action_reason=action.approval_reason,
        previous_status="pending",
        new_status=new_status,
        detail=json.dumps(action.dict()),
    )

    conn.commit()
    conn.close()

    result_text = "已批准" if action.approval_result == "approved" else "已拒绝"
    return {"success": True, "message": f"审批{result_text}"}


@router.get("/api/meeting/approvals")
def get_approval_list(
    status: Optional[str] = None,
    approval_type: Optional[str] = None,
    requester_id: Optional[int] = None,
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

    if approval_type:
        conditions.append("approval_type = ?")
        params.append(approval_type)

    if requester_id:
        conditions.append("requester_id = ?")
        params.append(requester_id)

    if start_date:
        conditions.append("DATE(request_time) >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("DATE(request_time) <= ?")
        params.append(end_date)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    offset = (page - 1) * page_size

    count_query = (
        f"SELECT COUNT(*) as total FROM meeting_approval_requests WHERE {where_clause}"
    )
    cursor.execute(count_query, params)
    total = cursor.fetchone()["total"]

    query = f"""
        SELECT * FROM meeting_approval_requests
        WHERE {where_clause}
        ORDER BY request_time DESC
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    cursor.execute(query, params)
    approvals = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "success": True,
        "data": {
            "approvals": approvals,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }


@router.get("/api/meeting/approval/{approval_id}")
def get_approval_detail(approval_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM meeting_approval_requests WHERE id = ?", (approval_id,)
    )
    approval = cursor.fetchone()

    if not approval:
        conn.close()
        raise HTTPException(status_code=404, detail="审批申请不存在")

    cursor.execute(
        """
        SELECT * FROM meeting_approval_history
        WHERE approval_id = ?
        ORDER BY action_time DESC
    """,
        (approval_id,),
    )
    history = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "success": True,
        "data": {"approval": dict(approval), "history": history},
    }


@router.post("/api/meeting/approval/batch-approve")
def batch_approve_requests(approval_ids: List[int], approver_name: str = "管理员"):
    conn = get_db()
    cursor = conn.cursor()
    success_count = 0

    for approval_id in approval_ids:
        cursor.execute(
            "SELECT * FROM meeting_approval_requests WHERE id = ? AND status = 'pending'",
            (approval_id,),
        )
        approval = cursor.fetchone()

        if not approval:
            continue

        cursor.execute(
            """
            UPDATE meeting_approval_requests
            SET status = 'approved',
                approval_result = 'approved',
                approver_name = ?,
                approval_time = ?,
                updated_at = ?
            WHERE id = ?
        """,
            (approver_name, datetime.now(), datetime.now(), approval_id),
        )

        if approval["approval_type"] == "cancel":
            cursor.execute(
                """
                UPDATE meeting_bookings
                SET status = 'cancelled',
                    cancelled_at = ?,
                    cancelled_by = ?,
                    updated_at = ?
                WHERE id = ?
            """,
                (datetime.now(), approver_name, datetime.now(), approval["booking_id"]),
            )

        log_approval_history(
            approval_id=approval_id,
            action_type="batch_approve",
            action_by=approver_name,
            previous_status="pending",
            new_status="approved",
        )

        success_count += 1

    conn.commit()
    conn.close()

    return {"success": True, "message": f"成功批准{success_count}条审批申请"}
