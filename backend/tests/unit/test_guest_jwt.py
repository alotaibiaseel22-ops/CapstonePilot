import uuid
from datetime import UTC, datetime, timedelta

from jose import jwt

from app.core.config import settings
from app.infrastructure.security.jwt import (
    create_access_token,
    create_guest_access_token,
    decode_access_token,
    decode_guest_access_token,
)


def test_guest_token_create_and_decode_roundtrip():
    guest_id = uuid.uuid4()
    project_id = uuid.uuid4()
    token = create_guest_access_token(guest_id, project_id)

    payload = decode_guest_access_token(token)

    assert payload is not None
    assert payload.guest_id == guest_id
    assert payload.project_id == project_id


def test_guest_token_fails_as_a_user_token():
    token = create_guest_access_token(uuid.uuid4(), uuid.uuid4())
    assert decode_access_token(token) is None


def test_user_token_fails_as_a_guest_token():
    token = create_access_token(uuid.uuid4())
    assert decode_guest_access_token(token) is None


def test_user_token_still_decodes_normally():
    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    assert decode_access_token(token) == user_id


def test_pre_scope_claim_user_token_still_decodes():
    """Simulates a token issued before the "scope" claim existed - must
    still work so nobody already holding one gets silently logged out."""
    user_id = uuid.uuid4()
    payload = {"sub": str(user_id), "exp": datetime.now(UTC) + timedelta(minutes=5)}
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    assert decode_access_token(token) == user_id


def test_expired_guest_token_fails_decode():
    payload = {
        "sub": str(uuid.uuid4()),
        "project_id": str(uuid.uuid4()),
        "scope": "guest",
        "exp": datetime.now(UTC) - timedelta(minutes=1),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    assert decode_guest_access_token(token) is None


def test_invalid_guest_token_returns_none():
    assert decode_guest_access_token("not-a-valid-token") is None
