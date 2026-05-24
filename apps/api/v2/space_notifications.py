"""
空间服务 - 站内通知API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from config.database import get_db
from models.user import User
from models.system import Notification
from depends.auth import get_current_user_required
from shared.schemas.space.response import ApiResponse

router = APIRouter(prefix="/space/notifications", tags=["空间通知"])


@router.get("", response_model=ApiResponse)
async def get_notifications(
    is_read: Optional[int] = Query(None, description="筛选已读/未读: 0未读 1已读"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """获取当前用户的通知列表"""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)

    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)

    total = query.count()
    items = (
        query.order_by(Notification.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "code": 200,
        "data": {
            "items": [
                {
                    "id": n.id,
                    "title": n.title,
                    "content": n.content,
                    "type": n.type,
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
                for n in items
            ],
            "total": total,
            "page": page,
            "limit": limit,
        },
        "message": "success",
    }


@router.get("/unread-count", response_model=ApiResponse)
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """获取未读通知数量"""
    count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == 0)
        .count()
    )
    return {"code": 200, "data": {"count": count}, "message": "success"}


@router.patch("/{notification_id}/read", response_model=ApiResponse)
async def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """标记单条通知为已读"""
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")

    notification.is_read = 1
    db.commit()
    return {"code": 200, "data": None, "message": "已标记为已读"}


@router.patch("/read-all", response_model=ApiResponse)
async def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """标记所有通知为已读"""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == 0,
    ).update({"is_read": 1})
    db.commit()
    return {"code": 200, "data": None, "message": "全部已标记为已读"}


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    content: str,
    notif_type: str = "info",
):
    """创建通知（供其他模块调用的工具函数）"""
    notification = Notification(
        user_id=user_id,
        title=title,
        content=content,
        type=notif_type,
        is_read=0,
    )
    db.add(notification)
    db.commit()
    return notification
