import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from app.application.ports.project_member_repository import ProjectMemberRepository
from app.application.ports.user_repository import UserRepository
from app.domain.entities import ProjectMember, User


class AlreadyAMemberError(Exception):
    pass


@dataclass
class ProjectMemberInfo:
    user_id: uuid.UUID
    name: str
    email: str
    role: str
    added_at: datetime


class ProjectMemberService:
    """Manages who is actually on a project. Membership is only ever created
    via InvitationService.accept_invitation - there is no direct "add by
    email" path anymore, since a Collaborator must consent by accepting an
    invitation rather than being added unilaterally."""

    def __init__(
        self, project_member_repository: ProjectMemberRepository, user_repository: UserRepository
    ):
        self._members = project_member_repository
        self._users = user_repository

    def add_member(self, project_id: uuid.UUID, user_id: uuid.UUID) -> ProjectMemberInfo:
        if self._members.exists(project_id, user_id):
            raise AlreadyAMemberError("This user is already a member of the project")

        member = ProjectMember(
            id=uuid.uuid4(),
            project_id=project_id,
            user_id=user_id,
            added_at=datetime.now(UTC),
        )
        created = self._members.add(member)
        user = self._users.get_by_id(user_id)
        return self._to_info(created, user)

    def list_members(self, project_id: uuid.UUID) -> list[ProjectMemberInfo]:
        members = self._members.list_by_project(project_id)
        infos = []
        for member in members:
            user = self._users.get_by_id(member.user_id)
            if user is not None:
                infos.append(self._to_info(member, user))
        return infos

    def remove_member(self, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
        self._members.remove(project_id, user_id)

    @staticmethod
    def _to_info(member: ProjectMember, user: User) -> ProjectMemberInfo:
        return ProjectMemberInfo(
            user_id=user.id,
            name=user.name,
            email=user.email,
            role=user.role.value,
            added_at=member.added_at,
        )
