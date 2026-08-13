"""
inventory_model.py — ODMantic model for current inventory snapshots.

This module defines the Inventory document structure stored in MongoDB.
ODMantic maps this model to the "inventory" collection.
"""

from datetime import datetime, timezone
from typing import Optional

from odmantic import Field, Index, Model, ObjectId


class Inventory(Model):
    """
    MongoDB document model for inventory snapshots.

    Stores real-time stock levels for a specific warehouse + seller + product combination.

    Core Invariants:
        on_hand >= 0
        reserved >= 0
        damaged >= 0
        reserved <= on_hand
        available = on_hand - reserved >= 0
    """

    warehouse_id: ObjectId
    seller_id: ObjectId
    product_id: ObjectId
    on_hand: int = Field(default=0, ge=0)
    reserved: int = Field(default=0, ge=0)
    damaged: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=10, ge=0)
    version: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def available(self) -> int:
        """
        Calculate available sellable inventory.

        Returns:
            int: Unreserved physical inventory (on_hand - reserved).
        """
        return self.on_hand - self.reserved

    model_config = {
        "collection": "inventory",
        "indexes": lambda: [
            Index(Inventory.warehouse_id, Inventory.seller_id, Inventory.product_id, unique=True),
            Index(Inventory.warehouse_id, Inventory.seller_id),
            Index(Inventory.product_id),
        ],
    }
