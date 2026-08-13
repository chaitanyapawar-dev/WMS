"""
movement_crud.py — Persistence operations for append-only inventory movements.

Provides database methods for recording stock movements and querying ledger history.
"""

from typing import Optional

from odmantic import ObjectId

from core import logger
from core.cruds.base import CRUDBase
from core.database.database import MongoDatabase
from core.models.movement_model import InventoryMovement, MovementType

logging = logger(__name__)


def _doc_to_movement(doc: dict) -> InventoryMovement:
    """Helper to convert Motor PyMongo document dict to ODMantic InventoryMovement model."""
    if "_id" in doc:
        doc["id"] = doc.pop("_id")
    return InventoryMovement(**doc)


class CRUDMovement(CRUDBase[InventoryMovement, dict, dict]):
    """Database access layer for inventory movement records."""

    def __init__(self):
        """
        Initialize movement CRUD helper.

        Binds the shared ODMantic engine to the InventoryMovement model.
        """
        super().__init__(model=InventoryMovement)

    async def create_movement(self, *, obj_in: dict, session=None) -> InventoryMovement:
        """
        Record a new append-only inventory movement event.

        Args:
            obj_in: Movement payload dictionary.
            session: Optional Motor client session for transactions.

        Returns:
            InventoryMovement: Created movement record.
        """
        try:
            logging.info("Executing CRUDMovement.create_movement")
            movement = InventoryMovement(**obj_in)
            if session:
                doc = movement.model_dump(by_alias=True)
                doc["_id"] = movement.id
                await MongoDatabase()["inventory_movements"].insert_one(doc, session=session)
                return movement
            return await self.engine.save(movement)
        except Exception as error:
            logging.error(f"Error in CRUDMovement.create_movement: {error}")
            raise

    async def list_movements(
        self,
        *,
        inventory_id: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        seller_id: Optional[str] = None,
        product_id: Optional[str] = None,
        movement_type: Optional[MovementType] = None,
        allowed_warehouse_ids: Optional[list[ObjectId]] = None,
    ) -> list[InventoryMovement]:
        """
        List inventory movements sorted chronologically.

        Args:
            inventory_id: Optional inventory ID filter.
            warehouse_id: Optional warehouse ID filter.
            seller_id: Optional seller ID filter.
            product_id: Optional product ID filter.
            movement_type: Optional movement type filter.
            allowed_warehouse_ids: Warehouse scope list for non-OWNER users (None for OWNER).

        Returns:
            list[InventoryMovement]: Matching movement history records.
        """
        try:
            logging.info("Executing CRUDMovement.list_movements")
            collection = MongoDatabase()["inventory_movements"]
            query = {}

            if inventory_id:
                try:
                    query["inventory_id"] = ObjectId(inventory_id)
                except Exception:
                    return []

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

            if movement_type:
                query["movement_type"] = (
                    movement_type.value
                    if isinstance(movement_type, MovementType)
                    else str(movement_type)
                )

            cursor = collection.find(query).sort("created_at", 1)
            docs = await cursor.to_list(length=1000)
            return [_doc_to_movement(doc) for doc in docs]
        except Exception as error:
            logging.error(f"Error in CRUDMovement.list_movements: {error}")
            raise
