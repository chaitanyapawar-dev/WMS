"""
audit_router.py — FastAPI router for security and operational audit trail endpoints.

Exposes HTTP routes for querying system audit logs. Only OWNER and MANAGER roles are permitted.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from commons.auth import require_roles
from core import logger
from core.apis.schemas.responses.audit_responses import AuditLogResponse
from core.controllers.inventory_controller import InventoryController
from core.models.user_model import User, UserRole

logging = logger(__name__)

audit_router = APIRouter(prefix="/v1/audit-logs")


@audit_router.get(
    "",
    response_model=list[AuditLogResponse],
    status_code=status.HTTP_200_OK,
    summary="List security and operational audit logs",
    description="Query audit logs filtered by warehouse, user, action, or entity. Only OWNER and MANAGER roles permitted.",
)
async def list_audit_logs(
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse ID"),
    user_id: Optional[str] = Query(None, description="Filter by actor user ID"),
    action: Optional[str] = Query(None, description="Filter by action name"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (RECEIPT, INVENTORY, ORDER, etc.)"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    current_user: User = Depends(require_roles([UserRole.OWNER, UserRole.MANAGER])),
) -> list[AuditLogResponse]:
    """
    Route handler for GET /v1/audit-logs.

    Args:
        warehouse_id: Optional warehouse filter.
        user_id: Optional user filter.
        action: Optional action filter.
        entity_type: Optional entity type filter.
        entity_id: Optional entity ID filter.
        current_user: Authenticated user with OWNER or MANAGER role.

    Returns:
        list[AuditLogResponse]: List of matching audit log entries.

    Raises:
        HTTPException: Standardized domain or HTTP exception.
    """
    try:
        logging.info("Calling GET /v1/audit-logs endpoint")
        return await InventoryController().list_audits(
            warehouse_id=warehouse_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            current_user=current_user,
        )
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in GET /v1/audit-logs endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
