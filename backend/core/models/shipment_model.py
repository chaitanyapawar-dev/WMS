"""
shipment_model.py — ODMantic model for outbound parcel shipments.

This module defines the Shipment document structure stored in MongoDB.
ODMantic maps this model to the "shipments" collection.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from odmantic import Field, Index, Model, ObjectId


class ShipmentStatus(str, Enum):
    """Lifecycle statuses for parcel shipments."""

    READY = "READY"
    SHIPPED = "SHIPPED"


class Shipment(Model):
    """
    MongoDB document model for order package shipments.

    Records carrier tracking details, physical dimensions, and dispatch state.
    """

    order_id: ObjectId
    warehouse_id: ObjectId
    carrier: str
    tracking_number: str
    weight: float = Field(default=0.0, ge=0.0)
    length: float = Field(default=0.0, ge=0.0)
    width: float = Field(default=0.0, ge=0.0)
    height: float = Field(default=0.0, ge=0.0)
    label_reference: Optional[str] = None
    status: ShipmentStatus = Field(default=ShipmentStatus.READY)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    shipped_at: Optional[datetime] = None

    model_config = {
        "collection": "shipments",
        "indexes": lambda: [
            Index(Shipment.order_id, unique=True),
            Index(Shipment.warehouse_id, Shipment.carrier),
            Index(Shipment.tracking_number),
        ],
    }
