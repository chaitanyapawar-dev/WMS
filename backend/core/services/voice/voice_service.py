"""Provider workflow for in-memory inbound receiving voice interpretation."""

from core import logger
from core.apis.schemas.responses.voice_responses import ReceivingVoiceIntent
from core.services.voice.deepgram_provider import DeepgramProvider
from core.services.voice.intent_parser import ReceivingIntentParser, ReceivingIntentProviderError

logging = logger(__name__)
MAX_AUDIO_BYTES = 2 * 1024 * 1024
SUPPORTED_AUDIO_CONTENT_TYPES = {
    "audio/webm",
    "audio/ogg",
    "audio/mp4",
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
}


class VoiceAudioValidationError(ValueError):
    """Raised when uploaded browser audio is empty, oversized, or unsupported."""


class ReceivingVoiceService:
    """Run speech-to-text and intent parsing without persisting audio or WMS data."""

    def __init__(self) -> None:
        """Initialize the two narrow provider responsibilities for one request."""
        logging.info("Executing ReceivingVoiceService.__init__")
        self.deepgram_provider = DeepgramProvider()
        self.intent_parser = ReceivingIntentParser()

    async def interpret(self, audio_bytes: bytes, content_type: str) -> tuple[str, ReceivingVoiceIntent]:
        """Turn validated in-memory browser audio into a typed receiving preview.

        Args:
            audio_bytes: Complete short recording held only for the current request.
            content_type: Audio MIME type provided by the browser upload.

        Returns:
            tuple[str, ReceivingVoiceIntent]: Transcript and strict parsed intent.

        Raises:
            VoiceAudioValidationError: If the audio upload is not suitable for processing.
            Exception: Provider-specific safe exceptions from transcription or parsing.
        """
        logging.info("Executing ReceivingVoiceService.interpret")
        normalized_content_type = content_type.split(";", 1)[0].strip().lower()
        if not audio_bytes:
            logging.warning("Voice interpretation rejected an empty audio upload")
            raise VoiceAudioValidationError("A short audio recording is required")
        if len(audio_bytes) > MAX_AUDIO_BYTES:
            logging.warning("Voice interpretation rejected an oversized audio upload")
            raise VoiceAudioValidationError("Audio recording is too large")
        if normalized_content_type not in SUPPORTED_AUDIO_CONTENT_TYPES:
            logging.warning("Voice interpretation rejected an unsupported audio MIME type")
            raise VoiceAudioValidationError("This audio format is not supported")

        transcript = await self.deepgram_provider.transcribe_audio(
            audio_bytes=audio_bytes,
            content_type=normalized_content_type,
        )
        try:
            intent = await self.intent_parser.parse_receiving_intent(transcript)
        except ReceivingIntentProviderError as error:
            raise ReceivingIntentProviderError(str(error), transcript=transcript) from error
        return transcript, intent
