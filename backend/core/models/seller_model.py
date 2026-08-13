"""Seller persistence model for Whitfield WMS master data."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from odmantic import Field, Index, Model
from pydantic import EmailStr


class SellerStatus(str, Enum):
    """Lifecycle status for seller records."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Seller(Model):
    """
    MongoDB document model for seller master data.

    Stores seller identity, contact, and operational status information.
    """

    name: str
    seller_code: str
    email: EmailStr
    phone: Optional[str] = None
    status: SellerStatus = SellerStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "collection": "sellers",
        "indexes": lambda: [Index(Seller.seller_code, unique=True)],
    }
