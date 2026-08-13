"""Safe typed responses for inbound receiving voice interpretation previews."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, StrictInt, model_validator


class ReceivingVoiceIntentType(str, Enum):
    """Allow only narrow non-mutating receiving interpretation outcomes."""

    RECEIVING_QUANTITY = "RECEIVING_QUANTITY"
    UNCLEAR = "UNCLEAR"
    UNSUPPORTED = "UNSUPPORTED"


class ReceivingVoiceIntent(BaseModel):
    """Represent server-validated receiving quantities extracted from speech."""

    type: ReceivingVoiceIntentType = Field(..., description="Strict voice interpretation outcome")
    good_qty: Optional[StrictInt] = Field(None, ge=0, description="Validated good quantity")
    damaged_qty: Optional[StrictInt] = Field(None, ge=0, description="Validated damaged quantity")

    @model_validator(mode="after")
    def validate_receiving_quantities(self) -> "ReceivingVoiceIntent":
        """Require usable, non-zero integer quantities only for receiving previews.

        Returns:
            ReceivingVoiceIntent: Validated intent model.

        Raises:
            ValueError: If a receiving quantity intent has invalid quantities.
        """
        if self.type != ReceivingVoiceIntentType.RECEIVING_QUANTITY:
            if self.good_qty is not None or self.damaged_qty is not None:
                raise ValueError("Only receiving quantity intents may include quantities")
            return self
        if self.good_qty is None or self.damaged_qty is None:
            raise ValueError("Receiving quantity intent requires both quantities")
        if self.good_qty + self.damaged_qty <= 0:
            raise ValueError("At least one unit must be received")
        return self


class ReceivingVoiceContext(BaseModel):
    """Return safe receipt and product context for a voice preview."""

    receipt_id: str
    product_id: str
    product_name: str
    upc: str


class ReceivingVoicePreviewResponse(BaseModel):
    """Return a read-only voice interpretation that still requires user confirmation."""

    transcript: str = Field(..., description="Safe transcript returned by the STT provider")
    intent: ReceivingVoiceIntent
    context: ReceivingVoiceContext
    requires_confirmation: bool = Field(..., description="Whether the existing item API may be confirmed")
    message: Optional[str] = Field(None, description="Friendly clarification or unsupported-command message")
    request_id: str = Field(..., description="Trace-safe server-generated request identifier")
