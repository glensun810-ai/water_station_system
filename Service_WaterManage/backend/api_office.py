"""
Office Management API Routes - 办公室管理 API 路由
提供办公室管理、账户管理、充值记录等功能接口
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from config.database import get_db
from models.office import Office
from models.account import OfficeAccount
from models.recharge import OfficeRecharge
from models.pickup import OfficePickup
from models.product import Product


router = APIRouter(prefix="/api", tags=["office-management"])


# ==================== Pydantic Schemas ====================
class OfficeBase(BaseModel):
    name: str
    room_number: Optional[str] = None
    description: Optional[str] = None
    leader_name: Optional[str] = None
    water_user_count: int = 0
    is_common: int = 1


class OfficeCreate(OfficeBase):
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


class OfficeResponse(OfficeBase):
    id: int
    is_active: int = 1
    is_common: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user_count: int = 0
    primary_admin_id: Optional[int] = None
    primary_admin_name: Optional[str] = None
    leader_phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OfficeAccountBase(BaseModel):
    office_id: int
    office_name: str
    office_room_number: Optional[str] = None
    product_id: int
    product_name: str
    product_specification: Optional[str] = None
    reserved_qty: int = 0
    remaining_qty: int = 0
    reserved_person: Optional[str] = None
    reserved_person_id: Optional[int] = None

    # 负责人信息（新增）
    manager_name: Optional[str] = None
    manager_id: Optional[int] = None

    # 配置人数（新增）
    configured_count: int = 0

    note: Optional[str] = None


class OfficeAccountCreate(OfficeAccountBase):
    pass


class OfficeAccountUpdate(BaseModel):
    reserved_qty: Optional[int] = None
    remaining_qty: Optional[int] = None
    reserved_person: Optional[str] = None
    reserved_person_id: Optional[int] = None

    # 负责人信息（新增）
    manager_name: Optional[str] = None
    manager_id: Optional[int] = None

    # 配置人数（新增）
    configured_count: Optional[int] = None

    note: Optional[str] = None


class OfficeAccountResponse(OfficeAccountBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OfficeRechargeResponse(BaseModel):
    id: int
    office_id: int
    office_name: str
    office_room_number: Optional[str] = None
    product_id: int
    product_name: str
    product_specification: Optional[str] = None
    quantity: int
    unit_price: float
    total_amount: float
    recharge_person: Optional[str] = None
    note: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OfficePickupResponse(BaseModel):
    id: int
    office_id: int
    office_name: str
    office_room_number: Optional[str] = None
    product_id: int
    product_name: str
    product_specification: Optional[str] = None
    quantity: int
    pickup_person: Optional[str] = None
    pickup_person_id: Optional[int] = None
    pickup_time: datetime
    payment_mode: Optional[str] = "credit"
    settlement_status: Optional[str] = "pending"
    unit_price: Optional[float] = 0
    total_amount: Optional[float] = 0
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== API Endpoints ====================


# --- Office APIs ---
@router.get("/offices")
def get_offices(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    获取办公室列表

    - **skip**: 跳过记录数
    - **limit**: 返回记录数限制
    - **is_active**: 筛选启用/禁用的办公室
    """
    try:
        # 动态导入 User 模型
        import main

        query = db.query(Office)

        if is_active is not None:
            query = query.filter(Office.is_active == is_active)

        offices = query.offset(skip).limit(limit).all()

        # 为每个办公室添加实际用户数（通过 department 匹配）
        result = []
        for office in offices:
            # 获取主要管理员信息
            primary_admin_name = None
            primary_admin_id = getattr(office, "primary_admin_id", None)
            if primary_admin_id:
                primary_admin = (
                    db.query(main.User).filter(main.User.id == primary_admin_id).first()
                )
                if primary_admin:
                    primary_admin_name = primary_admin.name

            office_dict = {
                "id": office.id,
                "name": office.name,
                "room_number": office.room_number,
                "description": office.description,
                "leader_name": office.leader_name,
                "leader_phone": getattr(office, "leader_phone", None),
                "water_user_count": office.water_user_count,
                "is_common": office.is_common,
                "is_active": office.is_active,
                "primary_admin_id": primary_admin_id,
                "primary_admin_name": primary_admin_name,
                "created_at": office.created_at.isoformat()
                if office.created_at
                else None,
                "updated_at": office.updated_at.isoformat()
                if office.updated_at
                else None,
            }
            # 统计实际用户数（通过 department 匹配）
            user_count = (
                db.query(main.User)
                .filter(main.User.department == office.name, main.User.is_active == 1)
                .count()
            )
            office_dict["user_count"] = user_count
            result.append(office_dict)

        return result
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取办公室列表失败: {str(e)}")


@router.post("/offices")
def create_office(office: OfficeCreate, db: Session = Depends(get_db)):
    """
    创建办公室

    - 如果填写了负责人姓名且 create_leader_account=True，会自动创建对应账号
    - 默认密码：123456
    - 默认角色：办公室管理员
    - 自动绑定该办公室
    """
    import main
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # 检查办公室名称是否已存在
    existing = (
        db.query(Office)
        .filter(Office.name == office.name, Office.is_active == 1)
        .first()
    )

    if existing:
        raise HTTPException(status_code=400, detail="办公室名称已存在")

    # 创建办公室
    db_office = Office(
        name=office.name,
        room_number=office.room_number,
        description=office.description,
        leader_name=office.leader_name,
        water_user_count=office.water_user_count,
        is_active=1,
    )

    db.add(db_office)
    db.commit()
    db.refresh(db_office)

    # 自动创建负责人账号
    created_user_info = None
    if office.leader_name and office.create_leader_account:
        # 检查是否已存在同名用户
        existing_user = (
            db.query(main.User).filter(main.User.name == office.leader_name).first()
        )

        if existing_user:
            # 同名用户已存在，不创建，但提示
            created_user_info = {
                "created": False,
                "reason": "同名用户已存在",
                "existing_user_id": existing_user.id,
                "existing_user_name": existing_user.name,
                "existing_user_role": existing_user.role,
                "existing_user_office": existing_user.department,
            }
        else:
            # 创建新用户
            try:
                default_password = "123456"
                password_hash = pwd_context.hash(default_password)

                new_user = main.User(
                    name=office.leader_name,
                    password_hash=password_hash,
                    department=office.name,  # 绑定该办公室
                    role="office_admin",  # 办公室管理员
                    is_active=1,
                    balance_credit=0,
                    created_at=datetime.now(),
                )

                db.add(new_user)
                db.commit()
                db.refresh(new_user)

                # 添加到办公室管理员关联表
                try:
                    from sqlalchemy import text

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

    # 在响应中添加用户创建信息
    response = {
        "id": db_office.id,
        "name": db_office.name,
        "room_number": db_office.room_number,
        "description": db_office.description,
        "leader_name": db_office.leader_name,
        "water_user_count": db_office.water_user_count,
        "is_common": db_office.is_common,
        "is_active": db_office.is_active,
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


@router.get("/offices/{office_id}", response_model=OfficeResponse)
def get_office(office_id: int, db: Session = Depends(get_db)):
    """获取办公室详情"""
    office = db.query(Office).filter(Office.id == office_id).first()

    if not office:
        raise HTTPException(status_code=404, detail="办公室不存在")

    return office


@router.put("/offices/{office_id}")
def update_office(
    office_id: int, office_update: OfficeUpdate, db: Session = Depends(get_db)
):
    """
    更新办公室信息

    - 如果更新了负责人姓名且 create_leader_account=True，会自动创建对应账号
    - 默认密码：123456
    - 默认角色：普通用户
    - 自动绑定该办公室
    """
    import main
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    office = db.query(Office).filter(Office.id == office_id).first()

    if not office:
        raise HTTPException(status_code=404, detail="办公室不存在")

    # 只更新传入的字段，如果是部分更新则跳过名称检查
    update_data = office_update.model_dump(exclude_unset=True)

    # 如果name被修改了，才检查名称冲突
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

    # 记录是否需要创建负责人账号
    create_leader_account = update_data.pop("create_leader_account", False)
    new_leader_name = update_data.get("leader_name")

    # 更新传入的字段
    for key, value in update_data.items():
        if hasattr(office, key):
            setattr(office, value)

    office.updated_at = datetime.now()

    db.commit()
    db.refresh(office)

    # 自动创建负责人账号
    created_user_info = None
    if new_leader_name and create_leader_account:
        # 检查是否已存在同名用户
        existing_user = (
            db.query(main.User).filter(main.User.name == new_leader_name).first()
        )

        if existing_user:
            # 同名用户已存在，不创建，但提示
            created_user_info = {
                "created": False,
                "reason": "同名用户已存在",
                "existing_user_id": existing_user.id,
                "existing_user_name": existing_user.name,
                "existing_user_role": existing_user.role,
                "existing_user_office": existing_user.department,
            }
        else:
            # 创建新用户
            try:
                default_password = "123456"
                password_hash = pwd_context.hash(default_password)

                new_user = main.User(
                    name=new_leader_name,
                    password_hash=password_hash,
                    department=office.name,  # 绑定该办公室
                    role="office_admin",  # 办公室管理员
                    is_active=1,
                    balance_credit=0,
                    created_at=datetime.now(),
                )

                db.add(new_user)
                db.commit()
                db.refresh(new_user)

                # 添加到办公室管理员关联表
                try:
                    from sqlalchemy import text

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

    # 构建响应
    response = {
        "id": office.id,
        "name": office.name,
        "room_number": office.room_number,
        "description": office.description,
        "leader_name": office.leader_name,
        "water_user_count": office.water_user_count,
        "is_common": office.is_common,
        "is_active": office.is_active,
        "created_at": office.created_at.isoformat() if office.created_at else None,
        "updated_at": office.updated_at.isoformat() if office.updated_at else None,
    }

    if created_user_info:
        response["leader_account_info"] = created_user_info

    return response


@router.delete("/offices/{office_id}")
def delete_office(office_id: int, force: bool = False, db: Session = Depends(get_db)):
    """
    删除办公室
    - force=False: 软删除（仅禁用）
    - force=True: 强制删除（包括关联的账户数据）
    """
    office = db.query(Office).filter(Office.id == office_id).first()

    if not office:
        raise HTTPException(status_code=404, detail="办公室不存在")

    # 检查是否有关联的账户
    accounts = (
        db.query(OfficeAccount).filter(OfficeAccount.office_id == office_id).all()
    )
    account_count = len(accounts)

    if account_count > 0:
        if not force:
            # 返回账户信息，提示用户确认是否强制删除
            account_info = [
                {
                    "id": a.id,
                    "product_name": a.product_name,
                    "remaining_qty": a.remaining_qty,
                }
                for a in accounts
            ]
            return {
                "has_related_data": True,
                "account_count": account_count,
                "accounts": account_info,
                "message": f"该办公室下存在 {account_count} 个预付账户，删除将同时清除这些账户数据。",
                "requires_confirmation": True,
            }
        else:
            # 强制删除：先删除关联的账户
            for account in accounts:
                db.delete(account)
            db.flush()

    # 导入主应用中的User模型，检查是否有用户关联到此办公室
    import main

    related_users = (
        db.query(main.User)
        .filter(main.User.department == office.name, main.User.is_active == 1)
        .count()
    )

    if related_users > 0 and not force:
        return {
            "has_related_data": True,
            "user_count": related_users,
            "message": f"该办公室下有 {related_users} 个员工，删除将影响这些员工的部门归属。",
            "requires_confirmation": True,
        }
    elif related_users > 0 and force:
        # 强制删除时，只禁用用户而非删除
        pass

    # 执行删除
    db.delete(office)
    db.commit()

    return {"message": "办公室已删除", "deleted": True}


@router.post("/offices/batch-delete")
def batch_delete_offices(office_ids: List[int], db: Session = Depends(get_db)):
    """
    批量删除办公室（软删除）
    """
    deleted_count = 0
    errors = []

    for office_id in office_ids:
        office = db.query(Office).filter(Office.id == office_id).first()
        if not office:
            errors.append(f"办公室ID {office_id} 不存在")
            continue

        # 检查是否有关联的账户
        accounts = (
            db.query(OfficeAccount).filter(OfficeAccount.office_id == office_id).all()
        )
        if accounts:
            errors.append(f"办公室 '{office.name}' 存在关联账户，无法删除")
            continue

        # 软删除
        office.is_active = 0
        office.updated_at = datetime.now()
        deleted_count += 1

    db.commit()

    return {
        "deleted_count": deleted_count,
        "errors": errors if errors else None,
        "message": f"成功删除 {deleted_count} 个办公室",
    }


@router.post("/offices/batch-common")
def batch_set_common(
    office_ids: List[int], is_common: int = 1, db: Session = Depends(get_db)
):
    """
    批量设置常用/不常用状态
    """
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


@router.post("/offices/batch-active")
def batch_set_active(
    office_ids: List[int], is_active: int = 1, db: Session = Depends(get_db)
):
    """
    批量设置启用/禁用状态
    """
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


@router.get("/admin-users")
def get_admin_users(db: Session = Depends(get_db)):
    """
    获取管理员用户列表（role为admin或super_admin的用户）
    """
    import main

    users = (
        db.query(main.User)
        .filter(main.User.role.in_(["admin", "super_admin"]), main.User.is_active == 1)
        .all()
    )

    return [
        {"id": u.id, "name": u.name, "role": u.role, "department": u.department}
        for u in users
    ]


@router.get("/offices/{office_id}/users", response_model=List[dict])
def get_office_users(office_id: int, db: Session = Depends(get_db)):
    """
    获取办公室关联的用户列表

    返回所有活动用户，前端根据需要进行筛选
    """
    office = db.query(Office).filter(Office.id == office_id).first()

    if not office:
        raise HTTPException(status_code=404, detail="办公室不存在")

    # 动态导入 User 模型
    import main

    users = db.query(main.User).filter(main.User.is_active == 1).all()

    return [
        {"id": u.id, "name": u.name, "department": u.department, "role": u.role}
        for u in users
    ]


# --- Office Account APIs ---
@router.get("/office-accounts")
def get_office_accounts(
    office_id: Optional[int] = None,
    product_id: Optional[int] = None,
    status: Optional[str] = None,  # normal/low/empty
    search: Optional[str] = None,
    sort_by: str = "office_name",
    sort_order: str = "asc",
    db: Session = Depends(get_db),
):
    """
    获取办公室账户列表

    - **office_id**: 按办公室 ID 筛选
    - **product_id**: 按产品 ID 筛选
    - **status**: 按状态筛选 (normal: 正常, low: 库存不足, empty: 已用完)
    - **search**: 搜索办公室名称/房间号
    - **sort_by**: 排序字段
    - **sort_order**: 排序顺序 (asc/desc)
    """
    # 动态导入 User 模型
    import main

    query = db.query(OfficeAccount)

    if office_id is not None:
        query = query.filter(OfficeAccount.office_id == office_id)

    if product_id is not None:
        query = query.filter(OfficeAccount.product_id == product_id)

    # 按状态筛选
    if status == "normal":
        query = query.filter(OfficeAccount.remaining_qty > 10)
    elif status == "low":
        query = query.filter(
            OfficeAccount.remaining_qty > 0, OfficeAccount.remaining_qty <= 10
        )
    elif status == "empty":
        query = query.filter(OfficeAccount.remaining_qty == 0)

    # 搜索
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (OfficeAccount.office_name.like(search_pattern))
            | (OfficeAccount.office_room_number.like(search_pattern))
        )

    # 排序
    if sort_by == "office_name":
        if sort_order == "asc":
            query = query.order_by(OfficeAccount.office_name)
        else:
            query = query.order_by(OfficeAccount.office_name.desc())
    elif sort_by == "room_number":
        if sort_order == "asc":
            query = query.order_by(OfficeAccount.office_room_number)
        else:
            query = query.order_by(OfficeAccount.office_room_number.desc())
    elif sort_by == "reserved_qty":
        if sort_order == "asc":
            query = query.order_by(OfficeAccount.reserved_qty)
        else:
            query = query.order_by(OfficeAccount.reserved_qty.desc())
    elif sort_by == "remaining_qty":
        if sort_order == "asc":
            query = query.order_by(OfficeAccount.remaining_qty)
        else:
            query = query.order_by(OfficeAccount.remaining_qty.desc())
    elif sort_by == "created_at":
        if sort_order == "asc":
            query = query.order_by(OfficeAccount.created_at)
        else:
            query = query.order_by(OfficeAccount.created_at.desc())

    accounts = query.all()

    # 转换为包含用户信息的字典列表
    result = []
    for acc in accounts:
        acc_dict = {
            "id": acc.id,
            "office_id": acc.office_id,
            "office_name": acc.office_name,
            "office_room_number": acc.office_room_number,
            "product_id": acc.product_id,
            "product_name": acc.product_name,
            "product_specification": acc.product_specification,
            "reserved_qty": acc.reserved_qty,
            "remaining_qty": acc.remaining_qty,
            "used_qty": acc.reserved_qty - acc.remaining_qty,
            "reserved_person": acc.reserved_person,
            "reserved_person_id": acc.reserved_person_id,
            "manager_name": acc.manager_name,
            "manager_id": acc.manager_id,
            "configured_count": acc.configured_count,
            "note": acc.note,
            "created_at": acc.created_at.isoformat() if acc.created_at else None,
            "updated_at": acc.updated_at.isoformat() if acc.updated_at else None,
            # 状态
            "status": "empty"
            if acc.remaining_qty == 0
            else ("low" if acc.remaining_qty <= 10 else "normal"),
        }

        # 如果有 reserved_person_id，获取用户信息
        if acc.reserved_person_id:
            user = (
                db.query(main.User)
                .filter(main.User.id == acc.reserved_person_id)
                .first()
            )
            if user:
                acc_dict["reserved_person_name"] = user.name
                acc_dict["reserved_person_department"] = user.department

        result.append(acc_dict)

    return result


@router.post("/office-accounts", response_model=OfficeAccountResponse)
def create_office_account(account: OfficeAccountCreate, db: Session = Depends(get_db)):
    """
    创建办公室账户
    """
    # 检查办公室是否存在
    office = db.query(Office).filter(Office.id == account.office_id).first()
    if not office:
        raise HTTPException(status_code=404, detail="办公室不存在")

    # 检查产品是否存在
    product = db.query(Product).filter(Product.id == account.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    # 检查该办公室和产品的组合是否已存在
    existing = (
        db.query(OfficeAccount)
        .filter(
            OfficeAccount.office_id == account.office_id,
            OfficeAccount.product_id == account.product_id,
        )
        .first()
    )

    if existing:
        raise HTTPException(status_code=400, detail="该办公室已存在此产品的账户")

    # 创建账户
    db_account = OfficeAccount(
        office_id=account.office_id,
        office_name=account.office_name,
        office_room_number=account.office_room_number,
        product_id=account.product_id,
        product_name=account.product_name,
        product_specification=account.product_specification,
        reserved_qty=account.reserved_qty,
        remaining_qty=account.remaining_qty,
        reserved_person=account.reserved_person,
        reserved_person_id=account.reserved_person_id,
        manager_name=account.manager_name,
        manager_id=account.manager_id,
        configured_count=account.configured_count,
        note=account.note,
    )

    db.add(db_account)
    db.commit()
    db.refresh(db_account)

    return db_account


@router.get("/office-accounts/{account_id}", response_model=OfficeAccountResponse)
def get_office_account(account_id: int, db: Session = Depends(get_db)):
    """获取办公室账户详情"""
    account = db.query(OfficeAccount).filter(OfficeAccount.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")

    return account


@router.put("/office-accounts/{account_id}", response_model=OfficeAccountResponse)
def update_office_account(
    account_id: int, account_update: OfficeAccountUpdate, db: Session = Depends(get_db)
):
    """
    更新办公室账户
    """
    account = db.query(OfficeAccount).filter(OfficeAccount.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")

    # 更新字段
    if account_update.reserved_qty is not None:
        account.reserved_qty = account_update.reserved_qty

    if account_update.remaining_qty is not None:
        account.remaining_qty = account_update.remaining_qty

    if account_update.reserved_person is not None:
        account.reserved_person = account_update.reserved_person

    if account_update.reserved_person_id is not None:
        account.reserved_person_id = account_update.reserved_person_id

    # 更新负责人信息（新增）
    if account_update.manager_name is not None:
        account.manager_name = account_update.manager_name

    if account_update.manager_id is not None:
        account.manager_id = account_update.manager_id

    # 更新配置人数（新增）
    if account_update.configured_count is not None:
        account.configured_count = account_update.configured_count

    if account_update.note is not None:
        account.note = account_update.note

    account.updated_at = datetime.now()

    db.commit()
    db.refresh(account)

    return account


@router.delete("/office-accounts/{account_id}")
def delete_office_account(account_id: int, db: Session = Depends(get_db)):
    """
    删除办公室账户
    """
    account = db.query(OfficeAccount).filter(OfficeAccount.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")

    db.delete(account)
    db.commit()

    return {"message": "账户已删除"}


class OfficeAccountRechargeRequest(BaseModel):
    quantity: int  # 充值数量（正数）或扣减数量（负数）


@router.post("/office-accounts/{account_id}/recharge")
def recharge_office_account(
    account_id: int,
    request: OfficeAccountRechargeRequest,
    db: Session = Depends(get_db),
):
    """
    充值/扣减办公室账户桶数
    - quantity > 0: 充值（增加桶数）
    - quantity < 0: 扣减（减少桶数）
    """
    account = db.query(OfficeAccount).filter(OfficeAccount.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")

    new_remaining = account.remaining_qty + request.quantity

    if new_remaining < 0:
        raise HTTPException(
            status_code=400,
            detail=f"桶数不足，当前剩余 {account.remaining_qty} 桶，无法扣减 {-request.quantity} 桶",
        )

    # 允许充值后超过预留桶数（支持额外购买）
    # 如果需要严格限制，可以取消下面这行注释
    # if new_remaining > account.reserved_qty:
    #     new_remaining = account.reserved_qty

    account.remaining_qty = new_remaining
    account.updated_at = datetime.now()

    db.commit()
    db.refresh(account)

    return {
        "message": f"操作成功，剩余桶数: {account.remaining_qty}",
        "remaining_qty": account.remaining_qty,
        "used_qty": account.reserved_qty - account.remaining_qty,
    }


@router.post("/office-accounts/{account_id}/reset")
def reset_office_account(
    account_id: int,
    db: Session = Depends(get_db),
):
    """
    重置办公室账户（将剩余桶数重置为预留桶数）
    """
    account = db.query(OfficeAccount).filter(OfficeAccount.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")

    account.remaining_qty = account.reserved_qty
    account.updated_at = datetime.now()

    db.commit()
    db.refresh(account)

    return {
        "message": "账户已重置",
        "remaining_qty": account.remaining_qty,
        "reserved_qty": account.reserved_qty,
    }


# --- Products API (for office accounts) ---
@router.get("/products-for-office")
def get_products_for_office(db: Session = Depends(get_db)):
    """获取可用于办公室账户的产品列表"""
    products = db.query(Product).filter(Product.is_active == 1).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "specification": p.specification,
            "unit": p.unit,
            "price": p.price,
            "stock": p.stock,
        }
        for p in products
    ]


# --- Office Recharge APIs ---
@router.get("/office-recharges", response_model=List[OfficeRechargeResponse])
def get_office_recharges(
    office_id: Optional[int] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
):
    """
    获取办公室充值记录列表

    - **office_id**: 按办公室 ID 筛选
    - **sort_by**: 排序字段
    - **sort_order**: 排序顺序 (asc/desc)
    """
    query = db.query(OfficeRecharge)

    if office_id is not None:
        query = query.filter(OfficeRecharge.office_id == office_id)

    # 排序
    if sort_by == "created_at":
        if sort_order == "asc":
            query = query.order_by(OfficeRecharge.created_at)
        else:
            query = query.order_by(OfficeRecharge.created_at.desc())
    elif sort_by == "total_amount":
        if sort_order == "asc":
            query = query.order_by(OfficeRecharge.total_amount)
        else:
            query = query.order_by(OfficeRecharge.total_amount.desc())

    records = query.all()
    return records


@router.post("/office-recharges", response_model=OfficeRechargeResponse)
def create_office_recharge(
    recharge: OfficeAccountCreate, db: Session = Depends(get_db)
):
    """
    创建办公室充值记录
    """
    # 创建充值记录
    db_recharge = OfficeRecharge(
        office_id=recharge.office_id,
        office_name=recharge.office_name,
        office_room_number=recharge.office_room_number,
        product_id=recharge.product_id,
        product_name=recharge.product_name,
        product_specification=recharge.product_specification,
        quantity=recharge.reserved_qty,  # 使用 reserved_qty 作为 quantity
        unit_price=0,  # 需要根据产品获取
        total_amount=0,
        note=recharge.note,
    )

    db.add(db_recharge)
    db.commit()
    db.refresh(db_recharge)

    return db_recharge


# --- Office Pickup APIs ---
@router.get("/office-pickups", response_model=List[OfficePickupResponse])
def get_office_pickups(
    office_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    _t: Optional[int] = None,  # 时间戳参数，用于防止缓存
):
    """
    获取办公室领水记录列表

    - **office_id**: 按办公室 ID 筛选
    - **limit**: 返回记录数限制
    - **_t**: 时间戳参数，用于防止浏览器缓存
    """
    # 每次都创建新查询，确保获取最新数据
    db.expire_all()  # 清除SQLAlchemy会话缓存

    query = db.query(OfficePickup)

    if office_id is not None:
        query = query.filter(OfficePickup.office_id == office_id)

    pickups = query.order_by(OfficePickup.pickup_time.desc()).limit(limit).all()
    return pickups


@router.post("/office-pickup/{pickup_id}/settle")
def settle_office_pickup(pickup_id: int, db: Session = Depends(get_db)):
    """结算办公室领水记录"""
    pickup = db.query(OfficePickup).filter(OfficePickup.id == pickup_id).first()
    if not pickup:
        raise HTTPException(status_code=404, detail="领水记录不存在")

    pickup.settlement_status = "settled"
    db.commit()

    return {"message": "结算成功"}


@router.delete("/office-pickup/{pickup_id}")
def delete_office_pickup(pickup_id: int, db: Session = Depends(get_db)):
    """删除办公室领水记录"""
    pickup = db.query(OfficePickup).filter(OfficePickup.id == pickup_id).first()
    if not pickup:
        raise HTTPException(status_code=404, detail="领水记录不存在")

    # 恢复库存
    product = db.query(Product).filter(Product.id == pickup.product_id).first()
    if product and pickup.quantity:
        if product.stock is None:
            product.stock = 0
        before_stock = product.stock
        product.stock += pickup.quantity

        # 记录库存流水
        try:
            from main import InventoryRecord

            inventory_record = InventoryRecord(
                product_id=product.id,
                type="adjust",
                quantity=pickup.quantity,
                before_stock=before_stock,
                after_stock=product.stock,
                reference_type="office_pickup_delete",
                reference_id=pickup.id,
                note=f"删除领水记录回退库存: {pickup.office_name}",
            )
            db.add(inventory_record)
        except Exception as e:
            print(f"创建库存流水失败: {e}")

    db.delete(pickup)
    db.commit()

    return {"message": "删除成功"}


@router.post("/office-pickups/batch-delete")
def batch_delete_office_pickups(pickup_ids: List[int], db: Session = Depends(get_db)):
    """批量删除办公室领水记录"""
    deleted_count = 0
    from main import InventoryRecord

    for pickup_id in pickup_ids:
        pickup = db.query(OfficePickup).filter(OfficePickup.id == pickup_id).first()
        if pickup:
            # 恢复库存
            product = db.query(Product).filter(Product.id == pickup.product_id).first()
            if product and pickup.quantity:
                if product.stock is None:
                    product.stock = 0
                before_stock = product.stock
                product.stock += pickup.quantity

                # 记录库存流水
                try:
                    inventory_record = InventoryRecord(
                        product_id=product.id,
                        type="adjust",
                        quantity=pickup.quantity,
                        before_stock=before_stock,
                        after_stock=product.stock,
                        reference_type="office_pickup_batch_delete",
                        reference_id=pickup.id,
                        note=f"批量删除领水记录回退库存: {pickup.office_name}",
                    )
                    db.add(inventory_record)
                except Exception as e:
                    print(f"创建库存流水失败: {e}")

            db.delete(pickup)
            deleted_count += 1

    db.commit()
    return {
        "deleted_count": deleted_count,
        "message": f"成功删除 {deleted_count} 条记录",
    }


@router.post("/office-pickup/{pickup_id}/remind")
def remind_office_pickup(pickup_id: int, db: Session = Depends(get_db)):
    """提醒结算办公室领水记录"""
    pickup = db.query(OfficePickup).filter(OfficePickup.id == pickup_id).first()
    if not pickup:
        raise HTTPException(status_code=404, detail="领水记录不存在")

    return {"message": "提醒已发送"}


@router.post("/office-pickup/{pickup_id}/pay")
def user_pay_pickup(pickup_id: int, db: Session = Depends(get_db)):
    """用户标记已付款 - 将状态从待付款改为付款待确认"""
    pickup = db.query(OfficePickup).filter(OfficePickup.id == pickup_id).first()
    if not pickup:
        raise HTTPException(status_code=404, detail="领水记录不存在")

    if pickup.settlement_status != "pending":
        raise HTTPException(status_code=400, detail="只有待付款状态才能标记已付款")

    pickup.settlement_status = "applied"
    db.commit()

    return {"message": "已标记为已付款，等待确认"}


@router.post("/office-pickup/{pickup_id}/confirm")
def admin_confirm_payment(pickup_id: int, db: Session = Depends(get_db)):
    """管理员确认收款 - 支持pending和applied两种状态的确认
    - pending: 待付款状态，直接确认收款（用户可能线下已付款但未在系统操作）
    - applied: 付款待确认状态，确认后转为已结清
    """
    pickup = db.query(OfficePickup).filter(OfficePickup.id == pickup_id).first()
    if not pickup:
        raise HTTPException(status_code=404, detail="领水记录不存在")

    # 支持pending和applied两种状态的确认
    if pickup.settlement_status not in ["pending", "applied"]:
        raise HTTPException(
            status_code=400, detail="只有待付款或付款待确认状态才能确认收款"
        )

    pickup.settlement_status = "settled"
    db.commit()

    return {"message": "确认收款成功"}


@router.post("/office-pickups/batch-pay")
def batch_user_pay(pickup_ids: List[int], db: Session = Depends(get_db)):
    """批量用户标记已付款"""
    updated_count = 0
    for pickup_id in pickup_ids:
        pickup = db.query(OfficePickup).filter(OfficePickup.id == pickup_id).first()
        if pickup and pickup.settlement_status == "pending":
            pickup.settlement_status = "applied"
            updated_count += 1

    db.commit()
    return {
        "updated_count": updated_count,
        "message": f"成功标记 {updated_count} 条记录为已付款",
    }


@router.post("/office-pickups/batch-confirm")
def batch_admin_confirm(pickup_ids: List[int], db: Session = Depends(get_db)):
    """批量管理员确认收款 - 支持pending和applied两种状态"""
    updated_count = 0
    for pickup_id in pickup_ids:
        pickup = db.query(OfficePickup).filter(OfficePickup.id == pickup_id).first()
        if pickup and pickup.settlement_status in ["pending", "applied"]:
            pickup.settlement_status = "settled"
            updated_count += 1

    db.commit()
    return {
        "updated_count": updated_count,
        "message": f"成功确认 {updated_count} 条记录的收款",
    }


class AutoSettlementRequest(BaseModel):
    office_id: Optional[int] = None
    include_all_pending: bool = False


@router.post("/office-settlements/auto-generate")
def auto_generate_settlement(
    request: AutoSettlementRequest, db: Session = Depends(get_db)
):
    """
    自动生成结算单
    - 每月末自动将待付款记录合并生成结算单
    - 也支持手动触发生成结算单
    """
    from datetime import datetime
    import random
    import string

    # 获取所有待付款的领水记录
    query = db.query(OfficePickup).filter(OfficePickup.settlement_status == "pending")

    if request.office_id:
        query = query.filter(OfficePickup.office_id == request.office_id)

    pending_pickups = query.all()

    if not pending_pickups:
        return {"message": "没有待付款的记录，无需生成结算单", "count": 0}

    # 按办公室分组
    office_groups = {}
    for pickup in pending_pickups:
        key = pickup.office_id
        if key not in office_groups:
            office_groups[key] = []
        office_groups[key].append(pickup)

    # 为每个办公室生成结算单
    settlement_count = 0
    for office_id, pickups in office_groups.items():
        # 计算总金额和桶数
        total_amount = sum(p.total_amount or 0 for p in pickups)
        total_quantity = sum(p.quantity or 0 for p in pickups)

        # 生成结算单号
        now = datetime.now()
        settlement_no = f"SET{now.strftime('%Y%m%d')}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"

        # 获取办公室信息
        office = db.query(Office).filter(Office.id == office_id).first()
        office_name = office.name if office else "未知办公室"
        office_room_number = office.room_number if office else ""

        # 创建结算单记录
        # 这里我们直接更新领水记录状态为applied，表示已申请结算
        pickup_ids = [p.id for p in pickups]
        for pickup in pickups:
            pickup.settlement_status = "applied"

        settlement_count += 1

    db.commit()

    return {
        "message": f"成功生成 {settlement_count} 个结算单，共 {len(pending_pickups)} 条记录",
        "settlement_count": settlement_count,
        "record_count": len(pending_pickups),
    }


@router.post("/office-settlements/auto-generate-monthly")
def auto_generate_monthly_settlement(db: Session = Depends(get_db)):
    """
    每月末自动生成结算单（定时任务调用接口）
    将所有待付款记录按办公室合并生成结算单
    """
    from datetime import datetime
    import random
    import string

    # 获取所有待付款的领水记录
    pending_pickups = (
        db.query(OfficePickup).filter(OfficePickup.settlement_status == "pending").all()
    )

    if not pending_pickups:
        return {"message": "没有待付款的记录", "count": 0, "settlements": 0}

    # 按办公室分组
    office_groups = {}
    for pickup in pending_pickups:
        key = pickup.office_id
        if key not in office_groups:
            office_groups[key] = []
        office_groups[key].append(pickup)

    # 为每个办公室生成结算单
    settlement_count = 0
    settlement_details = []

    for office_id, pickups in office_groups.items():
        # 计算总金额和桶数
        total_amount = sum(p.total_amount or 0 for p in pickups)
        total_quantity = sum(p.quantity or 0 for p in pickups)

        # 生成结算单号
        now = datetime.now()
        settlement_no = f"SET{now.strftime('%Y%m')}-{office_id:03d}-{''.join(random.choices(string.digits, k=3))}"

        # 获取办公室信息
        office = db.query(Office).filter(Office.id == office_id).first()
        office_name = office.name if office else "未知办公室"
        office_room_number = office.room_number if office else ""

        # 更新领水记录状态为applied，表示已申请结算
        for pickup in pickups:
            pickup.settlement_status = "applied"

        settlement_count += 1
        settlement_details.append(
            {
                "settlement_no": settlement_no,
                "office_name": office_name,
                "total_amount": total_amount,
                "total_quantity": total_quantity,
            }
        )

    db.commit()

    return {
        "message": f"成功生成 {settlement_count} 个结算单",
        "count": len(pending_pickups),
        "settlements": settlement_count,
        "details": settlement_details,
    }


# ========== 结算单管理API ==========


@router.get("/admin/office-settlements", response_model=List[dict])
def get_admin_office_settlements(
    status: Optional[str] = None,
    office_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    获取所有办公室结算单（管理端）
    从OfficePickup表按office_id分组统计
    返回每个办公室的详细结算信息，包括各状态的数量和金额
    返回所有办公室（即使没有领水记录也返回，计数为0）
    """
    # 获取所有办公室（包括非活跃的，因为可能有历史记录）
    office_list = db.query(Office).all()

    results = []
    for office in office_list:
        # 获取该办公室的所有领水记录
        query = db.query(OfficePickup).filter(OfficePickup.office_id == office.id)
        pickups = query.all()

        # 按状态分类统计（即使没有记录也处理）
        pending = [p for p in pickups if p.settlement_status == "pending"]
        applied = [p for p in pickups if p.settlement_status == "applied"]
        confirmed = [p for p in pickups if p.settlement_status == "settled"]

        # 各状态金额统计
        pending_amount = sum(p.total_amount or 0 for p in pending)
        applied_amount = sum(p.total_amount or 0 for p in applied)
        confirmed_amount = sum(p.total_amount or 0 for p in confirmed)

        # 根据status参数过滤（仅当明确传入status参数时）
        if status and status != "all":
            if status == "pending" and len(pending) == 0:
                continue
            if status == "applied" and len(applied) == 0:
                continue
            if status == "confirmed" and len(confirmed) == 0:
                continue

        total_amount = sum(p.total_amount or 0 for p in pickups)
        total_quantity = sum(p.quantity or 0 for p in pickups)

        # 确定当前状态（优先级：confirmed > applied > pending）
        current_status = (
            "confirmed"
            if confirmed
            else ("applied" if applied else ("pending" if pending else "pending"))
        )

        # 获取最早未结清时间（pending或applied的最早时间）
        applied_pickups = applied + pending
        earliest_date = (
            min([p.pickup_time for p in applied_pickups if p.pickup_time])
            if applied_pickups
            else None
        )

        # 获取最晚确认时间
        latest_confirmed_date = (
            max([p.pickup_time for p in confirmed if p.pickup_time])
            if confirmed
            else None
        )

        # 获取pending状态的首次领水时间（最早时间）
        pending_first_time = (
            min([p.pickup_time for p in pending if p.pickup_time]) if pending else None
        )

        # 获取applied状态的用户提交时间（最早时间）
        applied_submit_time = (
            min([p.pickup_time for p in applied if p.pickup_time]) if applied else None
        )

        # 获取最后提醒时间（pending状态中最早的时间 - 作为提醒基准）
        last_reminder_time = (
            min([p.pickup_time for p in pending if p.pickup_time]) if pending else None
        )

        # 计算逾期天数（基于pending首次领水时间）
        overdue_days = 0
        if pending_first_time:
            overdue_days = (datetime.now() - pending_first_time).days

        results.append(
            {
                "id": office.id,
                "office_id": office.id,
                "office_name": office.name,
                "office_room_number": office.room_number,
                "settlement_no": f"SET{office.id}",
                "total_amount": total_amount,
                "total_quantity": total_quantity,
                "status": current_status,
                "applied_at": earliest_date.isoformat() if earliest_date else None,
                "confirmed_at": latest_confirmed_date.isoformat()
                if latest_confirmed_date
                else None,
                "applied_by": "系统",
                # 各状态详细统计
                "pending_count": len(pending),
                "pending_amount": pending_amount,
                "pending_first_time": pending_first_time.isoformat()
                if pending_first_time
                else None,
                "applied_count": len(applied),
                "applied_amount": applied_amount,
                "applied_submit_time": applied_submit_time.isoformat()
                if applied_submit_time
                else None,
                "confirmed_count": len(confirmed),
                "confirmed_amount": confirmed_amount,
                # 逾期信息
                "is_overdue": len(pending) > 0 and overdue_days > 30,
                "overdue_days": overdue_days,
                # 提醒信息
                "last_reminder_at": last_reminder_time.isoformat()
                if last_reminder_time
                else None,
                "pickups": [
                    {
                        "id": p.id,
                        "product_name": p.product_name,
                        "quantity": p.quantity,
                        "total_amount": p.total_amount,
                        "settlement_status": p.settlement_status,
                        "pickup_person": p.pickup_person,
                        "pickup_time": p.pickup_time.isoformat()
                        if p.pickup_time
                        else None,
                    }
                    for p in pickups[:20]
                ],
            }
        )

    return results


@router.get("/user/office-settlements", response_model=List[dict])
def get_user_office_settlements(
    office_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    获取用户自己的结算单列表
    """
    query = db.query(OfficePickup)

    if office_id:
        query = query.filter(OfficePickup.office_id == office_id)

    if status and status != "all":
        query = query.filter(OfficePickup.settlement_status == status)

    pickups = query.order_by(OfficePickup.pickup_time.desc()).all()

    # 按办公室分组
    office_groups = {}
    for pickup in pickups:
        key = pickup.office_id
        if key not in office_groups:
            office_groups[key] = {
                "office_id": key,
                "office_name": pickup.office_name,
                "office_room_number": pickup.office_room_number,
                "pickups": [],
            }
        office_groups[key]["pickups"].append(pickup)

    results = []
    for office_id, group in office_groups.items():
        pickups_list = group["pickups"]
        pending = [p for p in pickups_list if p.settlement_status == "pending"]
        applied = [p for p in pickups_list if p.settlement_status == "applied"]
        confirmed = [p for p in pickups_list if p.settlement_status == "settled"]

        total_amount = sum(p.total_amount or 0 for p in pickups_list)
        total_quantity = sum(p.quantity or 0 for p in pickups_list)

        current_status = (
            "confirmed"
            if confirmed
            else ("applied" if applied else ("pending" if pending else "pending"))
        )

        earliest_date = (
            min([p.pickup_time for p in pickups_list if p.pickup_time])
            if pickups_list
            else None
        )

        results.append(
            {
                "id": office_id,
                "office_id": office_id,
                "office_name": group["office_name"],
                "office_room_number": group["office_room_number"],
                "settlement_no": f"SET{office_id}",
                "total_amount": total_amount,
                "total_quantity": total_quantity,
                "status": current_status,
                "applied_at": earliest_date.isoformat() if earliest_date else None,
                "confirmed_at": None,
                "created_at": earliest_date.isoformat() if earliest_date else None,
            }
        )

    return results


@router.delete("/office-settlements/{office_id}/pickups")
def delete_office_settlement_pickups(
    office_id: int, status: Optional[str] = None, db: Session = Depends(get_db)
):
    """
    删除某个办公室的结算相关领水记录（超级管理员权限）
    - office_id: 办公室ID
    - status: 可选参数，指定删除特定状态的记录（pending/applied/settled）
    删除后数据不可恢复，请谨慎使用
    """
    query = db.query(OfficePickup).filter(OfficePickup.office_id == office_id)

    if status:
        query = query.filter(OfficePickup.settlement_status == status)

    pickups = query.all()
    deleted_count = len(pickups)

    for pickup in pickups:
        db.delete(pickup)

    db.commit()

    status_text = f"状态为{status}" if status else "所有"
    return {
        "deleted_count": deleted_count,
        "message": f"成功删除办公室ID {office_id} 的 {deleted_count} 条{status_text}领水记录",
    }
