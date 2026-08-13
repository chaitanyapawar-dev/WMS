"""Request schemas for product master data APIs."""

from typing import Optional

from pydantic import BaseModel, Field

from core.models.product_model import ProductStatus


class ProductCreate(BaseModel):
    """Request body used to create a product."""

    seller_id: str = Field(..., description="Seller ObjectId that owns the product")
    name: str = Field(..., min_length=1, max_length=160)
    sku: str = Field(..., min_length=1, max_length=80)
    upc: str = Field(..., min_length=1, max_length=64)
    description: Optional[str] = Field(default=None, max_length=1000)


class ProductStatusUpdate(BaseModel):
    """Request body used to update product status."""

    status: ProductStatus = Field(description="New product lifecycle status")
