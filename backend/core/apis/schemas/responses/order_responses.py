"""
order_responses.py — Pydantic response serialization schemas for sales orders.

Defines client-facing data contracts for Order objects.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class OrderItemResponse(BaseModel):
    """Response schema for an order line item."""

    product_id: str
    sku: str
    quantity: int
    reserved_quantity: int
    picked_quantity: int

    model_config = {"from_attributes": True}

    @field_validator("product_id", mode="before")
    @classmethod
    def convert_objectid(cls, v):
        if v is not None:
            return str(v)
        return v


class OrderResponse(BaseModel):
    """Response schema for a sales order."""

    id: str
    order_number: str
    seller_id: str
    warehouse_id: str
    items: list[OrderItemResponse]
    status: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    reserved_at: Optional[datetime] = None
    picked_at: Optional[datetime] = None
    packed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    idempotency_key: Optional[str] = None

    model_config = {"from_attributes": True}

    @field_validator("id", "seller_id", "warehouse_id", "created_by", mode="before")
    @classmethod
    def convert_objectid(cls, v):
        if v is not None:
            return str(v)
        return v
