"""
order_requests.py — Pydantic request validation schemas for order creation.

Defines input contracts for creating sales orders.
"""

from typing import Optional
from pydantic import BaseModel, Field, model_validator


class CreateOrderItemRequest(BaseModel):
    """Line item payload for order creation."""

    sku: str = Field(..., min_length=1, description="Product SKU identifier")
    quantity: int = Field(..., gt=0, description="Quantity requested (> 0)")


class CreateOrderRequest(BaseModel):
    """
    Request payload for creating a new sales order.

    Requires seller, warehouse, order number, and at least one non-empty line item.
    """

    seller_id: str = Field(..., description="Seller ObjectId string")
    warehouse_id: str = Field(..., description="Warehouse ObjectId string")
    order_number: Optional[str] = Field(None, description="Optional custom order number (generated if omitted)")
    items: list[CreateOrderItemRequest] = Field(..., min_length=1, description="Line items requested")
    idempotency_key: Optional[str] = None

    @model_validator(mode="after")
    def validate_items(self) -> "CreateOrderRequest":
        """Validate non-empty item list."""
        if not self.items:
            raise ValueError("Order must contain at least one line item.")
        return self
