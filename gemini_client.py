import logging
import time

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)
MAX_RETRIES = 2
RETRY_BACKOFF_SECONDS = 0.5


class GeminiError(RuntimeError):
    """Raised when Gemini cannot provide a usable response."""


class GeminiQuotaError(GeminiError):
    """Raised when a Gemini model has exhausted its available quota."""


def generate_text(prompt: str, model: str) -> str:
    if not settings.gemini_api_key:
        raise GeminiError("Gemini is not configured. Add GEMINI_API_KEY to your .env file.")
    for attempt in range(MAX_RETRIES + 1):
        try:
            client = genai.Client(api_key=settings.gemini_api_key)
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=settings.gemini_temperature,
                    max_output_tokens=settings.gemini_max_output_tokens,
                ),
            )
            break
        except Exception as exc:
            response = getattr(exc, "response", None)
            status_code = (
                getattr(exc, "status_code", None)
                or getattr(exc, "code", None)
                or getattr(response, "status_code", None)
            )
            status_code = getattr(status_code, "value", status_code)
            if isinstance(status_code, str) and status_code.isdecimal():
                status_code = int(status_code)
            if status_code == 503 and attempt < MAX_RETRIES:
                delay = RETRY_BACKOFF_SECONDS * (2**attempt)
                logger.warning(
                    "Gemini request for model %s failed with status 503; retrying in %.1f seconds",
                    model,
                    delay,
                )
                time.sleep(delay)
                continue
            logger.warning(
                "Gemini request failed for model %s (%s; status=%s)",
                model,
                type(exc).__name__,
                status_code,
                exc_info=True,
            )
            if status_code == 429:
                message = (
                    "Gemini quota is exhausted for this API project. Check AI Studio rate limits "
                    "and billing, or retry after the quota resets."
                )
                raise GeminiQuotaError(message) from exc
            elif status_code in {401, 403}:
                message = "Gemini rejected this API key or the project does not have access. Check the key and project settings."
            elif status_code == 404:
                message = "The configured Gemini model is unavailable. Check GEMINI_WORKOUT_MODEL or GEMINI_TIP_MODEL."
            elif status_code == 503:
                diagnostic = f"{type(exc).__name__}, status {status_code}"
                message = (
                    f"Gemini is temporarily unavailable ({diagnostic}). "
                    "Please try again shortly; check the server log if this continues."
                )
            else:
                diagnostic = type(exc).__name__
                if status_code is not None:
                    diagnostic += f", status {status_code}"
                message = (
                    f"Gemini could not complete the request ({diagnostic}). "
                    "Check the API connection and model settings; see the server log for details."
                )
            raise GeminiError(message) from exc
    text = getattr(response, "text", None)
    if not isinstance(text, str) or not text.strip():
        raise GeminiError("Gemini returned an empty response. Please try again.")
    return text.strip()