"""CRUD operations for product master data."""

from datetime import datetime, timezone
from typing import Optional

from odmantic import ObjectId

from core import logger
from core.cruds.base import CRUDBase
from core.models.product_model import Product, ProductStatus

logging = logger(__name__)


class CRUDProduct(CRUDBase[Product, dict, dict]):
    """Database access layer for product records."""

    def __init__(self):
        """
        Initialize product CRUD helper.

        Binds the shared ODMantic engine to the Product model.
        """
        super().__init__(model=Product)

    async def create(self, *, obj_in: dict) -> Product:
        """
        Create a product record.

        Args:
            obj_in: Product creation data.

        Returns:
            Product: Created product record.
        """
        try:
            logging.info("Executing CRUDProduct.create")
            product = Product(**obj_in)
            return await self.engine.save(product)
        except Exception as error:
            logging.error(f"Error in CRUDProduct.create: {error}")
            raise

    async def get_by_id(self, *, id: str) -> Optional[Product]:
        """
        Read a product by ObjectId string.

        Args:
            id: Product ObjectId as a string.

        Returns:
            Product | None: Product record if found.
        """
        try:
            logging.info("Executing CRUDProduct.get_by_id")
            try:
                object_id = ObjectId(id)
            except Exception:
                logging.warning("Invalid product ObjectId rejected")
                return None
            return await self.engine.find_one(Product, Product.id == object_id)
        except Exception as error:
            logging.error(f"Error in CRUDProduct.get_by_id: {error}")
            raise

    async def get_by_seller_and_sku(
        self, *, seller_id: ObjectId, sku: str
    ) -> Optional[Product]:
        """
        Read a product by seller and SKU.

        Args:
            seller_id: Seller ObjectId.
            sku: Seller-specific SKU.

        Returns:
            Product | None: Product record if found.
        """
        try:
            logging.info("Executing CRUDProduct.get_by_seller_and_sku")
            return await self.engine.find_one(
                Product, Product.seller_id == seller_id, Product.sku == sku
            )
        except Exception as error:
            logging.error(f"Error in CRUDProduct.get_by_seller_and_sku: {error}")
            raise

    async def get_by_upc(self, *, upc: str) -> Optional[Product]:
        """
        Read a product by UPC.

        Args:
            upc: Product UPC value.

        Returns:
            Product | None: Product record if found.
        """
        try:
            logging.info("Executing CRUDProduct.get_by_upc")
            return await self.engine.find_one(Product, Product.upc == upc)
        except Exception as error:
            logging.error(f"Error in CRUDProduct.get_by_upc: {error}")
            raise

    async def get_by_sku(self, *, sku: str) -> Optional[Product]:
        """
        Read a product by SKU string.

        Args:
            sku: Product SKU value.

        Returns:
            Product | None: Product record if found.
        """
        try:
            logging.info("Executing CRUDProduct.get_by_sku")
            return await self.engine.find_one(Product, Product.sku == sku)
        except Exception as error:
            logging.error(f"Error in CRUDProduct.get_by_sku: {error}")
            raise

    async def get_all(self) -> list[Product]:
        """
        Read all product records.

        Returns:
            list[Product]: Products sorted by SKU.
        """
        try:
            logging.info("Executing CRUDProduct.get_all")
            products = await self.engine.find(Product)
            return sorted(products, key=lambda product: product.sku)
        except Exception as error:
            logging.error(f"Error in CRUDProduct.get_all: {error}")
            raise

    async def update_status(
        self, *, product: Product, status: ProductStatus
    ) -> Product:
        """
        Update a product status.

        Args:
            product: Existing product record.
            status: New product status.

        Returns:
            Product: Updated product record.
        """
        try:
            logging.info("Executing CRUDProduct.update_status")
            product.status = status
            product.updated_at = datetime.now(timezone.utc)
            return await self.engine.save(product)
        except Exception as error:
            logging.error(f"Error in CRUDProduct.update_status: {error}")
            raise
