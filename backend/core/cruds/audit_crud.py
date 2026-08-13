"""
audit_crud.py — Persistence operations for security and business audit logs.

Provides database methods for recording audit events and querying audit trails.
"""

from typing import Optional

from odmantic import ObjectId

from core import logger
from core.cruds.base import CRUDBase
from core.database.database import MongoDatabase
from core.models.audit_model import AuditLog

logging = logger(__name__)


def _doc_to_audit(doc: dict) -> AuditLog:
    """Helper to convert Motor PyMongo document dict to ODMantic AuditLog model."""
    if "_id" in doc:
        doc["id"] = doc.pop("_id")
    return AuditLog(**doc)


class CRUDAudit(CRUDBase[AuditLog, dict, dict]):
    """Database access layer for audit log records."""

    def __init__(self):
        """
        Initialize audit CRUD helper.

        Binds the shared ODMantic engine to the AuditLog model.
        """
        super().__init__(model=AuditLog)

    async def create_audit(self, *, obj_in: dict, session=None) -> AuditLog:
        """
        Record a new security or business action audit log event.

        Args:
            obj_in: Audit payload dictionary.
            session: Optional Motor client session for transactions.

        Returns:
            AuditLog: Created audit log document.
        """
        try:
            logging.info("Executing CRUDAudit.create_audit")
            audit = AuditLog(**obj_in)
            if session:
                doc = audit.model_dump(by_alias=True)
                doc["_id"] = audit.id
                await MongoDatabase()["audit_logs"].insert_one(doc, session=session)
                return audit
            return await self.engine.save(audit)
        except Exception as error:
            logging.error(f"Error in CRUDAudit.create_audit: {error}")
            raise

    async def list_audits(
        self,
        *,
        warehouse_id: Optional[str] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        allowed_warehouse_ids: Optional[list[ObjectId]] = None,
    ) -> list[AuditLog]:
        """
        List audit logs sorted chronologically descending (newest first).

        Args:
            warehouse_id: Optional warehouse ID filter.
            user_id: Optional user ID filter.
            action: Optional action name filter.
            entity_type: Optional entity type filter.
            entity_id: Optional entity ID filter.
            allowed_warehouse_ids: Warehouse scope list for non-OWNER users (None for OWNER).

        Returns:
            list[AuditLog]: Matching audit log records.
        """
        try:
            logging.info("Executing CRUDAudit.list_audits")
            collection = MongoDatabase()["audit_logs"]
            query = {}

            if warehouse_id:
                try:
                    query["warehouse_id"] = ObjectId(warehouse_id)
                except Exception:
                    return []
            elif allowed_warehouse_ids is not None:
                query["warehouse_id"] = {"$in": allowed_warehouse_ids}

            if user_id:
                try:
                    query["user_id"] = ObjectId(user_id)
                except Exception:
                    return []

            if action:
                query["action"] = action

            if entity_type:
                query["entity_type"] = entity_type

            if entity_id:
                query["entity_id"] = entity_id

            cursor = collection.find(query).sort("created_at", -1)
            docs = await cursor.to_list(length=1000)
            return [_doc_to_audit(doc) for doc in docs]
        except Exception as error:
            logging.error(f"Error in CRUDAudit.list_audits: {error}")
            raise
