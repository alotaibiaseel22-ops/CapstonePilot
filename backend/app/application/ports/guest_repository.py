from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import Guest


class GuestRepository(ABC):
    @abstractmethod
    def create(self, guest: Guest) -> Guest: ...

    @abstractmethod
    def get_by_id(self, guest_id: UUID) -> Guest | None: ...
