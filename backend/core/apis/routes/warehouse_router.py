"""Routes for warehouse master data APIs."""

from fastapi import APIRouter, Depends, HTTPException, status

from commons.auth import require_roles
from core import logger
from core.apis.schemas.responses.warehouse_responses import WarehouseResponse
from core.controllers.warehouse_controller import WarehouseController
from core.models.user_model import User, UserRole

logging = logger(__name__)
warehouse_router = APIRouter()

ALL_WMS_ROLES = [
    UserRole.OWNER,
    UserRole.MANAGER,
    UserRole.RECEIVING_STAFF,
    UserRole.FULFILLMENT_STAFF,
]


@warehouse_router.get(
    "/v1/warehouses",
    status_code=status.HTTP_200_OK,
    response_model=list[WarehouseResponse],
)
async def list_warehouses(
    current_user: User = Depends(require_roles(ALL_WMS_ROLES)),
):
    """
    List warehouses for authenticated WMS users.

    Args:
        current_user: Authenticated user authorized for warehouse reads.

    Returns:
        list[WarehouseResponse]: Safe warehouse records.

    Raises:
        HTTPException 401: Missing or invalid authentication.
        HTTPException 403: User role is not allowed.
        HTTPException 500: Unexpected server error.
    """
    try:
        logging.info("Calling GET /v1/warehouses endpoint")
        return await WarehouseController().list_warehouses(current_user=current_user)
    except HTTPException as httperror:
        logging.error(f"Error in GET /v1/warehouses endpoint: {httperror}")
        raise httperror
    except Exception as error:
        logging.error(f"Error in GET /v1/warehouses endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@warehouse_router.get(
    "/v1/warehouses/{warehouse_id}",
    status_code=status.HTTP_200_OK,
    response_model=WarehouseResponse,
)
async def get_warehouse(
    warehouse_id: str,
    current_user: User = Depends(require_roles(ALL_WMS_ROLES)),
):
    """
    Get a warehouse by ID for authenticated WMS users.

    Args:
        warehouse_id: Warehouse ObjectId as a string.
        current_user: Authenticated user authorized for warehouse reads.

    Returns:
        WarehouseResponse: Safe warehouse record.

    Raises:
        HTTPException 401: Missing or invalid authentication.
        HTTPException 403: User role is not allowed.
        HTTPException 404: Warehouse not found.
        HTTPException 500: Unexpected server error.
    """
    try:
        logging.info(f"Calling GET /v1/warehouses/{warehouse_id} endpoint")
        return await WarehouseController().get_warehouse(
            warehouse_id=warehouse_id, current_user=current_user
        )
    except HTTPException as httperror:
        logging.error(
            f"Error in GET /v1/warehouses/{warehouse_id} endpoint: {httperror}"
        )
        raise httperror
    except Exception as error:
        logging.error(f"Error in GET /v1/warehouses/{warehouse_id} endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
