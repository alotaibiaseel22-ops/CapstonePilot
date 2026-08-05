import logging
import secrets
import uuid
from datetime import UTC, datetime

from app.application.ports.user_repository import UserRepository
from app.core.config import settings
from app.domain.entities import User
from app.domain.enums import Language, UserRole
from app.infrastructure.security.password import hash_password, verify_password

logger = logging.getLogger(__name__)


def _mask_database_url(url: str) -> str:
    """user:password@host/db -> user:***@host/db - confirms which database
    a request actually hit without ever logging the real credential."""
    if "://" not in url or "@" not in url:
        return url
    scheme, rest = url.split("://", 1)
    creds, host_part = rest.rsplit("@", 1)
    user = creds.split(":", 1)[0]
    return f"{scheme}://{user}:***@{host_part}"


class EmailAlreadyRegisteredError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class IncorrectPasswordError(Exception):
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

        now = datetime.now(UTC)
        user = User(
            id=uuid.uuid4(),
            name=name,
            email=email,
            role=role,
            password_hash=hash_password(password),
            preferred_language=preferred_language,
            created_at=now,
            # A brand-new user starts "caught up" - nothing that happened
            # before they signed up should count as an unread notification.
            notifications_last_seen_at=now,
        )
        return self._users.create(user)

    def provision_invited_user(self, name: str, email: str) -> User:
        """Creates a Collaborator account for someone onboarding via the
        name-only invitation flow (invitations.py's /onboard endpoint) -
        mirrors register() exactly except the password is never supplied by
        the caller: a random, unguessable one is generated and hashed here,
        so there is no path for the frontend to influence it. The email
        comes from the invitation token on the server, never the request
        body - see get_email_invitation_or_raise in invitation_service.py."""
        if self._users.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError(f"{email} is already registered")

        now = datetime.now(UTC)
        user = User(
            id=uuid.uuid4(),
            name=name,
            email=email,
            role=UserRole.COLLABORATOR,
            password_hash=hash_password(secrets.token_urlsafe(32)),
            preferred_language=Language.EN,
            created_at=now,
            notifications_last_seen_at=now,
        )
        return self._users.create(user)

    def authenticate(self, email: str, password: str) -> User | None:
        # --- TEMPORARY DEBUG LOGGING - remove once the production 401 issue
        # is resolved (search "[LOGIN DEBUG]"). Never logs the plaintext
        # password or the full password hash/DATABASE_URL.
        logger.warning("[LOGIN DEBUG] Email received: %r", email)
        logger.warning(
            "[LOGIN DEBUG] Database URL (masked): %s", _mask_database_url(settings.DATABASE_URL)
        )

        user = self._users.get_by_email(email)
        logger.warning("[LOGIN DEBUG] User found: %s", user is not None)

        if user is None:
            logger.warning(
                "[LOGIN DEBUG] Reason for failure: no user row matched this exact email "
                "string (get_by_email does a case-sensitive '=' comparison)"
            )
            return None

        logger.warning(
            "[LOGIN DEBUG] Stored hash: %s...(%d chars total, masked)",
            user.password_hash[:10],
            len(user.password_hash),
        )

        verified = verify_password(password, user.password_hash)
        logger.warning("[LOGIN DEBUG] Password verification result: %s", verified)

        if not verified:
            logger.warning(
                "[LOGIN DEBUG] Reason for failure: password did not match the stored hash "
                "for user_id=%s",
                user.id,
            )
            return None
        # --- END TEMPORARY DEBUG LOGGING

        return user

    def update_profile(
        self,
        user_id: uuid.UUID,
        name: str | None = None,
        preferred_language: Language | None = None,
    ) -> User:
        user = self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")
        if name is not None:
            user.name = name
        if preferred_language is not None:
            user.preferred_language = preferred_language
        return self._users.update(user)

    def change_password(
        self, user_id: uuid.UUID, current_password: str, new_password: str
    ) -> User:
        user = self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")
        if not verify_password(current_password, user.password_hash):
            raise IncorrectPasswordError("Current password is incorrect")
        user.password_hash = hash_password(new_password)
        return self._users.update(user)
