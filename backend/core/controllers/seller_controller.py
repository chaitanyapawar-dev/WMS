"""Controller for seller master data APIs."""

from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from core import logger
from core.cruds.seller_crud import CRUDSeller
from core.models.seller_model import Seller, SellerStatus

logging = logger(__name__)


class SellerController:
    """Business orchestration for seller master data."""

    def __init__(self):
        """
        Initialize seller controller dependencies.

        Creates the seller CRUD helper used by controller methods.
        """
        self.crud_seller = CRUDSeller()

    def _to_response(self, seller: Seller) -> dict:
        """
        Convert a seller model to a safe response dictionary.

        Args:
            seller: Seller model instance.

        Returns:
            dict: Safe seller response payload.
        """
        return {
            "id": str(seller.id),
            "name": seller.name,
            "seller_code": seller.seller_code,
            "email": seller.email,
            "phone": seller.phone,
            "status": seller.status,
            "created_at": seller.created_at,
            "updated_at": seller.updated_at,
        }

    async def create_seller(self, seller_data: dict) -> dict:
        """
        Create a seller if the seller code is unique.

        Args:
            seller_data: Seller creation payload.

        Returns:
            dict: Safe created seller response payload.

        Raises:
            HTTPException 409: Seller code already exists.
            HTTPException 500: Unexpected creation failure.
        """
        try:
            logging.info("Executing SellerController.create_seller")
            existing = await self.crud_seller.get_by_code(
                seller_code=seller_data["seller_code"]
            )
            if existing:
                logging.warning("Duplicate seller code rejected")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Seller code already exists",
                )
            seller = await self.crud_seller.create(obj_in=seller_data)
            return self._to_response(seller)
        except HTTPException:
            raise
        except DuplicateKeyError:
            logging.warning("Duplicate seller code rejected by database")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Seller code already exists",
            )
        except Exception as error:
            logging.error(f"Error in SellerController.create_seller: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def list_sellers(self) -> list[dict]:
        """
        List all sellers.

        Returns:
            list[dict]: Safe seller response payloads.

        Raises:
            HTTPException 500: Unexpected list failure.
        """
        try:
            logging.info("Executing SellerController.list_sellers")
            sellers = await self.crud_seller.get_all()
            return [self._to_response(seller) for seller in sellers]
        except Exception as error:
            logging.error(f"Error in SellerController.list_sellers: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def get_seller(self, seller_id: str) -> dict:
        """
        Get a seller by ID.

        Args:
            seller_id: Seller ObjectId as a string.

        Returns:
            dict: Safe seller response payload.

        Raises:
            HTTPException 404: Seller not found.
            HTTPException 500: Unexpected lookup failure.
        """
        try:
            logging.info("Executing SellerController.get_seller")
            seller = await self.crud_seller.get_by_id(id=seller_id)
            if not seller:
                logging.warning(f"Seller not found: {seller_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Seller not found",
                )
            return self._to_response(seller)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in SellerController.get_seller: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def update_seller_status(
        self, seller_id: str, new_status: SellerStatus
    ) -> dict:
        """
        Update a seller status.

        Args:
            seller_id: Seller ObjectId as a string.
            new_status: New seller status value.

        Returns:
            dict: Safe updated seller response payload.

        Raises:
            HTTPException 404: Seller not found.
            HTTPException 500: Unexpected update failure.
        """
        try:
            logging.info("Executing SellerController.update_seller_status")
            seller = await self.crud_seller.get_by_id(id=seller_id)
            if not seller:
                logging.warning(f"Seller not found: {seller_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Seller not found",
                )
            updated = await self.crud_seller.update_status(
                seller=seller, status=new_status
            )
            return self._to_response(updated)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in SellerController.update_seller_status: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )
