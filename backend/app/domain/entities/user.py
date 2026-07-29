from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.enums import Language, UserRole


@dataclass
class User:
    id: UUID
    name: str
    email: str
    role: UserRole
    password_hash: str
    preferred_language: Language
    created_at: datetime
    notifications_last_seen_at: datetime | None
