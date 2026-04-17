"""
定价引擎服务
实现灵活的费用计算和折扣规则应用

对标标准: Airbnb定价系统 + WeWork会员定价体系
"""

from sqlalchemy.orm import Session
from datetime import datetime, date, time
from typing import List, Optional, Dict, Any
from decimal import Decimal

from shared.models.space.space_resource import SpaceResource
from shared.models.space.space_type import SpaceType
from shared.models.space.pricing.pricing_rule import PricingRule
from shared.models.space.pricing.pricing_time_slot import PricingTimeSlot
from shared.models.space.pricing.pricing_addon import PricingAddon
from shared.models.space.pricing.pricing_discount import PricingDiscount
from shared.models.space.user_member_info import UserMemberInfo


class PricingEngine:
    """定价引擎"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_booking_fee(
        self,
        resource: SpaceResource,
        space_type: Optional[SpaceType] = None,
        booking_date: date = None,
        start_time: str = None,
        end_time: str = None,
        user_id: Optional[int] = None,
        user_type: str = "external",
        attendees_count: int = 1,
        addons_selected: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        计算预约费用

        返回详细的费用明细：
        - 基础费用
        - 时段调整费用
        - 会员折扣
        - 增值服务费用
        - 批量优惠
        - 最终费用
        """

        calculation_result = {
            "base_fee": 0.0,
            "time_slot_adjustment": 0.0,
            "member_discount": 0.0,
            "addon_fee": 0.0,
            "bulk_discount": 0.0,
            "special_discount": 0.0,
            "subtotal": 0.0,
            "total_discount": 0.0,
            "final_fee": 0.0,
            "deposit_info": {
                "requires_deposit": False,
                "deposit_amount": 0.0,
                "deposit_percentage": 0.0,
            },
            "fee_breakdown": {},
            "applied_rules": [],
        }

        duration_hours = self._calculate_duration(start_time, end_time)

        base_fee = duration_hours * resource.base_price
        calculation_result["base_fee"] = base_fee
        calculation_result["fee_breakdown"]["base"] = {
            "hours": duration_hours,
            "price_per_hour": resource.base_price,
            "subtotal": base_fee,
        }

        time_adjustment = self._apply_time_slot_pricing(
            resource.id, booking_date, start_time, end_time, base_fee
        )
        calculation_result["time_slot_adjustment"] = time_adjustment

        member_info = self._get_user_member_info(user_id)
        if member_info:
            member_discount = base_fee * (1 - member_info.discount_rate)
            calculation_result["member_discount"] = member_discount
            calculation_result["fee_breakdown"]["member_discount"] = {
                "member_level": member_info.member_level,
                "discount_rate": member_info.discount_rate,
                "discount_amount": member_discount,
            }
            calculation_result["applied_rules"].append(
                f"会员折扣({member_info.member_level}): {member_info.discount_rate * 100}%"
            )
        elif user_type == "internal":
            internal_discount = base_fee * 0.2
            calculation_result["member_discount"] = internal_discount
            calculation_result["fee_breakdown"]["internal_discount"] = {
                "discount_rate": 0.8,
                "discount_amount": internal_discount,
            }
            calculation_result["applied_rules"].append("内部员工折扣: 20%")

        addon_fee, addon_details = self._calculate_addon_fee(
            resource.id, addons_selected, duration_hours
        )
        calculation_result["addon_fee"] = addon_fee
        calculation_result["fee_breakdown"]["addons"] = addon_details

        if duration_hours >= 4:
            bulk_discount = base_fee * 0.1
            calculation_result["bulk_discount"] = bulk_discount
            calculation_result["fee_breakdown"]["bulk_discount"] = {
                "rule": "连续预约4小时以上",
                "discount_rate": 0.1,
                "discount_amount": bulk_discount,
            }
            calculation_result["applied_rules"].append("批量优惠: 10%")

        subtotal = base_fee + time_adjustment + addon_fee
        total_discount = (
            calculation_result["member_discount"]
            + calculation_result["bulk_discount"]
            + calculation_result["special_discount"]
        )
        final_fee = subtotal - total_discount

        calculation_result["subtotal"] = subtotal
        calculation_result["total_discount"] = total_discount
        calculation_result["final_fee"] = max(0, final_fee)

        if space_type and space_type.requires_deposit:
            deposit_amount = (
                calculation_result["final_fee"] * space_type.deposit_percentage
            )
            calculation_result["deposit_info"] = {
                "requires_deposit": True,
                "deposit_amount": deposit_amount,
                "deposit_percentage": space_type.deposit_percentage,
            }

        calculation_result["payment_methods"] = [
            "wechat",
            "alipay",
            "internal_account",
            "credit_card",
        ]

        return calculation_result

    def _calculate_duration(self, start_time: str, end_time: str) -> float:
        """计算时长（小时）"""
        try:
            start_dt = datetime.strptime(start_time, "%H:%M")
            end_dt = datetime.strptime(end_time, "%H:%M")
            duration = (end_dt - start_dt).seconds / 3600
            return max(0.5, duration)
        except:
            return 1.0

    def _apply_time_slot_pricing(
        self,
        resource_id: int,
        booking_date: date,
        start_time: str,
        end_time: str,
        base_fee: float,
    ) -> float:
        """应用时段定价"""

        time_slots = (
            self.db.query(PricingTimeSlot)
            .filter(
                PricingTimeSlot.resource_id == resource_id,
                PricingTimeSlot.is_active == True,
            )
            .all()
        )

        if not time_slots:
            return 0.0

        adjustment = 0.0
        try:
            start_hour = int(start_time.split(":")[0])
            end_hour = int(end_time.split(":")[0])

            for slot in time_slots:
                slot_start = int(slot.start_time.split(":")[0])
                slot_end = int(slot.end_time.split(":")[0])

                overlap_hours = max(
                    0, min(end_hour, slot_end) - max(start_hour, slot_start)
                )
                if overlap_hours > 0:
                    adjustment += overlap_hours * slot.price_adjustment

        except:
            pass

        return adjustment

    def _get_user_member_info(self, user_id: Optional[int]) -> Optional[UserMemberInfo]:
        """获取用户会员信息"""
        if not user_id:
            return None

        return (
            self.db.query(UserMemberInfo)
            .filter(UserMemberInfo.user_id == user_id)
            .first()
        )

    def _calculate_addon_fee(
        self,
        resource_id: int,
        addons_selected: Optional[List[Dict]],
        duration_hours: float,
    ) -> tuple[float, List[Dict]]:
        """计算增值服务费用"""

        if not addons_selected:
            return 0.0, []

        addon_fee = 0.0
        addon_details = []

        for addon in addons_selected:
            addon_code = addon.get("code")
            quantity = addon.get("quantity", 1)

            addon_record = (
                self.db.query(PricingAddon)
                .filter(
                    PricingAddon.resource_id == resource_id,
                    PricingAddon.addon_code == addon_code,
                    PricingAddon.is_active == True,
                )
                .first()
            )

            if addon_record:
                subtotal = addon_record.price * quantity
                addon_fee += subtotal
                addon_details.append(
                    {
                        "addon_code": addon_code,
                        "addon_name": addon_record.addon_name,
                        "price": addon_record.price,
                        "quantity": quantity,
                        "subtotal": subtotal,
                    }
                )

        return addon_fee, addon_details

    def get_available_time_slots(
        self, resource_id: int, booking_date: date, duration_hours: float = 1.0
    ) -> List[Dict[str, str]]:
        """
        获取可用时段列表

        返回格式：
        [
            {"start_time": "09:00", "end_time": "10:00", "available": True, "price": 100},
            {"start_time": "10:00", "end_time": "11:00", "available": True, "price": 100},
            ...
        ]
        """

        from shared.models.space.space_booking import SpaceBooking

        resource = (
            self.db.query(SpaceResource).filter(SpaceResource.id == resource_id).first()
        )

        if not resource:
            return []

        existing_bookings = (
            self.db.query(SpaceBooking)
            .filter(
                SpaceBooking.resource_id == resource_id,
                SpaceBooking.booking_date == booking_date,
                SpaceBooking.status.in_(["pending", "approved", "confirmed", "active"]),
            )
            .all()
        )

        booked_slots = []
        for booking in existing_bookings:
            try:
                start_h = int(booking.start_time.split(":")[0])
                end_h = int(booking.end_time.split(":")[0])
                booked_slots.append((start_h, end_h))
            except:
                pass

        available_slots = []
        for hour in range(8, 18):
            end_hour = hour + int(duration_hours)

            if end_hour > 18:
                continue

            is_available = True
            for booked_start, booked_end in booked_slots:
                if not (end_hour <= booked_start or hour >= booked_end):
                    is_available = False
                    break

            slot_price = resource.base_price * duration_hours

            time_slots = (
                self.db.query(PricingTimeSlot)
                .filter(
                    PricingTimeSlot.resource_id == resource_id,
                    PricingTimeSlot.start_time == f"{hour:02d}:00",
                    PricingTimeSlot.is_active == True,
                )
                .first()
            )

            if time_slots:
                slot_price += time_slots.price_adjustment * duration_hours

            available_slots.append(
                {
                    "start_time": f"{hour:02d}:00",
                    "end_time": f"{end_hour:02d}:00",
                    "available": is_available,
                    "price": slot_price,
                    "duration_hours": duration_hours,
                }
            )

        return available_slots

    def recommend_alternative_spaces(
        self,
        resource_id: int,
        booking_date: date,
        start_time: str,
        end_time: str,
        type_id: int,
        limit: int = 5,
    ) -> List[Dict]:
        """
        推荐备选空间

        当预约时间段冲突时，推荐其他可用空间
        """

        alternatives = []

        similar_resources = (
            self.db.query(SpaceResource)
            .filter(
                SpaceResource.type_id == type_id,
                SpaceResource.is_active == True,
                SpaceResource.is_available == True,
                SpaceResource.id != resource_id,
            )
            .limit(limit)
            .all()
        )

        for resource in similar_resources:
            available_slots = self.get_available_time_slots(resource.id, booking_date)

            matching_slots = [
                slot
                for slot in available_slots
                if slot["available"] and slot["start_time"] == start_time
            ]

            if matching_slots:
                alternatives.append(
                    {
                        "resource_id": resource.id,
                        "resource_name": resource.name,
                        "location": resource.location,
                        "capacity": resource.capacity,
                        "available_slot": matching_slots[0],
                        "base_price": resource.base_price,
                    }
                )

        return alternatives


def calculate_fee_with_engine(
    db: Session,
    resource_id: int,
    booking_date: date,
    start_time: str,
    end_time: str,
    user_id: Optional[int] = None,
    user_type: str = "external",
    addons_selected: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    使用定价引擎计算费用的便捷函数
    """

    engine = PricingEngine(db)

    resource = db.query(SpaceResource).filter(SpaceResource.id == resource_id).first()

    if not resource:
        raise ValueError(f"空间资源 {resource_id} 不存在")

    space_type = db.query(SpaceType).filter(SpaceType.id == resource.type_id).first()

    return engine.calculate_booking_fee(
        resource=resource,
        space_type=space_type,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time,
        user_id=user_id,
        user_type=user_type,
        addons_selected=addons_selected,
    )
