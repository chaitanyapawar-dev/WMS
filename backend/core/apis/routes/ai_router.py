"""Authenticated route for the read-only Whitfield AI operational assistant."""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from commons.auth import get_current_user
from core import logger
from core.apis.schemas.requests.ai_requests import AIChatRequest
from core.apis.schemas.responses.ai_responses import AIChatResponse
from core.controllers.ai_controller import AIController
from core.models.user_model import User

logging = logger(__name__)
ai_router = APIRouter(prefix="/v1/ai")


@ai_router.post("/chat", response_model=AIChatResponse, status_code=status.HTTP_200_OK, summary="Ask the read-only Whitfield operational assistant")
async def chat(request: AIChatRequest, current_user: User = Depends(get_current_user)) -> AIChatResponse:
    """Route POST /v1/ai/chat to the trusted server-side AI controller.

    Uses the standard current-user dependency so token status and scope remain authoritative.

    Args:
        request: Validated AI question payload.
        current_user: Authenticated active MongoDB user.

    Returns:
        AIChatResponse: Typed grounded answer and tool names used.

    Raises:
        HTTPException: Preserves auth, provider, and validation failures.
    """
    try:
        request_id = uuid4().hex
        logging.info(f"Calling POST /v1/ai/chat endpoint request={request_id} user={current_user.id}")
        return await AIController().chat(request=request, current_user=current_user, request_id=request_id)
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in POST /v1/ai/chat endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error") from error
