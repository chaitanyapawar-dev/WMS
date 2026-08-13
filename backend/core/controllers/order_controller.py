"""
order_controller.py — Domain controller for sales order fulfillment lifecycle.

Orchestrates order creation, atomic multi-line reservation with oversell protection,
picking, packing, parcel shipment creation, shipping execution, and cancellation.
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from odmantic import ObjectId

from commons.auth import can_access_warehouse
from core import logger
from core.apis.schemas.requests.order_requests import CreateOrderRequest
from core.apis.schemas.requests.shipment_requests import CreateShipmentRequest
from core.apis.schemas.responses.order_responses import OrderResponse
from core.apis.schemas.responses.shipment_responses import ShipmentResponse
from core.cruds.audit_crud import CRUDAudit
from core.cruds.inventory_crud import CRUDInventory
from core.cruds.movement_crud import CRUDMovement
from core.cruds.order_crud import CRUDOrder
from core.cruds.product_crud import CRUDProduct
from core.cruds.seller_crud import CRUDSeller
from core.cruds.shipment_crud import CRUDShipment
from core.cruds.warehouse_crud import CRUDWarehouse
from core.database.database import MongoDatabase
from core.models.movement_model import MovementReferenceType, MovementType
from core.models.order_model import Order, OrderItem, OrderStatus
from core.models.shipment_model import Shipment, ShipmentStatus
from core.models.user_model import User, UserRole

logging = logger(__name__)


class OrderController:
    """Controller for order fulfillment domain workflows and security access checks."""

    def __init__(self):
        """Initialize controller with required CRUD helpers."""
        self.crud_order = CRUDOrder()
        self.crud_inventory = CRUDInventory()
        self.crud_product = CRUDProduct()
        self.crud_seller = CRUDSeller()
        self.crud_warehouse = CRUDWarehouse()
        self.crud_shipment = CRUDShipment()
        self.crud_movement = CRUDMovement()
        self.crud_audit = CRUDAudit()

    async def create_order(
        self,
        request: CreateOrderRequest,
        current_user: User,
    ) -> OrderResponse:
        """
        Create a new sales order for a seller and warehouse.

        Args:
            request: Order creation request payload.
            current_user: Authenticated active user.

        Returns:
            OrderResponse: Formatted created order response.

        Raises:
            HTTPException 403: If user lacks warehouse scope.
            HTTPException 404: If seller, warehouse, or product SKU is not found.
            HTTPException 400: If seller/warehouse inactive or SKU does not belong to seller.
            HTTPException 409: If order_number already exists.
        """
        try:
            logging.info("Executing OrderController.create_order")

            if not can_access_warehouse(current_user, request.warehouse_id):
                logging.warning(f"Warehouse access denied for user {current_user.id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this warehouse",
                )

            seller = await self.crud_seller.get_by_id(id=request.seller_id)
            if not seller:
                logging.warning(f"Seller not found: {request.seller_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Seller not found",
                )
            if seller.status.value != "ACTIVE":
                logging.warning(f"Inactive seller rejected: {request.seller_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Seller account is inactive",
                )

            warehouse = await self.crud_warehouse.get_by_id(id=request.warehouse_id)
            if not warehouse:
                logging.warning(f"Warehouse not found: {request.warehouse_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Warehouse not found",
                )
            if warehouse.status.value != "ACTIVE":
                logging.warning(f"Inactive warehouse rejected: {request.warehouse_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Warehouse is inactive",
                )

            seller_obj_id = ObjectId(request.seller_id)
            warehouse_obj_id = ObjectId(request.warehouse_id)

            # Resolve line items and validate SKUs
            order_items: list[OrderItem] = []
            for item_in in request.items:
                product = await self.crud_product.get_by_sku(sku=item_in.sku)
                if not product:
                    logging.warning(f"Product SKU not found: {item_in.sku}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Product with SKU '{item_in.sku}' not found",
                    )
                if str(product.seller_id) != str(seller.id):
                    logging.warning(f"SKU seller mismatch: product seller {product.seller_id} vs order seller {seller.id}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Product SKU '{item_in.sku}' does not belong to order's seller",
                    )
                order_items.append(
                    OrderItem(
                        product_id=product.id,
                        sku=product.sku,
                        quantity=item_in.quantity,
                        reserved_quantity=0,
                        picked_quantity=0,
                    )
                )

            order_num = request.order_number
            if not order_num:
                order_num = await self.crud_order.generate_order_number()

            existing = await self.crud_order.get_by_order_number(order_number=order_num)
            if existing:
                logging.warning(f"Duplicate order_number rejected: {order_num}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"An order with order number '{order_num}' already exists",
                )

            order_data = {
                "order_number": order_num,
                "seller_id": seller_obj_id,
                "warehouse_id": warehouse_obj_id,
                "items": [item.model_dump(by_alias=True) for item in order_items],
                "status": OrderStatus.NEW,
                "created_by": current_user.id,
                "idempotency_key": request.idempotency_key,
            }

            order = await self.crud_order.create(obj_in=order_data)

            await self.crud_audit.create_audit(
                obj_in={
                    "user_id": current_user.id,
                    "user_role": (
                        current_user.role.value
                        if isinstance(current_user.role, UserRole)
                        else str(current_user.role)
                    ),
                    "warehouse_id": order.warehouse_id,
                    "action": "ORDER_CREATED",
                    "entity_type": "ORDER",
                    "entity_id": str(order.id),
                    "new_state": {
                        "order_number": order.order_number,
                        "status": order.status.value,
                    },
                }
            )

            return OrderResponse.model_validate(order)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in OrderController.create_order: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def list_orders(
        self,
        warehouse_id: Optional[str],
        seller_id: Optional[str],
        status_filter: Optional[str],
        order_number: Optional[str],
        current_user: User,
    ) -> list[OrderResponse]:
        """List sales orders with scope filtering."""
        try:
            logging.info("Executing OrderController.list_orders")

            if warehouse_id and not can_access_warehouse(current_user, warehouse_id):
                logging.warning(f"Warehouse access denied for user {current_user.id}: {warehouse_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this warehouse",
                )

            allowed_warehouse_ids = (
                None if current_user.role == UserRole.OWNER else current_user.warehouse_ids
            )

            parsed_status = None
            if status_filter:
                try:
                    parsed_status = OrderStatus(status_filter.upper())
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid order status filter: '{status_filter}'",
                    )

            orders = await self.crud_order.list_orders(
                warehouse_id=warehouse_id,
                seller_id=seller_id,
                status=parsed_status,
                order_number=order_number,
                allowed_warehouse_ids=allowed_warehouse_ids,
            )
            return [OrderResponse.model_validate(o) for o in orders]
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in OrderController.list_orders: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def get_order_by_id(
        self,
        order_id: str,
        current_user: User,
    ) -> OrderResponse:
        """Get an order detail by ID."""
        try:
            logging.info("Executing OrderController.get_order_by_id")

            order = await self.crud_order.get_by_id(id=order_id)
            if not order:
                logging.warning(f"Order not found: {order_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found",
                )

            if not can_access_warehouse(current_user, order.warehouse_id):
                logging.warning(f"Warehouse access denied for user {current_user.id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this warehouse",
                )

            return OrderResponse.model_validate(order)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in OrderController.get_order_by_id: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def reserve_order(
        self,
        order_id: str,
        current_user: User,
    ) -> OrderResponse:
        """
        Perform multi-line atomic inventory reservation for an order (P6-T04).

        Prevents overselling under concurrent requests using atomic stock reservation queries.
        If any line item lacks sufficient inventory, all reserved lines are rolled back.

        Args:
            order_id: Order ObjectId string.
            current_user: Authenticated active user.

        Returns:
            OrderResponse: Formatted reserved order response.

        Raises:
            HTTPException 403: If user lacks warehouse scope.
            HTTPException 404: If order not found.
            HTTPException 409: If inventory is insufficient or order state is invalid.
        """
        try:
            logging.info("Executing OrderController.reserve_order")

            order = await self.crud_order.get_by_id(id=order_id)
            if not order:
                logging.warning(f"Order not found: {order_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found",
                )

            if not can_access_warehouse(current_user, order.warehouse_id):
                logging.warning(f"Warehouse access denied for user {current_user.id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this warehouse",
                )

            # Idempotency check: if already RESERVED or beyond, return order without double reserving
            if order.status != OrderStatus.NEW:
                if order.status in (
                    OrderStatus.RESERVED,
                    OrderStatus.PICKING,
                    OrderStatus.PICKED,
                    OrderStatus.PACKED,
                    OrderStatus.READY_TO_SHIP,
                    OrderStatus.SHIPPED,
                ):
                    return OrderResponse.model_validate(order)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot reserve order in status {order.status.value}",
                )

            # Reserve lines sequentially with rollback tracking for atomicity
            reserved_lines: list[tuple[ObjectId, int]] = []
            failed = False
            failed_product_sku = ""

            for item in order.items:
                inv = await self.crud_inventory.reserve_inventory_stock(
                    warehouse_id=order.warehouse_id,
                    seller_id=order.seller_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                )
                if not inv:
                    failed = True
                    failed_product_sku = item.sku
                    break
                reserved_lines.append((item.product_id, item.quantity))

            if failed:
                # Roll back all successfully reserved lines
                logging.warning(f"Reservation failed for SKU '{failed_product_sku}'; rolling back reserved lines")
                for prod_id, qty in reserved_lines:
                    await self.crud_inventory.release_inventory_reservation(
                        warehouse_id=order.warehouse_id,
                        seller_id=order.seller_id,
                        product_id=prod_id,
                        quantity=qty,
                    )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insufficient inventory available to reserve product '{failed_product_sku}'",
                )

            # Transition order status to RESERVED and update item reserved quantities
            now = datetime.now(timezone.utc)
            updated_items = []
            for item in order.items:
                dumped = item.model_dump(by_alias=True)
                dumped["reserved_quantity"] = item.quantity
                updated_items.append(dumped)

            updated_order = await self.crud_order.transition_status(
                order_id=order.id,
                from_statuses=[OrderStatus.NEW],
                to_status=OrderStatus.RESERVED,
                extra_fields={
                    "reserved_at": now,
                    "items": updated_items,
                },
            )

            if not updated_order:
                # Conflict on concurrent transition: release reserved stock
                for prod_id, qty in reserved_lines:
                    await self.crud_inventory.release_inventory_reservation(
                        warehouse_id=order.warehouse_id,
                        seller_id=order.seller_id,
                        product_id=prod_id,
                        quantity=qty,
                    )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Order reservation status transition conflict",
                )

            # Record InventoryMovements and AuditLog
            for item in updated_order.items:
                inv = await self.crud_inventory.get_by_scope(
                    warehouse_id=updated_order.warehouse_id,
                    seller_id=updated_order.seller_id,
                    product_id=item.product_id,
                )
                if inv:
                    await self.crud_movement.create_movement(
                        obj_in={
                            "warehouse_id": updated_order.warehouse_id,
                            "seller_id": updated_order.seller_id,
                            "product_id": item.product_id,
                            "inventory_id": inv.id,
                            "movement_type": MovementType.RESERVED,
                            "quantity": item.quantity,
                            "previous_on_hand": inv.on_hand,
                            "new_on_hand": inv.on_hand,
                            "previous_reserved": inv.reserved - item.quantity,
                            "new_reserved": inv.reserved,
                            "previous_damaged": inv.damaged,
                            "new_damaged": inv.damaged,
                            "reference_type": MovementReferenceType.ORDER,
                            "reference_id": str(updated_order.id),
                            "performed_by": current_user.id,
                        }
                    )

            await self.crud_audit.create_audit(
                obj_in={
                    "user_id": current_user.id,
                    "user_role": (
                        current_user.role.value
                        if isinstance(current_user.role, UserRole)
                        else str(current_user.role)
                    ),
                    "warehouse_id": updated_order.warehouse_id,
                    "action": "ORDER_RESERVED",
                    "entity_type": "ORDER",
                    "entity_id": str(updated_order.id),
                    "new_state": {"status": "RESERVED"},
                }
            )

            return OrderResponse.model_validate(updated_order)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in OrderController.reserve_order: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def start_picking(self, order_id: str, current_user: User) -> OrderResponse:
        """Transition order status RESERVED -> PICKING (P6-T06)."""
        try:
            logging.info("Executing OrderController.start_picking")
            order = await self.crud_order.get_by_id(id=order_id)
            if not order:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

            if not can_access_warehouse(current_user, order.warehouse_id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this warehouse")

            if order.status == OrderStatus.PICKING:
                return OrderResponse.model_validate(order)

            updated = await self.crud_order.transition_status(
                order_id=order.id,
                from_statuses=[OrderStatus.RESERVED],
                to_status=OrderStatus.PICKING,
            )
            if not updated:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot start picking order in status '{order.status.value}'",
                )

            await self.crud_audit.create_audit(
                obj_in={
                    "user_id": current_user.id,
                    "user_role": current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role),
                    "warehouse_id": order.warehouse_id,
                    "action": "ORDER_START_PICKING",
                    "entity_type": "ORDER",
                    "entity_id": str(order.id),
                    "new_state": {"status": "PICKING"},
                }
            )
            return OrderResponse.model_validate(updated)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in OrderController.start_picking: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def picked(self, order_id: str, current_user: User) -> OrderResponse:
        """Transition order status PICKING or RESERVED -> PICKED (P6-T06)."""
        try:
            logging.info("Executing OrderController.picked")
            order = await self.crud_order.get_by_id(id=order_id)
            if not order:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

            if not can_access_warehouse(current_user, order.warehouse_id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this warehouse")

            if order.status == OrderStatus.PICKED:
                return OrderResponse.model_validate(order)

            now = datetime.now(timezone.utc)
            updated_items = []
            for item in order.items:
                dumped = item.model_dump(by_alias=True)
                dumped["picked_quantity"] = item.quantity
                updated_items.append(dumped)

            updated = await self.crud_order.transition_status(
                order_id=order.id,
                from_statuses=[OrderStatus.PICKING, OrderStatus.RESERVED],
                to_status=OrderStatus.PICKED,
                extra_fields={"picked_at": now, "items": updated_items},
            )
            if not updated:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot mark order picked from status '{order.status.value}'",
                )

            await self.crud_audit.create_audit(
                obj_in={
                    "user_id": current_user.id,
                    "user_role": current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role),
                    "warehouse_id": order.warehouse_id,
                    "action": "ORDER_PICKED",
                    "entity_type": "ORDER",
                    "entity_id": str(order.id),
                    "new_state": {"status": "PICKED"},
                }
            )
            return OrderResponse.model_validate(updated)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in OrderController.picked: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def packed(self, order_id: str, current_user: User) -> OrderResponse:
        """Transition order status PICKED -> PACKED (P6-T07)."""
        try:
            logging.info("Executing OrderController.packed")
            order = await self.crud_order.get_by_id(id=order_id)
            if not order:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

            if not can_access_warehouse(current_user, order.warehouse_id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this warehouse")

            if order.status == OrderStatus.PACKED:
                return OrderResponse.model_validate(order)

            now = datetime.now(timezone.utc)
            updated = await self.crud_order.transition_status(
                order_id=order.id,
                from_statuses=[OrderStatus.PICKED],
                to_status=OrderStatus.PACKED,
                extra_fields={"packed_at": now},
            )
            if not updated:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot pack order in status '{order.status.value}'",
                )

            await self.crud_audit.create_audit(
                obj_in={
                    "user_id": current_user.id,
                    "user_role": current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role),
                    "warehouse_id": order.warehouse_id,
                    "action": "ORDER_PACKED",
                    "entity_type": "ORDER",
                    "entity_id": str(order.id),
                    "new_state": {"status": "PACKED"},
                }
            )
            return OrderResponse.model_validate(updated)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in OrderController.packed: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def create_shipment(
        self,
        order_id: str,
        request: CreateShipmentRequest,
        current_user: User,
    ) -> ShipmentResponse:
        """Create parcel shipment details and transition order to READY_TO_SHIP (P6-T09)."""
        try:
            logging.info("Executing OrderController.create_shipment")
            order = await self.crud_order.get_by_id(id=order_id)
            if not order:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

            if not can_access_warehouse(current_user, order.warehouse_id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this warehouse")

            existing_shipment = await self.crud_shipment.get_by_order_id(order_id=order.id)
            if existing_shipment:
                return ShipmentResponse.model_validate(existing_shipment)

            if order.status not in (OrderStatus.PACKED, OrderStatus.READY_TO_SHIP):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot create shipment for order in status '{order.status.value}'",
                )

            shipment_data = {
                "order_id": order.id,
                "warehouse_id": order.warehouse_id,
                "carrier": request.carrier,
                "tracking_number": request.tracking_number,
                "weight": request.weight,
                "length": request.length,
                "width": request.width,
                "height": request.height,
                "label_reference": request.label_reference,
                "status": ShipmentStatus.READY,
            }
            shipment = await self.crud_shipment.create(obj_in=shipment_data)

            await self.crud_order.transition_status(
                order_id=order.id,
                from_statuses=[OrderStatus.PACKED],
                to_status=OrderStatus.READY_TO_SHIP,
            )

            await self.crud_audit.create_audit(
                obj_in={
                    "user_id": current_user.id,
                    "user_role": current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role),
                    "warehouse_id": order.warehouse_id,
                    "action": "SHIPMENT_CREATED",
                    "entity_type": "SHIPMENT",
                    "entity_id": str(shipment.id),
                    "new_state": {"tracking_number": shipment.tracking_number, "carrier": shipment.carrier},
                }
            )

            return ShipmentResponse.model_validate(shipment)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in OrderController.create_shipment: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def ship_order(self, order_id: str, current_user: User) -> OrderResponse:
        """
        Ship order exactly once, decrementing stock on_hand and reserved (P6-T10).

        Idempotency: Replaying ship_order on an already SHIPPED order returns clean response without double-decrementing stock.
        """
        try:
            logging.info("Executing OrderController.ship_order")
            order = await self.crud_order.get_by_id(id=order_id)
            if not order:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

            if not can_access_warehouse(current_user, order.warehouse_id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this warehouse")

            if order.status == OrderStatus.SHIPPED:
                return OrderResponse.model_validate(order)

            if order.status not in (OrderStatus.READY_TO_SHIP, OrderStatus.PACKED):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot ship order in status '{order.status.value}'",
                )

            # Atomic transition to SHIPPED first to claim single execution
            now = datetime.now(timezone.utc)
            updated_order = await self.crud_order.transition_status(
                order_id=order.id,
                from_statuses=[OrderStatus.READY_TO_SHIP, OrderStatus.PACKED],
                to_status=OrderStatus.SHIPPED,
                extra_fields={"shipped_at": now},
            )
            if not updated_order:
                refetched = await self.crud_order.get_by_id(id=order_id)
                if refetched and refetched.status == OrderStatus.SHIPPED:
                    return OrderResponse.model_validate(refetched)
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Order shipping status conflict")

            # Decrement inventory stock on_hand and reserved
            for item in updated_order.items:
                inv = await self.crud_inventory.ship_inventory_stock(
                    warehouse_id=updated_order.warehouse_id,
                    seller_id=updated_order.seller_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                )
                if inv:
                    await self.crud_movement.create_movement(
                        obj_in={
                            "warehouse_id": updated_order.warehouse_id,
                            "seller_id": updated_order.seller_id,
                            "product_id": item.product_id,
                            "inventory_id": inv.id,
                            "movement_type": MovementType.SHIPPED,
                            "quantity": item.quantity,
                            "previous_on_hand": inv.on_hand + item.quantity,
                            "new_on_hand": inv.on_hand,
                            "previous_reserved": inv.reserved + item.quantity,
                            "new_reserved": inv.reserved,
                            "previous_damaged": inv.damaged,
                            "new_damaged": inv.damaged,
                            "reference_type": MovementReferenceType.ORDER,
                            "reference_id": str(updated_order.id),
                            "performed_by": current_user.id,
                        }
                    )

            # Update shipment status
            shipment = await self.crud_shipment.get_by_order_id(order_id=updated_order.id)
            if shipment:
                await self.crud_shipment.transition_status(
                    shipment_id=shipment.id,
                    from_status=ShipmentStatus.READY,
                    to_status=ShipmentStatus.SHIPPED,
                )

            await self.crud_audit.create_audit(
                obj_in={
                    "user_id": current_user.id,
                    "user_role": current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role),
                    "warehouse_id": updated_order.warehouse_id,
                    "action": "ORDER_SHIPPED",
                    "entity_type": "ORDER",
                    "entity_id": str(updated_order.id),
                    "new_state": {"status": "SHIPPED"},
                }
            )

            return OrderResponse.model_validate(updated_order)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in OrderController.ship_order: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def cancel_order(self, order_id: str, current_user: User) -> OrderResponse:
        """Cancel order and release reserved stock (P6-T11)."""
        try:
            logging.info("Executing OrderController.cancel_order")
            order = await self.crud_order.get_by_id(id=order_id)
            if not order:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

            if not can_access_warehouse(current_user, order.warehouse_id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this warehouse")

            if order.status == OrderStatus.CANCELLED:
                return OrderResponse.model_validate(order)

            if order.status == OrderStatus.SHIPPED:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot cancel an already shipped order",
                )

            now = datetime.now(timezone.utc)
            updated = await self.crud_order.transition_status(
                order_id=order.id,
                from_statuses=[
                    OrderStatus.NEW,
                    OrderStatus.RESERVED,
                    OrderStatus.PICKING,
                    OrderStatus.PICKED,
                    OrderStatus.PACKED,
                    OrderStatus.READY_TO_SHIP,
                ],
                to_status=OrderStatus.CANCELLED,
                extra_fields={"cancelled_at": now},
            )
            if not updated:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot cancel order in status '{order.status.value}'",
                )

            # Release reserved quantities if any were reserved
            for item in updated.items:
                if item.reserved_quantity > 0:
                    inv = await self.crud_inventory.release_inventory_reservation(
                        warehouse_id=updated.warehouse_id,
                        seller_id=updated.seller_id,
                        product_id=item.product_id,
                        quantity=item.reserved_quantity,
                    )
                    if inv:
                        await self.crud_movement.create_movement(
                            obj_in={
                                "warehouse_id": updated.warehouse_id,
                                "seller_id": updated.seller_id,
                                "product_id": item.product_id,
                                "inventory_id": inv.id,
                                "movement_type": MovementType.RESERVATION_RELEASED,
                                "quantity": item.reserved_quantity,
                                "previous_on_hand": inv.on_hand,
                                "new_on_hand": inv.on_hand,
                                "previous_reserved": inv.reserved + item.reserved_quantity,
                                "new_reserved": inv.reserved,
                                "previous_damaged": inv.damaged,
                                "new_damaged": inv.damaged,
                                "reference_type": MovementReferenceType.ORDER,
                                "reference_id": str(updated.id),
                                "performed_by": current_user.id,
                            }
                        )

            await self.crud_audit.create_audit(
                obj_in={
                    "user_id": current_user.id,
                    "user_role": current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role),
                    "warehouse_id": updated.warehouse_id,
                    "action": "ORDER_CANCELLED",
                    "entity_type": "ORDER",
                    "entity_id": str(updated.id),
                    "new_state": {"status": "CANCELLED"},
                }
            )

            return OrderResponse.model_validate(updated)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in OrderController.cancel_order: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
