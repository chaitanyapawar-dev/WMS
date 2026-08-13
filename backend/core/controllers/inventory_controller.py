"""
inventory_controller.py — Domain controller for inventory stock queries and updates.

Orchestrates stock retrieval, warehouse scoping, controlled adjustments,
and movement/audit log retrieval.
"""

from typing import Optional
from fastapi import HTTPException, status
from odmantic import ObjectId

from commons.auth import can_access_warehouse
from core import logger
from core.apis.schemas.requests.inventory_requests import AdjustInventoryRequest
from core.apis.schemas.responses.audit_responses import AuditLogResponse
from core.apis.schemas.responses.inventory_responses import InventoryResponse
from core.apis.schemas.responses.movement_responses import InventoryMovementResponse
from core.cruds.audit_crud import CRUDAudit
from core.cruds.inventory_crud import CRUDInventory
from core.cruds.movement_crud import CRUDMovement
from core.models.movement_model import MovementReferenceType, MovementType
from core.models.user_model import User, UserRole

logging = logger(__name__)


class InventoryController:
    """Controller for inventory domain logic and scope enforcement."""

    def __init__(self):
        """Initialize controller with inventory, movement, and audit CRUD helpers."""
        self.crud_inventory = CRUDInventory()
        self.crud_movement = CRUDMovement()
        self.crud_audit = CRUDAudit()

    async def list_inventory(
        self,
        warehouse_id: Optional[str],
        seller_id: Optional[str],
        product_id: Optional[str],
        current_user: User,
    ) -> list[InventoryResponse]:
        """
        List inventory stock levels matching query parameters and user warehouse scope.

        Args:
            warehouse_id: Optional warehouse ID filter.
            seller_id: Optional seller ID filter.
            product_id: Optional product ID filter.
            current_user: Authenticated active user.

        Returns:
            list[InventoryResponse]: Formatted inventory snapshots.

        Raises:
            HTTPException 403: If user attempts to query a warehouse outside their allowed scope.
        """
        try:
            logging.info("Executing InventoryController.list_inventory")

            if warehouse_id and not can_access_warehouse(current_user, warehouse_id):
                logging.warning(f"Warehouse access denied for user {current_user.id}: {warehouse_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this warehouse",
                )

            allowed_warehouse_ids = (
                None if current_user.role == UserRole.OWNER else current_user.warehouse_ids
            )

            records = await self.crud_inventory.list_inventory(
                warehouse_id=warehouse_id,
                seller_id=seller_id,
                product_id=product_id,
                allowed_warehouse_ids=allowed_warehouse_ids,
            )
            return [InventoryResponse.model_validate(record) for record in records]
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in InventoryController.list_inventory: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def get_inventory_by_id(
        self,
        inventory_id: str,
        current_user: User,
    ) -> InventoryResponse:
        """
        Get an inventory snapshot by ID.

        Args:
            inventory_id: Inventory ObjectId string.
            current_user: Authenticated active user.

        Returns:
            InventoryResponse: Formatted inventory snapshot.

        Raises:
            HTTPException 403: If user lacks warehouse scope.
            HTTPException 404: If inventory record is not found.
        """
        try:
            logging.info("Executing InventoryController.get_inventory_by_id")

            record = await self.crud_inventory.get_by_id(id=inventory_id)
            if not record:
                logging.warning(f"Inventory record not found: {inventory_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Inventory record not found",
                )

            if not can_access_warehouse(current_user, record.warehouse_id):
                logging.warning(f"Warehouse access denied for user {current_user.id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this warehouse",
                )

            return InventoryResponse.model_validate(record)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in InventoryController.get_inventory_by_id: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def adjust_inventory(
        self,
        inventory_id: str,
        request: AdjustInventoryRequest,
        current_user: User,
    ) -> InventoryResponse:
        """
        Perform a controlled inventory stock correction with required reason and history tracking.

        Only OWNER and MANAGER roles may perform inventory adjustments.

        Args:
            inventory_id: Target inventory ObjectId string.
            request: Adjustment payload (delta and reason).
            current_user: Authenticated active user.

        Returns:
            InventoryResponse: Updated inventory snapshot.

        Raises:
            HTTPException 403: If user role is not OWNER or MANAGER, or lacks warehouse scope.
            HTTPException 404: If inventory record is not found.
            HTTPException 409: If adjustment violates stock invariants (negative on_hand or reserved > on_hand).
        """
        try:
            logging.info("Executing InventoryController.adjust_inventory")

            if current_user.role not in (UserRole.OWNER, UserRole.MANAGER):
                logging.warning(f"User {current_user.id} with role {current_user.role} denied inventory adjustment")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only OWNER or MANAGER can perform controlled inventory adjustments",
                )

            inventory = await self.crud_inventory.get_by_id(id=inventory_id)
            if not inventory:
                logging.warning(f"Inventory record not found for adjustment: {inventory_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Inventory record not found",
                )

            if not can_access_warehouse(current_user, inventory.warehouse_id):
                logging.warning(f"Warehouse access denied for user {current_user.id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this warehouse",
                )

            prev_on_hand = inventory.on_hand
            new_on_hand = prev_on_hand + request.delta

            if new_on_hand < 0 or new_on_hand < inventory.reserved:
                logging.warning(
                    f"Invalid stock adjustment delta {request.delta} rejected: "
                    f"prev_on_hand={prev_on_hand}, reserved={inventory.reserved}"
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Adjustment delta {request.delta} would result in invalid stock level (on_hand={new_on_hand}, reserved={inventory.reserved})",
                )

            updated_inventory = await self.crud_inventory.adjust_stock(
                inventory_id=inventory.id,
                delta=request.delta,
            )
            if not updated_inventory:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Adjustment violates stock availability constraints",
                )

            m_type = (
                MovementType.ADJUSTMENT_INCREASE
                if request.delta > 0
                else MovementType.ADJUSTMENT_DECREASE
            )
            await self.crud_movement.create_movement(
                obj_in={
                    "warehouse_id": inventory.warehouse_id,
                    "seller_id": inventory.seller_id,
                    "product_id": inventory.product_id,
                    "inventory_id": inventory.id,
                    "movement_type": m_type,
                    "quantity": abs(request.delta),
                    "previous_on_hand": prev_on_hand,
                    "new_on_hand": updated_inventory.on_hand,
                    "previous_reserved": inventory.reserved,
                    "new_reserved": updated_inventory.reserved,
                    "previous_damaged": inventory.damaged,
                    "new_damaged": updated_inventory.damaged,
                    "reference_type": MovementReferenceType.ADJUSTMENT,
                    "reference_id": str(inventory.id),
                    "reason": request.reason,
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
                    "warehouse_id": inventory.warehouse_id,
                    "action": "INVENTORY_ADJUSTED",
                    "entity_type": "INVENTORY",
                    "entity_id": str(inventory.id),
                    "old_state": {"on_hand": prev_on_hand},
                    "new_state": {"on_hand": updated_inventory.on_hand},
                    "reason": request.reason,
                }
            )

            return InventoryResponse.model_validate(updated_inventory)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in InventoryController.adjust_inventory: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def list_movements(
        self,
        inventory_id: str,
        movement_type: Optional[str],
        current_user: User,
    ) -> list[InventoryMovementResponse]:
        """
        Get chronological stock movement history for an inventory snapshot.

        Args:
            inventory_id: Target inventory ObjectId string.
            movement_type: Optional movement type string filter.
            current_user: Authenticated active user.

        Returns:
            list[InventoryMovementResponse]: List of movement records.

        Raises:
            HTTPException 403: If user lacks warehouse scope.
            HTTPException 404: If inventory record is not found.
        """
        try:
            logging.info("Executing InventoryController.list_movements")

            inventory = await self.crud_inventory.get_by_id(id=inventory_id)
            if not inventory:
                logging.warning(f"Inventory record not found: {inventory_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Inventory record not found",
                )

            if not can_access_warehouse(current_user, inventory.warehouse_id):
                logging.warning(f"Warehouse access denied for user {current_user.id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this warehouse",
                )

            parsed_type = None
            if movement_type:
                try:
                    parsed_type = MovementType(movement_type.upper())
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid movement type: '{movement_type}'",
                    )

            movements = await self.crud_movement.list_movements(
                inventory_id=inventory_id,
                movement_type=parsed_type,
            )
            return [InventoryMovementResponse.model_validate(m) for m in movements]
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in InventoryController.list_movements: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def list_audits(
        self,
        warehouse_id: Optional[str],
        user_id: Optional[str],
        action: Optional[str],
        entity_type: Optional[str],
        entity_id: Optional[str],
        current_user: User,
    ) -> list[AuditLogResponse]:
        """
        List security and business audit logs matching filters and user scope.

        Only OWNER and MANAGER roles may query audit logs.

        Args:
            warehouse_id: Optional warehouse ID filter.
            user_id: Optional user ID filter.
            action: Optional action name filter.
            entity_type: Optional entity type filter.
            entity_id: Optional entity ID filter.
            current_user: Authenticated active user.

        Returns:
            list[AuditLogResponse]: List of matching audit log entries.

        Raises:
            HTTPException 403: If user role is not OWNER or MANAGER.
        """
        try:
            logging.info("Executing InventoryController.list_audits")

            if current_user.role not in (UserRole.OWNER, UserRole.MANAGER):
                logging.warning(f"User {current_user.id} denied access to audit logs")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only OWNER or MANAGER can access audit logs",
                )

            if warehouse_id and not can_access_warehouse(current_user, warehouse_id):
                logging.warning(f"Warehouse access denied for user {current_user.id}: {warehouse_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this warehouse",
                )

            allowed_warehouse_ids = (
                None if current_user.role == UserRole.OWNER else current_user.warehouse_ids
            )

            audits = await self.crud_audit.list_audits(
                warehouse_id=warehouse_id,
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                allowed_warehouse_ids=allowed_warehouse_ids,
            )
            return [AuditLogResponse.model_validate(audit) for audit in audits]
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in InventoryController.list_audits: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )
