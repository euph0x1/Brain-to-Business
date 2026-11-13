"""Thin wrapper around the Gemini API: structured output, retries, friendly errors."""
import os
import time
from functools import lru_cache

from pydantic import ValidationError

from . import config

RETRYABLE_CODES = {429, 500, 503, 504}


class LLMError(RuntimeError):
    """Raised for any model/API failure with a human-readable message."""


@lru_cache(maxsize=1)
def _client():
    from google import genai

    key = os.getenv("GEMINI_API_KEY")
    if not key or key == "paste_your_key_here":
        raise LLMError(
            "GEMINI_API_KEY is missing. Copy .env.example to .env and add a free key "
            "from https://aistudio.google.com"
        )
    return genai.Client(api_key=key)


def ask(system: str, user: str, schema):
    """Call the model and return a validated instance of `schema`."""
    from google.genai import errors, types

    client = _client()
    last_err = None
    for attempt in range(config.MAX_RETRIES):
        try:
            resp = client.models.generate_content(
                model=config.MODEL,
                contents=user,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.7,
                ),
            )
            if isinstance(resp.parsed, schema):
                return resp.parsed
            return schema.model_validate_json(resp.text)
        except errors.APIError as e:
            code = getattr(e, "code", None)
            last_err = e
            if code in RETRYABLE_CODES and attempt < config.MAX_RETRIES - 1:
                wait = min(60, 10 * (2 ** attempt))  # 10s, 20s, 40s
                print(f"  ...API busy or rate-limited ({code}); retrying in {wait}s")
                time.sleep(wait)
                continue
            hint = ""
            if code == 404:
                hint = " Check MODEL in your .env against the model list in AI Studio."
            elif code in (400, 401, 403):
                hint = " Check that your GEMINI_API_KEY is valid."
            raise LLMError(f"Gemini API error {code}: {getattr(e, 'message', e)}.{hint}") from e
        except (ValidationError, ValueError) as e:
            last_err = e  # malformed JSON from the model: just try again
            if attempt < config.MAX_RETRIES - 1:
                continue
        except Exception as e:  # network down, DNS, timeout...
            raise LLMError(
                f"Could not reach the Gemini API ({type(e).__name__}). Check your internet connection."
            ) from e
    raise LLMError(f"Model returned unusable output after {config.MAX_RETRIES} tries: {last_err}")
