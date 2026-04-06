"""
用户管理API
提供用户的查看、编辑、分配办公室等功能
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/users", tags=["user_management"])


def get_db():
    """获取数据库会话"""
    from api_meeting import MeetingSessionLocal

    db = MeetingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== 数据模型 ====================


class UserUpdate(BaseModel):
    """更新用户"""

    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    office_id: Optional[int] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """用户响应"""

    id: int
    username: str
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    office_id: Optional[int]
    office_name: Optional[str]
    role: str
    is_active: bool
    balance: float = 0.0
    created_at: datetime


# ==================== API接口 ====================


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    office_id: Optional[int] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """获取用户列表"""
    try:
        query = """
            SELECT u.*, o.name as office_name,
                   COALESCE(a.balance, 0) as balance
            FROM admin_users u
            LEFT JOIN offices o ON u.office_id = o.id
            LEFT JOIN office_accounts a ON u.id = a.user_id
            WHERE 1=1
        """
        params = {}

        if office_id is not None:
            query += " AND u.office_id = :office_id"
            params["office_id"] = office_id

        if role is not None:
            query += " AND u.role = :role"
            params["role"] = role

        if is_active is not None:
            query += " AND u.is_active = :is_active"
            params["is_active"] = 1 if is_active else 0

        query += f" ORDER BY u.created_at DESC LIMIT :limit OFFSET :skip"
        params["limit"] = limit
        params["skip"] = skip

        result = db.execute(text(query), params)
        users = []

        for row in result:
            users.append(
                UserResponse(
                    id=row.id,
                    username=row.username,
                    name=row.username,
                    email=row.email,
                    phone=getattr(row, "phone", None),
                    office_id=row.office_id,
                    office_name=row.office_name,
                    role=row.role_id == 1 and "super_admin" or "staff",
                    is_active=bool(row.is_active),
                    balance=float(row.balance or 0),
                    created_at=row.created_at or datetime.now(),
                )
            )

        return users

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户列表失败: {str(e)}")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取用户详情"""
    try:
        result = db.execute(
            text("""
            SELECT u.*, o.name as office_name,
                   COALESCE(a.balance, 0) as balance
            FROM admin_users u
            LEFT JOIN offices o ON u.office_id = o.id
            LEFT JOIN office_accounts a ON u.id = a.user_id
            WHERE u.id = :id
        """),
            {"id": user_id},
        )

        user = result.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        return UserResponse(
            id=user.id,
            username=user.username,
            name=user.username,
            email=user.email,
            phone=getattr(user, "phone", None),
            office_id=user.office_id,
            office_name=user.office_name,
            role=user.role_id == 1 and "super_admin" or "staff",
            is_active=bool(user.is_active),
            balance=float(user.balance or 0),
            created_at=user.created_at or datetime.now(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户详情失败: {str(e)}")


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    """更新用户"""
    try:
        # 检查用户是否存在
        result = db.execute(
            text("SELECT * FROM admin_users WHERE id = :id"), {"id": user_id}
        )
        existing_user = result.fetchone()

        if not existing_user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 构建更新SQL
        updates = []
        params = {"id": user_id}

        if user.office_id is not None:
            updates.append("office_id = :office_id")
            params["office_id"] = user.office_id

        if user.role is not None:
            role_id = (
                1 if user.role == "super_admin" else (2 if user.role == "admin" else 3)
            )
            updates.append("role_id = :role_id")
            params["role_id"] = role_id

        if user.is_active is not None:
            updates.append("is_active = :is_active")
            params["is_active"] = 1 if user.is_active else 0

        if updates:
            sql = f"UPDATE admin_users SET {', '.join(updates)} WHERE id = :id"
            db.execute(text(sql), params)
            db.commit()

        # 获取更新后的用户
        return await get_user(user_id, db)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新用户失败: {str(e)}")


@router.get("/{user_id}/records")
async def get_user_records(
    user_id: int, limit: int = 50, db: Session = Depends(get_db)
):
    """获取用户使用记录"""
    try:
        # 获取领水记录
        water_records = db.execute(
            text("""
            SELECT 'water' as type, id, total_price as amount, status, created_at
            FROM office_pickups
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit
        """),
            {"user_id": user_id, "limit": limit},
        ).fetchall()

        # 获取会议室预约记录
        meeting_records = db.execute(
            text("""
            SELECT 'meeting' as type, id, total_amount as amount, status, created_at
            FROM bookings
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit
        """),
            {"user_id": user_id, "limit": limit},
        ).fetchall()

        records = []
        for record in water_records:
            records.append(
                {
                    "type": "water",
                    "id": record.id,
                    "amount": float(record.amount or 0),
                    "status": record.status,
                    "created_at": str(record.created_at),
                }
            )

        for record in meeting_records:
            records.append(
                {
                    "type": "meeting",
                    "id": record.id,
                    "amount": float(record.amount or 0),
                    "status": record.status,
                    "created_at": str(record.created_at),
                }
            )

        # 按时间排序
        records.sort(key=lambda x: x["created_at"], reverse=True)

        return {"records": records[:limit]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户记录失败: {str(e)}")
