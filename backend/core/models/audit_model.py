"""
audit_model.py — ODMantic model for security and operational audit logs.

This module defines the AuditLog document structure stored in MongoDB.
ODMantic maps this model to the "audit_logs" collection.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from odmantic import Field, Index, Model, ObjectId


class AuditLog(Model):
    """
    MongoDB document model for security and business action audit trails.

    Records who performed sensitive operational actions, target entity IDs,
    state deltas, timestamps, and optional context.
    """

    user_id: ObjectId
    user_role: str
    warehouse_id: Optional[ObjectId] = None
    action: str
    entity_type: str
    entity_id: str
    old_state: Optional[dict[str, Any]] = None
    new_state: Optional[dict[str, Any]] = None
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "collection": "audit_logs",
        "indexes": lambda: [
            Index(AuditLog.created_at),
            Index(AuditLog.user_id),
            Index(AuditLog.entity_type, AuditLog.entity_id),
            Index(AuditLog.warehouse_id),
        ],
    }
