"""
空间预约模型
记录所有空间预约信息

架构优化版本 v2.0
- 简化状态定义
- 统一状态命名
- 增加状态变化历史追踪
"""

import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Float,
    Text,
    ForeignKey,
    Date,
    DateTime,
    JSON,
)
from sqlalchemy.orm import relationship
from datetime import datetime, date

from .base import Base, TimestampMixin


class BookingStatus(str, enum.Enum):
    """
    预约状态枚举（简化版）

    状态流转:
    pending → approved → confirmed → active → completed → settled
                ↓           ↓          ↓
              rejected   cancelled  cancelled

    状态说明:
    - pending:      待审批，初始状态
    - approved:     已批准，等待用户确认支付
    - confirmed:    已确认，预约生效
    - active:       进行中，正在使用
    - completed:    已完成，使用结束
    - settled:      已结算，费用处理完毕
    - cancelled:    已取消
    - rejected:     已拒绝
    """

    pending = "pending"  # 待审批
    approved = "approved"  # 已批准
    rejected = "rejected"  # 已拒绝
    confirmed = "confirmed"  # 已确认
    active = "active"  # 进行中
    completed = "completed"  # 已完成
    settled = "settled"  # 已结算
    cancelled = "cancelled"  # 已取消


class PaymentStatus(str, enum.Enum):
    """
    支付状态枚举

    状态说明:
    - none:           无需支付（免费预约）
    - pending:        待支付
    - deposit_paid:    押金已付
    - partial:         部分支付（押金已付，余额待结）
    - paid:            已全额支付
    - refunded:        已退款
    """

    none = "none"  # 无需支付（免费）
    pending = "pending"  # 待支付
    deposit_paid = "deposit_paid"  # 押金已付
    partial = "partial"  # 部分支付
    paid = "paid"  # 已支付
    refunded = "refunded"  # 已退款


class SettlementStatus(str, enum.Enum):
    """
    结算状态枚举（向后兼容）

    注意: 新版本建议直接使用 status='settled' 表示已结算
    此枚举保留用于API兼容和数据库迁移过渡
    """

    unsettled = "unsettled"
    pending = "pending"
    applied = "applied"
    confirmed = "confirmed"
    settled = "settled"


# 状态显示配置
STATUS_CONFIG = {
    "pending": {
        "icon": "⏳",
        "text": "待审批",
        "color": "#f59e0b",
        "bgColor": "rgba(245, 158, 11, 0.1)",
        "user_actions": ["查看详情", "取消预约", "修改预约"],
        "admin_actions": ["审批通过", "审批拒绝", "要求修改", "查看详情"],
        "next_hint": "等待管理员审批...",
        "transitions": ["approved", "rejected", "cancelled"],
    },
    "approved": {
        "icon": "✅",
        "text": "已批准",
        "color": "#22c55e",
        "bgColor": "rgba(34, 197, 94, 0.1)",
        "user_actions": ["支付押金", "确认预约", "取消预约", "查看详情"],
        "admin_actions": ["确认押金", "取消预约", "查看详情"],
        "next_hint": "请支付押金锁定预约",
        "transitions": ["confirmed", "cancelled"],
    },
    "rejected": {
        "icon": "❌",
        "text": "已拒绝",
        "color": "#ef4444",
        "bgColor": "rgba(239, 68, 68, 0.1)",
        "user_actions": ["查看原因", "重新提交"],
        "admin_actions": ["查看详情"],
        "next_hint": "预约已被拒绝",
        "transitions": [],
    },
    "confirmed": {
        "icon": "📋",
        "text": "已确认",
        "color": "#3b82f6",
        "bgColor": "rgba(59, 130, 246, 0.1)",
        "user_actions": ["查看详情", "取消预约"],
        "admin_actions": ["标记开始", "取消预约", "修改预约", "查看详情"],
        "next_hint": "预约已生效，请按时使用",
        "transitions": ["active", "completed", "cancelled"],
    },
    "active": {
        "icon": "🎯",
        "text": "进行中",
        "color": "#8b5cf6",
        "bgColor": "rgba(139, 92, 246, 0.1)",
        "user_actions": ["查看详情"],
        "admin_actions": ["标记完成", "延长时间", "查看详情"],
        "next_hint": "正在使用中",
        "transitions": ["completed"],
    },
    "completed": {
        "icon": "✔️",
        "text": "已完成",
        "color": "#64748b",
        "bgColor": "rgba(100, 116, 139, 0.1)",
        "user_actions": ["支付余额", "确认结算", "申请发票", "评价反馈"],
        "admin_actions": ["确认结算", "调整费用", "发送账单", "查看详情"],
        "next_hint": "使用已完成，请确认结算",
        "transitions": ["settled"],
    },
    "settled": {
        "icon": "💰",
        "text": "已结算",
        "color": "#10b981",
        "bgColor": "rgba(16, 185, 129, 0.1)",
        "user_actions": ["查看详情", "下载发票"],
        "admin_actions": ["开具发票", "查看详情"],
        "next_hint": "费用已结算完毕",
        "transitions": [],
    },
    "cancelled": {
        "icon": "🚫",
        "text": "已取消",
        "color": "#94a3b8",
        "bgColor": "rgba(148, 163, 184, 0.1)",
        "user_actions": ["查看详情"],
        "admin_actions": ["查看详情"],
        "next_hint": "预约已取消",
        "transitions": [],
    },
}

PAYMENT_STATUS_CONFIG = {
    "none": {"icon": "🎁", "text": "免费", "color": "#22c55e"},
    "pending": {"icon": "⏳", "text": "待支付", "color": "#f59e0b"},
    "deposit_paid": {"icon": "💵", "text": "押金已付", "color": "#3b82f6"},
    "partial": {"icon": "📊", "text": "部分支付", "color": "#8b5cf6"},
    "paid": {"icon": "✅", "text": "已支付", "color": "#22c55e"},
    "refunded": {"icon": "↩️", "text": "已退款", "color": "#94a3b8"},
}


class SpaceBooking(Base, TimestampMixin):
    """空间预约模型"""

    __tablename__ = "space_bookings"

    id = Column(Integer, primary_key=True, index=True)

    booking_no = Column(String(50), unique=True, nullable=False, index=True)

    resource_id = Column(
        Integer, ForeignKey("space_resources.id"), nullable=False, index=True
    )
    resource_name = Column(String(100))
    resource_location = Column(String(200))
    resource_capacity = Column(Integer)
    type_id = Column(Integer)
    type_code = Column(String(50))

    user_id = Column(Integer, index=True)
    user_type = Column(String(20), default="external")
    user_name = Column(String(100), nullable=False)
    user_phone = Column(String(20))
    user_email = Column(String(100))
    department = Column(String(100))
    office_id = Column(Integer)

    booking_date = Column(Date, nullable=False, index=True)
    start_time = Column(String(10), nullable=False)
    end_time = Column(String(10), nullable=False)
    duration = Column(Float)
    duration_hours = Column(Float)
    duration_unit = Column(String(20))

    end_date = Column(Date)
    booking_days = Column(Integer, default=1)

    meal_session = Column(String(20))
    meal_standard = Column(String(20))
    guests_count = Column(Integer, default=1)

    content_type = Column(String(50))
    content_url = Column(String(200))
    content_approved = Column(Boolean, default=False)
    play_frequency = Column(Integer, default=1)

    exhibition_type = Column(String(50))
    exhibition_plan_url = Column(String(200))

    purpose = Column(String(200))
    title = Column(String(200))
    attendees_count = Column(Integer, default=1)
    attendees_info = Column(Text)

    special_requests = Column(Text)
    addons_selected = Column(Text)

    base_fee = Column(Float, default=0.0)
    addon_fee = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    total_fee = Column(Float, default=0.0)
    actual_fee = Column(Float, default=0.0)
    fee_unit = Column(String(20))

    requires_deposit = Column(Boolean, default=False)
    deposit_amount = Column(Float, default=0.0)
    deposit_paid = Column(Boolean, default=False)
    deposit_paid_at = Column(DateTime)
    deposit_payment_method = Column(String(20))
    deposit_refunded = Column(Boolean, default=False)
    deposit_refund_amount = Column(Float)
    deposit_refund_at = Column(DateTime)

    balance_amount = Column(Float, default=0.0)
    balance_paid = Column(Boolean, default=False)
    balance_paid_at = Column(DateTime)
    balance_payment_method = Column(String(20))

    status = Column(String(20), default="pending", index=True)
    payment_status = Column(String(20), default="none")
    payment_mode = Column(
        String(20), default="credit", comment="credit/balance_deduct/prepay"
    )

    credit_note_id = Column(Integer, comment="记账账单ID")
    deduct_record_id = Column(Integer, comment="抵扣记录ID")

    deduct_amount = Column(Float, default=0.0, comment="余额抵扣金额")
    credit_amount = Column(Float, default=0.0, comment="记账金额")

    approval_id = Column(Integer)
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    approval_notes = Column(Text)
    rejected_reason = Column(Text)
    rejected_at = Column(DateTime)
    rejected_by = Column(String(100))

    confirmed_at = Column(DateTime)
    confirmed_by = Column(String(100))

    activated_at = Column(DateTime)
    activated_by = Column(String(100))

    cancelled_at = Column(DateTime)
    cancelled_by = Column(String(100))
    cancel_reason = Column(String(500))
    cancel_type = Column(String(20))

    completed_at = Column(DateTime)
    completed_by = Column(String(100))
    completion_notes = Column(Text)

    settled_at = Column(DateTime)
    settled_by = Column(String(100))
    settlement_notes = Column(Text)

    checked_in_at = Column(DateTime)
    checked_in_by = Column(String(100))
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    actual_duration = Column(Float)

    rated_at = Column(DateTime)
    rating_score = Column(Float)
    rating_feedback = Column(Text)

    invoice_requested = Column(Boolean, default=False)
    invoice_status = Column(String(20))
    invoice_id = Column(Integer)
    invoice_info = Column(Text)

    can_modify = Column(Boolean, default=True)
    can_cancel = Column(Boolean, default=True)
    cancel_deadline = Column(DateTime)
    modify_deadline = Column(DateTime)

    user_payment_confirmed = Column(Boolean, default=False)
    user_payment_confirmed_at = Column(DateTime)
    admin_payment_verified = Column(Boolean, default=False)
    admin_payment_verified_at = Column(DateTime)
    admin_payment_verified_by = Column(String(100))

    is_deleted = Column(Integer, default=0, index=True)
    deleted_at = Column(DateTime)
    deleted_by = Column(String(100))
    delete_reason = Column(String(500))

    booking_source = Column(String(20))
    booking_channel = Column(String(20))

    calendar_invite_sent = Column(Boolean, default=False)
    calendar_invite_id = Column(String(100))

    status_history = Column(JSON, default=list)

    resource = relationship("SpaceResource", back_populates="bookings")

    def __repr__(self):
        return f"<SpaceBooking(id={self.id}, booking_no={self.booking_no}, status={self.status})>"

    def add_status_history(self, from_status, to_status, by_user, reason=None):
        """记录状态变化历史"""
        if self.status_history is None:
            self.status_history = []

        history_entry = {
            "from_status": from_status,
            "to_status": to_status,
            "changed_at": datetime.now().isoformat(),
            "changed_by": by_user,
            "reason": reason,
        }
        self.status_history.append(history_entry)

    def get_current_status_info(self):
        """获取当前状态的完整信息"""
        return STATUS_CONFIG.get(self.status, STATUS_CONFIG["pending"])

    def get_payment_status_info(self):
        """获取支付状态的完整信息"""
        return PAYMENT_STATUS_CONFIG.get(
            self.payment_status, PAYMENT_STATUS_CONFIG["none"]
        )

    def get_allowed_transitions(self):
        """获取允许的状态转换"""
        return STATUS_CONFIG.get(self.status, {}).get("transitions", [])

    def can_transition_to(self, target_status):
        """检查是否可以转换到目标状态"""
        return target_status in self.get_allowed_transitions()


class BookingStatusHistory(Base, TimestampMixin):
    """预约状态变化历史模型"""

    __tablename__ = "booking_status_history"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(
        Integer, ForeignKey("space_bookings.id"), nullable=False, index=True
    )
    booking_no = Column(String(50), index=True)

    from_status = Column(String(20))
    to_status = Column(String(20), nullable=False)

    changed_at = Column(DateTime, nullable=False, default=datetime.now)
    changed_by_id = Column(Integer)
    changed_by_name = Column(String(100))
    changed_by_role = Column(String(20))

    change_reason = Column(Text)
    change_type = Column(String(20))

    notes = Column(Text)
    extra_data = Column(JSON)

    def __repr__(self):
        return f"<BookingStatusHistory(booking_id={self.booking_id}, {self.from_status}→{self.to_status})>"
