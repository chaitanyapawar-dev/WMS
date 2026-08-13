"""CRUD operations for seller master data."""

from datetime import datetime, timezone
from typing import Optional

from odmantic import ObjectId

from core import logger
from core.cruds.base import CRUDBase
from core.models.seller_model import Seller, SellerStatus

logging = logger(__name__)


class CRUDSeller(CRUDBase[Seller, dict, dict]):
    """Database access layer for seller records."""

    def __init__(self):
        """
        Initialize seller CRUD helper.

        Binds the shared ODMantic engine to the Seller model.
        """
        super().__init__(model=Seller)

    async def create(self, *, obj_in: dict) -> Seller:
        """
        Create a seller record.

        Args:
            obj_in: Seller creation data.

        Returns:
            Seller: Created seller record.
        """
        try:
            logging.info("Executing CRUDSeller.create")
            seller = Seller(**obj_in)
            return await self.engine.save(seller)
        except Exception as error:
            logging.error(f"Error in CRUDSeller.create: {error}")
            raise

    async def get_by_id(self, *, id: str) -> Optional[Seller]:
        """
        Read a seller by ObjectId string.

        Args:
            id: Seller ObjectId as a string.

        Returns:
            Seller | None: Seller record if found.
        """
        try:
            logging.info("Executing CRUDSeller.get_by_id")
            try:
                object_id = ObjectId(id)
            except Exception:
                logging.warning("Invalid seller ObjectId rejected")
                return None
            return await self.engine.find_one(Seller, Seller.id == object_id)
        except Exception as error:
            logging.error(f"Error in CRUDSeller.get_by_id: {error}")
            raise

    async def get_by_code(self, *, seller_code: str) -> Optional[Seller]:
        """
        Read a seller by unique seller code.

        Args:
            seller_code: Seller code.

        Returns:
            Seller | None: Seller record if found.
        """
        try:
            logging.info("Executing CRUDSeller.get_by_code")
            return await self.engine.find_one(
                Seller, Seller.seller_code == seller_code
            )
        except Exception as error:
            logging.error(f"Error in CRUDSeller.get_by_code: {error}")
            raise

    async def get_all(self) -> list[Seller]:
        """
        Read all seller records.

        Returns:
            list[Seller]: Sellers sorted by seller code.
        """
        try:
            logging.info("Executing CRUDSeller.get_all")
            sellers = await self.engine.find(Seller)
            return sorted(sellers, key=lambda seller: seller.seller_code)
        except Exception as error:
            logging.error(f"Error in CRUDSeller.get_all: {error}")
            raise

    async def update_status(self, *, seller: Seller, status: SellerStatus) -> Seller:
        """
        Update a seller status.

        Args:
            seller: Existing seller record.
            status: New seller status.

        Returns:
            Seller: Updated seller record.
        """
        try:
            logging.info("Executing CRUDSeller.update_status")
            seller.status = status
            seller.updated_at = datetime.now(timezone.utc)
            return await self.engine.save(seller)
        except Exception as error:
            logging.error(f"Error in CRUDSeller.update_status: {error}")
            raise
