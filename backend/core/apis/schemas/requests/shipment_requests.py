"""
shipment_requests.py — Pydantic request validation schemas for parcel shipment creation.

Defines input contracts for preparing parcel shipments.
"""

from typing import Optional
from pydantic import BaseModel, Field, model_validator


class CreateShipmentRequest(BaseModel):
    """
    Request payload for preparing an order shipment.

    Requires carrier, tracking number, physical dimensions, and weight.
    """

    carrier: str = Field(..., min_length=1, description="Shipping carrier (UPS, FedEx, USPS, DHL)")
    tracking_number: str = Field(..., min_length=1, description="Carrier tracking number")
    weight: float = Field(0.0, ge=0.0, description="Package weight in lbs")
    length: float = Field(0.0, ge=0.0, description="Package length in inches")
    width: float = Field(0.0, ge=0.0, description="Package width in inches")
    height: float = Field(0.0, ge=0.0, description="Package height in inches")
    label_reference: Optional[str] = Field(None, description="Optional label identifier or URL")

    @model_validator(mode="after")
    def validate_strings(self) -> "CreateShipmentRequest":
        """Clean string inputs."""
        self.carrier = self.carrier.strip()
        self.tracking_number = self.tracking_number.strip()
        return self
