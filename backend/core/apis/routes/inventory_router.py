"""
inventory_router.py — FastAPI router for inventory querying and controlled adjustment endpoints.

Exposes HTTP routes for listing stock snapshots, retrieving inventory detail,
performing manager stock adjustments, and reading stock movement history.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from commons.auth import get_current_user, require_roles
from core import logger
from core.apis.schemas.requests.inventory_requests import AdjustInventoryRequest
from core.apis.schemas.responses.inventory_responses import InventoryResponse
from core.apis.schemas.responses.movement_responses import InventoryMovementResponse
from core.controllers.inventory_controller import InventoryController
from core.models.user_model import User, UserRole

logging = logger(__name__)

inventory_router = APIRouter(prefix="/v1/inventory")


@inventory_router.get(
    "",
    response_model=list[InventoryResponse],
    status_code=status.HTTP_200_OK,
    summary="List inventory stock levels",
    description="List inventory snapshots filtered by warehouse, seller, or product within user scope.",
)
async def list_inventory(
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse ID"),
    seller_id: Optional[str] = Query(None, description="Filter by seller ID"),
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    current_user: User = Depends(get_current_user),
) -> list[InventoryResponse]:
    """
    Route handler for GET /v1/inventory.

    Args:
        warehouse_id: Optional warehouse ID filter.
        seller_id: Optional seller ID filter.
        product_id: Optional product ID filter.
        current_user: Authenticated user.

    Returns:
        list[InventoryResponse]: List of inventory snapshots.

    Raises:
        HTTPException: Standardized domain or HTTP exception.
    """
    try:
        logging.info("Calling GET /v1/inventory endpoint")
        return await InventoryController().list_inventory(
            warehouse_id=warehouse_id,
            seller_id=seller_id,
            product_id=product_id,
            current_user=current_user,
        )
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in GET /v1/inventory endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@inventory_router.get(
    "/{inventory_id}",
    response_model=InventoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get inventory details",
    description="Get detailed stock snapshot by inventory ID.",
)
async def get_inventory_by_id(
    inventory_id: str,
    current_user: User = Depends(get_current_user),
) -> InventoryResponse:
    """
    Route handler for GET /v1/inventory/{inventory_id}.

    Args:
        inventory_id: Inventory ObjectId string.
        current_user: Authenticated user.

    Returns:
        InventoryResponse: Inventory snapshot detail payload.

    Raises:
        HTTPException: Standardized domain or HTTP exception.
    """
    try:
        logging.info(f"Calling GET /v1/inventory/{inventory_id} endpoint")
        return await InventoryController().get_inventory_by_id(
            inventory_id=inventory_id, current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in GET /v1/inventory/{inventory_id} endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@inventory_router.post(
    "/{inventory_id}/adjust",
    response_model=InventoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform controlled inventory adjustment",
    description="Adjust stock quantity on_hand with required operational reason. Only OWNER and MANAGER roles permitted.",
)
async def adjust_inventory(
    inventory_id: str,
    request: AdjustInventoryRequest,
    current_user: User = Depends(require_roles([UserRole.OWNER, UserRole.MANAGER])),
) -> InventoryResponse:
    """
    Route handler for POST /v1/inventory/{inventory_id}/adjust.

    Args:
        inventory_id: Inventory ObjectId string.
        request: Adjustment delta and reason.
        current_user: Authenticated user with OWNER or MANAGER role.

    Returns:
        InventoryResponse: Updated inventory snapshot.

    Raises:
        HTTPException: Standardized domain or HTTP exception.
    """
    try:
        logging.info(f"Calling POST /v1/inventory/{inventory_id}/adjust endpoint")
        return await InventoryController().adjust_inventory(
            inventory_id=inventory_id, request=request, current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in POST /v1/inventory/{inventory_id}/adjust endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@inventory_router.get(
    "/{inventory_id}/movements",
    response_model=list[InventoryMovementResponse],
    status_code=status.HTTP_200_OK,
    summary="Get stock movement history",
    description="List chronological stock movement records for an inventory snapshot.",
)
async def list_inventory_movements(
    inventory_id: str,
    movement_type: Optional[str] = Query(None, description="Optional movement type filter"),
    current_user: User = Depends(get_current_user),
) -> list[InventoryMovementResponse]:
    """
    Route handler for GET /v1/inventory/{inventory_id}/movements.

    Args:
        inventory_id: Inventory ObjectId string.
        movement_type: Optional movement type filter.
        current_user: Authenticated user.

    Returns:
        list[InventoryMovementResponse]: Movement history records.

    Raises:
        HTTPException: Standardized domain or HTTP exception.
    """
    try:
        logging.info(f"Calling GET /v1/inventory/{inventory_id}/movements endpoint")
        return await InventoryController().list_movements(
            inventory_id=inventory_id,
            movement_type=movement_type,
            current_user=current_user,
        )
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in GET /v1/inventory/{inventory_id}/movements endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
