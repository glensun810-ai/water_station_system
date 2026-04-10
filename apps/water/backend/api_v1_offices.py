"""
办公室管理API - v1版本
为前端 offices.html 页面提供完整的办公室管理接口
路径: /api/v1/offices
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from config.database import get_db
from models.office import Office
from models.user import User

router = APIRouter(prefix="/api/v1/offices", tags=["办公室管理"])


class OfficeCreate(BaseModel):
    name: str
    room_number: Optional[str] = None
    description: Optional[str] = None
    leader_name: Optional[str] = None
    water_user_count: int = 0
    is_common: int = 1
    primary_admin_id: Optional[int] = None
    create_leader_account: bool = False


class OfficeUpdate(BaseModel):
    name: Optional[str] = None
    room_number: Optional[str] = None
    description: Optional[str] = None
    leader_name: Optional[str] = None
    leader_phone: Optional[str] = None
    water_user_count: Optional[int] = None
    is_common: Optional[int] = None
    is_active: Optional[int] = None
    primary_admin_id: Optional[int] = None
    create_leader_account: bool = False


class OfficeAdminCreate(BaseModel):
    office_id: int
    user_id: int
    is_primary: int = 0
    role_type: int = 1


@router.get("")
def get_offices(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    获取办公室列表 - 返回完整信息
    包括 user_count, water_user_count, is_common, primary_admin_name 等
    """
    try:
        query = db.query(Office)

        if is_active is not None:
            query = query.filter(Office.is_active == is_active)

        offices = query.offset(skip).limit(limit).all()

        result = []
        for office in offices:
            primary_admin_name = None
            primary_admin_id = getattr(office, "primary_admin_id", None)
            if primary_admin_id:
                primary_admin = (
                    db.query(User).filter(User.id == primary_admin_id).first()
                )
                if primary_admin:
                    primary_admin_name = primary_admin.name

            user_count = (
                db.query(User)
                .filter(User.department == office.name, User.is_active == 1)
                .count()
            )

            office_dict = {
                "id": office.id,
                "name": office.name,
                "room_number": office.room_number,
                "description": office.description,
                "leader_name": office.leader_name,
                "leader_phone": getattr(office, "leader_phone", None),
                "water_user_count": office.water_user_count or 0,
                "is_common": office.is_common or 1,
                "is_active": office.is_active or 1,
                "primary_admin_id": primary_admin_id,
                "primary_admin_name": primary_admin_name,
                "user_count": user_count,
                "created_at": office.created_at.isoformat()
                if office.created_at
                else None,
                "updated_at": office.updated_at.isoformat()
                if office.updated_at
                else None,
            }
            result.append(office_dict)

        return result
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取办公室列表失败: {str(e)}")


@router.get("/{office_id}")
def get_office(office_id: int, db: Session = Depends(get_db)):
    """获取单个办公室详情"""
    office = db.query(Office).filter(Office.id == office_id).first()

    if not office:
        raise HTTPException(status_code=404, detail="办公室不存在")

    primary_admin_name = None
    primary_admin_id = getattr(office, "primary_admin_id", None)
    if primary_admin_id:
        primary_admin = db.query(User).filter(User.id == primary_admin_id).first()
        if primary_admin:
            primary_admin_name = primary_admin.name

    user_count = (
        db.query(User)
        .filter(User.department == office.name, User.is_active == 1)
        .count()
    )

    return {
        "id": office.id,
        "name": office.name,
        "room_number": office.room_number,
        "description": office.description,
        "leader_name": office.leader_name,
        "leader_phone": getattr(office, "leader_phone", None),
        "water_user_count": office.water_user_count or 0,
        "is_common": office.is_common or 1,
        "is_active": office.is_active or 1,
        "primary_admin_id": primary_admin_id,
        "primary_admin_name": primary_admin_name,
        "user_count": user_count,
        "created_at": office.created_at.isoformat() if office.created_at else None,
        "updated_at": office.updated_at.isoformat() if office.updated_at else None,
    }


@router.post("")
def create_office(office: OfficeCreate, db: Session = Depends(get_db)):
    """创建办公室"""
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    existing = (
        db.query(Office)
        .filter(Office.name == office.name, Office.is_active == 1)
        .first()
    )

    if existing:
        raise HTTPException(status_code=400, detail="办公室名称已存在")

    db_office = Office(
        name=office.name,
        room_number=office.room_number,
        description=office.description,
        leader_name=office.leader_name,
        water_user_count=office.water_user_count,
        is_common=office.is_common,
        is_active=1,
        primary_admin_id=office.primary_admin_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.add(db_office)
    db.commit()
    db.refresh(db_office)

    created_user_info = None
    if office.leader_name and office.create_leader_account:
        existing_user = db.query(User).filter(User.name == office.leader_name).first()

        if existing_user:
            created_user_info = {
                "created": False,
                "reason": "同名用户已存在",
                "existing_user_id": existing_user.id,
                "existing_user_name": existing_user.name,
                "existing_user_role": existing_user.role,
                "existing_user_office": existing_user.department,
            }
        else:
            try:
                default_password = "123456"
                password_hash = pwd_context.hash(default_password)

                new_user = User(
                    name=office.leader_name,
                    password_hash=password_hash,
                    department=office.name,
                    role="office_admin",
                    is_active=1,
                    balance_credit=0,
                    created_at=datetime.now(),
                )

                db.add(new_user)
                db.commit()
                db.refresh(new_user)

                try:
                    db.execute(
                        text("""
                        INSERT OR IGNORE INTO office_admin_relations 
                        (office_id, user_id, is_primary, role_type, created_at)
                        VALUES (:office_id, :user_id, 1, 1, :created_at)
                    """),
                        {
                            "office_id": db_office.id,
                            "user_id": new_user.id,
                            "created_at": datetime.now(),
                        },
                    )
                    db.commit()
                except Exception as e:
                    print(f"添加办公室管理员关联失败: {e}")

                created_user_info = {
                    "created": True,
                    "user_id": new_user.id,
                    "user_name": new_user.name,
                    "default_password": default_password,
                    "office_name": office.name,
                    "role": "office_admin",
                    "role_name": "办公室管理员",
                    "permissions": [
                        "审核该办公室新用户注册",
                        "管理该办公室用户",
                        "查看该办公室统计数据",
                    ],
                }
            except Exception as e:
                db.rollback()
                created_user_info = {
                    "created": False,
                    "reason": f"创建用户失败: {str(e)}",
                }

    response = {
        "id": db_office.id,
        "name": db_office.name,
        "room_number": db_office.room_number,
        "description": db_office.description,
        "leader_name": db_office.leader_name,
        "water_user_count": db_office.water_user_count,
        "is_common": db_office.is_common,
        "is_active": db_office.is_active,
        "primary_admin_id": db_office.primary_admin_id,
        "created_at": db_office.created_at.isoformat()
        if db_office.created_at
        else None,
        "updated_at": db_office.updated_at.isoformat()
        if db_office.updated_at
        else None,
    }

    if created_user_info:
        response["leader_account_info"] = created_user_info

    return response


@router.put("/{office_id}")
def update_office(
    office_id: int, office_update: OfficeUpdate, db: Session = Depends(get_db)
):
    """更新办公室信息"""
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    office = db.query(Office).filter(Office.id == office_id).first()

    if not office:
        raise HTTPException(status_code=404, detail="办公室不存在")

    update_data = office_update.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] != office.name:
        existing = (
            db.query(Office)
            .filter(
                Office.name == update_data["name"],
                Office.id != office_id,
                Office.is_active == 1,
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="办公室名称已存在")

    create_leader_account = update_data.pop("create_leader_account", False)
    new_leader_name = update_data.get("leader_name")

    for key, value in update_data.items():
        if hasattr(office, key):
            setattr(office, key, value)

    office.updated_at = datetime.now()

    db.commit()
    db.refresh(office)

    created_user_info = None
    if new_leader_name and create_leader_account:
        existing_user = db.query(User).filter(User.name == new_leader_name).first()

        if existing_user:
            created_user_info = {
                "created": False,
                "reason": "同名用户已存在",
                "existing_user_id": existing_user.id,
                "existing_user_name": existing_user.name,
                "existing_user_role": existing_user.role,
                "existing_user_office": existing_user.department,
            }
        else:
            try:
                default_password = "123456"
                password_hash = pwd_context.hash(default_password)

                new_user = User(
                    name=new_leader_name,
                    password_hash=password_hash,
                    department=office.name,
                    role="office_admin",
                    is_active=1,
                    balance_credit=0,
                    created_at=datetime.now(),
                )

                db.add(new_user)
                db.commit()
                db.refresh(new_user)

                try:
                    db.execute(
                        text("""
                        INSERT OR IGNORE INTO office_admin_relations 
                        (office_id, user_id, is_primary, role_type, created_at)
                        VALUES (:office_id, :user_id, 1, 1, :created_at)
                    """),
                        {
                            "office_id": office.id,
                            "user_id": new_user.id,
                            "created_at": datetime.now(),
                        },
                    )
                    db.commit()
                except Exception as e:
                    print(f"添加办公室管理员关联失败: {e}")

                created_user_info = {
                    "created": True,
                    "user_id": new_user.id,
                    "user_name": new_user.name,
                    "default_password": default_password,
                    "office_name": office.name,
                    "role": "office_admin",
                    "role_name": "办公室管理员",
                    "permissions": [
                        "审核该办公室新用户注册",
                        "管理该办公室用户",
                        "查看该办公室统计数据",
                    ],
                }
            except Exception as e:
                db.rollback()
                created_user_info = {
                    "created": False,
                    "reason": f"创建用户失败: {str(e)}",
                }

    response = {
        "id": office.id,
        "name": office.name,
        "room_number": office.room_number,
        "description": office.description,
        "leader_name": office.leader_name,
        "water_user_count": office.water_user_count,
        "is_common": office.is_common,
        "is_active": office.is_active,
        "primary_admin_id": office.primary_admin_id,
        "created_at": office.created_at.isoformat() if office.created_at else None,
        "updated_at": office.updated_at.isoformat() if office.updated_at else None,
    }

    if created_user_info:
        response["leader_account_info"] = created_user_info

    return response


@router.delete("/{office_id}")
def delete_office(office_id: int, force: bool = False, db: Session = Depends(get_db)):
    """删除办公室"""
    office = db.query(Office).filter(Office.id == office_id).first()

    if not office:
        raise HTTPException(status_code=404, detail="办公室不存在")

    related_users = (
        db.query(User)
        .filter(User.department == office.name, User.is_active == 1)
        .count()
    )

    if related_users > 0 and not force:
        return {
            "has_related_data": True,
            "user_count": related_users,
            "message": f"该办公室下有 {related_users} 个员工，删除将影响这些员工的部门归属。",
            "requires_confirmation": True,
        }

    db.delete(office)
    db.commit()

    return {"message": "办公室已删除", "deleted": True}


@router.post("/batch-delete")
def batch_delete_offices(office_ids: List[int], db: Session = Depends(get_db)):
    """批量删除办公室"""
    deleted_count = 0
    errors = []

    for office_id in office_ids:
        office = db.query(Office).filter(Office.id == office_id).first()
        if not office:
            errors.append(f"办公室ID {office_id} 不存在")
            continue

        related_users = (
            db.query(User)
            .filter(User.department == office.name, User.is_active == 1)
            .count()
        )

        if related_users > 0:
            errors.append(f"办公室 '{office.name}' 存在关联用户，无法删除")
            continue

        office.is_active = 0
        office.updated_at = datetime.now()
        deleted_count += 1

    db.commit()

    return {
        "deleted_count": deleted_count,
        "errors": errors if errors else None,
        "message": f"成功删除 {deleted_count} 个办公室",
    }


@router.post("/batch-common")
def batch_set_common(
    office_ids: List[int], is_common: int = 1, db: Session = Depends(get_db)
):
    """批量设置常用/不常用状态"""
    updated_count = 0

    for office_id in office_ids:
        office = db.query(Office).filter(Office.id == office_id).first()
        if office:
            office.is_common = is_common
            office.updated_at = datetime.now()
            updated_count += 1

    db.commit()

    status_text = "常用" if is_common == 1 else "不常用"
    return {
        "updated_count": updated_count,
        "message": f"成功设置 {updated_count} 个办公室为 {status_text}",
    }


@router.post("/batch-active")
def batch_set_active(
    office_ids: List[int], is_active: int = 1, db: Session = Depends(get_db)
):
    """批量设置启用/禁用状态"""
    updated_count = 0

    for office_id in office_ids:
        office = db.query(Office).filter(Office.id == office_id).first()
        if office:
            office.is_active = is_active
            office.updated_at = datetime.now()
            updated_count += 1

    db.commit()

    status_text = "启用" if is_active == 1 else "禁用"
    return {
        "updated_count": updated_count,
        "message": f"成功设置 {updated_count} 个办公室为 {status_text}",
    }


@router.get("/{office_id}/users")
def get_office_users(office_id: int, db: Session = Depends(get_db)):
    """获取办公室关联的用户列表"""
    office = db.query(Office).filter(Office.id == office_id).first()

    if not office:
        raise HTTPException(status_code=404, detail="办公室不存在")

    users = (
        db.query(User).filter(User.department == office.name, User.is_active == 1).all()
    )

    return [
        {"id": u.id, "name": u.name, "department": u.department, "role": u.role}
        for u in users
    ]


@router.get("/admin-users")
def get_admin_users(db: Session = Depends(get_db)):
    """获取管理员用户列表"""
    users = (
        db.query(User)
        .filter(User.role.in_(["admin", "super_admin"]), User.is_active == 1)
        .all()
    )

    return [
        {"id": u.id, "name": u.name, "role": u.role, "department": u.department}
        for u in users
    ]


@router.get("/office-admins/candidates")
def get_office_admin_candidates(db: Session = Depends(get_db)):
    """获取可设置为办公室管理员的候选人列表"""
    users = (
        db.query(User)
        .filter(
            User.role.in_(["user", "office_admin", "admin", "super_admin"]),
            User.is_active == 1,
        )
        .all()
    )

    role_names = {
        "super_admin": "超级管理员",
        "admin": "系统管理员",
        "office_admin": "办公室管理员",
        "user": "普通用户",
    }

    return [
        {
            "id": u.id,
            "name": u.name,
            "role": u.role,
            "role_name": role_names.get(u.role, u.role),
            "department": u.department,
        }
        for u in users
    ]


@router.get("/office-admins/office/{office_id}")
def get_office_admins(office_id: int, db: Session = Depends(get_db)):
    """获取办公室的管理员列表"""
    try:
        results = db.execute(
            text("""
            SELECT oar.id, oar.office_id, oar.user_id, oar.is_primary, oar.role_type,
                   u.name as user_name, u.role, u.department
            FROM office_admin_relations oar
            LEFT JOIN user u ON oar.user_id = u.id
            WHERE oar.office_id = :office_id
        """),
            {"office_id": office_id},
        ).fetchall()

        role_type_names = {1: "负责人", 2: "行政对接人", 3: "其他管理员"}
        role_names = {
            "super_admin": "超级管理员",
            "admin": "系统管理员",
            "office_admin": "办公室管理员",
            "user": "普通用户",
        }

        return [
            {
                "id": r.id,
                "office_id": r.office_id,
                "user_id": r.user_id,
                "user_name": r.user_name,
                "is_primary": r.is_primary,
                "role_type": r.role_type,
                "role_type_name": role_type_names.get(r.role_type, "管理员"),
                "role": r.role,
                "role_name": role_names.get(r.role, r.role),
                "department": r.department,
            }
            for r in results
        ]
    except Exception as e:
        return []


@router.post("/office-admins")
def add_office_admin(admin: OfficeAdminCreate, db: Session = Depends(get_db)):
    """添加办公室管理员"""
    try:
        db.execute(
            text("""
            INSERT OR IGNORE INTO office_admin_relations 
            (office_id, user_id, is_primary, role_type, created_at)
            VALUES (:office_id, :user_id, :is_primary, :role_type, :created_at)
        """),
            {
                "office_id": admin.office_id,
                "user_id": admin.user_id,
                "is_primary": admin.is_primary,
                "role_type": admin.role_type,
                "created_at": datetime.now(),
            },
        )
        db.commit()

        return {"message": "管理员添加成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"添加失败: {str(e)}")


@router.put("/office-admins/{admin_id}")
def update_office_admin(
    admin_id: int, is_primary: int = 0, db: Session = Depends(get_db)
):
    """更新办公室管理员"""
    try:
        if is_primary:
            db.execute(
                text("""
                UPDATE office_admin_relations 
                SET is_primary = 0
                WHERE office_id = (SELECT office_id FROM office_admin_relations WHERE id = :admin_id)
            """),
                {"admin_id": admin_id},
            )

        db.execute(
            text("""
            UPDATE office_admin_relations 
            SET is_primary = :is_primary
            WHERE id = :admin_id
        """),
            {"admin_id": admin_id, "is_primary": is_primary},
        )
        db.commit()

        return {"message": "更新成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新失败: {str(e)}")


@router.delete("/office-admins/{admin_id}")
def remove_office_admin(admin_id: int, db: Session = Depends(get_db)):
    """移除办公室管理员"""
    try:
        db.execute(
            text("""
            DELETE FROM office_admin_relations WHERE id = :admin_id
        """),
            {"admin_id": admin_id},
        )
        db.commit()

        return {"message": "移除成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"移除失败: {str(e)}")


@router.get("/users/check-name/{name}")
def check_user_name(name: str, db: Session = Depends(get_db)):
    """检查用户名是否已存在"""
    user = db.query(User).filter(User.name == name).first()

    if user:
        return {
            "exists": True,
            "user": {
                "id": user.id,
                "name": user.name,
                "role": user.role,
                "department": user.department,
            },
        }

    return {"exists": False}
