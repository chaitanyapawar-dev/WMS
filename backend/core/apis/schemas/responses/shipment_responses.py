"""
shipment_responses.py — Pydantic response serialization schemas for parcel shipments.

Defines client-facing data contracts for Shipment objects.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class ShipmentResponse(BaseModel):
    """Response schema for a parcel shipment."""

    id: str
    order_id: str
    warehouse_id: str
    carrier: str
    tracking_number: str
    weight: float
    length: float
    width: float
    height: float
    label_reference: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    shipped_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @field_validator("id", "order_id", "warehouse_id", mode="before")
    @classmethod
    def convert_objectid(cls, v):
        if v is not None:
            return str(v)
        return v
