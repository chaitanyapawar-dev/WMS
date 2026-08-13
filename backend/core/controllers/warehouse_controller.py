"""Controller for warehouse master data APIs."""

from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from commons.auth import can_access_warehouse
from core import logger
from core.cruds.warehouse_crud import CRUDWarehouse
from core.models.warehouse_model import Warehouse, WarehouseStatus
from core.models.user_model import User

logging = logger(__name__)


class WarehouseController:
    """Business orchestration for warehouse master data."""

    def __init__(self):
        """
        Initialize warehouse controller dependencies.

        Creates the warehouse CRUD helper used by controller methods.
        """
        self.crud_warehouse = CRUDWarehouse()

    def _to_response(self, warehouse: Warehouse) -> dict:
        """
        Convert a warehouse model to a safe response dictionary.

        Args:
            warehouse: Warehouse model instance.

        Returns:
            dict: Safe warehouse response payload.
        """
        return {
            "id": str(warehouse.id),
            "name": warehouse.name,
            "code": warehouse.code,
            "city": warehouse.city,
            "state": warehouse.state,
            "status": warehouse.status,
            "created_at": warehouse.created_at,
            "updated_at": warehouse.updated_at,
        }

    async def list_warehouses(self, current_user: User) -> list[dict]:
        """
        List all warehouses.

        Args:
            current_user: Authenticated user used for warehouse scope filtering.

        Returns:
            list[dict]: Safe warehouse response payloads.

        Raises:
            HTTPException 500: Unexpected list failure.
        """
        try:
            logging.info("Executing WarehouseController.list_warehouses")
            warehouses = await self.crud_warehouse.get_all()
            scoped_warehouses = [
                warehouse
                for warehouse in warehouses
                if can_access_warehouse(current_user, warehouse.id)
            ]
            return [self._to_response(warehouse) for warehouse in scoped_warehouses]
        except Exception as error:
            logging.error(f"Error in WarehouseController.list_warehouses: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def get_warehouse(self, warehouse_id: str, current_user: User) -> dict:
        """
        Get a warehouse by ID.

        Args:
            warehouse_id: Warehouse ObjectId as a string.
            current_user: Authenticated user used for warehouse scope enforcement.

        Returns:
            dict: Safe warehouse response payload.

        Raises:
            HTTPException 404: Warehouse not found.
            HTTPException 500: Unexpected lookup failure.
        """
        try:
            logging.info("Executing WarehouseController.get_warehouse")
            warehouse = await self.crud_warehouse.get_by_id(id=warehouse_id)
            if not warehouse:
                logging.warning(f"Warehouse not found: {warehouse_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Warehouse not found",
                )
            if not can_access_warehouse(current_user, warehouse.id):
                logging.warning(
                    f"Warehouse access denied for user {current_user.id}: {warehouse_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this warehouse",
                )
            return self._to_response(warehouse)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in WarehouseController.get_warehouse: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def create_warehouse(self, warehouse_data: dict) -> dict:
        """
        Create a warehouse if its code is unique.

        Args:
            warehouse_data: Warehouse creation payload.

        Returns:
            dict: Safe created warehouse response payload.

        Raises:
            HTTPException 409: Warehouse code already exists.
            HTTPException 500: Unexpected creation failure.
        """
        try:
            logging.info("Executing WarehouseController.create_warehouse")
            existing = await self.crud_warehouse.get_by_code(
                code=warehouse_data["code"]
            )
            if existing:
                logging.warning("Duplicate warehouse code rejected")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Warehouse code already exists",
                )
            warehouse = await self.crud_warehouse.create(obj_in=warehouse_data)
            return self._to_response(warehouse)
        except HTTPException:
            raise
        except DuplicateKeyError:
            logging.warning("Duplicate warehouse code rejected by database")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Warehouse code already exists",
            )
        except Exception as error:
            logging.error(f"Error in WarehouseController.create_warehouse: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def update_warehouse_status(
        self, warehouse_id: str, new_status: WarehouseStatus
    ) -> dict:
        """
        Update a warehouse status.

        Args:
            warehouse_id: Warehouse ObjectId as a string.
            new_status: New warehouse status value.

        Returns:
            dict: Safe updated warehouse response payload.

        Raises:
            HTTPException 404: Warehouse not found.
            HTTPException 500: Unexpected update failure.
        """
        try:
            logging.info("Executing WarehouseController.update_warehouse_status")
            warehouse = await self.crud_warehouse.get_by_id(id=warehouse_id)
            if not warehouse:
                logging.warning(f"Warehouse not found: {warehouse_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Warehouse not found",
                )
            updated = await self.crud_warehouse.update_status(
                warehouse=warehouse, status=new_status
            )
            return self._to_response(updated)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(
                f"Error in WarehouseController.update_warehouse_status: {error}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )
