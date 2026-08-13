"""Server-side Deepgram speech-to-text provider for short receiving recordings."""

import os

import httpx
from dotenv import load_dotenv

from core import logger

logging = logger(__name__)
DEEPGRAM_LISTEN_URL = "https://api.deepgram.com/v1/listen"
DEEPGRAM_TIMEOUT_SECONDS = 20

load_dotenv()


class DeepgramConfigurationError(RuntimeError):
    """Raised when Deepgram cannot be used because its server configuration is missing."""


class DeepgramProviderError(RuntimeError):
    """Raised when Deepgram cannot safely return a usable transcription."""


class DeepgramProvider:
    """Transcribe short audio recordings without storing audio or WMS context."""

    async def transcribe_audio(self, audio_bytes: bytes, content_type: str) -> str:
        """Send one short audio payload to Deepgram and return its transcript.

        Args:
            audio_bytes: In-memory browser recording bytes.
            content_type: Browser-supplied audio MIME type after server validation.

        Returns:
            str: Trimmed speech transcript.

        Raises:
            DeepgramConfigurationError: If the server-side API key is absent.
            DeepgramProviderError: If the provider fails or produces no transcript.
        """
        logging.info("Executing DeepgramProvider.transcribe_audio")
        api_key = os.getenv("DEEPGRAM_API_KEY", "").strip()
        if not api_key:
            logging.warning("Deepgram provider requested while DEEPGRAM_API_KEY is not configured")
            raise DeepgramConfigurationError("Voice transcription is not configured")

        try:
            async with httpx.AsyncClient(timeout=DEEPGRAM_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    DEEPGRAM_LISTEN_URL,
                    params={"model": "nova-3", "smart_format": "true"},
                    headers={"Authorization": f"Token {api_key}", "Content-Type": content_type},
                    content=audio_bytes,
                )
            if response.status_code >= 400:
                logging.warning("Deepgram transcription request was rejected")
                raise DeepgramProviderError("Voice transcription provider is unavailable")

            payload = response.json()
            channels = payload.get("results", {}).get("channels", [])
            alternatives = channels[0].get("alternatives", []) if channels else []
            transcript = alternatives[0].get("transcript", "").strip() if alternatives else ""
            if not transcript:
                logging.warning("Deepgram returned an empty transcript")
                raise DeepgramProviderError("No speech was detected in that recording")
            return transcript
        except DeepgramProviderError:
            raise
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as error:
            logging.error(f"Deepgram transcription failed: {type(error).__name__}")
            raise DeepgramProviderError("Voice transcription provider is unavailable") from error
