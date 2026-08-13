"""
order_crud.py — Persistence operations for sales orders.

Provides database methods for creating, retrieving, querying, and updating order status.
"""

from datetime import datetime, timezone
from typing import Optional, Any

from odmantic import ObjectId

from core import logger
from core.cruds.base import CRUDBase
from core.database.database import MongoDatabase
from core.models.order_model import Order, OrderStatus

logging = logger(__name__)


def _doc_to_order(doc: dict) -> Order:
    """Helper to convert Motor PyMongo document dict to ODMantic Order model."""
    if "_id" in doc:
        doc["id"] = doc.pop("_id")
    return Order(**doc)


class CRUDOrder(CRUDBase[Order, dict, dict]):
    """Database access layer for sales orders."""

    def __init__(self):
        """
        Initialize order CRUD helper.

        Binds the shared ODMantic engine to the Order model.
        """
        super().__init__(model=Order)

    async def generate_order_number(self) -> str:
        """
        Generate a unique human-readable order number.

        Returns:
            str: Unique order identifier string (e.g. ORD-1001).
        """
        collection = MongoDatabase()["orders"]
        count = await collection.count_documents({})
        return f"ORD-{1001 + count}"

    async def get_by_id(self, *, id: str, session=None) -> Optional[Order]:
        """
        Read an order by ObjectId string.

        Args:
            id: Order ObjectId as a string.
            session: Optional Motor client session for transactions.

        Returns:
            Order | None: Order record if found.
        """
        try:
            logging.info("Executing CRUDOrder.get_by_id")
            try:
                object_id = ObjectId(id)
            except Exception:
                logging.warning("Invalid order ObjectId rejected")
                return None

            doc = await MongoDatabase()["orders"].find_one({"_id": object_id}, session=session)
            if not doc:
                return None
            return _doc_to_order(doc)
        except Exception as error:
            logging.error(f"Error in CRUDOrder.get_by_id: {error}")
            raise

    async def get_by_order_number(self, *, order_number: str, session=None) -> Optional[Order]:
        """
        Read an order by order number string.

        Args:
            order_number: Order number (e.g. ORD-1001).
            session: Optional Motor client session.

        Returns:
            Order | None: Order record if found.
        """
        try:
            logging.info("Executing CRUDOrder.get_by_order_number")
            doc = await MongoDatabase()["orders"].find_one({"order_number": order_number}, session=session)
            if not doc:
                return None
            return _doc_to_order(doc)
        except Exception as error:
            logging.error(f"Error in CRUDOrder.get_by_order_number: {error}")
            raise

    async def list_orders(
        self,
        *,
        warehouse_id: Optional[str] = None,
        seller_id: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        order_number: Optional[str] = None,
        allowed_warehouse_ids: Optional[list[ObjectId]] = None,
    ) -> list[Order]:
        """
        List orders matching query filters and user warehouse scope.

        Args:
            warehouse_id: Optional warehouse filter.
            seller_id: Optional seller filter.
            status: Optional order status filter.
            order_number: Optional order number search string.
            allowed_warehouse_ids: Warehouse scope list for non-OWNER users (None for OWNER).

        Returns:
            list[Order]: List of matching sales orders.
        """
        try:
            logging.info("Executing CRUDOrder.list_orders")
            collection = MongoDatabase()["orders"]
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
                query["status"] = status.value if isinstance(status, OrderStatus) else str(status)

            if order_number:
                query["order_number"] = order_number

            cursor = collection.find(query).sort("created_at", -1)
            docs = await cursor.to_list(length=1000)
            return [_doc_to_order(doc) for doc in docs]
        except Exception as error:
            logging.error(f"Error in CRUDOrder.list_orders: {error}")
            raise

    async def transition_status(
        self,
        *,
        order_id: ObjectId,
        from_statuses: list[OrderStatus],
        to_status: OrderStatus,
        extra_fields: Optional[dict[str, Any]] = None,
        session=None,
    ) -> Optional[Order]:
        """
        Atomically transition an order from one of allowed from_statuses to to_status.

        Args:
            order_id: Order ObjectId.
            from_statuses: List of allowed current statuses.
            to_status: Target new status.
            extra_fields: Additional fields to update (e.g. timestamps, items reserved_quantity).
            session: Optional Motor client session for transactions.

        Returns:
            Order | None: Updated Order if transition succeeded, None if current status not matching.
        """
        try:
            logging.info(f"Executing CRUDOrder.transition_status from {[s.value for s in from_statuses]} to {to_status.value}")
            collection = MongoDatabase()["orders"]
            now = datetime.now(timezone.utc)

            from_values = [s.value if isinstance(s, OrderStatus) else str(s) for s in from_statuses]
            filter_doc = {
                "_id": order_id,
                "status": {"$in": from_values},
            }

            set_doc = {
                "status": to_status.value,
                "updated_at": now,
            }
            if extra_fields:
                set_doc.update(extra_fields)

            update_doc = {"$set": set_doc}

            result = await collection.find_one_and_update(
                filter_doc,
                update_doc,
                return_document=True,
                session=session,
            )
            if not result:
                return None
            return _doc_to_order(result)
        except Exception as error:
            logging.error(f"Error in CRUDOrder.transition_status: {error}")
            raise
