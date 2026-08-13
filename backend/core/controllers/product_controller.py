"""Controller for product master data APIs."""

from fastapi import HTTPException, status
from odmantic import ObjectId
from pymongo.errors import DuplicateKeyError

from core import logger
from core.cruds.product_crud import CRUDProduct
from core.cruds.seller_crud import CRUDSeller
from core.models.product_model import Product, ProductStatus

logging = logger(__name__)


class ProductController:
    """Business orchestration for product master data."""

    def __init__(self):
        """
        Initialize product controller dependencies.

        Creates product and seller CRUD helpers used by controller methods.
        """
        self.crud_product = CRUDProduct()
        self.crud_seller = CRUDSeller()

    def _to_response(self, product: Product) -> dict:
        """
        Convert a product model to a safe response dictionary.

        Args:
            product: Product model instance.

        Returns:
            dict: Safe product response payload.
        """
        return {
            "id": str(product.id),
            "seller_id": str(product.seller_id),
            "name": product.name,
            "sku": product.sku,
            "upc": product.upc,
            "description": product.description,
            "status": product.status,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
        }

    def _parse_seller_id(self, seller_id: str) -> ObjectId:
        """
        Parse a seller ObjectId string.

        Args:
            seller_id: Seller ObjectId as a string.

        Returns:
            ObjectId: Parsed seller ObjectId.

        Raises:
            HTTPException 400: Seller ID is invalid.
        """
        try:
            return ObjectId(seller_id)
        except Exception:
            logging.warning("Invalid seller ID rejected for product")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid seller_id",
            )

    async def create_product(self, product_data: dict) -> dict:
        """
        Create a product if seller, SKU, and UPC constraints are valid.

        Args:
            product_data: Product creation payload.

        Returns:
            dict: Safe created product response payload.

        Raises:
            HTTPException 400: Invalid seller ID.
            HTTPException 404: Seller not found.
            HTTPException 409: SKU or UPC conflict.
            HTTPException 500: Unexpected creation failure.
        """
        try:
            logging.info("Executing ProductController.create_product")
            seller_object_id = self._parse_seller_id(product_data["seller_id"])
            seller = await self.crud_seller.get_by_id(id=str(seller_object_id))
            if not seller:
                logging.warning(f"Seller not found for product: {seller_object_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Seller not found",
                )

            existing_sku = await self.crud_product.get_by_seller_and_sku(
                seller_id=seller_object_id, sku=product_data["sku"]
            )
            if existing_sku:
                logging.warning("Duplicate seller SKU rejected")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Product SKU already exists for this seller",
                )

            existing_upc = await self.crud_product.get_by_upc(upc=product_data["upc"])
            if existing_upc:
                logging.warning("Duplicate UPC rejected")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Product UPC already exists",
                )

            data = dict(product_data)
            data["seller_id"] = seller_object_id
            product = await self.crud_product.create(obj_in=data)
            return self._to_response(product)
        except HTTPException:
            raise
        except DuplicateKeyError:
            logging.warning("Duplicate product key rejected by database")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product SKU or UPC already exists",
            )
        except Exception as error:
            logging.error(f"Error in ProductController.create_product: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def list_products(self) -> list[dict]:
        """
        List all products.

        Returns:
            list[dict]: Safe product response payloads.

        Raises:
            HTTPException 500: Unexpected list failure.
        """
        try:
            logging.info("Executing ProductController.list_products")
            products = await self.crud_product.get_all()
            return [self._to_response(product) for product in products]
        except Exception as error:
            logging.error(f"Error in ProductController.list_products: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def get_product(self, product_id: str) -> dict:
        """
        Get a product by ID.

        Args:
            product_id: Product ObjectId as a string.

        Returns:
            dict: Safe product response payload.

        Raises:
            HTTPException 404: Product not found.
            HTTPException 500: Unexpected lookup failure.
        """
        try:
            logging.info("Executing ProductController.get_product")
            product = await self.crud_product.get_by_id(id=product_id)
            if not product:
                logging.warning(f"Product not found: {product_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found",
                )
            return self._to_response(product)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ProductController.get_product: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def lookup_by_upc(self, upc: str) -> dict:
        """
        Lookup a product by UPC.

        Args:
            upc: UPC value from warehouse scanning.

        Returns:
            dict: Safe product response payload.

        Raises:
            HTTPException 404: Product not found.
            HTTPException 500: Unexpected lookup failure.
        """
        try:
            logging.info("Executing ProductController.lookup_by_upc")
            product = await self.crud_product.get_by_upc(upc=upc)
            if not product:
                logging.warning(f"Product UPC not found: {upc}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found",
                )
            return self._to_response(product)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ProductController.lookup_by_upc: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def update_product_status(
        self, product_id: str, new_status: ProductStatus
    ) -> dict:
        """
        Update a product status.

        Args:
            product_id: Product ObjectId as a string.
            new_status: New product status value.

        Returns:
            dict: Safe updated product response payload.

        Raises:
            HTTPException 404: Product not found.
            HTTPException 500: Unexpected update failure.
        """
        try:
            logging.info("Executing ProductController.update_product_status")
            product = await self.crud_product.get_by_id(id=product_id)
            if not product:
                logging.warning(f"Product not found: {product_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found",
                )
            updated = await self.crud_product.update_status(
                product=product, status=new_status
            )
            return self._to_response(updated)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ProductController.update_product_status: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )
