"""
receipt_model.py — ODMantic model for physical inbound shipments.

This module defines the Receipt and embedded ReceiptItem document structure stored in MongoDB.
ODMantic maps the Receipt model to the "receipts" collection.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from odmantic import EmbeddedModel, Field, Index, Model, ObjectId


class ReceiptStatus(str, Enum):
    """
    Lifecycle state of an inbound physical receipt.

    Enforces allowed state transitions for receiving workflows.
    """

    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ReceiptItem(EmbeddedModel):
    """
    Embedded document model for a line item within an inbound receipt.

    Stores product reference, UPC barcode, and item quantities.
    """

    product_id: ObjectId
    upc: str
    received_qty: int = Field(default=0, ge=0)
    good_qty: int = Field(default=0, ge=0)
    damaged_qty: int = Field(default=0, ge=0)


class Receipt(Model):
    """
    MongoDB document model for inbound receipts.

    Stores receipt identity, warehouse/seller scope, physical tracking metadata,
    item line array, and completion status.
    """

    receipt_number: str
    seller_id: ObjectId
    warehouse_id: ObjectId
    tracking_number: Optional[str] = None
    ticket_number: Optional[str] = None
    status: ReceiptStatus = ReceiptStatus.DRAFT
    items: list[ReceiptItem] = Field(default_factory=list)
    idempotency_key: Optional[str] = None
    created_by: ObjectId
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_by: Optional[ObjectId] = None
    completed_at: Optional[datetime] = None

    model_config = {
        "collection": "receipts",
        "indexes": lambda: [
            Index(Receipt.receipt_number, unique=True),
            Index(Receipt.warehouse_id, Receipt.seller_id, Receipt.status),
        ],
    }
