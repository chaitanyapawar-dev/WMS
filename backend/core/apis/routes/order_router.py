"""
order_router.py — FastAPI router for sales order fulfillment endpoints.

Exposes HTTP routes for order creation, reservation, picking, packing,
parcel shipment creation, shipping, and order cancellation.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from commons.auth import get_current_user, require_roles
from core import logger
from core.apis.schemas.requests.order_requests import CreateOrderRequest
from core.apis.schemas.requests.shipment_requests import CreateShipmentRequest
from core.apis.schemas.responses.order_responses import OrderResponse
from core.apis.schemas.responses.shipment_responses import ShipmentResponse
from core.controllers.order_controller import OrderController
from core.models.user_model import User, UserRole

logging = logger(__name__)

order_router = APIRouter(prefix="/v1/orders")


@order_router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new sales order",
    description="Create a sales order in NEW status for a seller and warehouse.",
)
async def create_order(
    request: CreateOrderRequest,
    current_user: User = Depends(
        require_roles(
            [UserRole.OWNER, UserRole.MANAGER, UserRole.FULFILLMENT_STAFF]
        )
    ),
) -> OrderResponse:
    """
    Create an outbound order for an authorized warehouse user.

    Args:
        request: Validated order creation payload.
        current_user: Authenticated outbound-capable user.

    Returns:
        OrderResponse: Created order in NEW status.

    Raises:
        HTTPException: Preserves authorization, validation, and domain errors.
    """
    try:
        logging.info("Calling POST /v1/orders endpoint")
        return await OrderController().create_order(request=request, current_user=current_user)
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in POST /v1/orders endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@order_router.get(
    "",
    response_model=list[OrderResponse],
    status_code=status.HTTP_200_OK,
    summary="List sales orders",
    description="List sales orders filtered by warehouse, seller, status, or order number within user scope.",
)
async def list_orders(
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse ID"),
    seller_id: Optional[str] = Query(None, description="Filter by seller ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by order status"),
    order_number: Optional[str] = Query(None, description="Filter by order number"),
    current_user: User = Depends(get_current_user),
) -> list[OrderResponse]:
    """Route handler for GET /v1/orders."""
    try:
        logging.info("Calling GET /v1/orders endpoint")
        return await OrderController().list_orders(
            warehouse_id=warehouse_id,
            seller_id=seller_id,
            status_filter=status_filter,
            order_number=order_number,
            current_user=current_user,
        )
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in GET /v1/orders endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@order_router.get(
    "/{order_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Get order details",
    description="Get detailed sales order by ID.",
)
async def get_order_by_id(
    order_id: str,
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    """Route handler for GET /v1/orders/{order_id}."""
    try:
        logging.info(f"Calling GET /v1/orders/{order_id} endpoint")
        return await OrderController().get_order_by_id(order_id=order_id, current_user=current_user)
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in GET /v1/orders/{order_id} endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@order_router.post(
    "/{order_id}/reserve",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Reserve inventory stock for order",
    description="Atomically reserve inventory stock across all line items for an order. Oversell protected.",
)
async def reserve_order(
    order_id: str,
    current_user: User = Depends(
        require_roles(
            [UserRole.OWNER, UserRole.MANAGER, UserRole.FULFILLMENT_STAFF]
        )
    ),
) -> OrderResponse:
    """
    Reserve inventory for an order using an outbound-capable account.

    Args:
        order_id: Target order ID.
        current_user: Authenticated outbound-capable user.

    Returns:
        OrderResponse: Order after reservation.

    Raises:
        HTTPException: Preserves authorization, stock, and state errors.
    """
    try:
        logging.info(f"Calling POST /v1/orders/{order_id}/reserve endpoint")
        return await OrderController().reserve_order(order_id=order_id, current_user=current_user)
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in POST /v1/orders/{order_id}/reserve endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@order_router.post(
    "/{order_id}/start-picking",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Start picking workflow",
    description="Transition order from RESERVED to PICKING.",
)
async def start_picking(
    order_id: str,
    current_user: User = Depends(
        require_roles(
            [UserRole.OWNER, UserRole.MANAGER, UserRole.FULFILLMENT_STAFF]
        )
    ),
) -> OrderResponse:
    """
    Start picking for an authorized outbound user.

    Args:
        order_id: Target order ID.
        current_user: Authenticated outbound-capable user.

    Returns:
        OrderResponse: Order in PICKING status.

    Raises:
        HTTPException: Preserves authorization and state errors.
    """
    try:
        logging.info(f"Calling POST /v1/orders/{order_id}/start-picking endpoint")
        return await OrderController().start_picking(order_id=order_id, current_user=current_user)
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in POST /v1/orders/{order_id}/start-picking endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@order_router.post(
    "/{order_id}/picked",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete picking workflow",
    description="Transition order from PICKING to PICKED.",
)
async def picked(
    order_id: str,
    current_user: User = Depends(
        require_roles(
            [UserRole.OWNER, UserRole.MANAGER, UserRole.FULFILLMENT_STAFF]
        )
    ),
) -> OrderResponse:
    """
    Mark an order picked for an authorized outbound user.

    Args:
        order_id: Target order ID.
        current_user: Authenticated outbound-capable user.

    Returns:
        OrderResponse: Order in PICKED status.

    Raises:
        HTTPException: Preserves authorization and state errors.
    """
    try:
        logging.info(f"Calling POST /v1/orders/{order_id}/picked endpoint")
        return await OrderController().picked(order_id=order_id, current_user=current_user)
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in POST /v1/orders/{order_id}/picked endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@order_router.post(
    "/{order_id}/packed",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete packing workflow",
    description="Transition order from PICKED to PACKED.",
)
async def packed(
    order_id: str,
    current_user: User = Depends(
        require_roles(
            [UserRole.OWNER, UserRole.MANAGER, UserRole.FULFILLMENT_STAFF]
        )
    ),
) -> OrderResponse:
    """
    Mark an order packed for an authorized outbound user.

    Args:
        order_id: Target order ID.
        current_user: Authenticated outbound-capable user.

    Returns:
        OrderResponse: Order in PACKED status.

    Raises:
        HTTPException: Preserves authorization and state errors.
    """
    try:
        logging.info(f"Calling POST /v1/orders/{order_id}/packed endpoint")
        return await OrderController().packed(order_id=order_id, current_user=current_user)
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in POST /v1/orders/{order_id}/packed endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@order_router.post(
    "/{order_id}/shipment",
    response_model=ShipmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Prepare shipment for order",
    description="Create parcel shipment details and transition order to READY_TO_SHIP.",
)
async def create_shipment(
    order_id: str,
    request: CreateShipmentRequest,
    current_user: User = Depends(
        require_roles(
            [UserRole.OWNER, UserRole.MANAGER, UserRole.FULFILLMENT_STAFF]
        )
    ),
) -> ShipmentResponse:
    """
    Create shipment details for an authorized outbound user.

    Args:
        order_id: Target order ID.
        request: Validated shipment payload.
        current_user: Authenticated outbound-capable user.

    Returns:
        ShipmentResponse: Created shipment details.

    Raises:
        HTTPException: Preserves authorization and shipment errors.
    """
    try:
        logging.info(f"Calling POST /v1/orders/{order_id}/shipment endpoint")
        return await OrderController().create_shipment(
            order_id=order_id, request=request, current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in POST /v1/orders/{order_id}/shipment endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@order_router.post(
    "/{order_id}/ship",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Ship order exactly once",
    description="Dispatch order, transition status to SHIPPED, and decrement on_hand and reserved stock.",
)
async def ship_order(
    order_id: str,
    current_user: User = Depends(
        require_roles(
            [UserRole.OWNER, UserRole.MANAGER, UserRole.FULFILLMENT_STAFF]
        )
    ),
) -> OrderResponse:
    """
    Ship an order for an authorized outbound user.

    Args:
        order_id: Target order ID.
        current_user: Authenticated outbound-capable user.

    Returns:
        OrderResponse: Shipped order.

    Raises:
        HTTPException: Preserves authorization, stock, and state errors.
    """
    try:
        logging.info(f"Calling POST /v1/orders/{order_id}/ship endpoint")
        return await OrderController().ship_order(order_id=order_id, current_user=current_user)
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in POST /v1/orders/{order_id}/ship endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@order_router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel order and release reserved stock",
    description="Cancel an unshipped order and release any reserved inventory.",
)
async def cancel_order(
    order_id: str,
    current_user: User = Depends(
        require_roles(
            [UserRole.OWNER, UserRole.MANAGER, UserRole.FULFILLMENT_STAFF]
        )
    ),
) -> OrderResponse:
    """
    Cancel an order for an authorized outbound user.

    Args:
        order_id: Target order ID.
        current_user: Authenticated outbound-capable user.

    Returns:
        OrderResponse: Cancelled order.

    Raises:
        HTTPException: Preserves authorization and state errors.
    """
    try:
        logging.info(f"Calling POST /v1/orders/{order_id}/cancel endpoint")
        return await OrderController().cancel_order(order_id=order_id, current_user=current_user)
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in POST /v1/orders/{order_id}/cancel endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
