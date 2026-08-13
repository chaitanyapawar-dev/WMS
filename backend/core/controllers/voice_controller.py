"""Domain orchestration for the non-mutating inbound receiving voice preview."""

from fastapi import HTTPException, status

from commons.auth import can_access_warehouse
from core import logger
from core.apis.schemas.requests.voice_requests import VoiceWorkflow
from core.apis.schemas.responses.voice_responses import (
    ReceivingVoiceContext,
    ReceivingVoiceIntent,
    ReceivingVoiceIntentType,
    ReceivingVoicePreviewResponse,
)
from core.cruds.product_crud import CRUDProduct
from core.cruds.receipt_crud import CRUDReceipt
from core.models.receipt_model import ReceiptStatus
from core.models.user_model import User
from core.services.voice.deepgram_provider import DeepgramConfigurationError, DeepgramProviderError
from core.services.voice.intent_parser import ReceivingIntentProviderError
from core.services.voice.voice_service import ReceivingVoiceService, VoiceAudioValidationError

logging = logger(__name__)


class VoiceController:
    """Validate receiving context before returning a typed, read-only voice preview."""

    def __init__(self) -> None:
        """Initialize existing receipt/product CRUD helpers and voice providers."""
        logging.info("Executing VoiceController.__init__")
        self.crud_receipt = CRUDReceipt()
        self.crud_product = CRUDProduct()
        self.voice_service = ReceivingVoiceService()

    async def interpret_receiving(
        self,
        workflow: VoiceWorkflow,
        receipt_id: str,
        upc: str,
        audio_bytes: bytes,
        content_type: str,
        current_user: User,
        request_id: str,
    ) -> ReceivingVoicePreviewResponse:
        """Interpret one authorized receiving recording without mutating WMS state.

        Args:
            workflow: Fixed supported workflow value from the multipart request.
            receipt_id: Existing receipt identifier supplied as non-authoritative context.
            upc: Product barcode supplied as non-authoritative context.
            audio_bytes: Short in-memory browser recording.
            content_type: Browser audio MIME type.
            current_user: Authenticated receiving-capable MongoDB user.
            request_id: Server-generated trace identifier.

        Returns:
            ReceivingVoicePreviewResponse: Preview requiring separate user confirmation.

        Raises:
            HTTPException: For invalid context, forbidden scope, or unavailable providers.
        """
        try:
            logging.info(f"Executing VoiceController.interpret_receiving request={request_id}")
            if workflow != VoiceWorkflow.RECEIVING:
                logging.warning(f"Unsupported voice workflow rejected request={request_id}")
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported voice workflow")

            receipt = await self.crud_receipt.get_by_id(id=receipt_id)
            if not receipt:
                logging.warning(f"Voice preview receipt not found: {receipt_id}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")
            if not can_access_warehouse(current_user, receipt.warehouse_id):
                logging.warning(f"Voice preview warehouse access denied for user {current_user.id}")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this warehouse")
            if receipt.status in (ReceiptStatus.COMPLETED, ReceiptStatus.CANCELLED):
                logging.warning(f"Voice preview rejected immutable receipt: {receipt.id}")
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Cannot edit receipt in {receipt.status.value} status")

            normalized_upc = upc.strip()
            product = await self.crud_product.get_by_upc(upc=normalized_upc)
            if not product:
                logging.warning(f"Voice preview product UPC not found: {normalized_upc}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
            if str(product.seller_id) != str(receipt.seller_id):
                logging.warning(f"Voice preview UPC seller mismatch for receipt {receipt.id}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product UPC does not belong to the receipt's seller")

            context = ReceivingVoiceContext(
                receipt_id=str(receipt.id),
                product_id=str(product.id),
                product_name=product.name,
                upc=product.upc,
            )
            try:
                transcript, intent = await self.voice_service.interpret(audio_bytes, content_type)
            except VoiceAudioValidationError as error:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
            except (DeepgramConfigurationError, DeepgramProviderError) as error:
                logging.warning(f"Voice transcription unavailable request={request_id}: {type(error).__name__}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="I couldn't transcribe that recording. Please try again or enter quantities manually.",
                ) from error
            except ReceivingIntentProviderError as error:
                logging.warning(f"Voice intent parsing unavailable request={request_id}")
                return ReceivingVoicePreviewResponse(
                    transcript=error.transcript,
                    intent=ReceivingVoiceIntent(type=ReceivingVoiceIntentType.UNCLEAR),
                    context=context,
                    requires_confirmation=False,
                    message="I couldn't interpret the quantities right now. Please enter them manually.",
                    request_id=request_id,
                )

            messages = {
                ReceivingVoiceIntentType.UNCLEAR: "I couldn't confidently determine the quantities. Please try again or enter them manually.",
                ReceivingVoiceIntentType.UNSUPPORTED: "This voice command is not supported in receiving mode.",
            }
            return ReceivingVoicePreviewResponse(
                transcript=transcript,
                intent=intent,
                context=context,
                requires_confirmation=intent.type == ReceivingVoiceIntentType.RECEIVING_QUANTITY,
                message=messages.get(intent.type),
                request_id=request_id,
            )
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in VoiceController.interpret_receiving request={request_id}: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error") from error
