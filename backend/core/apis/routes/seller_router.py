"""Routes for seller master data APIs."""

from fastapi import APIRouter, Depends, HTTPException, status

from commons.auth import require_roles
from core import logger
from core.apis.schemas.requests.seller_request import SellerCreate, SellerStatusUpdate
from core.apis.schemas.responses.seller_responses import SellerResponse
from core.controllers.seller_controller import SellerController
from core.models.user_model import User, UserRole

logging = logger(__name__)
seller_router = APIRouter()

READ_ROLES = [
    UserRole.OWNER,
    UserRole.MANAGER,
    UserRole.RECEIVING_STAFF,
    UserRole.FULFILLMENT_STAFF,
]
WRITE_ROLES = [UserRole.OWNER, UserRole.MANAGER]


@seller_router.post(
    "/v1/sellers",
    status_code=status.HTTP_201_CREATED,
    response_model=SellerResponse,
)
async def create_seller(
    request: SellerCreate,
    current_user: User = Depends(require_roles(WRITE_ROLES)),
):
    """
    Create a seller for authorized master-data users.

    Args:
        request: Seller creation payload.
        current_user: Authenticated OWNER or MANAGER user.

    Returns:
        SellerResponse: Safe created seller record.

    Raises:
        HTTPException 401: Missing or invalid authentication.
        HTTPException 403: User role is not allowed.
        HTTPException 409: Seller code already exists.
        HTTPException 500: Unexpected server error.
    """
    try:
        logging.info("Calling POST /v1/sellers endpoint")
        return await SellerController().create_seller(seller_data=request.model_dump())
    except HTTPException as httperror:
        logging.error(f"Error in POST /v1/sellers endpoint: {httperror}")
        raise httperror
    except Exception as error:
        logging.error(f"Error in POST /v1/sellers endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@seller_router.get(
    "/v1/sellers",
    status_code=status.HTTP_200_OK,
    response_model=list[SellerResponse],
)
async def list_sellers(
    current_user: User = Depends(require_roles(READ_ROLES)),
):
    """
    List sellers for authenticated WMS users.

    Args:
        current_user: Authenticated user authorized for seller reads.

    Returns:
        list[SellerResponse]: Safe seller records.

    Raises:
        HTTPException 401: Missing or invalid authentication.
        HTTPException 403: User role is not allowed.
        HTTPException 500: Unexpected server error.
    """
    try:
        logging.info("Calling GET /v1/sellers endpoint")
        return await SellerController().list_sellers()
    except HTTPException as httperror:
        logging.error(f"Error in GET /v1/sellers endpoint: {httperror}")
        raise httperror
    except Exception as error:
        logging.error(f"Error in GET /v1/sellers endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@seller_router.get(
    "/v1/sellers/{seller_id}",
    status_code=status.HTTP_200_OK,
    response_model=SellerResponse,
)
async def get_seller(
    seller_id: str,
    current_user: User = Depends(require_roles(READ_ROLES)),
):
    """
    Get a seller by ID for authenticated WMS users.

    Args:
        seller_id: Seller ObjectId as a string.
        current_user: Authenticated user authorized for seller reads.

    Returns:
        SellerResponse: Safe seller record.

    Raises:
        HTTPException 401: Missing or invalid authentication.
        HTTPException 403: User role is not allowed.
        HTTPException 404: Seller not found.
        HTTPException 500: Unexpected server error.
    """
    try:
        logging.info(f"Calling GET /v1/sellers/{seller_id} endpoint")
        return await SellerController().get_seller(seller_id=seller_id)
    except HTTPException as httperror:
        logging.error(f"Error in GET /v1/sellers/{seller_id} endpoint: {httperror}")
        raise httperror
    except Exception as error:
        logging.error(f"Error in GET /v1/sellers/{seller_id} endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@seller_router.patch(
    "/v1/sellers/{seller_id}/status",
    status_code=status.HTTP_200_OK,
    response_model=SellerResponse,
)
async def update_seller_status(
    seller_id: str,
    request: SellerStatusUpdate,
    current_user: User = Depends(require_roles(WRITE_ROLES)),
):
    """
    Update seller status for authorized master-data users.

    Args:
        seller_id: Seller ObjectId as a string.
        request: Seller status update payload.
        current_user: Authenticated OWNER or MANAGER user.

    Returns:
        SellerResponse: Safe updated seller record.

    Raises:
        HTTPException 401: Missing or invalid authentication.
        HTTPException 403: User role is not allowed.
        HTTPException 404: Seller not found.
        HTTPException 500: Unexpected server error.
    """
    try:
        logging.info(f"Calling PATCH /v1/sellers/{seller_id}/status endpoint")
        return await SellerController().update_seller_status(
            seller_id=seller_id, new_status=request.status
        )
    except HTTPException as httperror:
        logging.error(
            f"Error in PATCH /v1/sellers/{seller_id}/status endpoint: {httperror}"
        )
        raise httperror
    except Exception as error:
        logging.error(
            f"Error in PATCH /v1/sellers/{seller_id}/status endpoint: {error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
