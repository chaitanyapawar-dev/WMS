"""
movement_model.py — ODMantic model for append-only inventory movements.

This module defines the InventoryMovement document structure stored in MongoDB.
ODMantic maps this model to the "inventory_movements" collection.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from odmantic import Field, Index, Model, ObjectId


class MovementType(str, Enum):
    """Types of stock movements that alter inventory quantities."""

    RECEIVED = "RECEIVED"
    DAMAGED_RECEIVED = "DAMAGED_RECEIVED"
    ADJUSTMENT_INCREASE = "ADJUSTMENT_INCREASE"
    ADJUSTMENT_DECREASE = "ADJUSTMENT_DECREASE"
    RESERVED = "RESERVED"
    RESERVATION_RELEASED = "RESERVATION_RELEASED"
    SHIPPED = "SHIPPED"


class MovementReferenceType(str, Enum):
    """Domain entities that can generate an inventory movement."""

    RECEIPT = "RECEIPT"
    ORDER = "ORDER"
    ADJUSTMENT = "ADJUSTMENT"


class InventoryMovement(Model):
    """
    MongoDB document model for append-only inventory movements.

    Records previous and resulting quantities for every stock mutation.
    """

    warehouse_id: ObjectId
    seller_id: ObjectId
    product_id: ObjectId
    inventory_id: ObjectId
    movement_type: MovementType
    quantity: int
    previous_on_hand: int
    new_on_hand: int
    previous_reserved: int
    new_reserved: int
    previous_damaged: int
    new_damaged: int
    reference_type: MovementReferenceType
    reference_id: str
    reason: Optional[str] = None
    performed_by: ObjectId
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "collection": "inventory_movements",
        "indexes": lambda: [
            Index(InventoryMovement.inventory_id, InventoryMovement.created_at),
            Index(InventoryMovement.warehouse_id, InventoryMovement.seller_id),
            Index(InventoryMovement.reference_type, InventoryMovement.reference_id),
        ],
    }
