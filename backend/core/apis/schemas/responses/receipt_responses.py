"""
receipt_responses.py — Pydantic response serialization schemas for receipt operations.

Defines response payloads for receipt line items and full receipt objects.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ReceiptItemResponse(BaseModel):
    """
    Response schema for an embedded receipt item line.

    Exposes product ID, UPC, and quantity breakdown.
    """

    product_id: str
    upc: str
    received_qty: int
    good_qty: int
    damaged_qty: int

    model_config = {"from_attributes": True}

    @field_validator("product_id", mode="before")
    @classmethod
    def convert_objectid(cls, v):
        if v is not None:
            return str(v)
        return v


class ReceiptResponse(BaseModel):
    """
    Response schema for an inbound receipt object.

    Provides formatted serialization for clients and Swagger.
    """

    id: str
    receipt_number: str
    seller_id: str
    warehouse_id: str
    tracking_number: Optional[str] = None
    ticket_number: Optional[str] = None
    status: str
    items: list[ReceiptItemResponse] = Field(default_factory=list)
    idempotency_key: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @field_validator("id", "seller_id", "warehouse_id", "created_by", "completed_by", mode="before")
    @classmethod
    def convert_objectid(cls, v):
        if v is not None:
            return str(v)
        return v
