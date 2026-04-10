"""
预定领取模型
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base


class ReservationPickup(Base):
    """预定领取记录表"""

    __tablename__ = "reservation_pickups"

    id = Column(Integer, primary_key=True, index=True)
    reservation_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    pickup_qty = Column(Integer, nullable=False)
    picked_at = Column(DateTime, default=datetime.now)
    picked_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="completed")

    reservation = relationship("Transaction")
    picker = relationship("User")
