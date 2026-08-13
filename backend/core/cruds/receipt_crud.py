"""
receipt_crud.py — Persistence operations for inbound physical receipts.

Provides database access methods for creating, reading, updating items,
and atomically completing receipts.
"""

from datetime import datetime, timezone
import random
import string
from typing import Optional

from odmantic import ObjectId
from pymongo.errors import DuplicateKeyError

from core import logger
from core.cruds.base import CRUDBase
from core.database.database import MongoDatabase
from core.models.receipt_model import Receipt, ReceiptItem, ReceiptStatus

logging = logger(__name__)


class CRUDReceipt(CRUDBase[Receipt, dict, dict]):
    """Database access layer for receipt records."""

    def __init__(self):
        """
        Initialize receipt CRUD helper.

        Binds the shared ODMantic engine to the Receipt model.
        """
        super().__init__(model=Receipt)

    def _generate_receipt_number(self) -> str:
        """
        Generate a unique human-readable receipt number.

        Returns:
            str: Generated receipt number string (e.g. REC-20260813-A8F2).
        """
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"REC-{now_str}-{random_suffix}"

    async def create(self, *, obj_in: dict) -> Receipt:
        """
        Create a new inbound receipt document.

        Args:
            obj_in: Receipt fields dictionary.

        Returns:
            Receipt: Created receipt document.

        Raises:
            DuplicateKeyError: If duplicate physical tracking/ticket or receipt_number occurs.
        """
        try:
            logging.info("Executing CRUDReceipt.create")
            if "receipt_number" not in obj_in or not obj_in["receipt_number"]:
                obj_in["receipt_number"] = self._generate_receipt_number()

            receipt = Receipt(**obj_in)
            return await self.engine.save(receipt)
        except DuplicateKeyError:
            logging.warning("Duplicate receipt identity or tracking/ticket rejected by DB index")
            raise
        except Exception as error:
            logging.error(f"Error in CRUDReceipt.create: {error}")
            raise

    async def get_by_id(self, *, id: str, session=None) -> Optional[Receipt]:
        """
        Read a receipt by ObjectId string.

        Args:
            id: Receipt ObjectId string.
            session: Optional Motor client session for transactions.

        Returns:
            Receipt | None: Receipt document if found.
        """
        try:
            logging.info("Executing CRUDReceipt.get_by_id")
            try:
                object_id = ObjectId(id)
            except Exception:
                logging.warning("Invalid receipt ObjectId rejected")
                return None

            if session:
                doc = await MongoDatabase()["receipts"].find_one({"_id": object_id}, session=session)
                if not doc:
                    return None
                return Receipt(**doc)

            return await self.engine.find_one(Receipt, Receipt.id == object_id)
        except Exception as error:
            logging.error(f"Error in CRUDReceipt.get_by_id: {error}")
            raise

    async def get_duplicate_physical_receipt(
        self,
        *,
        seller_id: ObjectId,
        warehouse_id: ObjectId,
        tracking_number: Optional[str] = None,
        ticket_number: Optional[str] = None,
    ) -> Optional[Receipt]:
        """
        Check whether an active or completed receipt exists for the physical shipment identity.

        Args:
            seller_id: Seller ObjectId.
            warehouse_id: Warehouse ObjectId.
            tracking_number: Optional tracking number.
            ticket_number: Optional ticket number.

        Returns:
            Receipt | None: Existing receipt if conflict found.
        """
        try:
            logging.info("Executing CRUDReceipt.get_duplicate_physical_receipt")
            collection = MongoDatabase()["receipts"]

            if tracking_number:
                doc = await collection.find_one(
                    {
                        "seller_id": seller_id,
                        "warehouse_id": warehouse_id,
                        "tracking_number": tracking_number,
                        "status": {"$ne": ReceiptStatus.CANCELLED.value},
                    }
                )
                if doc:
                    return Receipt(**doc)

            if ticket_number:
                doc = await collection.find_one(
                    {
                        "warehouse_id": warehouse_id,
                        "ticket_number": ticket_number,
                        "status": {"$ne": ReceiptStatus.CANCELLED.value},
                    }
                )
                if doc:
                    return Receipt(**doc)

            return None
        except Exception as error:
            logging.error(f"Error in CRUDReceipt.get_duplicate_physical_receipt: {error}")
            raise

    async def add_or_update_item(self, *, receipt: Receipt, item: ReceiptItem) -> Receipt:
        """
        Add a new line item to a receipt or update an existing item with matching UPC.

        Args:
            receipt: Existing Receipt model.
            item: ReceiptItem embedded model.

        Returns:
            Receipt: Updated receipt document.
        """
        try:
            logging.info("Executing CRUDReceipt.add_or_update_item")
            now = datetime.now(timezone.utc)
            updated_items = []
            found = False

            for existing in receipt.items:
                if existing.upc == item.upc:
                    existing.good_qty = item.good_qty
                    existing.damaged_qty = item.damaged_qty
                    existing.received_qty = item.good_qty + item.damaged_qty
                    found = True
                updated_items.append(existing)

            if not found:
                item.received_qty = item.good_qty + item.damaged_qty
                updated_items.append(item)

            receipt.items = updated_items
            receipt.status = ReceiptStatus.IN_PROGRESS
            receipt.updated_at = now
            return await self.engine.save(receipt)
        except Exception as error:
            logging.error(f"Error in CRUDReceipt.add_or_update_item: {error}")
            raise

    async def claim_and_complete_receipt(
        self,
        *,
        receipt_id: ObjectId,
        completed_by: ObjectId,
        session=None,
    ) -> Optional[Receipt]:
        """
        Atomically transition a receipt status to COMPLETED if not already completed.

        This atomic conditional update guarantees receipt completion logic runs exactly once.

        Args:
            receipt_id: Receipt ObjectId.
            completed_by: User ObjectId completing the receipt.
            session: Optional Motor client session for transactions.

        Returns:
            Receipt | None: Updated receipt if claimed successfully; None if already completed/cancelled.
        """
        try:
            logging.info("Executing CRUDReceipt.claim_and_complete_receipt")
            collection = MongoDatabase()["receipts"]
            now = datetime.now(timezone.utc)

            filter_doc = {
                "_id": receipt_id,
                "status": {"$in": [ReceiptStatus.DRAFT.value, ReceiptStatus.IN_PROGRESS.value]},
            }
            update_doc = {
                "$set": {
                    "status": ReceiptStatus.COMPLETED.value,
                    "completed_by": completed_by,
                    "completed_at": now,
                    "updated_at": now,
                }
            }

            result = await collection.find_one_and_update(
                filter_doc,
                update_doc,
                return_document=True,
                session=session,
            )
            if not result:
                return None
            return Receipt(**result)
        except Exception as error:
            logging.error(f"Error in CRUDReceipt.claim_and_complete_receipt: {error}")
            raise

    async def list_receipts(
        self,
        *,
        warehouse_id: Optional[str] = None,
        seller_id: Optional[str] = None,
        status: Optional[ReceiptStatus] = None,
        tracking_number: Optional[str] = None,
        allowed_warehouse_ids: Optional[list[ObjectId]] = None,
    ) -> list[Receipt]:
        """
        List receipt records matching optional query filters and user warehouse scope.

        Args:
            warehouse_id: Optional warehouse filter.
            seller_id: Optional seller filter.
            status: Optional receipt status filter.
            tracking_number: Optional tracking number filter.
            allowed_warehouse_ids: Warehouse scope list for non-OWNER users (None for OWNER).

        Returns:
            list[Receipt]: List of matching receipt documents.
        """
        try:
            logging.info("Executing CRUDReceipt.list_receipts")
            collection = MongoDatabase()["receipts"]
            query = {}

            if warehouse_id:
                try:
                    query["warehouse_id"] = ObjectId(warehouse_id)
                except Exception:
                    return []
            elif allowed_warehouse_ids is not None:
                query["warehouse_id"] = {"$in": allowed_warehouse_ids}

            if seller_id:
                try:
                    query["seller_id"] = ObjectId(seller_id)
                except Exception:
                    return []

            if status:
                query["status"] = status.value if isinstance(status, ReceiptStatus) else str(status)

            if tracking_number:
                query["tracking_number"] = tracking_number

            cursor = collection.find(query)
            docs = await cursor.to_list(length=1000)
            return [Receipt(**doc) for doc in docs]
        except Exception as error:
            logging.error(f"Error in CRUDReceipt.list_receipts: {error}")
            raise
