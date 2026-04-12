"""
领水记录相关模型
包含OfficePickup模型定义
"""

from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from models.base import Base


class OfficePickup(Base):
    """
    办公室领水记录表

    状态流转：
    pending(待付款) → paid(已付款待确认) → confirmed(已确认收款)

    业务流程：
    1. 用户领水登记 → pending
    2. 用户付款 → paid
    3. 管理员确认收款 → confirmed
    """

    __tablename__ = "office_pickup"

    id = Column(Integer, primary_key=True, index=True)
    office_id = Column(Integer, nullable=False)
    office_name = Column(String(100), nullable=False)
    office_room_number = Column(String(50), nullable=True)
    product_id = Column(Integer, nullable=False)
    product_name = Column(String(100), nullable=False)
    product_specification = Column(String(50), nullable=True)

    # 领水数量
    quantity = Column(Integer, nullable=False)

    # 领水人信息
    pickup_person = Column(String(100), nullable=True)
    pickup_person_id = Column(Integer, nullable=True)

    # 领水时间
    pickup_time = Column(DateTime, nullable=False)

    # 支付模式: prepaid(预付) / credit(信用/先用后付)
    payment_mode = Column(String(20), default="credit")

    # 结算状态: pending(待付款) / paid(已付款待确认) / confirmed(已确认收款)
    settlement_status = Column(String(20), default="pending")

    # 付款信息
    payment_time = Column(DateTime, nullable=True)
    payment_method = Column(
        String(20), nullable=True
    )  # cash/transfer/prepaid/wechat/alipay
    payment_note = Column(String(200), nullable=True)

    # 确认信息
    confirmed_time = Column(DateTime, nullable=True)
    confirmed_by = Column(Integer, nullable=True)
    confirmed_by_name = Column(String(100), nullable=True)
    confirm_note = Column(String(200), nullable=True)

    # 金额
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    free_qty = Column(Integer, default=0)  # 赠送数量

    # 备注
    note = Column(String(500), nullable=True)

    # 软删除字段
    is_deleted = Column(Integer, default=0)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, nullable=True)
    delete_reason = Column(String(500), nullable=True)

    # 审计字段
    created_at = Column(DateTime, default=datetime.now)
