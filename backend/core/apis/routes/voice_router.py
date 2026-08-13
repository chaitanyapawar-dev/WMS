"""Authenticated preview endpoint for the narrow inbound receiving voice workflow."""

from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from commons.auth import require_roles
from core import logger
from core.apis.schemas.requests.voice_requests import VoiceWorkflow
from core.apis.schemas.responses.voice_responses import ReceivingVoicePreviewResponse
from core.controllers.voice_controller import VoiceController
from core.models.user_model import User, UserRole

logging = logger(__name__)
voice_router = APIRouter(prefix="/v1/voice")


@voice_router.post(
    "/interpret",
    response_model=ReceivingVoicePreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Interpret a receiving quantity recording as a confirmation preview",
)
async def interpret_receiving_voice(
    audio: UploadFile = File(..., description="Short browser recording for quantity interpretation"),
    workflow: VoiceWorkflow = Form(..., description="Only the receiving workflow is supported"),
    receipt_id: str = Form(..., min_length=1, description="Existing receipt context"),
    upc: str = Form(..., min_length=1, description="Selected product barcode context"),
    current_user: User = Depends(require_roles([UserRole.OWNER, UserRole.MANAGER, UserRole.RECEIVING_STAFF])),
) -> ReceivingVoicePreviewResponse:
    """Return a read-only receiving preview from one short microphone recording.

    Validates the authenticated user's receiving role, receipt context, and warehouse
    scope before calling external providers. It never adds a receipt item or changes stock.

    Args:
        audio: Uploaded in-memory browser audio file.
        workflow: Fixed receiving workflow selector.
        receipt_id: Receipt context used for server-side access checks.
        upc: Product barcode context used for server-side seller validation.
        current_user: Authenticated user with receiving access.

    Returns:
        ReceivingVoicePreviewResponse: Typed preview that requires user confirmation.

    Raises:
        HTTPException: Preserves authentication, authorization, validation, and provider errors.
    """
    try:
        request_id = uuid4().hex
        logging.info(f"Calling POST /v1/voice/interpret endpoint request={request_id} receipt={receipt_id}")
        audio_bytes = await audio.read()
        logging.info(
            f"Voice audio received request={request_id} content_type={audio.content_type or 'missing'} bytes={len(audio_bytes)}"
        )
        return await VoiceController().interpret_receiving(
            workflow=workflow,
            receipt_id=receipt_id,
            upc=upc,
            audio_bytes=audio_bytes,
            content_type=audio.content_type or "",
            current_user=current_user,
            request_id=request_id,
        )
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in POST /v1/voice/interpret endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error") from error
