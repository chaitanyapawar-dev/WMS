"""
receipt_router.py — FastAPI router for inbound physical receiving endpoints.

Exposes HTTP routes for receipt creation, item entry, receipt reading, and completion.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from commons.auth import get_current_user, require_roles
from core import logger
from core.apis.schemas.requests.receipt_requests import (
    AddReceiptItemRequest,
    CreateReceiptRequest,
)
from core.apis.schemas.responses.receipt_responses import ReceiptResponse
from core.controllers.receipt_controller import ReceiptController
from core.models.user_model import User, UserRole

logging = logger(__name__)

receipt_router = APIRouter(prefix="/v1/receipts")


@receipt_router.post(
    "",
    response_model=ReceiptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new inbound receipt",
    description="Create an inbound shipment receipt for a specific seller and warehouse.",
)
async def create_receipt(
    request: CreateReceiptRequest,
    current_user: User = Depends(
        require_roles([UserRole.OWNER, UserRole.MANAGER, UserRole.RECEIVING_STAFF])
    ),

) -> ReceiptResponse:
    """
    Route handler for POST /v1/receipts.

    Args:
        request: Receipt creation payload.
        current_user: Authenticated user with receiving permission.

    Returns:
        ReceiptResponse: Created receipt data.

    Raises:
        HTTPException: Standardized domain or HTTP exception.
    """
    try:
        logging.info("Calling POST /v1/receipts endpoint")
        return await ReceiptController().create_receipt(
            request=request, current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in POST /v1/receipts endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@receipt_router.post(
    "/{receipt_id}/items",
    response_model=ReceiptResponse,
    status_code=status.HTTP_200_OK,
    summary="Add or update a receipt item line by UPC",
    description="Resolves product UPC and adds or updates good/damaged quantities on an open receipt.",
)
async def add_receipt_item(
    receipt_id: str,
    request: AddReceiptItemRequest,
    current_user: User = Depends(
        require_roles([UserRole.OWNER, UserRole.MANAGER, UserRole.RECEIVING_STAFF])
    ),
) -> ReceiptResponse:
    """
    Route handler for POST /v1/receipts/{receipt_id}/items.

    Args:
        receipt_id: Receipt ObjectId string.
        request: Item entry payload.
        current_user: Authenticated user with receiving permission.

    Returns:
        ReceiptResponse: Updated receipt data.

    Raises:
        HTTPException: Standardized domain or HTTP exception.
    """
    try:
        logging.info(f"Calling POST /v1/receipts/{receipt_id}/items endpoint")
        return await ReceiptController().add_receipt_item(
            receipt_id=receipt_id, request=request, current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in POST /v1/receipts/{receipt_id}/items endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@receipt_router.get(
    "",
    response_model=list[ReceiptResponse],
    status_code=status.HTTP_200_OK,
    summary="List receipts",
    description="List receipts filtered by warehouse, seller, status, or tracking number within user scope.",
)
async def list_receipts(
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse ID"),
    seller_id: Optional[str] = Query(None, description="Filter by seller ID"),
    status_param: Optional[str] = Query(None, alias="status", description="Filter by status (DRAFT, IN_PROGRESS, COMPLETED, CANCELLED)"),
    tracking_number: Optional[str] = Query(None, description="Filter by tracking number"),
    current_user: User = Depends(get_current_user),
) -> list[ReceiptResponse]:
    """
    Route handler for GET /v1/receipts.

    Args:
        warehouse_id: Optional warehouse ID filter.
        seller_id: Optional seller ID filter.
        status_param: Optional status filter.
        tracking_number: Optional tracking number filter.
        current_user: Authenticated user.

    Returns:
        list[ReceiptResponse]: List of receipts.

    Raises:
        HTTPException: Standardized domain or HTTP exception.
    """
    try:
        logging.info("Calling GET /v1/receipts endpoint")
        return await ReceiptController().list_receipts(
            warehouse_id=warehouse_id,
            seller_id=seller_id,
            status_param=status_param,
            tracking_number=tracking_number,
            current_user=current_user,
        )
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in GET /v1/receipts endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@receipt_router.get(
    "/{receipt_id}",
    response_model=ReceiptResponse,
    status_code=status.HTTP_200_OK,
    summary="Get receipt details",
    description="Get detailed receipt payload including line items.",
)
async def get_receipt_by_id(
    receipt_id: str,
    current_user: User = Depends(get_current_user),
) -> ReceiptResponse:
    """
    Route handler for GET /v1/receipts/{receipt_id}.

    Args:
        receipt_id: Receipt ObjectId string.
        current_user: Authenticated user.

    Returns:
        ReceiptResponse: Receipt detail payload.

    Raises:
        HTTPException: Standardized domain or HTTP exception.
    """
    try:
        logging.info(f"Calling GET /v1/receipts/{receipt_id} endpoint")
        return await ReceiptController().get_receipt_by_id(
            receipt_id=receipt_id, current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in GET /v1/receipts/{receipt_id} endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@receipt_router.post(
    "/{receipt_id}/complete",
    response_model=ReceiptResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete receipt and apply inventory",
    description="Completes an inbound receipt exactly once and increments sellable/damaged stock.",
)
async def complete_receipt(
    receipt_id: str,
    current_user: User = Depends(
        require_roles([UserRole.OWNER, UserRole.MANAGER, UserRole.RECEIVING_STAFF])
    ),
) -> ReceiptResponse:
    """
    Route handler for POST /v1/receipts/{receipt_id}/complete.

    Args:
        receipt_id: Receipt ObjectId string.
        current_user: Authenticated user with receiving permission.

    Returns:
        ReceiptResponse: Completed receipt response.

    Raises:
        HTTPException: Standardized domain or HTTP exception.
    """
    try:
        logging.info(f"Calling POST /v1/receipts/{receipt_id}/complete endpoint")
        return await ReceiptController().complete_receipt(
            receipt_id=receipt_id, current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in POST /v1/receipts/{receipt_id}/complete endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
