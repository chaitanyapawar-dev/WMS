"""Request schemas for the read-only Whitfield AI assistant."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AIChatRequest(BaseModel):
    """Validate one natural-language question for the AI assistant.

    Optional UI context can improve phrasing but is never authorization input.
    """

    message: str = Field(..., min_length=1, max_length=2000, description="Warehouse question")
    current_route: Optional[str] = Field(None, max_length=256, description="Optional current UI route")
    active_warehouse_id: Optional[str] = Field(
        None,
        max_length=64,
        description="Optional UI warehouse selection; never trusted for authorization",
    )

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        """Normalize the submitted assistant message.

        Rejects whitespace-only content after trimming the user-provided text.

        Args:
            value: Raw assistant message.

        Returns:
            str: Trimmed assistant message.

        Raises:
            ValueError: If the message is blank after trimming.
        """
        normalized = value.strip()
        if not normalized:
            raise ValueError("Message cannot be blank")
        return normalized
