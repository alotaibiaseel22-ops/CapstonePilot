from abc import ABC, abstractmethod


class EmailService(ABC):
    @abstractmethod
    def send_invitation_email(
        self, *, to_email: str, project_name: str, inviter_name: str, invite_url: str
    ) -> None: ...
