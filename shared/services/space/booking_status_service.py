"""
空间预约状态管理服务
提供统一的状态转换、验证和管理功能

架构设计:
- 状态转换规则验证
- 自动状态流转处理
- 状态变化历史记录
- 状态变化通知触发
"""

from datetime import datetime
from typing import Optional, Dict, List, Tuple
from sqlalchemy.orm import Session

from shared.models.space.space_booking import (
    SpaceBooking,
    BookingStatus,
    PaymentStatus,
    BookingStatusHistory,
    STATUS_CONFIG,
    PAYMENT_STATUS_CONFIG,
)


class BookingStateManager:
    """预约状态管理器"""

    def __init__(self, db: Session):
        self.db = db

    def validate_transition(
        self, booking: SpaceBooking, target_status: str
    ) -> Tuple[bool, str]:
        """
        验证状态转换是否有效

        Returns:
            (is_valid, error_message)
        """
        current_status = booking.status

        if current_status == target_status:
            return False, "目标状态与当前状态相同"

        allowed_transitions = booking.get_allowed_transitions()

        if target_status not in allowed_transitions:
            config = STATUS_CONFIG.get(current_status, {})
            return (
                False,
                f"状态 '{current_status}' 不能直接转换到 '{target_status}'，允许的转换: {allowed_transitions}",
            )

        return True, ""

    def transition_status(
        self,
        booking: SpaceBooking,
        target_status: str,
        changed_by_id: int,
        changed_by_name: str,
        changed_by_role: str,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
        auto_trigger: bool = False,
    ) -> Tuple[bool, str]:
        """
        执行状态转换

        Args:
            booking: 预约对象
            target_status: 目标状态
            changed_by_id: 操作人ID
            changed_by_name: 操作人名称
            changed_by_role: 操作人角色
            reason: 变化原因
            notes: 备注
            auto_trigger: 是否自动触发

        Returns:
            (success, message)
        """
        is_valid, error_msg = self.validate_transition(booking, target_status)

        if not is_valid:
            return False, error_msg

        from_status = booking.status
        booking.status = target_status

        # 更新状态时间戳
        now = datetime.now()
        self._update_status_timestamp(booking, target_status, now, changed_by_name)

        # 添加状态历史记录
        booking.add_status_history(from_status, target_status, changed_by_name, reason)

        # 创建详细历史记录
        history = BookingStatusHistory(
            booking_id=booking.id,
            booking_no=booking.booking_no,
            from_status=from_status,
            to_status=target_status,
            changed_at=now,
            changed_by_id=changed_by_id,
            changed_by_name=changed_by_name,
            changed_by_role=changed_by_role,
            change_reason=reason,
            change_type="auto" if auto_trigger else "manual",
            notes=notes,
        )
        self.db.add(history)

        # 自动触发支付状态更新
        self._auto_update_payment_status(booking, target_status)

        # 自动触发下一步状态
        self._auto_trigger_next_status(
            booking, target_status, changed_by_id, changed_by_name, changed_by_role
        )

        self.db.commit()

        return True, f"状态已从 '{from_status}' 更新为 '{target_status}'"

    def _update_status_timestamp(
        self, booking: SpaceBooking, status: str, timestamp: datetime, by_user: str
    ):
        """更新状态对应的时间戳字段"""
        timestamp_fields = {
            "approved": ("approved_at", "approved_by"),
            "rejected": ("rejected_at", "rejected_by"),
            "confirmed": ("confirmed_at", "confirmed_by"),
            "active": ("activated_at", "activated_by"),
            "completed": ("completed_at", "completed_by"),
            "settled": ("settled_at", "settled_by"),
            "cancelled": ("cancelled_at", "cancelled_by"),
        }

        if status in timestamp_fields:
            time_field, by_field = timestamp_fields[status]
            setattr(booking, time_field, timestamp)
            setattr(booking, by_field, by_user)

    def _auto_update_payment_status(self, booking: SpaceBooking, status: str):
        """根据预约状态自动更新支付状态"""
        if status == "confirmed":
            if booking.actual_fee == 0 or booking.total_fee == 0:
                booking.payment_status = "none"
            elif booking.deposit_paid and booking.balance_amount > 0:
                booking.payment_status = "partial"
            elif booking.deposit_paid:
                booking.payment_status = "deposit_paid"
            elif booking.requires_deposit:
                booking.payment_status = "pending"
            else:
                booking.payment_status = "pending"

        elif status == "settled":
            booking.payment_status = "paid"

        elif status == "cancelled":
            if booking.deposit_paid and not booking.deposit_refunded:
                booking.payment_status = "refunded"

    def _auto_trigger_next_status(
        self,
        booking: SpaceBooking,
        current_status: str,
        by_id: int,
        by_name: str,
        by_role: str,
    ):
        """自动触发下一步状态（适用于无需审批的场景）"""
        if current_status == "approved":
            if not booking.requires_deposit and booking.actual_fee == 0:
                self.transition_status(
                    booking,
                    "confirmed",
                    by_id,
                    by_name,
                    by_role,
                    reason="免费预约自动确认",
                    auto_trigger=True,
                )

    def approve_booking(
        self,
        booking: SpaceBooking,
        approver_id: int,
        approver_name: str,
        approver_role: str,
        notes: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """审批通过预约"""
        return self.transition_status(
            booking,
            "approved",
            approver_id,
            approver_name,
            approver_role,
            reason="审批通过",
            notes=notes,
        )

    def reject_booking(
        self,
        booking: SpaceBooking,
        rejector_id: int,
        rejector_name: str,
        rejector_role: str,
        reason: str,
        notes: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """审批拒绝预约"""
        booking.rejected_reason = reason
        return self.transition_status(
            booking,
            "rejected",
            rejector_id,
            rejector_name,
            rejector_role,
            reason=reason,
            notes=notes,
        )

    def confirm_booking(
        self,
        booking: SpaceBooking,
        confirmer_id: int,
        confirmer_name: str,
        confirmer_role: str,
        notes: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """确认预约生效"""
        return self.transition_status(
            booking,
            "confirmed",
            confirmer_id,
            confirmer_name,
            confirmer_role,
            reason="用户确认/支付完成",
            notes=notes,
        )

    def activate_booking(
        self,
        booking: SpaceBooking,
        activator_id: int,
        activator_name: str,
        activator_role: str,
        notes: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """标记预约开始使用"""
        return self.transition_status(
            booking,
            "active",
            activator_id,
            activator_name,
            activator_role,
            reason="开始使用",
            notes=notes,
        )

    def complete_booking(
        self,
        booking: SpaceBooking,
        completer_id: int,
        completer_name: str,
        completer_role: str,
        notes: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """标记预约完成"""
        return self.transition_status(
            booking,
            "completed",
            completer_id,
            completer_name,
            completer_role,
            reason="使用完成",
            notes=notes,
        )

    def settle_booking(
        self,
        booking: SpaceBooking,
        settler_id: int,
        settler_name: str,
        settler_role: str,
        notes: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """标记预约结算"""
        return self.transition_status(
            booking,
            "settled",
            settler_id,
            settler_name,
            settler_role,
            reason="费用结算确认",
            notes=notes,
        )

    def cancel_booking(
        self,
        booking: SpaceBooking,
        canceller_id: int,
        canceller_name: str,
        canceller_role: str,
        reason: str,
        cancel_type: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """取消预约"""
        booking.cancel_reason = reason
        booking.cancel_type = cancel_type or "user"

        if booking.deposit_paid and not booking.deposit_refunded:
            booking.deposit_refunded = True
            booking.deposit_refund_amount = booking.deposit_amount
            booking.deposit_refund_at = datetime.now()

        return self.transition_status(
            booking,
            "cancelled",
            canceller_id,
            canceller_name,
            canceller_role,
            reason=reason,
            notes=notes,
        )

    def get_status_display_info(self, booking: SpaceBooking) -> Dict:
        """获取预约状态的完整展示信息"""
        status_info = booking.get_current_status_info()
        payment_info = booking.get_payment_status_info()

        return {
            "status": {
                "code": booking.status,
                "icon": status_info["icon"],
                "text": status_info["text"],
                "color": status_info["color"],
                "bgColor": status_info["bgColor"],
                "next_hint": status_info["next_hint"],
                "user_actions": status_info["user_actions"],
                "admin_actions": status_info["admin_actions"],
            },
            "payment": {
                "code": booking.payment_status,
                "icon": payment_info["icon"],
                "text": payment_info["text"],
                "color": payment_info["color"],
            },
            "is_free": booking.payment_status == "none" or booking.actual_fee == 0,
            "requires_deposit": booking.requires_deposit,
            "deposit_paid": booking.deposit_paid,
            "deposit_amount": booking.deposit_amount,
            "balance_amount": booking.balance_amount,
            "total_fee": booking.actual_fee or booking.total_fee,
        }

    def get_timeline(self, booking: SpaceBooking) -> List[Dict]:
        """获取预约状态变化时间线"""
        timeline = []

        status_events = [
            ("pending", booking.created_at, "提交预约", "提交预约申请"),
            ("approved", booking.approved_at, "审批通过", booking.approved_by),
            ("rejected", booking.rejected_at, "审批拒绝", booking.rejected_by),
            ("confirmed", booking.confirmed_at, "确认预约", booking.confirmed_by),
            ("active", booking.activated_at, "开始使用", booking.activated_by),
            ("completed", booking.completed_at, "使用完成", booking.completed_by),
            ("settled", booking.settled_at, "结算确认", booking.settled_by),
            ("cancelled", booking.cancelled_at, "取消预约", booking.cancelled_by),
        ]

        for status, timestamp, text, by_user in status_events:
            if timestamp:
                config = STATUS_CONFIG.get(status, {})
                timeline.append(
                    {
                        "status": status,
                        "timestamp": timestamp.isoformat() if timestamp else None,
                        "text": text,
                        "by_user": by_user,
                        "icon": config.get("icon", ""),
                        "color": config.get("color", ""),
                    }
                )

        return sorted(timeline, key=lambda x: x["timestamp"] if x["timestamp"] else "")


def get_status_text(status: str) -> str:
    """获取状态的中文显示文本"""
    return STATUS_CONFIG.get(status, {}).get("text", status)


def get_status_icon(status: str) -> str:
    """获取状态的图标"""
    return STATUS_CONFIG.get(status, {}).get("icon", "📍")


def get_status_color(status: str) -> str:
    """获取状态的颜色"""
    return STATUS_CONFIG.get(status, {}).get("color", "#6b7280")


def get_payment_status_text(payment_status: str) -> str:
    """获取支付状态的中文显示文本"""
    return PAYMENT_STATUS_CONFIG.get(payment_status, {}).get("text", payment_status)


def get_payment_status_icon(payment_status: str) -> str:
    """获取支付状态的图标"""
    return PAYMENT_STATUS_CONFIG.get(payment_status, {}).get("icon", "💰")


def get_next_hint(status: str) -> str:
    """获取状态下一步提示"""
    return STATUS_CONFIG.get(status, {}).get("next_hint", "")


def get_user_actions(status: str) -> List[str]:
    """获取用户可执行的操作"""
    return STATUS_CONFIG.get(status, {}).get("user_actions", ["查看详情"])


def get_admin_actions(status: str) -> List[str]:
    """获取管理员可执行的操作"""
    return STATUS_CONFIG.get(status, {}).get("admin_actions", ["查看详情"])
