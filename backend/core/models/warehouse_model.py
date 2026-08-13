"""Warehouse persistence model for Whitfield WMS master data."""

from datetime import datetime, timezone
from enum import Enum

from odmantic import Field, Index, Model


class WarehouseStatus(str, Enum):
    """Lifecycle status for warehouse records."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Warehouse(Model):
    """
    MongoDB document model for warehouse master data.

    Stores the warehouse identity and location fields needed for access scope.
    """

    name: str
    code: str
    city: str
    state: str
    status: WarehouseStatus = WarehouseStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "collection": "warehouses",
        "indexes": lambda: [Index(Warehouse.code, unique=True)],
    }
