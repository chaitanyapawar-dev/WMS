"""Routes for product master data APIs."""

from fastapi import APIRouter, Depends, HTTPException, status

from commons.auth import require_roles
from core import logger
from core.apis.schemas.requests.product_request import (
    ProductCreate,
    ProductStatusUpdate,
)
from core.apis.schemas.responses.product_responses import ProductResponse
from core.controllers.product_controller import ProductController
from core.models.user_model import User, UserRole

logging = logger(__name__)
product_router = APIRouter()

READ_ROLES = [
    UserRole.OWNER,
    UserRole.MANAGER,
    UserRole.RECEIVING_STAFF,
    UserRole.FULFILLMENT_STAFF,
]
WRITE_ROLES = [UserRole.OWNER, UserRole.MANAGER]


@product_router.post(
    "/v1/products",
    status_code=status.HTTP_201_CREATED,
    response_model=ProductResponse,
)
async def create_product(
    request: ProductCreate,
    current_user: User = Depends(require_roles(WRITE_ROLES)),
):
    """
    Create a product for authorized master-data users.

    Args:
        request: Product creation payload.
        current_user: Authenticated OWNER or MANAGER user.

    Returns:
        ProductResponse: Safe created product record.

    Raises:
        HTTPException 400: Invalid seller ID.
        HTTPException 401: Missing or invalid authentication.
        HTTPException 403: User role is not allowed.
        HTTPException 404: Seller not found.
        HTTPException 409: Product SKU or UPC conflict.
        HTTPException 500: Unexpected server error.
    """
    try:
        logging.info("Calling POST /v1/products endpoint")
        return await ProductController().create_product(
            product_data=request.model_dump()
        )
    except HTTPException as httperror:
        logging.error(f"Error in POST /v1/products endpoint: {httperror}")
        raise httperror
    except Exception as error:
        logging.error(f"Error in POST /v1/products endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@product_router.get(
    "/v1/products",
    status_code=status.HTTP_200_OK,
    response_model=list[ProductResponse],
)
async def list_products(
    current_user: User = Depends(require_roles(READ_ROLES)),
):
    """
    List products for authenticated WMS users.

    Args:
        current_user: Authenticated user authorized for product reads.

    Returns:
        list[ProductResponse]: Safe product records.

    Raises:
        HTTPException 401: Missing or invalid authentication.
        HTTPException 403: User role is not allowed.
        HTTPException 500: Unexpected server error.
    """
    try:
        logging.info("Calling GET /v1/products endpoint")
        return await ProductController().list_products()
    except HTTPException as httperror:
        logging.error(f"Error in GET /v1/products endpoint: {httperror}")
        raise httperror
    except Exception as error:
        logging.error(f"Error in GET /v1/products endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@product_router.get(
    "/v1/products/upc/{upc}",
    status_code=status.HTTP_200_OK,
    response_model=ProductResponse,
)
async def lookup_product_by_upc(
    upc: str,
    current_user: User = Depends(require_roles(READ_ROLES)),
):
    """
    Lookup a product by UPC for authenticated WMS users.

    Args:
        upc: UPC value from warehouse scanning.
        current_user: Authenticated user authorized for product reads.

    Returns:
        ProductResponse: Safe product record.

    Raises:
        HTTPException 401: Missing or invalid authentication.
        HTTPException 403: User role is not allowed.
        HTTPException 404: Product not found.
        HTTPException 500: Unexpected server error.
    """
    try:
        logging.info(f"Calling GET /v1/products/upc/{upc} endpoint")
        return await ProductController().lookup_by_upc(upc=upc)
    except HTTPException as httperror:
        logging.error(
            f"Error in GET /v1/products/upc/{upc} endpoint: {httperror}"
        )
        raise httperror
    except Exception as error:
        logging.error(f"Error in GET /v1/products/upc/{upc} endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@product_router.get(
    "/v1/products/{product_id}",
    status_code=status.HTTP_200_OK,
    response_model=ProductResponse,
)
async def get_product(
    product_id: str,
    current_user: User = Depends(require_roles(READ_ROLES)),
):
    """
    Get a product by ID for authenticated WMS users.

    Args:
        product_id: Product ObjectId as a string.
        current_user: Authenticated user authorized for product reads.

    Returns:
        ProductResponse: Safe product record.

    Raises:
        HTTPException 401: Missing or invalid authentication.
        HTTPException 403: User role is not allowed.
        HTTPException 404: Product not found.
        HTTPException 500: Unexpected server error.
    """
    try:
        logging.info(f"Calling GET /v1/products/{product_id} endpoint")
        return await ProductController().get_product(product_id=product_id)
    except HTTPException as httperror:
        logging.error(
            f"Error in GET /v1/products/{product_id} endpoint: {httperror}"
        )
        raise httperror
    except Exception as error:
        logging.error(f"Error in GET /v1/products/{product_id} endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@product_router.patch(
    "/v1/products/{product_id}/status",
    status_code=status.HTTP_200_OK,
    response_model=ProductResponse,
)
async def update_product_status(
    product_id: str,
    request: ProductStatusUpdate,
    current_user: User = Depends(require_roles(WRITE_ROLES)),
):
    """
    Update product status for authorized master-data users.

    Args:
        product_id: Product ObjectId as a string.
        request: Product status update payload.
        current_user: Authenticated OWNER or MANAGER user.

    Returns:
        ProductResponse: Safe updated product record.

    Raises:
        HTTPException 401: Missing or invalid authentication.
        HTTPException 403: User role is not allowed.
        HTTPException 404: Product not found.
        HTTPException 500: Unexpected server error.
    """
    try:
        logging.info(f"Calling PATCH /v1/products/{product_id}/status endpoint")
        return await ProductController().update_product_status(
            product_id=product_id, new_status=request.status
        )
    except HTTPException as httperror:
        logging.error(
            f"Error in PATCH /v1/products/{product_id}/status endpoint: {httperror}"
        )
        raise httperror
    except Exception as error:
        logging.error(
            f"Error in PATCH /v1/products/{product_id}/status endpoint: {error}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
