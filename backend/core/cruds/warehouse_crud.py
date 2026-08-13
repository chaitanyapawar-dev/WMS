"""CRUD operations for warehouse master data."""

from datetime import datetime, timezone
from typing import Optional

from odmantic import ObjectId

from core import logger
from core.cruds.base import CRUDBase
from core.models.warehouse_model import Warehouse, WarehouseStatus

logging = logger(__name__)


class CRUDWarehouse(CRUDBase[Warehouse, dict, dict]):
    """Database access layer for warehouse records."""

    def __init__(self):
        """
        Initialize warehouse CRUD helper.

        Binds the shared ODMantic engine to the Warehouse model.
        """
        super().__init__(model=Warehouse)

    async def get_by_id(self, *, id: str) -> Optional[Warehouse]:
        """
        Read a warehouse by ObjectId string.

        Args:
            id: Warehouse ObjectId as a string.

        Returns:
            Warehouse | None: Warehouse record if found.
        """
        try:
            logging.info("Executing CRUDWarehouse.get_by_id")
            try:
                object_id = ObjectId(id)
            except Exception:
                logging.warning("Invalid warehouse ObjectId rejected")
                return None
            return await self.engine.find_one(Warehouse, Warehouse.id == object_id)
        except Exception as error:
            logging.error(f"Error in CRUDWarehouse.get_by_id: {error}")
            raise

    async def get_by_code(self, *, code: str) -> Optional[Warehouse]:
        """
        Read a warehouse by unique code.

        Args:
            code: Warehouse code.

        Returns:
            Warehouse | None: Warehouse record if found.
        """
        try:
            logging.info("Executing CRUDWarehouse.get_by_code")
            return await self.engine.find_one(Warehouse, Warehouse.code == code)
        except Exception as error:
            logging.error(f"Error in CRUDWarehouse.get_by_code: {error}")
            raise

    async def get_all(self) -> list[Warehouse]:
        """
        Read all warehouse records.

        Returns:
            list[Warehouse]: Warehouses sorted by code.
        """
        try:
            logging.info("Executing CRUDWarehouse.get_all")
            warehouses = await self.engine.find(Warehouse)
            return sorted(warehouses, key=lambda warehouse: warehouse.code)
        except Exception as error:
            logging.error(f"Error in CRUDWarehouse.get_all: {error}")
            raise

    async def create(self, *, obj_in: dict) -> Warehouse:
        """
        Create a warehouse record.

        Args:
            obj_in: Warehouse creation data.

        Returns:
            Warehouse: Created warehouse record.
        """
        try:
            logging.info("Executing CRUDWarehouse.create")
            warehouse = Warehouse(**obj_in)
            return await self.engine.save(warehouse)
        except Exception as error:
            logging.error(f"Error in CRUDWarehouse.create: {error}")
            raise

    async def update_status(
        self, *, warehouse: Warehouse, status: WarehouseStatus
    ) -> Warehouse:
        """
        Update a warehouse status.

        Args:
            warehouse: Existing warehouse record.
            status: New warehouse status.

        Returns:
            Warehouse: Updated warehouse record.
        """
        try:
            logging.info("Executing CRUDWarehouse.update_status")
            warehouse.status = status
            warehouse.updated_at = datetime.now(timezone.utc)
            return await self.engine.save(warehouse)
        except Exception as error:
            logging.error(f"Error in CRUDWarehouse.update_status: {error}")
            raise
