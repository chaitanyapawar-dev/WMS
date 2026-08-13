"""
receipt_controller.py — Domain controller for inbound physical receipts.

Orchestrates receipt creation, UPC line item addition, list/detail retrieval,
and atomic receipt completion.
"""

from typing import Optional
from fastapi import HTTPException, status
from odmantic import ObjectId
from pymongo.errors import DuplicateKeyError

from commons.auth import can_access_warehouse
from core import logger
from core.apis.schemas.requests.receipt_requests import (
    AddReceiptItemRequest,
    CreateReceiptRequest,
)
from core.apis.schemas.responses.receipt_responses import ReceiptResponse
from core.cruds.audit_crud import CRUDAudit
from core.cruds.inventory_crud import CRUDInventory
from core.cruds.movement_crud import CRUDMovement
from core.cruds.product_crud import CRUDProduct
from core.cruds.receipt_crud import CRUDReceipt
from core.cruds.seller_crud import CRUDSeller
from core.cruds.warehouse_crud import CRUDWarehouse
from core.database.database import MongoDatabase
from core.models.movement_model import InventoryMovement, MovementReferenceType, MovementType
from core.models.receipt_model import ReceiptItem, ReceiptStatus
from core.models.user_model import User, UserRole

logging = logger(__name__)


class ReceiptController:
    """Controller for receipt business workflows and access control."""

    def __init__(self):
        """Initialize controller with required CRUD helpers."""
        self.crud_receipt = CRUDReceipt()
        self.crud_inventory = CRUDInventory()
        self.crud_product = CRUDProduct()
        self.crud_seller = CRUDSeller()
        self.crud_warehouse = CRUDWarehouse()
        self.crud_movement = CRUDMovement()
        self.crud_audit = CRUDAudit()

    async def create_receipt(
        self,
        request: CreateReceiptRequest,
        current_user: User,
    ) -> ReceiptResponse:
        """
        Create a new inbound receipt for a seller and warehouse.

        Args:
            request: Receipt creation request payload.
            current_user: Authenticated active user.

        Returns:
            ReceiptResponse: Formatted receipt response.

        Raises:
            HTTPException 403: If user lacks warehouse scope or role permission.
            HTTPException 404: If seller or warehouse is not found.
            HTTPException 400: If seller or warehouse is inactive.
            HTTPException 409: If physical shipment identifier already exists.
        """
        try:
            logging.info("Executing ReceiptController.create_receipt")

            # Enforce role permission (FULFILLMENT_STAFF is not allowed to create receipts)
            if current_user.role == UserRole.FULFILLMENT_STAFF:
                logging.warning(f"Fulfillment staff user {current_user.id} denied receipt creation")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Fulfillment staff cannot create receiving receipts",
                )

            # Enforce warehouse access scope
            if not can_access_warehouse(current_user, request.warehouse_id):
                logging.warning(f"Warehouse access denied for user {current_user.id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this warehouse",
                )

            # Validate seller existence & status
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

            # Validate warehouse existence & status
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

            # Validate duplicate physical shipment identity
            seller_obj_id = ObjectId(request.seller_id)
            warehouse_obj_id = ObjectId(request.warehouse_id)

            existing_duplicate = await self.crud_receipt.get_duplicate_physical_receipt(
                seller_id=seller_obj_id,
                warehouse_id=warehouse_obj_id,
                tracking_number=request.tracking_number,
                ticket_number=request.ticket_number,
            )
            if existing_duplicate:
                logging.warning("Duplicate physical receipt rejected")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An active or completed receipt already exists for this physical shipment (tracking or ticket number)",
                )

            receipt_data = {
                "seller_id": seller_obj_id,
                "warehouse_id": warehouse_obj_id,
                "tracking_number": request.tracking_number,
                "ticket_number": request.ticket_number,
                "idempotency_key": request.idempotency_key,
                "status": ReceiptStatus.DRAFT,
                "items": [],
                "created_by": current_user.id,
            }

            try:
                receipt = await self.crud_receipt.create(obj_in=receipt_data)
                await self.crud_audit.create_audit(
                    obj_in={
                        "user_id": current_user.id,
                        "user_role": (
                            current_user.role.value
                            if isinstance(current_user.role, UserRole)
                            else str(current_user.role)
                        ),
                        "warehouse_id": receipt.warehouse_id,
                        "action": "RECEIPT_CREATED",
                        "entity_type": "RECEIPT",
                        "entity_id": str(receipt.id),
                        "new_state": {
                            "receipt_number": receipt.receipt_number,
                            "status": receipt.status.value,
                        },
                    }
                )
                return ReceiptResponse.model_validate(receipt)
            except Exception as error:
                if "duplicate key" in str(error).lower() or "11000" in str(error):
                    logging.warning("Duplicate physical tracking/ticket rejected by DB constraint")
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="An active or completed receipt already exists for this physical shipment",
                    )
                raise
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ReceiptController.create_receipt: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def add_receipt_item(
        self,
        receipt_id: str,
        request: AddReceiptItemRequest,
        current_user: User,
    ) -> ReceiptResponse:
        """
        Add or update a line item on an in-progress receipt by UPC.

        Args:
            receipt_id: Receipt ObjectId string.
            request: Item UPC and quantity data.
            current_user: Authenticated active user.

        Returns:
            ReceiptResponse: Formatted updated receipt response.

        Raises:
            HTTPException 403: If user lacks warehouse scope or role permission.
            HTTPException 404: If receipt or UPC is not found.
            HTTPException 400: If UPC belongs to a different seller.
            HTTPException 409: If receipt is already COMPLETED or CANCELLED.
        """
        try:
            logging.info("Executing ReceiptController.add_receipt_item")

            if current_user.role == UserRole.FULFILLMENT_STAFF:
                logging.warning(f"Fulfillment staff user {current_user.id} denied item entry")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Fulfillment staff cannot modify receiving receipts",
                )

            receipt = await self.crud_receipt.get_by_id(id=receipt_id)
            if not receipt:
                logging.warning(f"Receipt not found: {receipt_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Receipt not found",
                )

            if not can_access_warehouse(current_user, receipt.warehouse_id):
                logging.warning(f"Warehouse access denied for user {current_user.id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this warehouse",
                )

            if receipt.status in (ReceiptStatus.COMPLETED, ReceiptStatus.CANCELLED):
                logging.warning(f"Attempted to modify immutable receipt: {receipt.id}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot edit receipt in {receipt.status.value} status",
                )

            # Resolve UPC to Product
            product = await self.crud_product.get_by_upc(upc=request.upc)
            if not product:
                logging.warning(f"Product UPC not found: {request.upc}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with UPC '{request.upc}' not found",
                )

            if str(product.seller_id) != str(receipt.seller_id):
                logging.warning(f"UPC seller mismatch: product seller {product.seller_id} vs receipt seller {receipt.seller_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Product UPC does not belong to the receipt's seller",
                )

            item = ReceiptItem(
                product_id=product.id,
                upc=product.upc,
                good_qty=request.good_qty,
                damaged_qty=request.damaged_qty,
                received_qty=request.good_qty + request.damaged_qty,
            )

            updated_receipt = await self.crud_receipt.add_or_update_item(
                receipt=receipt, item=item
            )
            await self.crud_audit.create_audit(
                obj_in={
                    "user_id": current_user.id,
                    "user_role": (
                        current_user.role.value
                        if isinstance(current_user.role, UserRole)
                        else str(current_user.role)
                    ),
                    "warehouse_id": updated_receipt.warehouse_id,
                    "action": "RECEIPT_ITEM_ADDED_OR_UPDATED",
                    "entity_type": "RECEIPT",
                    "entity_id": str(updated_receipt.id),
                    "new_state": {
                        "upc": request.upc,
                        "good_qty": request.good_qty,
                        "damaged_qty": request.damaged_qty,
                    },
                }
            )
            return ReceiptResponse.model_validate(updated_receipt)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ReceiptController.add_receipt_item: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def get_receipt_by_id(
        self,
        receipt_id: str,
        current_user: User,
    ) -> ReceiptResponse:
        """
        Get receipt detail by ID.

        Args:
            receipt_id: Receipt ObjectId string.
            current_user: Authenticated active user.

        Returns:
            ReceiptResponse: Formatted receipt detail.

        Raises:
            HTTPException 403: If user lacks warehouse scope.
            HTTPException 404: If receipt is not found.
        """
        try:
            logging.info("Executing ReceiptController.get_receipt_by_id")
            receipt = await self.crud_receipt.get_by_id(id=receipt_id)
            if not receipt:
                logging.warning(f"Receipt not found: {receipt_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Receipt not found",
                )

            if not can_access_warehouse(current_user, receipt.warehouse_id):
                logging.warning(f"Warehouse access denied for user {current_user.id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this warehouse",
                )

            return ReceiptResponse.model_validate(receipt)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ReceiptController.get_receipt_by_id: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def list_receipts(
        self,
        warehouse_id: Optional[str],
        seller_id: Optional[str],
        status_param: Optional[str],
        tracking_number: Optional[str],
        current_user: User,
    ) -> list[ReceiptResponse]:
        """
        List receipt records filtered by query parameters and user scope.

        Args:
            warehouse_id: Optional warehouse filter.
            seller_id: Optional seller filter.
            status_param: Optional receipt status filter.
            tracking_number: Optional tracking number filter.
            current_user: Authenticated active user.

        Returns:
            list[ReceiptResponse]: Formatted list of receipts.

        Raises:
            HTTPException 403: If requested warehouse is out of user scope.
        """
        try:
            logging.info("Executing ReceiptController.list_receipts")

            allowed_warehouse_ids = (
                None if current_user.role == UserRole.OWNER else current_user.warehouse_ids
            )

            if warehouse_id and not can_access_warehouse(current_user, warehouse_id):
                logging.warning(f"Warehouse access denied for user {current_user.id}: {warehouse_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this warehouse",
                )

            parsed_status = None
            if status_param:
                try:
                    parsed_status = ReceiptStatus(status_param.upper())
                except ValueError:
                    logging.warning(f"Invalid receipt status filter: {status_param}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid receipt status: '{status_param}'",
                    )

            receipts = await self.crud_receipt.list_receipts(
                warehouse_id=warehouse_id,
                seller_id=seller_id,
                status=parsed_status,
                tracking_number=tracking_number,
                allowed_warehouse_ids=allowed_warehouse_ids,
            )
            return [ReceiptResponse.model_validate(receipt) for receipt in receipts]
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ReceiptController.list_receipts: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def complete_receipt(
        self,
        receipt_id: str,
        current_user: User,
    ) -> ReceiptResponse:
        """
        Complete an inbound receipt and apply good/damaged quantities to inventory.

        Guarantees exact-once execution under retries or concurrent requests.

        Args:
            receipt_id: Receipt ObjectId string.
            current_user: Authenticated active user.

        Returns:
            ReceiptResponse: Formatted completed receipt.

        Raises:
            HTTPException 403: If user lacks warehouse scope or role permission.
            HTTPException 404: If receipt is not found.
            HTTPException 400: If receipt has no line items.
            HTTPException 409: If receipt is already COMPLETED or CANCELLED.
        """
        try:
            logging.info("Executing ReceiptController.complete_receipt")

            if current_user.role == UserRole.FULFILLMENT_STAFF:
                logging.warning(f"Fulfillment staff user {current_user.id} denied receipt completion")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Fulfillment staff cannot complete receiving receipts",
                )

            receipt = await self.crud_receipt.get_by_id(id=receipt_id)
            if not receipt:
                logging.warning(f"Receipt not found: {receipt_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Receipt not found",
                )

            if not can_access_warehouse(current_user, receipt.warehouse_id):
                logging.warning(f"Warehouse access denied for user {current_user.id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this warehouse",
                )

            # Idempotency check: if already COMPLETED, return current receipt without incrementing inventory!
            if receipt.status == ReceiptStatus.COMPLETED:
                logging.info(f"Receipt {receipt.id} is already COMPLETED; returning idempotent result")
                return ReceiptResponse.model_validate(receipt)

            if receipt.status == ReceiptStatus.CANCELLED:
                logging.warning(f"Cannot complete cancelled receipt: {receipt.id}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot complete a cancelled receipt",
                )

            if not receipt.items:
                logging.warning(f"Receipt {receipt.id} has no line items")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot complete a receipt with no item lines",
                )

            # Attempt transaction if supported, or fall back to standalone atomic state claiming
            try:
                db = MongoDatabase()
                client = db.client
                async with await client.start_session() as session:
                    async with session.start_transaction():
                        claimed_receipt = await self.crud_receipt.claim_and_complete_receipt(
                            receipt_id=receipt.id,
                            completed_by=current_user.id,
                            session=session,
                        )
                        if not claimed_receipt:
                            refetched = await self.crud_receipt.get_by_id(id=receipt_id, session=session)
                            if refetched and refetched.status == ReceiptStatus.COMPLETED:
                                return ReceiptResponse.model_validate(refetched)
                            raise HTTPException(
                                status_code=status.HTTP_409_CONFLICT,
                                detail="Receipt completion status conflict",
                            )

                        await self._record_completion_movements_and_audit(
                            claimed_receipt=claimed_receipt,
                            current_user=current_user,
                            session=session,
                        )
                        return ReceiptResponse.model_validate(claimed_receipt)
            except HTTPException:
                raise
            except Exception as tx_error:
                if "transaction numbers" in str(tx_error).lower() or "replica set" in str(tx_error).lower():
                    logging.info("Standalone MongoDB detected; using atomic state claiming without multi-document transaction session")
                    claimed_receipt = await self.crud_receipt.claim_and_complete_receipt(
                        receipt_id=receipt.id,
                        completed_by=current_user.id,
                    )
                    if not claimed_receipt:
                        refetched = await self.crud_receipt.get_by_id(id=receipt_id)
                        if refetched and refetched.status == ReceiptStatus.COMPLETED:
                            return ReceiptResponse.model_validate(refetched)
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="Receipt completion status conflict",
                        )

                    await self._record_completion_movements_and_audit(
                        claimed_receipt=claimed_receipt,
                        current_user=current_user,
                    )
                    return ReceiptResponse.model_validate(claimed_receipt)
                raise
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ReceiptController.complete_receipt: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def _record_completion_movements_and_audit(
        self,
        claimed_receipt,
        current_user: User,
        session=None,
    ) -> None:
        """
        Record inventory movement history and audit log entry for a completed receipt.

        Args:
            claimed_receipt: Completed receipt document.
            current_user: Authenticated user completing the receipt.
            session: Optional Motor client session for transactions.
        """
        logging.info("Executing ReceiptController._record_completion_movements_and_audit")
        for item in claimed_receipt.items:
            inv = await self.crud_inventory.increment_stock(
                warehouse_id=claimed_receipt.warehouse_id,
                seller_id=claimed_receipt.seller_id,
                product_id=item.product_id,
                good_qty=item.good_qty,
                damaged_qty=item.damaged_qty,
                session=session,
            )

            if item.good_qty > 0:
                await self.crud_movement.create_movement(
                    obj_in={
                        "warehouse_id": claimed_receipt.warehouse_id,
                        "seller_id": claimed_receipt.seller_id,
                        "product_id": item.product_id,
                        "inventory_id": inv.id,
                        "movement_type": MovementType.RECEIVED,
                        "quantity": item.good_qty,
                        "previous_on_hand": inv.on_hand - item.good_qty,
                        "new_on_hand": inv.on_hand,
                        "previous_reserved": inv.reserved,
                        "new_reserved": inv.reserved,
                        "previous_damaged": inv.damaged - item.damaged_qty,
                        "new_damaged": inv.damaged,
                        "reference_type": MovementReferenceType.RECEIPT,
                        "reference_id": str(claimed_receipt.id),
                        "performed_by": current_user.id,
                    },
                    session=session,
                )

            if item.damaged_qty > 0:
                await self.crud_movement.create_movement(
                    obj_in={
                        "warehouse_id": claimed_receipt.warehouse_id,
                        "seller_id": claimed_receipt.seller_id,
                        "product_id": item.product_id,
                        "inventory_id": inv.id,
                        "movement_type": MovementType.DAMAGED_RECEIVED,
                        "quantity": item.damaged_qty,
                        "previous_on_hand": inv.on_hand,
                        "new_on_hand": inv.on_hand,
                        "previous_reserved": inv.reserved,
                        "new_reserved": inv.reserved,
                        "previous_damaged": inv.damaged - item.damaged_qty,
                        "new_damaged": inv.damaged,
                        "reference_type": MovementReferenceType.RECEIPT,
                        "reference_id": str(claimed_receipt.id),
                        "performed_by": current_user.id,
                    },
                    session=session,
                )

        await self.crud_audit.create_audit(
            obj_in={
                "user_id": current_user.id,
                "user_role": (
                    current_user.role.value
                    if isinstance(current_user.role, UserRole)
                    else str(current_user.role)
                ),
                "warehouse_id": claimed_receipt.warehouse_id,
                "action": "RECEIPT_COMPLETED",
                "entity_type": "RECEIPT",
                "entity_id": str(claimed_receipt.id),
                "new_state": {"status": "COMPLETED"},
            },
            session=session,
        )
