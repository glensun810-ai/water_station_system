"""
办公室管理员API
支持一个办公室配置多个管理员
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/office-admins", tags=["office_admin_management"])


def get_db():
    """获取数据库会话"""
    from config.database import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== 数据模型 ====================


class OfficeAdminCreate(BaseModel):
    """添加办公室管理员"""

    office_id: int
    user_id: int
    is_primary: int = 0
    role_type: int = 1


class OfficeAdminResponse(BaseModel):
    """办公室管理员响应"""

    id: int
    office_id: int
    office_name: str
    user_id: int
    user_name: str
    is_primary: int
    role_type: int
    role_type_name: str
    created_at: Optional[datetime] = None


# ==================== 初始化表 ====================


def init_office_admin_table(db: Session):
    """初始化办公室管理员关联表"""
    db.execute(
        text("""
        CREATE TABLE IF NOT EXISTS office_admin_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            office_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            is_primary INTEGER DEFAULT 0,
            role_type INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(office_id, user_id)
        )
    """)
    )
    db.commit()


# ==================== API接口 ====================


@router.get("/office/{office_id}")
def get_office_admins(office_id: int, db: Session = Depends(get_db)):
    """
    获取办公室的所有管理员

    返回该办公室配置的所有管理员列表
    """
    try:
        init_office_admin_table(db)
        import main

        office = db.query(main.Office).filter(main.Office.id == office_id).first()
        if not office:
            raise HTTPException(status_code=404, detail="办公室不存在")

        result = db.execute(
            text("""
            SELECT r.*, u.name as user_name, o.name as office_name
            FROM office_admin_relations r
            LEFT JOIN users u ON r.user_id = u.id
            LEFT JOIN office o ON r.office_id = o.id
            WHERE r.office_id = :office_id
            ORDER BY r.is_primary DESC, r.created_at ASC
        """),
            {"office_id": office_id},
        )

        admins = []
        for row in result:
            role_type_name = {1: "负责人", 2: "行政对接人", 3: "其他管理员"}.get(
                row.role_type, "其他"
            )
            admins.append(
                {
                    "id": row.id,
                    "office_id": row.office_id,
                    "office_name": row.office_name,
                    "user_id": row.user_id,
                    "user_name": row.user_name,
                    "is_primary": row.is_primary,
                    "role_type": row.role_type,
                    "role_type_name": role_type_name,
                    "created_at": str(row.created_at) if row.created_at else None,
                }
            )

        return admins
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取管理员列表失败: {str(e)}")


@router.get("/user/{user_id}")
def get_user_managed_offices(user_id: int, db: Session = Depends(get_db)):
    """
    获取用户管理的所有办公室

    返回该用户作为管理员的所有办公室
    """
    try:
        init_office_admin_table(db)
        import main

        user = db.query(main.User).filter(main.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        result = db.execute(
            text("""
            SELECT r.*, u.name as user_name, o.name as office_name
            FROM office_admin_relations r
            LEFT JOIN users u ON r.user_id = u.id
            LEFT JOIN office o ON r.office_id = o.id
            WHERE r.user_id = :user_id
            ORDER BY r.is_primary DESC, r.created_at ASC
        """),
            {"user_id": user_id},
        )

        offices = []
        for row in result:
            role_type_name = {1: "负责人", 2: "行政对接人", 3: "其他管理员"}.get(
                row.role_type, "其他"
            )
            offices.append(
                {
                    "id": row.id,
                    "office_id": row.office_id,
                    "office_name": row.office_name,
                    "user_id": row.user_id,
                    "user_name": row.user_name,
                    "is_primary": row.is_primary,
                    "role_type": row.role_type,
                    "role_type_name": role_type_name,
                    "created_at": str(row.created_at) if row.created_at else None,
                }
            )

        return offices
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取管理办公室失败: {str(e)}")


@router.post("")
def add_office_admin(data: OfficeAdminCreate, db: Session = Depends(get_db)):
    """
    添加办公室管理员

    - office_id: 办公室ID
    - user_id: 用户ID
    - is_primary: 是否主要管理员(0或1)
    - role_type: 管理员类型(1=负责人 2=行政对接人 3=其他)
    """
    try:
        init_office_admin_table(db)
        import main

        office = db.query(main.Office).filter(main.Office.id == data.office_id).first()
        if not office:
            raise HTTPException(status_code=404, detail="办公室不存在")

        user = db.query(main.User).filter(main.User.id == data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        if user.role not in ["super_admin", "admin", "office_admin", "user"]:
            raise HTTPException(status_code=400, detail="用户角色无效")

        existing = db.execute(
            text("""
            SELECT id FROM office_admin_relations 
            WHERE office_id = :office_id AND user_id = :user_id
        """),
            {"office_id": data.office_id, "user_id": data.user_id},
        ).fetchone()

        if existing:
            raise HTTPException(status_code=400, detail="该用户已是此办公室的管理员")

        if data.is_primary == 1:
            db.execute(
                text("""
                UPDATE office_admin_relations 
                SET is_primary = 0 
                WHERE office_id = :office_id
            """),
                {"office_id": data.office_id},
            )

            db.execute(
                text("""
                UPDATE office SET primary_admin_id = :user_id WHERE id = :office_id
            """),
                {"user_id": data.user_id, "office_id": data.office_id},
            )

        if user.role == "user":
            user.role = "office_admin"

        db.execute(
            text("""
            INSERT INTO office_admin_relations (office_id, user_id, is_primary, role_type, created_at)
            VALUES (:office_id, :user_id, :is_primary, :role_type, :created_at)
        """),
            {
                "office_id": data.office_id,
                "user_id": data.user_id,
                "is_primary": data.is_primary,
                "role_type": data.role_type,
                "created_at": datetime.now(),
            },
        )

        db.commit()

        role_type_name = {1: "负责人", 2: "行政对接人", 3: "其他管理员"}.get(
            data.role_type, "其他"
        )

        return {
            "message": "添加成功",
            "office_name": office.name,
            "user_name": user.name,
            "is_primary": data.is_primary,
            "role_type_name": role_type_name,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"添加管理员失败: {str(e)}")


@router.put("/{relation_id}")
def update_office_admin(
    relation_id: int,
    is_primary: Optional[int] = None,
    role_type: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """更新办公室管理员信息"""
    try:
        init_office_admin_table(db)

        relation = db.execute(
            text("""
            SELECT * FROM office_admin_relations WHERE id = :id
        """),
            {"id": relation_id},
        ).fetchone()

        if not relation:
            raise HTTPException(status_code=404, detail="管理员关系不存在")

        updates = []
        params = {"id": relation_id}

        if is_primary is not None:
            if is_primary == 1:
                db.execute(
                    text("""
                    UPDATE office_admin_relations 
                    SET is_primary = 0 
                    WHERE office_id = :office_id
                """),
                    {"office_id": relation.office_id},
                )

                db.execute(
                    text("""
                    UPDATE office SET primary_admin_id = :user_id WHERE id = :office_id
                """),
                    {"user_id": relation.user_id, "office_id": relation.office_id},
                )

            updates.append("is_primary = :is_primary")
            params["is_primary"] = is_primary

        if role_type is not None:
            updates.append("role_type = :role_type")
            params["role_type"] = role_type

        if updates:
            db.execute(
                text(f"""
                UPDATE office_admin_relations 
                SET {", ".join(updates)} 
                WHERE id = :id
            """),
                params,
            )
            db.commit()

        return {"message": "更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/{relation_id}")
def remove_office_admin(relation_id: int, db: Session = Depends(get_db)):
    """
    移除办公室管理员

    移除后如果用户没有其他办公室管理权限，角色将降为普通用户
    """
    try:
        init_office_admin_table(db)

        relation = db.execute(
            text("""
            SELECT * FROM office_admin_relations WHERE id = :id
        """),
            {"id": relation_id},
        ).fetchone()

        if not relation:
            raise HTTPException(status_code=404, detail="管理员关系不存在")

        db.execute(
            text("""
            DELETE FROM office_admin_relations WHERE id = :id
        """),
            {"id": relation_id},
        )

        other_offices = db.execute(
            text("""
            SELECT COUNT(*) as count FROM office_admin_relations WHERE user_id = :user_id
        """),
            {"user_id": relation.user_id},
        ).fetchone()

        if other_offices.count == 0:
            import main

            user = db.query(main.User).filter(main.User.id == relation.user_id).first()
            if user and user.role == "office_admin":
                user.role = "user"

        db.execute(
            text("""
            UPDATE office SET primary_admin_id = NULL 
            WHERE id = :office_id AND primary_admin_id = :user_id
        """),
            {"office_id": relation.office_id, "user_id": relation.user_id},
        )

        db.commit()

        return {"message": "移除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"移除失败: {str(e)}")


@router.delete("/office/{office_id}/user/{user_id}")
def remove_admin_from_office(
    office_id: int, user_id: int, db: Session = Depends(get_db)
):
    """从办公室移除指定管理员"""
    try:
        init_office_admin_table(db)

        relation = db.execute(
            text("""
            SELECT * FROM office_admin_relations 
            WHERE office_id = :office_id AND user_id = :user_id
        """),
            {"office_id": office_id, "user_id": user_id},
        ).fetchone()

        if not relation:
            raise HTTPException(status_code=404, detail="该用户不是此办公室的管理员")

        return remove_office_admin(relation.id, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"移除失败: {str(e)}")


@router.get("/candidates")
def get_admin_candidates(db: Session = Depends(get_db)):
    """
    获取可设置为办公室管理员的候选人列表

    返回所有系统管理员和有办公室归属的用户
    """
    try:
        import main

        users = (
            db.query(main.User)
            .filter(
                main.User.is_active == 1,
                main.User.role.in_(["super_admin", "admin", "office_admin", "user"]),
            )
            .all()
        )

        return [
            {
                "id": u.id,
                "name": u.name,
                "department": u.department,
                "role": u.role,
                "role_name": get_role_display_name(u.role, u.department),
            }
            for u in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取候选人失败: {str(e)}")


def get_role_display_name(role: str, department: str = None) -> str:
    """获取角色显示名称"""
    if role == "super_admin":
        return "超级管理员"
    elif role == "admin":
        return "系统管理员"
    elif role == "office_admin":
        return f"{department}管理员" if department else "办公室管理员"
    else:
        return "普通用户"
