"""Controller for the read-only Whitfield AI operational assistant."""

from fastapi import HTTPException, status

from core import logger
from core.apis.schemas.requests.ai_requests import AIChatRequest
from core.apis.schemas.responses.ai_responses import AIChatResponse
from core.models.user_model import User
from core.services.ai.assistant_service import AIAssistantService, AIProviderUnavailableError
from core.services.ai.tool_registry import ToolContext

logging = logger(__name__)


class AIController:
    """Orchestrate AI chat requests using the authenticated live WMS user.

    The controller never accepts identity, role, or warehouse scope from client payloads.
    """

    def __init__(self) -> None:
        """Initialize the read-only AI orchestration service."""
        logging.info("Executing AIController.__init__")
        self.service = AIAssistantService()

    async def chat(self, request: AIChatRequest, current_user: User, request_id: str) -> AIChatResponse:
        """Answer one validated warehouse question with trusted current-user authorization.

        Args:
            request: Validated natural-language assistant request.
            current_user: Active user loaded from MongoDB by authentication dependency.
            request_id: Trace-safe request identifier generated server-side.

        Returns:
            AIChatResponse: Typed grounded answer and tool usage metadata.

        Raises:
            HTTPException 503: If the Gemini provider is unavailable.
            HTTPException 500: If an unexpected AI orchestration failure occurs.
        """
        try:
            logging.info(f"Executing AIController.chat request={request_id} user={current_user.id}")
            answer, tool_calls, sources = await self.service.answer(request.message, ToolContext(current_user=current_user, request_id=request_id))
            return AIChatResponse(answer=answer, tool_calls=tool_calls, sources=sources, request_id=request_id)
        except AIProviderUnavailableError as error:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AIController.chat request={request_id}: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error") from error
