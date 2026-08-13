"""
inventory_responses.py — Pydantic response serialization schemas for inventory operations.

Defines client-facing data contracts for inventory stock queries.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class InventoryResponse(BaseModel):
    """
    Response schema for an inventory snapshot.

    Exposes current stock levels, calculated available stock, threshold, and metadata.
    """

    id: str
    warehouse_id: str
    seller_id: str
    product_id: str
    on_hand: int
    reserved: int
    available: int
    damaged: int
    low_stock_threshold: int
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("id", "warehouse_id", "seller_id", "product_id", mode="before")
    @classmethod
    def convert_objectid(cls, v):
        if v is not None:
            return str(v)
        return v
