"""
会员套餐API路由 - v1版本
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel

from config.database import get_db
from models.membership_plan import MembershipPlan
from depends.auth import get_current_user, get_admin_user
from models.user import User

router = APIRouter(prefix="/membership", tags=["会员套餐"])


class MembershipPlanResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    original_price: Optional[float]
    duration_months: int
    features: Optional[List[str]]
    icon: Optional[str]
    is_active: bool
    sort_order: int

    class Config:
        from_attributes = True


class MembershipPlanList(BaseModel):
    plans: List[MembershipPlanResponse]
    total: int


@router.get("/plans", response_model=MembershipPlanList)
async def get_membership_plans(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """获取会员套餐列表"""
    try:
        query = db.query(MembershipPlan)

        if is_active is not None:
            query = query.filter(MembershipPlan.is_active == is_active)

        plans = query.order_by(MembershipPlan.sort_order).all()

        return {
            "plans": [
                {
                    "id": plan.id,
                    "name": plan.name,
                    "description": plan.description,
                    "price": float(plan.price),
                    "original_price": float(plan.original_price)
                    if plan.original_price
                    else None,
                    "duration_months": plan.duration_months,
                    "features": plan.features if plan.features else [],
                    "icon": plan.icon if plan.icon else "👑",
                    "is_active": plan.is_active,
                    "sort_order": plan.sort_order,
                }
                for plan in plans
            ],
            "total": len(plans),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会员套餐失败: {str(e)}")


@router.get("/plans/{plan_id}", response_model=MembershipPlanResponse)
async def get_membership_plan(
    plan_id: int,
    db: Session = Depends(get_db),
):
    """获取单个会员套餐详情"""
    try:
        plan = db.query(MembershipPlan).filter(MembershipPlan.id == plan_id).first()

        if not plan:
            raise HTTPException(status_code=404, detail="会员套餐不存在")

        return {
            "id": plan.id,
            "name": plan.name,
            "description": plan.description,
            "price": float(plan.price),
            "original_price": float(plan.original_price)
            if plan.original_price
            else None,
            "duration_months": plan.duration_months,
            "features": plan.features if plan.features else [],
            "icon": plan.icon if plan.icon else "👑",
            "is_active": plan.is_active,
            "sort_order": plan.sort_order,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会员套餐失败: {str(e)}")


class MembershipPlanCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    duration_months: int
    features: Optional[List[str]] = None
    icon: Optional[str] = "👑"
    is_active: bool = True
    sort_order: int = 0


class MembershipPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    duration_months: Optional[int] = None
    features: Optional[List[str]] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


@router.post("/admin/plans")
async def create_membership_plan(
    plan_data: MembershipPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """创建会员套餐（管理员）"""
    try:
        plan = MembershipPlan(
            name=plan_data.name,
            description=plan_data.description,
            price=Decimal(str(plan_data.price)),
            original_price=Decimal(str(plan_data.original_price))
            if plan_data.original_price
            else None,
            duration_months=plan_data.duration_months,
            features=plan_data.features,
            icon=plan_data.icon if plan_data.icon else "👑",
            is_active=plan_data.is_active,
            sort_order=plan_data.sort_order,
        )

        db.add(plan)
        db.commit()
        db.refresh(plan)

        return {"success": True, "message": "会员套餐创建成功", "plan_id": plan.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建会员套餐失败: {str(e)}")


@router.put("/admin/plans/{plan_id}")
async def update_membership_plan(
    plan_id: int,
    plan_data: MembershipPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """更新会员套餐（管理员）"""
    try:
        plan = db.query(MembershipPlan).filter(MembershipPlan.id == plan_id).first()

        if not plan:
            raise HTTPException(status_code=404, detail="会员套餐不存在")

        if plan_data.name is not None:
            plan.name = plan_data.name
        if plan_data.description is not None:
            plan.description = plan_data.description
        if plan_data.price is not None:
            plan.price = Decimal(str(plan_data.price))
        if plan_data.original_price is not None:
            plan.original_price = Decimal(str(plan_data.original_price))
        if plan_data.duration_months is not None:
            plan.duration_months = plan_data.duration_months
        if plan_data.features is not None:
            plan.features = plan_data.features
        if plan_data.icon is not None:
            plan.icon = plan_data.icon
        if plan_data.is_active is not None:
            plan.is_active = plan_data.is_active
        if plan_data.sort_order is not None:
            plan.sort_order = plan_data.sort_order

        db.commit()

        return {"success": True, "message": "会员套餐更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新会员套餐失败: {str(e)}")


@router.delete("/admin/plans/{plan_id}")
async def delete_membership_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """删除会员套餐（管理员）"""
    try:
        plan = db.query(MembershipPlan).filter(MembershipPlan.id == plan_id).first()

        if not plan:
            raise HTTPException(status_code=404, detail="会员套餐不存在")

        db.delete(plan)
        db.commit()

        return {"success": True, "message": "会员套餐删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除会员套餐失败: {str(e)}")
