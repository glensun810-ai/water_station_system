"""
旧版API兼容路由
处理旧版前端中 /api/v1/users 等路径，映射到统一的system路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from config.database import get_db
from models.user import User
from depends.auth import get_current_user, get_admin_user, get_super_admin_user

router = APIRouter(tags=["旧版兼容"])

# 导入system路由的处理函数
from apps.api.v1.system import (
    get_users,
    get_user,
    update_user,
    delete_user,
    create_user,
    batch_update_users,
    batch_delete_users,
    get_user_stats,
    get_offices,
    reset_user_password,
    get_user_login_history,
    get_user_managed_offices_api,
    update_user_managed_offices_api,
    get_office_admins_api,
)


@router.get("/users/stats/overview")
def legacy_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    return get_user_stats(db, current_user)


@router.get("/users")
def legacy_get_users(
    page: int = Query(1),
    limit: int = Query(50),
    role: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_users(page, limit, role, department, is_active, search, db, current_user)


@router.get("/users/{user_id}")
def legacy_get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    return get_user(user_id, db, current_user)


@router.put("/users/{user_id}")
def legacy_update_user(
    user_id: int,
    user_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    return update_user(user_id, user_data, db, current_user)


@router.delete("/users/{user_id}")
def legacy_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin_user),
):
    return delete_user(user_id, db, current_user)


@router.post("/users")
def legacy_create_user(
    user_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    return create_user(user_data, db, current_user)


@router.post("/users/batch")
def legacy_batch_update_users(
    batch_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    return batch_update_users(batch_data, db, current_user)


@router.post("/users/batch-delete")
def legacy_batch_delete_users(
    batch_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin_user),
):
    return batch_delete_users(batch_data, db, current_user)


@router.post("/users/{user_id}/reset-password")
def legacy_reset_password(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    return reset_user_password(user_id, db, current_user)


@router.get("/users/{user_id}/login-history")
def legacy_get_login_history(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    return get_user_login_history(user_id, db, current_user)


# ==================== 管理端批量操作（旧版路径） ====================


@router.post("/admin/users/batch-status")
def legacy_admin_batch_update_users(
    batch_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    return batch_update_users(batch_data, db, current_user)


@router.post("/admin/users/batch-delete")
def legacy_admin_batch_delete_users(
    batch_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin_user),
):
    return batch_delete_users(batch_data, db, current_user)


# ==================== 仪表盘概览 ====================


@router.get("/admin/dashboard/summary")
def legacy_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """仪表盘概览数据"""
    from models.office import Office
    from models.product import Product
    from models.pickup import OfficePickup
    from models.user import User as UserModel

    total_offices = db.query(Office).filter(Office.is_active == True).count()
    total_products = db.query(Product).filter(Product.is_active == True).count()
    total_users = db.query(UserModel).filter(UserModel.is_active == True).count()
    today_pickups = db.query(OfficePickup).filter(
        OfficePickup.is_deleted == False
    ).count()

    return {
        "total_offices": total_offices,
        "total_products": total_products,
        "total_users": total_users,
        "today_pickups": today_pickups,
    }


@router.get("/admin/dashboard/quick-stats")
def legacy_quick_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """快速统计数据"""
    return legacy_dashboard_summary(db, current_user)
