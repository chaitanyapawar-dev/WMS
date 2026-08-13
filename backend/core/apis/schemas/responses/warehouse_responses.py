"""Response schemas for warehouse master data APIs."""

from datetime import datetime

from pydantic import BaseModel


class WarehouseResponse(BaseModel):
    """Safe warehouse response model."""

    id: str
    name: str
    code: str
    city: str
    state: str
    status: str
    created_at: datetime
    updated_at: datetime
