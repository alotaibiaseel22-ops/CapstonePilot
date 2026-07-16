from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import User


class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: UUID) -> User | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    def create(self, user: User) -> User: ...

    @abstractmethod
    def list_all(self) -> list[User]: ...
