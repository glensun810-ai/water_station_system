"""
空间审批模型
记录审批流程详情
"""

import enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base, TimestampMixin


class ApprovalStatus(str, enum.Enum):
    """审批状态枚举"""

    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    need_modify = "need_modify"


class SpaceApproval(Base, TimestampMixin):
    """空间审批模型"""

    __tablename__ = "space_approvals"

    id = Column(Integer, primary_key=True, index=True)

    approval_no = Column(String(50), unique=True, nullable=False, index=True)

    booking_id = Column(
        Integer, ForeignKey("space_bookings.id"), nullable=False, index=True
    )
    booking_no = Column(String(50))

    approval_type = Column(String(20), nullable=False)
    approval_stage = Column(String(20))

    approval_content = Column(Text)
    attachments = Column(Text)

    approver_id = Column(Integer)
    approver_name = Column(String(100))
    approver_role = Column(String(20))
    approver_department = Column(String(100))

    status = Column(String(20), default="pending", index=True)
    result = Column(String(20))

    submitted_at = Column(DateTime, default=datetime.now)
    assigned_at = Column(DateTime)
    reviewed_at = Column(DateTime)
    approved_at = Column(DateTime)
    rejected_at = Column(DateTime)

    approval_notes = Column(Text)
    rejection_reason = Column(Text)
    modify_suggestions = Column(Text)

    prev_approver_id = Column(Integer)
    next_approver_id = Column(Integer)
    escalation_count = Column(Integer, default=0)

    deadline = Column(DateTime)
    is_overdue = Column(Boolean, default=False)
    overdue_hours = Column(Integer)

    approval_method = Column(String(20))
    approval_channel = Column(String(20))

    booking = relationship("SpaceBooking", backref="approvals")

    def __repr__(self):
        return f"<SpaceApproval(id={self.id}, approval_no={self.approval_no}, status={self.status})>"
