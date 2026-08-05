from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(user_id: UUID) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire, "scope": "user"}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> UUID | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
    # A guest token must never authenticate as a real user. Tokens issued
    # before the "scope" claim existed have none at all and still decode
    # fine here (only "guest" is rejected, "user" is never required) - no
    # one holding an already-issued owner/collaborator token gets logged out
    # by this change.
    if payload.get("scope") == "guest":
        return None
    subject = payload.get("sub")
    return UUID(subject) if subject else None


@dataclass
class GuestTokenPayload:
    guest_id: UUID
    project_id: UUID


def create_guest_access_token(guest_id: UUID, project_id: UUID) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.GUEST_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(guest_id),
        "project_id": str(project_id),
        "scope": "guest",
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_guest_access_token(token: str) -> GuestTokenPayload | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
    # The inverse of decode_access_token's check - a real user token must
    # never authenticate as a guest, so this requires the scope claim
    # explicitly rather than merely tolerating its absence.
    if payload.get("scope") != "guest":
        return None
    try:
        return GuestTokenPayload(
            guest_id=UUID(payload["sub"]), project_id=UUID(payload["project_id"])
        )
    except (KeyError, ValueError, TypeError):
        return None
