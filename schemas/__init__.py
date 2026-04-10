"""
schemas包
"""

from schemas.water import OfficePickupCreate, OfficePickupResponse
from schemas.system import UserResponse, OfficeResponse, AuthResponse

__all__ = [
    "OfficePickupCreate",
    "OfficePickupResponse",
    "UserResponse",
    "OfficeResponse",
    "AuthResponse",
]
