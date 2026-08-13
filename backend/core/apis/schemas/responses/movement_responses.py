"""
movement_responses.py — Pydantic response serialization schemas for movement history.

Defines client-facing data contracts for inventory ledger movement records.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class InventoryMovementResponse(BaseModel):
    """
    Response schema for an inventory movement record.

    Exposes stock quantities, movement type, reference metadata, actor, and timestamp.
    """

    id: str
    warehouse_id: str
    seller_id: str
    product_id: str
    inventory_id: str
    movement_type: str
    quantity: int
    previous_on_hand: int
    new_on_hand: int
    previous_reserved: int
    new_reserved: int
    previous_damaged: int
    new_damaged: int
    reference_type: str
    reference_id: str
    reason: Optional[str] = None
    performed_by: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator(
        "id",
        "warehouse_id",
        "seller_id",
        "product_id",
        "inventory_id",
        "performed_by",
        mode="before",
    )
    @classmethod
    def convert_objectid(cls, v):
        if v is not None:
            return str(v)
        return v
