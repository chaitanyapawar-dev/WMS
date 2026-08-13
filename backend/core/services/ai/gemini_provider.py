"""Server-side Gemini provider setup for the Whitfield AI assistant."""

import os

from dotenv import load_dotenv

from core import logger

logging = logger(__name__)

load_dotenv()


class GeminiConfigurationError(RuntimeError):
    """Raised when the server-side Gemini provider is not configured."""


class GeminiProvider:
    """Create Gemini clients lazily so provider configuration cannot break WMS startup.

    The API key is read only at chat execution time and is never logged or returned.
    """

    def __init__(self) -> None:
        """Initialize the provider facade without constructing a remote client.

        Defers SDK loading and credential use until a chat request needs Gemini.
        """
        logging.info("Executing GeminiProvider.__init__")

    @property
    def model_name(self) -> str:
        """Return the configured Gemini model name.

        Returns:
            str: Gemini model identifier with a stable development default.
        """
        return os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    def get_client(self):
        """Create a configured Gemini SDK client for one AI request.

        Returns:
            genai.Client: Configured official Google Gen AI SDK client.

        Raises:
            GeminiConfigurationError: If the key is missing or the SDK is unavailable.
        """
        logging.info("Executing GeminiProvider.get_client")
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            logging.warning("Gemini provider requested while GEMINI_API_KEY is not configured")
            raise GeminiConfigurationError("Gemini AI is not configured")

        try:
            from google import genai
        except ImportError as error:
            logging.error("Google Gen AI SDK is not installed")
            raise GeminiConfigurationError("Gemini AI provider dependency is unavailable") from error

        return genai.Client(api_key=api_key)
