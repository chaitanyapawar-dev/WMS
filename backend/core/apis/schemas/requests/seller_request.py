"""Request schemas for seller master data APIs."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from core.models.seller_model import SellerStatus


class SellerCreate(BaseModel):
    """Request body used to create a seller."""

    name: str = Field(..., min_length=1, max_length=120)
    seller_code: str = Field(..., min_length=1, max_length=50)
    email: EmailStr = Field(description="Seller contact email")
    phone: Optional[str] = Field(default=None, max_length=30)


class SellerStatusUpdate(BaseModel):
    """Request body used to update seller status."""

    status: SellerStatus = Field(description="New seller lifecycle status")
