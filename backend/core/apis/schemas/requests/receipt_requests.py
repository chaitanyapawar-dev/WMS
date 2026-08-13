"""
receipt_requests.py — Pydantic request validation schemas for receipt operations.

Defines input payload constraints for creating receipts and adding/updating receipt lines.
"""

from typing import Optional
from pydantic import BaseModel, Field, model_validator


class CreateReceiptRequest(BaseModel):
    """
    Request schema for creating a new inbound receipt.

    Requires seller and warehouse IDs, and at least one physical shipment identifier
    (tracking number or ticket number).
    """

    seller_id: str = Field(..., description="ObjectId string of the owning seller")
    warehouse_id: str = Field(..., description="ObjectId string of the target warehouse")
    tracking_number: Optional[str] = Field(None, description="Carrier tracking number")
    ticket_number: Optional[str] = Field(None, description="Internal or vendor ticket number")
    idempotency_key: Optional[str] = Field(None, description="Optional client idempotency key")

    @model_validator(mode="after")
    def validate_shipment_identifier(self) -> "CreateReceiptRequest":
        """
        Validate that at least one physical shipment identifier is provided.

        Returns:
            CreateReceiptRequest: Validated request object.

        Raises:
            ValueError: If neither tracking_number nor ticket_number is present.
        """
        tracking = self.tracking_number.strip() if self.tracking_number else None
        ticket = self.ticket_number.strip() if self.ticket_number else None
        if not tracking and not ticket:
            raise ValueError(
                "At least one physical shipment identifier (tracking_number or ticket_number) must be provided."
            )
        self.tracking_number = tracking
        self.ticket_number = ticket
        return self


class AddReceiptItemRequest(BaseModel):
    """
    Request schema for adding or updating a receipt line item by UPC.

    Validates that good and damaged quantities are non-negative and total > 0.
    """

    upc: str = Field(..., min_length=1, description="Product UPC barcode")
    good_qty: int = Field(0, ge=0, description="Quantity of items in good condition")
    damaged_qty: int = Field(0, ge=0, description="Quantity of items in damaged condition")

    @model_validator(mode="after")
    def validate_quantities(self) -> "AddReceiptItemRequest":
        """
        Validate that item quantities are non-negative and total quantity > 0.

        Returns:
            AddReceiptItemRequest: Validated request object.

        Raises:
            ValueError: If combined good and damaged quantity is zero or less.
        """
        if self.good_qty < 0 or self.damaged_qty < 0:
            raise ValueError("Quantities cannot be negative.")
        if self.good_qty + self.damaged_qty <= 0:
            raise ValueError("At least one unit (good or damaged) must be received.")
        self.upc = self.upc.strip()
        return self
