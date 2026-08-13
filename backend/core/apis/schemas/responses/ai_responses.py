"""Typed response schemas for the read-only Whitfield AI assistant."""

from pydantic import BaseModel, Field


class AISource(BaseModel):
    """Represent a safe citation for approved Whitfield SOP evidence."""

    title: str = Field(..., description="Human-readable approved SOP title")
    source: str = Field(..., description="Approved SOP filename")
    section: str = Field(..., description="Approved SOP section heading")


class AIChatResponse(BaseModel):
    """Return a grounded assistant answer without provider implementation details.

    Exposes only the answer, approved tool names used, and a trace-safe request ID.
    """

    answer: str = Field(..., description="Grounded, user-facing assistant answer")
    tool_calls: list[str] = Field(default_factory=list, description="Approved tools used for the answer")
    sources: list[AISource] = Field(default_factory=list, description="Approved SOP sources used for the answer")
    request_id: str = Field(..., description="Trace-safe request identifier")
