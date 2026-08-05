import logging

import pytest
from crewai.llms.providers.gemini.completion import GeminiCompletion
from google.genai.errors import APIError

from app.infrastructure.agents.gemini_client import RetryingGeminiCompletion


def _api_error(code: int, message: str = "boom") -> APIError:
    return APIError(code, {"error": {"code": code, "message": message, "status": "ERROR"}})


@pytest.fixture(autouse=True)
def no_real_sleep(monkeypatch):
    """Every test below exercises the real backoff branches - patch time.sleep
    so the suite doesn't actually wait 1s/2s/4s per retrying test."""
    monkeypatch.setattr("app.infrastructure.agents.gemini_client.time.sleep", lambda _: None)


@pytest.fixture
def llm(monkeypatch):
    """A RetryingGeminiCompletion configured with 3 fake keys, independent of
    real Settings/.env - construction only builds an SDK client wrapper, no
    network call happens until .call() (which every test below mocks)."""
    monkeypatch.setattr(
        "app.infrastructure.agents.gemini_client.settings.GEMINI_API_KEY_1", "key-1"
    )
    monkeypatch.setattr(
        "app.infrastructure.agents.gemini_client.settings.GEMINI_API_KEY_2", "key-2"
    )
    monkeypatch.setattr(
        "app.infrastructure.agents.gemini_client.settings.GEMINI_API_KEY_3", "key-3"
    )
    return RetryingGeminiCompletion(
        model="gemini-flash-lite-latest",
        provider="gemini",
        api_key="key-1",
        max_output_tokens=100,
        temperature=0.1,
    )


def test_succeeds_on_first_attempt_without_retry(llm, monkeypatch):
    calls = []
    monkeypatch.setattr(GeminiCompletion, "call", lambda self, *a, **k: calls.append(1) or "ok")

    result = llm.call("hi")

    assert result == "ok"
    assert len(calls) == 1
    assert llm._key_pool.current_index == 1


def test_retries_transient_500_on_same_key_no_rotation(llm, monkeypatch):
    attempts = []

    def fake_call(self, *a, **k):
        attempts.append(1)
        if len(attempts) < 3:
            raise _api_error(500)
        return "ok"

    monkeypatch.setattr(GeminiCompletion, "call", fake_call)

    result = llm.call("hi")

    assert result == "ok"
    assert len(attempts) == 3
    # A plain 500 is a server-side transient error, not a per-key problem -
    # must not have rotated off key #1.
    assert llm._key_pool.current_index == 1


def test_rotates_key_on_429_then_succeeds(llm, monkeypatch):
    attempts = []

    def fake_call(self, *a, **k):
        attempts.append(self.api_key)
        if len(attempts) == 1:
            raise _api_error(429, "quota exceeded")
        return "ok"

    monkeypatch.setattr(GeminiCompletion, "call", fake_call)

    result = llm.call("hi")

    assert result == "ok"
    assert attempts == ["key-1", "key-2"]
    assert llm._key_pool.current_index == 2


def test_rotates_through_all_keys_on_repeated_503(llm, monkeypatch):
    attempts = []

    def fake_call(self, *a, **k):
        attempts.append(self.api_key)
        raise _api_error(503, "service unavailable")

    monkeypatch.setattr(GeminiCompletion, "call", fake_call)

    with pytest.raises(APIError):
        llm.call("hi")

    # 4 total attempts (1 initial + 3 retries), rotating key each time but
    # never advancing past the last configured key once exhausted.
    assert attempts == ["key-1", "key-2", "key-3", "key-3"]


def test_single_key_never_crashes_on_repeated_rotation_trigger(monkeypatch):
    prefix = "app.infrastructure.agents.gemini_client.settings"
    monkeypatch.setattr(f"{prefix}.GEMINI_API_KEY_1", "")
    monkeypatch.setattr(f"{prefix}.GEMINI_API_KEY_2", "")
    monkeypatch.setattr(f"{prefix}.GEMINI_API_KEY_3", "")
    monkeypatch.setattr(f"{prefix}.GEMINI_API_KEY", "only-key")
    llm = RetryingGeminiCompletion(
        model="gemini-flash-lite-latest",
        provider="gemini",
        api_key="only-key",
        max_output_tokens=100,
        temperature=0.1,
    )

    def fake_call(self, *a, **k):
        raise _api_error(429)

    monkeypatch.setattr(GeminiCompletion, "call", fake_call)

    with pytest.raises(APIError):
        llm.call("hi")

    assert llm._key_pool.current_index == 1


def test_non_retryable_error_propagates_immediately(llm, monkeypatch):
    calls = []

    def fake_call(self, *a, **k):
        calls.append(1)
        raise ValueError("malformed response, not an API error")

    monkeypatch.setattr(GeminiCompletion, "call", fake_call)

    with pytest.raises(ValueError):
        llm.call("hi")

    assert len(calls) == 1


def test_400_is_not_retried(llm, monkeypatch):
    calls = []

    def fake_call(self, *a, **k):
        calls.append(1)
        raise _api_error(400, "invalid argument")

    monkeypatch.setattr(GeminiCompletion, "call", fake_call)

    with pytest.raises(APIError):
        llm.call("hi")

    assert len(calls) == 1


def test_retry_log_never_contains_the_raw_key(llm, monkeypatch, caplog):
    attempts = []

    def fake_call(self, *a, **k):
        attempts.append(1)
        if len(attempts) == 1:
            raise _api_error(503, "service unavailable")
        return "ok"

    monkeypatch.setattr(GeminiCompletion, "call", fake_call)

    with caplog.at_level(logging.WARNING):
        llm.call("hi")

    log_text = caplog.text
    assert "Retry 1/3" in log_text
    assert "Model: gemini-flash-lite-latest" in log_text
    assert "Using API Key #2" in log_text
    assert "Reason: HTTP 503" in log_text
    assert "key-1" not in log_text
    assert "key-2" not in log_text
