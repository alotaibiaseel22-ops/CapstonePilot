from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import Invitation


class InvitationRepository(ABC):
    @abstractmethod
    def create(self, invitation: Invitation) -> Invitation: ...

    @abstractmethod
    def get_by_id(self, invitation_id: UUID) -> Invitation | None: ...

    @abstractmethod
    def get_by_token(self, token: str) -> Invitation | None: ...

    @abstractmethod
    def list_by_project(self, project_id: UUID) -> list[Invitation]: ...

    @abstractmethod
    def get_active_link_invitation(self, project_id: UUID) -> Invitation | None:
        """The one reusable, not-yet-revoked link-type invitation (email is None), if any."""
        ...

    @abstractmethod
    def list_pending_by_email(self, email: str) -> list[Invitation]: ...

    @abstractmethod
    def update(self, invitation: Invitation) -> Invitation: ...
