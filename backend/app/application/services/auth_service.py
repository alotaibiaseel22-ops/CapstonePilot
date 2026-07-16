import uuid
from datetime import UTC, datetime

from app.application.ports.user_repository import UserRepository
from app.domain.entities import User
from app.domain.enums import Language, UserRole
from app.infrastructure.security.password import hash_password, verify_password


class EmailAlreadyRegisteredError(Exception):
    pass


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self._users = user_repository

    def register(
        self,
        name: str,
        email: str,
        password: str,
        role: UserRole = UserRole.COLLABORATOR,
        preferred_language: Language = Language.EN,
    ) -> User:
        if self._users.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError(f"{email} is already registered")

        user = User(
            id=uuid.uuid4(),
            name=name,
            email=email,
            role=role,
            password_hash=hash_password(password),
            preferred_language=preferred_language,
            created_at=datetime.now(UTC),
        )
        return self._users.create(user)

    def authenticate(self, email: str, password: str) -> User | None:
        user = self._users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            return None
        return user
