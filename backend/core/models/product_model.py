"""Product persistence model for Whitfield WMS master data."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from odmantic import Field, Index, Model, ObjectId


class ProductStatus(str, Enum):
    """Lifecycle status for product records."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Product(Model):
    """
    MongoDB document model for product master data.

    Stores seller-owned SKU and UPC data used by warehouse scanning workflows.
    """

    seller_id: ObjectId
    name: str
    sku: str
    upc: str
    description: Optional[str] = None
    status: ProductStatus = ProductStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "collection": "products",
        "indexes": lambda: [
            Index(Product.seller_id, Product.sku, unique=True),
            Index(Product.upc, unique=True),
            Index(Product.seller_id, Product.sku, Product.upc, unique=True),
        ],
    }
