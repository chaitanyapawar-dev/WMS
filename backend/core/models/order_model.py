"""
order_model.py — ODMantic model for sales orders and order items.

This module defines the Order and OrderItem document structures stored in MongoDB.
ODMantic maps this model to the "orders" collection.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from odmantic import EmbeddedModel, Field, Index, Model, ObjectId


class OrderStatus(str, Enum):
    """Lifecycle statuses for outbound fulfillment orders."""

    NEW = "NEW"
    RESERVED = "RESERVED"
    PICKING = "PICKING"
    PICKED = "PICKED"
    PACKED = "PACKED"
    READY_TO_SHIP = "READY_TO_SHIP"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class OrderItem(EmbeddedModel):
    """
    Embedded document model for a line item within an Order.

    Records ordered, reserved, and picked quantities for a specific product.
    """

    product_id: ObjectId
    sku: str
    quantity: int = Field(gt=0)
    reserved_quantity: int = Field(default=0, ge=0)
    picked_quantity: int = Field(default=0, ge=0)


class Order(Model):
    """
    MongoDB document model for sales orders.

    Tracks customer fulfillment lifecycle from NEW -> RESERVED -> PICKING -> PICKED -> PACKED -> READY_TO_SHIP -> SHIPPED.
    """

    order_number: str = Field(unique=True)
    seller_id: ObjectId
    warehouse_id: ObjectId
    items: list[OrderItem] = Field(default_factory=list)
    status: OrderStatus = Field(default=OrderStatus.NEW)
    created_by: ObjectId
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reserved_at: Optional[datetime] = None
    picked_at: Optional[datetime] = None
    packed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    idempotency_key: Optional[str] = None

    model_config = {
        "collection": "orders",
        "indexes": lambda: [
            Index(Order.order_number, unique=True),
            Index(Order.warehouse_id, Order.seller_id, Order.status),
            Index(Order.created_at),
        ],
    }
