"""Centralized, retrying, key-rotating Gemini client.

The single place that constructs the LLM object every Crew (documentation
analysis, planner, risk analyst) actually calls Gemini through - see
infrastructure/agents/llm.py, whose three factory functions all now delegate
to build_gemini_llm() here instead of each duplicating retry/rotation logic.

crewai.LLM(model="gemini/...") can't be subclassed for this: its __new__
inspects the model string and always returns a plain
crewai.llms.providers.gemini.completion.GeminiCompletion instance for any
"gemini/" model (confirmed by reading crewai's LLM.__new__/_get_native_provider
source - there's no provider-class injection point). RetryingGeminiCompletion
below subclasses GeminiCompletion directly instead and is constructed without
going through crewai.LLM at all; crewai.Agent's `llm` field accepts any
BaseLLM subclass (confirmed via Agent.model_fields["llm"]), so this is a drop-in
replacement from every Crew's point of view.
"""

import logging
import time
from typing import Any

from google.genai.errors import APIError
from pydantic import PrivateAttr

from app.core.config import settings
from app.infrastructure.agents.error_classification import describe_error

try:
    from crewai.llms.providers.gemini.completion import GeminiCompletion
except ImportError as exc:  # pragma: no cover - crewai is a hard dependency
    raise ImportError(
        "crewai's native Gemini provider is required for RetryingGeminiCompletion"
    ) from exc

logger = logging.getLogger(__name__)

# Exact schedule the reliability work asked for: up to 3 retries (4 attempts
# total including the first try), waiting 1s/2s/4s before each retry.
_BACKOFF_SECONDS: tuple[float, ...] = (1, 2, 4)
_MAX_RETRIES = len(_BACKOFF_SECONDS)
_TOTAL_ATTEMPTS = _MAX_RETRIES + 1

# HTTP statuses considered temporary and worth retrying on. Everything else
# (400 INVALID_ARGUMENT, a malformed-response ValueError from
# GeminiCompletion's own parsing, etc.) is never an APIError with one of
# these codes and so is never retried - see _is_retryable's docstring.
_RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})

# Narrower than _RETRYABLE_STATUS_CODES: a plain 500/502/504 is a transient
# server error unrelated to which key made the call, so those just retry on
# the same key. Only a 429/503 or explicit quota/rate-limit wording means
# *this key* is the problem, worth spending a rotation on.
_KEY_ROTATION_STATUS_CODES = frozenset({429, 503})
_KEY_ROTATION_TEXT_MARKERS = ("RESOURCE_EXHAUSTED", "quota", "rate limit")


class GeminiKeyPool:
    """Tracks which of settings.GEMINI_API_KEYS is currently in use for one
    LLM instance's lifetime, advancing to the next one when a key looks
    exhausted. Deliberately scoped per-LLM-instance (see
    RetryingGeminiCompletion.model_post_init below) rather than shared
    process-wide: every Crew builder constructs a fresh LLM per call, so
    there's no concurrent-request state to coordinate, and each request's
    rotation naturally starts clean."""

    def __init__(self, keys: list[str]) -> None:
        self._keys = keys
        self._index = 0

    @property
    def current_key(self) -> str:
        return self._keys[self._index] if self._keys else ""

    @property
    def current_index(self) -> int:
        """1-based, for logging only - the key itself is never logged."""
        return self._index + 1 if self._keys else 0

    def rotate(self) -> bool:
        """Advances to the next key if one exists. Returns whether it
        actually moved, so exhausting the whole pool doesn't wrap back
        around to an already-exhausted key within the same retry burst."""
        if self._index + 1 < len(self._keys):
            self._index += 1
            return True
        return False


def _matches_key_rotation_text(exc: APIError) -> bool:
    text = f"{exc.message or ''} {exc.status or ''}".lower()
    return any(marker.lower() in text for marker in _KEY_ROTATION_TEXT_MARKERS)


def _is_retryable(exc: APIError) -> bool:
    """Only ever evaluated on a google.genai.errors.APIError - a real failed
    HTTP response from Gemini. GeminiCompletion.call() raises parsing/
    validation failures (malformed JSON, a response_model mismatch) as a
    plain ValueError/Exception instead, which RetryingGeminiCompletion.call
    below never catches at all, so those propagate on the first attempt with
    no retry - exactly the "do not retry validation or parsing errors"
    requirement, for free, from the SDK's own exception shape."""
    return exc.code in _RETRYABLE_STATUS_CODES or _matches_key_rotation_text(exc)


def _should_rotate_key(exc: APIError) -> bool:
    return exc.code in _KEY_ROTATION_STATUS_CODES or _matches_key_rotation_text(exc)


def _reason_text(exc: APIError) -> str:
    return f"HTTP {exc.code}" if exc.code else describe_error(exc)


class RetryingGeminiCompletion(GeminiCompletion):
    """A GeminiCompletion that retries transient failures with exponential
    backoff and rotates to the next configured API key when a failure looks
    like that key is rate-limited/quota-exhausted, instead of the caller
    (any Crew's Agent) ever seeing a transient 429/500/502/503/504 at all.
    Everything else about GeminiCompletion (message formatting, structured
    output, streaming) is inherited unchanged - only call() is overridden."""

    _key_pool: GeminiKeyPool = PrivateAttr()

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        self._key_pool = GeminiKeyPool(settings.GEMINI_API_KEYS)

    def call(self, *args: Any, **kwargs: Any) -> str | Any:
        for attempt in range(1, _TOTAL_ATTEMPTS + 1):
            # Re-point at the pool's current key before every attempt (not
            # just after a rotation) and drop the cached client so
            # GeminiCompletion._get_sync_client() rebuilds it against
            # whichever key is current - the client is cached in a private
            # attr after first use, so merely reassigning api_key would
            # otherwise keep talking to Gemini with the old key.
            self.api_key = self._key_pool.current_key
            self._client = None
            try:
                return super().call(*args, **kwargs)
            except APIError as exc:
                if attempt > _MAX_RETRIES or not _is_retryable(exc):
                    if attempt > _MAX_RETRIES:
                        logger.error(
                            "Gemini call failed after %d attempt(s), giving up. "
                            "Model: %s | Reason: %s",
                            attempt,
                            self.model,
                            _reason_text(exc),
                        )
                    raise
                if _should_rotate_key(exc):
                    self._key_pool.rotate()
                delay = _BACKOFF_SECONDS[attempt - 1]
                logger.warning(
                    "Retry %d/%d\nModel: %s\nUsing API Key #%d\nReason: %s",
                    attempt,
                    _MAX_RETRIES,
                    self.model,
                    self._key_pool.current_index,
                    _reason_text(exc),
                )
                time.sleep(delay)
        raise RuntimeError("unreachable: the retry loop above always returns or raises")


def build_gemini_llm(
    *, max_output_tokens: int, temperature: float, thinking_config: Any
) -> RetryingGeminiCompletion:
    """The one place every Crew's LLM object gets built - see llm.py's three
    factory functions, each just a thin per-use-case wrapper around this."""
    keys = settings.GEMINI_API_KEYS
    return RetryingGeminiCompletion(
        model=settings.GEMINI_MODEL,
        provider="gemini",
        api_key=keys[0] if keys else "",
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        thinking_config=thinking_config,
    )
