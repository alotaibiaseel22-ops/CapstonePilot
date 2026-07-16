import uuid

from app.infrastructure.security.jwt import create_access_token, decode_access_token


def test_create_and_decode_roundtrip():
    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    assert decode_access_token(token) == user_id


def test_invalid_token_returns_none():
    assert decode_access_token("not-a-valid-token") is None
