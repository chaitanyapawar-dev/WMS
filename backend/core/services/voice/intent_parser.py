"""Narrow Gemini parser for receiving quantities and nothing else."""

import asyncio
import json

from core import logger
from core.apis.schemas.responses.voice_responses import ReceivingVoiceIntent, ReceivingVoiceIntentType
from core.services.ai.gemini_provider import GeminiConfigurationError, GeminiProvider

logging = logger(__name__)
VOICE_INTENT_TIMEOUT_SECONDS = 20
VOICE_INTENT_INSTRUCTION = """You are a strict receiving quantity parser. Return JSON only with intent, good_qty, and damaged_qty. Allowed intent values are RECEIVING_QUANTITY, UNCLEAR, and UNSUPPORTED. Your only supported job is to parse short receiving quantity statements. Never execute actions, never modify inventory, and never guess. Valid examples: 'two good and one damaged' => RECEIVING_QUANTITY, 2, 1; 'five good' => RECEIVING_QUANTITY, 5, 0; 'three damaged' => RECEIVING_QUANTITY, 0, 3. Vague or uncertain wording is UNCLEAR with null quantities. Any request about orders, users, stock changes, databases, navigation, or other operations is UNSUPPORTED with null quantities."""


class ReceivingIntentProviderError(RuntimeError):
    """Raised when Gemini cannot safely interpret a receiving transcript."""

    def __init__(self, message: str, transcript: str = "") -> None:
        """Store an optional already-transcribed safe fallback message.

        Args:
            message: Provider-safe error message for internal exception chaining.
            transcript: Safe STT transcript retained only for a manual-entry fallback.
        """
        super().__init__(message)
        self.transcript = transcript


class ReceivingIntentParser:
    """Convert transcript text into the fixed server-validated receiving intent vocabulary."""

    def __init__(self) -> None:
        """Initialize the existing server-side Gemini provider facade."""
        logging.info("Executing ReceivingIntentParser.__init__")
        self.provider = GeminiProvider()

    @staticmethod
    def _provider_failure_category(error: Exception) -> str:
        """Classify provider failures without logging provider response content.

        Args:
            error: Exception raised by the Gemini SDK or transport layer.

        Returns:
            str: Safe error category for operational logs.
        """
        code = getattr(error, "code", None)
        status = str(getattr(error, "status", "") or "").upper()
        if code == 429 or status == "RESOURCE_EXHAUSTED":
            return "quota_or_rate_limit"
        if code in (401, 403) or status in {"UNAUTHENTICATED", "PERMISSION_DENIED"}:
            return "authentication_or_project_access"
        if code == 400 or status == "INVALID_ARGUMENT":
            return "request_rejected"
        if isinstance(error, asyncio.TimeoutError):
            return "timeout"
        return "provider_unavailable"

    async def parse_receiving_intent(self, transcript: str) -> ReceivingVoiceIntent:
        """Interpret one transcript as a strict receiving quantity intent.

        Args:
            transcript: Non-empty Deepgram transcript for the current recording.

        Returns:
            ReceivingVoiceIntent: Server-validated typed interpretation.

        Raises:
            ReceivingIntentProviderError: If Gemini is unavailable or returns malformed output.
        """
        logging.info("Executing ReceivingIntentParser.parse_receiving_intent")
        try:
            with self.provider.get_client() as client:
                response = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=self.provider.model_name,
                        contents=[{"role": "user", "parts": [{"text": transcript}]}],
                        config={
                            "system_instruction": VOICE_INTENT_INSTRUCTION,
                            "temperature": 0,
                            "response_mime_type": "application/json",
                        },
                    ),
                    timeout=VOICE_INTENT_TIMEOUT_SECONDS,
                )
            raw_text = (getattr(response, "text", None) or "").strip()
            parsed = json.loads(raw_text)
            intent_value = parsed.get("intent")
            intent = ReceivingVoiceIntent(
                type=ReceivingVoiceIntentType(intent_value),
                good_qty=parsed.get("good_qty"),
                damaged_qty=parsed.get("damaged_qty"),
            )
            return intent
        except (GeminiConfigurationError, asyncio.TimeoutError, json.JSONDecodeError, ValueError, TypeError) as error:
            logging.error(f"Receiving intent parsing failed: {type(error).__name__}")
            raise ReceivingIntentProviderError("Voice quantity interpretation is unavailable") from error
        except Exception as error:
            logging.error(
                "Receiving intent provider failed "
                f"type={type(error).__name__} category={self._provider_failure_category(error)}"
            )
            raise ReceivingIntentProviderError("Voice quantity interpretation is unavailable") from error
