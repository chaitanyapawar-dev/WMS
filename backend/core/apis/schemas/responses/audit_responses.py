"""
audit_responses.py — Pydantic response serialization schemas for audit log queries.

Defines client-facing data contracts for security and operational audit records.
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, field_validator


class AuditLogResponse(BaseModel):
    """
    Response schema for an audit log record.

    Exposes user actor, action, target entity, state changes, and timestamp.
    """

    id: str
    user_id: str
    user_role: str
    warehouse_id: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    old_state: Optional[dict[str, Any]] = None
    new_state: Optional[dict[str, Any]] = None
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("id", "user_id", "warehouse_id", mode="before")
    @classmethod
    def convert_objectid(cls, v):
        if v is not None:
            return str(v)
        return v
