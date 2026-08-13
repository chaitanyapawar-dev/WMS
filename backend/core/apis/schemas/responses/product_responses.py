"""Response schemas for product master data APIs."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProductResponse(BaseModel):
    """Safe product response model."""

    id: str
    seller_id: str
    name: str
    sku: str
    upc: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
