"""Response schemas for seller master data APIs."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class SellerResponse(BaseModel):
    """Safe seller response model."""

    id: str
    name: str
    seller_code: str
    email: EmailStr
    phone: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
