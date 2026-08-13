"""
user_model.py — ODMantic model for the users collection.

This file defines the User document structure stored in MongoDB.
ODMantic automatically maps this class to a "user" collection.

Key concepts:
  - Inherit from Base (odmantic.Model) to get MongoDB mapping
  - Use Python type hints — ODMantic validates them at runtime
  - Enums enforce controlled vocabulary (status, role)
  - Optional fields with defaults keep documents forward-compatible
"""

from odmantic import Model, Field, Index, ObjectId
from typing import Optional
from datetime import datetime, timezone
from pydantic import EmailStr
from enum import Enum


class UserStatus(str, Enum):
    """Lifecycle state of a user account."""

    ACTIVE = "ACTIVE"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    SUSPENDED = "SUSPENDED"
    BLOCKED = "BLOCKED"


class UserRole(str, Enum):
    """Warehouse management access-control role assigned to a user."""

    OWNER = "OWNER"
    MANAGER = "MANAGER"
    RECEIVING_STAFF = "RECEIVING_STAFF"
    FULFILLMENT_STAFF = "FULFILLMENT_STAFF"


class User(Model):
    """
    MongoDB document model for users.

    Fields:
        first_name, last_name — display name
        email — unique identifier for login (EmailStr validates format)
        hashed_password — bcrypt hash; never store plain text
        mobile_number — optional contact number
        role — UserRole enum (default FULFILLMENT_STAFF)
        status — UserStatus enum (default PENDING_VERIFICATION)
        warehouse_ids — warehouse ObjectIds this user can access
        created_at / updated_at — UTC timestamps for auditing

    ODMantic Notes:
        - `id` field (ObjectId) is added automatically
        - Collection name defaults to lowercase class name ("user")
        - Use engine.find_one(User, User.email == email) for queries
        - email has a unique index to protect concurrent registration
    """

    first_name: str
    last_name: str
    email: EmailStr
    hashed_password: str
    mobile_number: Optional[str] = None
    role: UserRole = UserRole.FULFILLMENT_STAFF
    status: UserStatus = UserStatus.PENDING_VERIFICATION
    warehouse_ids: list[ObjectId] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "collection": "users",
        "indexes": lambda: [Index(User.email, unique=True)],
    }
