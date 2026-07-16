import smtplib
from email.message import EmailMessage

from app.application.ports.email_service import EmailService
from app.core.config import settings


class ConsoleEmailService(EmailService):
    """Fallback used when no SMTP credentials are configured. Prints the
    email instead of sending it so invitation flows keep working in local
    dev. Uses print() rather than logging so it's visible unconditionally,
    regardless of whatever log level/handlers happen to be configured."""

    def send_invitation_email(
        self, *, to_email: str, project_name: str, inviter_name: str, invite_url: str
    ) -> None:
        print(
            f"[email:console] To={to_email} "
            f'Subject="You\'ve been invited to collaborate on {project_name}"\n'
            f'{inviter_name} has invited you to join "{project_name}" on CapstonePilot.\n'
            f"Accept: {invite_url}",
            flush=True,
        )


class SmtpEmailService(EmailService):
    """Sends real email over SMTP using whatever provider's credentials are
    configured via SMTP_* settings (e.g. SendGrid, Postmark, Gmail SMTP)."""

    def send_invitation_email(
        self, *, to_email: str, project_name: str, inviter_name: str, invite_url: str
    ) -> None:
        message = EmailMessage()
        message["Subject"] = f"You've been invited to collaborate on {project_name}"
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = to_email
        message.set_content(
            f'{inviter_name} has invited you to collaborate on "{project_name}" on '
            "CapstonePilot.\n\n"
            f"Accept the invitation: {invite_url}\n\n"
            "If you weren't expecting this, you can safely ignore this email."
        )
        message.add_alternative(
            f"""<div style="font-family:sans-serif;max-width:480px">
<p><strong>{inviter_name}</strong> has invited you to collaborate on
<strong>{project_name}</strong> on CapstonePilot.</p>
<p>
  <a href="{invite_url}"
     style="display:inline-block;padding:10px 20px;background:#2563eb;color:#fff;
            border-radius:8px;text-decoration:none">Accept Invitation</a>
</p>
<p style="color:#6b7280;font-size:13px">
  If you weren't expecting this, you can safely ignore this email.
</p>
</div>""",
            subtype="html",
        )
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            if settings.SMTP_USERNAME:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)


def build_email_service() -> EmailService:
    if settings.SMTP_HOST:
        return SmtpEmailService()
    return ConsoleEmailService()
