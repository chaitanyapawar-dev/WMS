"""Request schemas for warehouse master data APIs."""

from pydantic import BaseModel, Field

from core.models.warehouse_model import WarehouseStatus


class WarehouseStatusUpdate(BaseModel):
    """Request body used to update warehouse status."""

    status: WarehouseStatus = Field(description="New warehouse lifecycle status")
