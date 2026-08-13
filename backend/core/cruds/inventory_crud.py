"""
inventory_crud.py — Persistence operations for inventory snapshots.

Provides database queries, upserts, atomic increments, and conditional updates
for warehouse stock management.
"""

from datetime import datetime, timezone
from typing import Optional

from odmantic import ObjectId

from core import logger
from core.cruds.base import CRUDBase
from core.database.database import MongoDatabase
from core.models.inventory_model import Inventory

logging = logger(__name__)


def _doc_to_inventory(doc: dict) -> Inventory:
    """Helper to convert Motor PyMongo document dict to ODMantic Inventory model."""
    if "_id" in doc:
        doc["id"] = doc.pop("_id")
    return Inventory(**doc)


class CRUDInventory(CRUDBase[Inventory, dict, dict]):
    """Database access layer for inventory records."""

    def __init__(self):
        """
        Initialize inventory CRUD helper.

        Binds the shared ODMantic engine to the Inventory model.
        """
        super().__init__(model=Inventory)

    async def get_by_id(self, *, id: str, session=None) -> Optional[Inventory]:
        """
        Read an inventory snapshot by ObjectId string.

        Args:
            id: Inventory ObjectId as a string.
            session: Optional Motor client session for transactions.

        Returns:
            Inventory | None: Inventory record if found.
        """
        try:
            logging.info("Executing CRUDInventory.get_by_id")
            try:
                object_id = ObjectId(id)
            except Exception:
                logging.warning("Invalid inventory ObjectId rejected")
                return None

            doc = await MongoDatabase()["inventory"].find_one({"_id": object_id}, session=session)
            if not doc:
                return None
            return _doc_to_inventory(doc)
        except Exception as error:
            logging.error(f"Error in CRUDInventory.get_by_id: {error}")
            raise

    async def get_by_scope(
        self,
        *,
        warehouse_id: ObjectId,
        seller_id: ObjectId,
        product_id: ObjectId,
        session=None,
    ) -> Optional[Inventory]:
        """
        Read an inventory snapshot by exact warehouse + seller + product scope.

        Args:
            warehouse_id: Warehouse ObjectId.
            seller_id: Seller ObjectId.
            product_id: Product ObjectId.
            session: Optional Motor client session for transactions.

        Returns:
            Inventory | None: Inventory record if found.
        """
        try:
            logging.info("Executing CRUDInventory.get_by_scope")
            doc = await MongoDatabase()["inventory"].find_one(
                {
                    "warehouse_id": warehouse_id,
                    "seller_id": seller_id,
                    "product_id": product_id,
                },
                session=session,
            )
            if not doc:
                return None
            return _doc_to_inventory(doc)
        except Exception as error:
            logging.error(f"Error in CRUDInventory.get_by_scope: {error}")
            raise

    async def get_or_create_snapshot(
        self,
        *,
        warehouse_id: ObjectId,
        seller_id: ObjectId,
        product_id: ObjectId,
        session=None,
    ) -> Inventory:
        """
        Ensure an inventory record exists for the given scope.

        Uses atomic upsert to prevent duplicate creation race conditions.

        Args:
            warehouse_id: Warehouse ObjectId.
            seller_id: Seller ObjectId.
            product_id: Product ObjectId.
            session: Optional Motor client session for transactions.

        Returns:
            Inventory: Guaranteed existing or newly created inventory snapshot.
        """
        try:
            logging.info("Executing CRUDInventory.get_or_create_snapshot")
            collection = MongoDatabase()["inventory"]
            now = datetime.now(timezone.utc)

            filter_doc = {
                "warehouse_id": warehouse_id,
                "seller_id": seller_id,
                "product_id": product_id,
            }
            update_doc = {
                "$setOnInsert": {
                    "on_hand": 0,
                    "reserved": 0,
                    "damaged": 0,
                    "low_stock_threshold": 10,
                    "version": 1,
                    "created_at": now,
                    "updated_at": now,
                }
            }

            result = await collection.find_one_and_update(
                filter_doc,
                update_doc,
                upsert=True,
                return_document=True,
                session=session,
            )
            return _doc_to_inventory(result)
        except Exception as error:
            logging.error(f"Error in CRUDInventory.get_or_create_snapshot: {error}")
            raise

    async def increment_stock(
        self,
        *,
        warehouse_id: ObjectId,
        seller_id: ObjectId,
        product_id: ObjectId,
        good_qty: int,
        damaged_qty: int,
        session=None,
    ) -> Inventory:
        """
        Atomically increment good (on_hand) and damaged stock for a product snapshot.

        Good quantity increases `on_hand`. Damaged quantity increases `damaged`.

        Args:
            warehouse_id: Warehouse ObjectId.
            seller_id: Seller ObjectId.
            product_id: Product ObjectId.
            good_qty: Quantity of good items to add.
            damaged_qty: Quantity of damaged items to add.
            session: Optional Motor client session for transactions.

        Returns:
            Inventory: Updated inventory snapshot.
        """
        try:
            logging.info("Executing CRUDInventory.increment_stock")
            collection = MongoDatabase()["inventory"]
            now = datetime.now(timezone.utc)

            filter_doc = {
                "warehouse_id": warehouse_id,
                "seller_id": seller_id,
                "product_id": product_id,
            }

            inc_fields = {}
            if good_qty > 0:
                inc_fields["on_hand"] = good_qty
            if damaged_qty > 0:
                inc_fields["damaged"] = damaged_qty

            update_doc = {
                "$inc": inc_fields,
                "$set": {"updated_at": now},
                "$setOnInsert": {
                    "reserved": 0,
                    "low_stock_threshold": 10,
                    "version": 1,
                    "created_at": now,
                },
            }

            # Add zero fallbacks if inserting new snapshot with 0 good or 0 damaged
            if "on_hand" not in inc_fields:
                update_doc["$setOnInsert"]["on_hand"] = 0
            if "damaged" not in inc_fields:
                update_doc["$setOnInsert"]["damaged"] = 0

            result = await collection.find_one_and_update(
                filter_doc,
                update_doc,
                upsert=True,
                return_document=True,
                session=session,
            )
            return _doc_to_inventory(result)
        except Exception as error:
            logging.error(f"Error in CRUDInventory.increment_stock: {error}")
            raise

    async def list_inventory(
        self,
        *,
        warehouse_id: Optional[str] = None,
        seller_id: Optional[str] = None,
        product_id: Optional[str] = None,
        allowed_warehouse_ids: Optional[list[ObjectId]] = None,
    ) -> list[Inventory]:
        """
        List inventory records matching query filters and user warehouse scope.

        Args:
            warehouse_id: Optional warehouse filter.
            seller_id: Optional seller filter.
            product_id: Optional product filter.
            allowed_warehouse_ids: Warehouse scope list for non-OWNER users (None for OWNER).

        Returns:
            list[Inventory]: List of matching inventory snapshots.
        """
        try:
            logging.info("Executing CRUDInventory.list_inventory")
            collection = MongoDatabase()["inventory"]
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

            if product_id:
                try:
                    query["product_id"] = ObjectId(product_id)
                except Exception:
                    return []

            cursor = collection.find(query)
            docs = await cursor.to_list(length=1000)
            return [_doc_to_inventory(doc) for doc in docs]
        except Exception as error:
            logging.error(f"Error in CRUDInventory.list_inventory: {error}")
            raise

    async def adjust_stock(
        self,
        *,
        inventory_id: ObjectId,
        delta: int,
        session=None,
    ) -> Optional[Inventory]:
        """
        Atomically adjust inventory on_hand stock by a positive or negative delta.

        Enforces that resulting on_hand >= 0 and resulting on_hand >= reserved.

        Args:
            inventory_id: Inventory ObjectId.
            delta: Quantity delta.
            session: Optional Motor client session for transactions.

        Returns:
            Inventory | None: Updated inventory, or None if condition violated.
        """
        try:
            logging.info("Executing CRUDInventory.adjust_stock")
            collection = MongoDatabase()["inventory"]
            now = datetime.now(timezone.utc)

            filter_doc = {"_id": inventory_id}
            if delta < 0:
                abs_delta = abs(delta)
                filter_doc["$expr"] = {
                    "$gte": [
                        {"$subtract": ["$on_hand", abs_delta]},
                        "$reserved",
                    ]
                }

            update_doc = {
                "$inc": {"on_hand": delta},
                "$set": {"updated_at": now},
            }

            result = await collection.find_one_and_update(
                filter_doc,
                update_doc,
                return_document=True,
                session=session,
            )
            if not result:
                return None
            return _doc_to_inventory(result)
        except Exception as error:
            logging.error(f"Error in CRUDInventory.adjust_stock: {error}")
            raise

    async def reserve_inventory_stock(
        self,
        *,
        warehouse_id: ObjectId,
        seller_id: ObjectId,
        product_id: ObjectId,
        quantity: int,
        session=None,
    ) -> Optional[Inventory]:
        """
        Atomic single-item inventory reservation primitive (P6-T03).

        Enforces (on_hand - reserved) >= quantity in the database query.

        Args:
            warehouse_id: Warehouse ObjectId.
            seller_id: Seller ObjectId.
            product_id: Product ObjectId.
            quantity: Quantity to reserve (> 0).
            session: Optional Motor client session for transactions.

        Returns:
            Inventory | None: Updated inventory if reservation succeeded, None if stock insufficient.
        """
        try:
            logging.info("Executing CRUDInventory.reserve_inventory_stock")
            collection = MongoDatabase()["inventory"]
            now = datetime.now(timezone.utc)

            filter_doc = {
                "warehouse_id": warehouse_id,
                "seller_id": seller_id,
                "product_id": product_id,
                "$expr": {
                    "$gte": [
                        {"$subtract": ["$on_hand", "$reserved"]},
                        quantity,
                    ]
                },
            }

            update_doc = {
                "$inc": {"reserved": quantity},
                "$set": {"updated_at": now},
            }

            result = await collection.find_one_and_update(
                filter_doc,
                update_doc,
                return_document=True,
                session=session,
            )
            if not result:
                return None
            return _doc_to_inventory(result)
        except Exception as error:
            logging.error(f"Error in CRUDInventory.reserve_inventory_stock: {error}")
            raise

    async def release_inventory_reservation(
        self,
        *,
        warehouse_id: ObjectId,
        seller_id: ObjectId,
        product_id: ObjectId,
        quantity: int,
        session=None,
    ) -> Optional[Inventory]:
        """
        Atomic reservation release primitive for order cancellations or compensation.

        Args:
            warehouse_id: Warehouse ObjectId.
            seller_id: Seller ObjectId.
            product_id: Product ObjectId.
            quantity: Quantity to release (> 0).
            session: Optional Motor client session.

        Returns:
            Inventory | None: Updated inventory if release succeeded, None otherwise.
        """
        try:
            logging.info("Executing CRUDInventory.release_inventory_reservation")
            collection = MongoDatabase()["inventory"]
            now = datetime.now(timezone.utc)

            filter_doc = {
                "warehouse_id": warehouse_id,
                "seller_id": seller_id,
                "product_id": product_id,
                "reserved": {"$gte": quantity},
            }

            update_doc = {
                "$inc": {"reserved": -quantity},
                "$set": {"updated_at": now},
            }

            result = await collection.find_one_and_update(
                filter_doc,
                update_doc,
                return_document=True,
                session=session,
            )
            if not result:
                return None
            return _doc_to_inventory(result)
        except Exception as error:
            logging.error(f"Error in CRUDInventory.release_inventory_reservation: {error}")
            raise

    async def ship_inventory_stock(
        self,
        *,
        warehouse_id: ObjectId,
        seller_id: ObjectId,
        product_id: ObjectId,
        quantity: int,
        session=None,
    ) -> Optional[Inventory]:
        """
        Atomic stock reduction primitive for order shipping (P6-T10).

        Decrements both on_hand and reserved by quantity.

        Args:
            warehouse_id: Warehouse ObjectId.
            seller_id: Seller ObjectId.
            product_id: Product ObjectId.
            quantity: Quantity shipped (> 0).
            session: Optional Motor client session for transactions.

        Returns:
            Inventory | None: Updated inventory if shipping succeeded, None if conditions violated.
        """
        try:
            logging.info("Executing CRUDInventory.ship_inventory_stock")
            collection = MongoDatabase()["inventory"]
            now = datetime.now(timezone.utc)

            filter_doc = {
                "warehouse_id": warehouse_id,
                "seller_id": seller_id,
                "product_id": product_id,
                "on_hand": {"$gte": quantity},
                "reserved": {"$gte": quantity},
            }

            update_doc = {
                "$inc": {
                    "on_hand": -quantity,
                    "reserved": -quantity,
                },
                "$set": {"updated_at": now},
            }

            result = await collection.find_one_and_update(
                filter_doc,
                update_doc,
                return_document=True,
                session=session,
            )
            if not result:
                return None
            return _doc_to_inventory(result)
        except Exception as error:
            logging.error(f"Error in CRUDInventory.ship_inventory_stock: {error}")
            raise
