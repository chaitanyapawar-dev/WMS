"""
inventory_requests.py — Pydantic request validation schemas for inventory adjustments.

Defines input constraints for manager inventory adjustment operations.
"""

from pydantic import BaseModel, Field, model_validator


class AdjustInventoryRequest(BaseModel):
    """
    Request schema for performing a controlled inventory quantity adjustment.

    Requires a quantity delta (positive or negative) and a non-empty explanation reason.
    """

    delta: int = Field(..., description="Quantity delta (positive for increase, negative for decrease)")
    reason: str = Field(..., min_length=3, description="Required operational explanation reason")

    @model_validator(mode="after")
    def validate_adjustment_payload(self) -> "AdjustInventoryRequest":
        """
        Validate that delta is non-zero and reason is trimmed.

        Returns:
            AdjustInventoryRequest: Validated request object.

        Raises:
            ValueError: If delta is 0 or reason is blank.
        """
        if self.delta == 0:
            raise ValueError("Adjustment delta must be non-zero.")
        reason_clean = self.reason.strip()
        if not reason_clean:
            raise ValueError("A valid reason for stock adjustment must be provided.")
        self.reason = reason_clean
        return self
