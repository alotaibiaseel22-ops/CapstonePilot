from uuid import UUID

from sqlalchemy.orm import Session

from app.application.ports.user_repository import UserRepository
from app.domain.entities import User
from app.domain.enums import Language, UserRole
from app.infrastructure.db.models import UserModel


def _to_entity(model: UserModel) -> User:
    return User(
        id=model.id,
        name=model.name,
        email=model.email,
        role=UserRole(model.role),
        password_hash=model.password_hash,
        preferred_language=Language(model.preferred_language),
        created_at=model.created_at,
        notifications_last_seen_at=model.notifications_last_seen_at,
    )


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, user_id: UUID) -> User | None:
        model = self._session.get(UserModel, user_id)
        return _to_entity(model) if model else None

    def get_by_email(self, email: str) -> User | None:
        model = self._session.query(UserModel).filter(UserModel.email == email).first()
        return _to_entity(model) if model else None

    def create(self, user: User) -> User:
        model = UserModel(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role.value,
            password_hash=user.password_hash,
            preferred_language=user.preferred_language.value,
            created_at=user.created_at,
            notifications_last_seen_at=user.notifications_last_seen_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def list_all(self) -> list[User]:
        return [_to_entity(model) for model in self._session.query(UserModel).all()]

    def update(self, user: User) -> User:
        model = self._session.get(UserModel, user.id)
        if model is None:
            raise ValueError(f"User {user.id} not found")
        model.name = user.name
        model.password_hash = user.password_hash
        model.preferred_language = user.preferred_language.value
        model.notifications_last_seen_at = user.notifications_last_seen_at
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)
