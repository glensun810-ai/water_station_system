"""
用户管理API - 完整的用户管理功能
提供用户的增删改查、角色管理、办公室分配等功能
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from passlib.context import CryptContext

from config.database import get_db

router = APIRouter(prefix="/api/users", tags=["user_management"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==================== 数据模型 ====================


class UserCreate(BaseModel):
    name: str
    password: str
    department: Optional[str] = None
    role: str = "user"
    is_active: int = 1


class UserUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[int] = None
    password: Optional[str] = None


class UserBatchUpdate(BaseModel):
    user_ids: List[int]
    department: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[int] = None


# ==================== 统计API（放在路径参数之前）====================


@router.get("/stats/overview")
def get_user_stats(db: Session = Depends(get_db)):
    """获取用户统计概览"""
    try:
        import main

        total = db.query(main.User).count()
        super_admins = (
            db.query(main.User).filter(main.User.role == "super_admin").count()
        )
        admins = db.query(main.User).filter(main.User.role == "admin").count()
        office_admins = (
            db.query(main.User).filter(main.User.role == "office_admin").count()
        )
        users = db.query(main.User).filter(main.User.role == "user").count()
        active = db.query(main.User).filter(main.User.is_active == 1).count()
        inactive = db.query(main.User).filter(main.User.is_active == 0).count()

        # 新增：按用户类型统计
        internal_users = (
            db.query(main.User)
            .filter(getattr(main.User, "user_type", "internal") == "internal")
            .count()
        )
        external_users = (
            db.query(main.User)
            .filter(getattr(main.User, "user_type", "internal") == "external")
            .count()
        )

        return {
            "total": total,
            "super_admins": super_admins,
            "admins": admins,
            "office_admins": office_admins,
            "users": users,
            "active": active,
            "inactive": inactive,
            "internal_users": internal_users,
            "external_users": external_users,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")


@router.get("/check-name")
def check_username_availability(name: str, db: Session = Depends(get_db)):
    """
    检查用户名是否可用

    用于注册页面实时检查用户名是否已被注册
    """
    try:
        import main

        existing_user = db.query(main.User).filter(main.User.name == name).first()

        return {"available": existing_user is None, "name": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查用户名失败: {str(e)}")


@router.get("/admin-list")
def get_admin_list(db: Session = Depends(get_db)):
    """获取所有管理员列表（用于选择办公室管理员等场景）"""
    try:
        import main

        users = (
            db.query(main.User)
            .filter(
                main.User.role.in_(["super_admin", "admin", "office_admin"]),
                main.User.is_active == 1,
            )
            .all()
        )

        return [
            {"id": u.id, "name": u.name, "department": u.department, "role": u.role}
            for u in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取管理员列表失败: {str(e)}")


@router.get("/check-name/{name}")
def check_username(name: str, db: Session = Depends(get_db)):
    """
    检查用户名是否已存在

    用于创建办公室负责人时检查同名用户
    """
    try:
        import main

        user = db.query(main.User).filter(main.User.name == name).first()

        if user:
            return {
                "exists": True,
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "department": user.department,
                    "role": user.role,
                    "is_active": user.is_active,
                },
            }
        else:
            return {"exists": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查用户名失败: {str(e)}")


# ==================== 用户列表和CRUD ====================


@router.get("")
def list_users(
    skip: int = 0,
    limit: int = 200,
    role: Optional[str] = None,
    user_type: Optional[str] = None,
    department: Optional[str] = None,
    is_active: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取用户列表（包含user_type和详细信息）"""
    try:
        import main

        query = db.query(main.User)

        if role:
            query = query.filter(main.User.role == role)

        if user_type:
            # 使用 hasattr 和 getattr 安全访问 user_type 字段
            if hasattr(main.User, "user_type"):
                query = query.filter(main.User.user_type == user_type)
            else:
                # 如果字段不存在，跳过筛选
                pass

        if department:
            query = query.filter(main.User.department == department)

        if is_active is not None:
            query = query.filter(main.User.is_active == is_active)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    main.User.name.like(search_pattern),
                    main.User.department.like(search_pattern),
                    main.User.phone.like(search_pattern),
                    main.User.email.like(search_pattern),
                )
            )

        users = (
            query.order_by(main.User.created_at.desc()).offset(skip).limit(limit).all()
        )

        return [
            {
                "id": u.id,
                "name": u.name,
                "user_type": getattr(u, "user_type", "internal"),
                "phone": getattr(u, "phone", None),
                "email": getattr(u, "email", None),
                "company": getattr(u, "company", None),
                "department": u.department,
                "role": u.role,
                "is_active": u.is_active,
                "balance_credit": u.balance_credit or 0,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户列表失败: {str(e)}")


@router.post("")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    创建用户

    - 用户名必须唯一
    - 办公室管理员必须分配到具体办公室
    - 密码会自动加密存储
    """
    try:
        import main

        # 验证用户名是否已存在
        existing = db.query(main.User).filter(main.User.name == user.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="用户名已存在")

        # 验证办公室管理员必须分配办公室
        if user.role == "office_admin" and not user.department:
            raise HTTPException(
                status_code=400, detail="办公室管理员需要分配到具体办公室"
            )

        # 验证办公室是否存在
        if user.department:
            office = (
                db.query(main.Office)
                .filter(main.Office.name == user.department, main.Office.is_active == 1)
                .first()
            )
            if not office:
                raise HTTPException(
                    status_code=400, detail=f"办公室「{user.department}」不存在或已停用"
                )

        # 加密密码
        password_hash = pwd_context.hash(user.password) if user.password else None

        # 创建用户
        new_user = main.User(
            name=user.name,
            password_hash=password_hash,
            department=user.department,
            role=user.role,
            is_active=user.is_active,
            balance_credit=0,
            created_at=datetime.now(),
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # 如果是办公室管理员，自动添加到办公室管理员关联表
        if user.role == "office_admin" and user.department:
            try:
                from sqlalchemy import text

                office_id = (
                    db.query(main.Office.id)
                    .filter(main.Office.name == user.department)
                    .scalar()
                )

                if office_id:
                    db.execute(
                        text("""
                        INSERT OR IGNORE INTO office_admin_relations 
                        (office_id, user_id, is_primary, role_type, created_at)
                        VALUES (:office_id, :user_id, 0, 2, :created_at)
                    """),
                        {
                            "office_id": office_id,
                            "user_id": new_user.id,
                            "created_at": datetime.now(),
                        },
                    )
                    db.commit()
            except Exception as e:
                # 关联表添加失败不影响用户创建
                print(f"添加办公室管理员关联失败: {e}")

        return {
            "id": new_user.id,
            "name": new_user.name,
            "department": new_user.department,
            "role": new_user.role,
            "is_active": new_user.is_active,
            "balance_credit": new_user.balance_credit or 0,
            "created_at": new_user.created_at.isoformat()
            if new_user.created_at
            else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建用户失败: {str(e)}")


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取用户详情"""
    try:
        import main

        user = db.query(main.User).filter(main.User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        return {
            "id": user.id,
            "name": user.name,
            "department": user.department,
            "role": user.role,
            "is_active": user.is_active,
            "balance_credit": user.balance_credit or 0,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户详情失败: {str(e)}")


@router.put("/{user_id}")
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    """
    更新用户

    包含超级管理员保护逻辑：
    - 不能停用最后一个活跃的超级管理员
    - 不能降级最后一个超级管理员的角色
    """
    try:
        import main

        existing = db.query(main.User).filter(main.User.id == user_id).first()

        if not existing:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 检查是否是最后一个活跃的超级管理员
        is_last_active_super = (
            existing.role == "super_admin"
            and existing.is_active == 1
            and db.query(main.User)
            .filter(
                main.User.role == "super_admin",
                main.User.is_active == 1,
                main.User.id != user_id,
            )
            .count()
            == 0
        )

        # 保护：不能停用最后一个活跃的超级管理员
        if is_last_active_super and user.is_active == 0:
            raise HTTPException(
                status_code=400,
                detail="无法停用最后一个活跃的超级管理员。请先创建新的超级管理员。",
            )

        # 保护：不能降级最后一个活跃的超级管理员
        if (
            is_last_active_super
            and user.role is not None
            and user.role != "super_admin"
        ):
            raise HTTPException(
                status_code=400,
                detail="无法降级最后一个活跃的超级管理员。请先创建新的超级管理员。",
            )

        if user.name is not None:
            duplicate = (
                db.query(main.User)
                .filter(main.User.name == user.name, main.User.id != user_id)
                .first()
            )
            if duplicate:
                raise HTTPException(status_code=400, detail="用户名已存在")
            existing.name = user.name

        if user.department is not None:
            existing.department = user.department

        if user.role is not None:
            existing.role = user.role

        if user.is_active is not None:
            existing.is_active = user.is_active

        if user.password is not None:
            existing.password_hash = pwd_context.hash(user.password)

        existing.updated_at = datetime.now()
        db.commit()
        db.refresh(existing)

        return {
            "id": existing.id,
            "name": existing.name,
            "department": existing.department,
            "role": existing.role,
            "is_active": existing.is_active,
            "balance_credit": existing.balance_credit or 0,
            "created_at": existing.created_at.isoformat()
            if existing.created_at
            else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新用户失败: {str(e)}")


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """删除用户"""
    try:
        import main

        user = db.query(main.User).filter(main.User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        if user.role == "super_admin":
            super_admin_count = (
                db.query(main.User).filter(main.User.role == "super_admin").count()
            )
            if super_admin_count <= 1:
                raise HTTPException(
                    status_code=400, detail="不能删除最后一个超级管理员"
                )

        db.delete(user)
        db.commit()

        return {"message": "用户已删除"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除用户失败: {str(e)}")


@router.post("/{user_id}/activate")
def activate_user(user_id: int, db: Session = Depends(get_db)):
    """
    激活用户

    用于激活待激活状态的内部用户
    """
    try:
        import main

        user = db.query(main.User).filter(main.User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        if user.is_active == 1:
            raise HTTPException(status_code=400, detail="用户已经是激活状态")

        # 激活用户
        user.is_active = 1
        db.commit()

        return {
            "success": True,
            "message": "用户已激活",
            "user_id": user.id,
            "name": user.name,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"激活用户失败: {str(e)}")


@router.post("/batch/activate")
def batch_activate_users(user_ids: List[int], db: Session = Depends(get_db)):
    """
    批量激活用户
    """
    try:
        import main

        if not user_ids:
            raise HTTPException(status_code=400, detail="请选择要激活的用户")

        users = (
            db.query(main.User)
            .filter(main.User.id.in_(user_ids), main.User.is_active == 0)
            .all()
        )

        activated_count = 0
        for user in users:
            user.is_active = 1
            activated_count += 1

        db.commit()

        return {
            "success": True,
            "activated_count": activated_count,
            "message": f"成功激活 {activated_count} 个用户",
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量激活失败: {str(e)}")


@router.post("/batch")
def batch_update_users(data: UserBatchUpdate, db: Session = Depends(get_db)):
    """
    批量更新用户

    包含超级管理员保护逻辑：
    - 不能批量停用所有活跃的超级管理员
    - 不能批量降级所有超级管理员的角色
    """
    try:
        import main

        if not data.user_ids:
            raise HTTPException(status_code=400, detail="请选择要操作的用户")

        users = db.query(main.User).filter(main.User.id.in_(data.user_ids)).all()

        # 检查是否会影响超级管理员
        if data.is_active == 0 or (
            data.role is not None and data.role != "super_admin"
        ):
            # 获取选中的活跃超级管理员
            selected_active_super_admins = [
                u for u in users if u.role == "super_admin" and u.is_active == 1
            ]

            if selected_active_super_admins:
                # 获取未选中的活跃超级管理员数量
                unselected_active_super = (
                    db.query(main.User)
                    .filter(
                        main.User.role == "super_admin",
                        main.User.is_active == 1,
                        ~main.User.id.in_(data.user_ids),
                    )
                    .count()
                )

                if (
                    unselected_active_super == 0
                    and len(selected_active_super_admins) > 0
                ):
                    if data.is_active == 0:
                        raise HTTPException(
                            status_code=400,
                            detail="无法批量停用所有活跃的超级管理员。请至少保留一个活跃的超级管理员。",
                        )
                    if data.role is not None and data.role != "super_admin":
                        raise HTTPException(
                            status_code=400,
                            detail="无法批量降级所有超级管理员。请至少保留一个超级管理员。",
                        )

        for user in users:
            if data.department is not None:
                user.department = data.department
            if data.role is not None:
                user.role = data.role
            if data.is_active is not None:
                user.is_active = data.is_active
            user.updated_at = datetime.now()

        db.commit()

        return {"updated_count": len(users), "message": f"成功更新 {len(users)} 个用户"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量更新失败: {str(e)}")


@router.post("/batch-delete")
def batch_delete_users(user_ids: List[int], db: Session = Depends(get_db)):
    """批量删除用户"""
    try:
        import main

        if not user_ids:
            raise HTTPException(status_code=400, detail="请选择要删除的用户")

        super_admin_ids = (
            db.query(main.User.id)
            .filter(main.User.id.in_(user_ids), main.User.role == "super_admin")
            .all()
        )

        if super_admin_ids:
            super_admin_count = (
                db.query(main.User).filter(main.User.role == "super_admin").count()
            )
            if len(super_admin_ids) >= super_admin_count:
                raise HTTPException(status_code=400, detail="不能删除所有超级管理员")

        deleted_count = (
            db.query(main.User)
            .filter(main.User.id.in_(user_ids))
            .delete(synchronize_session=False)
        )
        db.commit()

        return {
            "deleted_count": deleted_count,
            "message": f"成功删除 {deleted_count} 个用户",
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量删除失败: {str(e)}")


@router.post("/{user_id}/reset-password")
def reset_user_password(
    user_id: int, new_password: str = "123456", db: Session = Depends(get_db)
):
    """重置用户密码"""
    try:
        import main

        user = db.query(main.User).filter(main.User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        user.password_hash = pwd_context.hash(new_password)
        user.updated_at = datetime.now()
        db.commit()

        return {"message": f"密码已重置为: {new_password}"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"重置密码失败: {str(e)}")
