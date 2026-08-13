"""
shipment_crud.py — Persistence operations for outbound parcel shipments.

Provides database methods for creating, retrieving, and updating shipment status.
"""

from datetime import datetime, timezone
from typing import Optional

from odmantic import ObjectId

from core import logger
from core.cruds.base import CRUDBase
from core.database.database import MongoDatabase
from core.models.shipment_model import Shipment, ShipmentStatus

logging = logger(__name__)


def _doc_to_shipment(doc: dict) -> Shipment:
    """Helper to convert Motor PyMongo document dict to ODMantic Shipment model."""
    if "_id" in doc:
        doc["id"] = doc.pop("_id")
    return Shipment(**doc)


class CRUDShipment(CRUDBase[Shipment, dict, dict]):
    """Database access layer for parcel shipments."""

    def __init__(self):
        """
        Initialize shipment CRUD helper.

        Binds the shared ODMantic engine to the Shipment model.
        """
        super().__init__(model=Shipment)

    async def get_by_id(self, *, id: str, session=None) -> Optional[Shipment]:
        """
        Read a shipment by ObjectId string.

        Args:
            id: Shipment ObjectId as a string.
            session: Optional Motor client session for transactions.

        Returns:
            Shipment | None: Shipment record if found.
        """
        try:
            logging.info("Executing CRUDShipment.get_by_id")
            try:
                object_id = ObjectId(id)
            except Exception:
                logging.warning("Invalid shipment ObjectId rejected")
                return None

            doc = await MongoDatabase()["shipments"].find_one({"_id": object_id}, session=session)
            if not doc:
                return None
            return _doc_to_shipment(doc)
        except Exception as error:
            logging.error(f"Error in CRUDShipment.get_by_id: {error}")
            raise

    async def get_by_order_id(self, *, order_id: ObjectId, session=None) -> Optional[Shipment]:
        """
        Read active shipment for a specific order.

        Args:
            order_id: Order ObjectId.
            session: Optional Motor client session.

        Returns:
            Shipment | None: Shipment record if found.
        """
        try:
            logging.info("Executing CRUDShipment.get_by_order_id")
            doc = await MongoDatabase()["shipments"].find_one({"order_id": order_id}, session=session)
            if not doc:
                return None
            return _doc_to_shipment(doc)
        except Exception as error:
            logging.error(f"Error in CRUDShipment.get_by_order_id: {error}")
            raise

    async def transition_status(
        self,
        *,
        shipment_id: ObjectId,
        from_status: ShipmentStatus,
        to_status: ShipmentStatus,
        session=None,
    ) -> Optional[Shipment]:
        """
        Atomically transition shipment status.

        Args:
            shipment_id: Shipment ObjectId.
            from_status: Expected current status.
            to_status: Target status.
            session: Optional Motor client session for transactions.

        Returns:
            Shipment | None: Updated Shipment if transition succeeded, None otherwise.
        """
        try:
            logging.info(f"Executing CRUDShipment.transition_status from {from_status.value} to {to_status.value}")
            collection = MongoDatabase()["shipments"]
            now = datetime.now(timezone.utc)

            filter_doc = {
                "_id": shipment_id,
                "status": from_status.value,
            }

            update_doc = {
                "$set": {
                    "status": to_status.value,
                    "updated_at": now,
                    "shipped_at": now if to_status == ShipmentStatus.SHIPPED else None,
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
            return _doc_to_shipment(result)
        except Exception as error:
            logging.error(f"Error in CRUDShipment.transition_status: {error}")
            raise
