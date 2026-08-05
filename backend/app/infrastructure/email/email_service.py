import logging
import smtplib
from email.message import EmailMessage

from app.application.ports.email_service import EmailService
from app.core.config import settings

logger = logging.getLogger(__name__)


def _mask_identifier(value: str) -> str:
    """First char only, e.g. 'alice@x.com' -> 'a***@x.com' - enough to
    confirm in logs which account is configured without exposing it."""
    if not value:
        return "(not set)"
    if "@" not in value:
        return "***"
    local, _, domain = value.partition("@")
    return f"{local[0]}***@{domain}"


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

        logger.info(
            "[SMTP] Preparing invitation email | to=%s | from=%s | host=%s:%s | "
            "tls=%s | username=%s | password_set=%s",
            to_email,
            settings.SMTP_FROM_EMAIL,
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            settings.SMTP_USE_TLS,
            _mask_identifier(settings.SMTP_USERNAME),
            bool(settings.SMTP_PASSWORD),
        )
        try:
            logger.info("[SMTP] Connecting to %s:%s", settings.SMTP_HOST, settings.SMTP_PORT)
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
                if settings.SMTP_USE_TLS:
                    logger.info("[SMTP] Starting TLS (STARTTLS)")
                    smtp.starttls()
                else:
                    logger.warning(
                        "[SMTP] SMTP_USE_TLS is False - sending without TLS on %s:%s",
                        settings.SMTP_HOST,
                        settings.SMTP_PORT,
                    )
                if settings.SMTP_USERNAME:
                    logger.info(
                        "[SMTP] Authenticating as %s", _mask_identifier(settings.SMTP_USERNAME)
                    )
                    smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                else:
                    logger.warning(
                        "[SMTP] SMTP_USERNAME is not set - skipping authentication "
                        "(will fail unless %s:%s accepts anonymous mail)",
                        settings.SMTP_HOST,
                        settings.SMTP_PORT,
                    )
                logger.info("[SMTP] Sending message to %s", to_email)
                smtp.send_message(message)
            logger.info("[SMTP] Invitation email sent successfully to %s", to_email)
        except Exception:
            logger.exception(
                "[SMTP] Failed to send invitation email to %s via %s:%s "
                "(from=%s, tls=%s, username=%s)",
                to_email,
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                settings.SMTP_FROM_EMAIL,
                settings.SMTP_USE_TLS,
                _mask_identifier(settings.SMTP_USERNAME),
            )
            raise


def build_email_service() -> EmailService:
    if settings.SMTP_HOST:
        logger.info(
            "SMTP is enabled | host=%s:%s | tls=%s | username=%s | password_set=%s | from=%s",
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            settings.SMTP_USE_TLS,
            _mask_identifier(settings.SMTP_USERNAME),
            bool(settings.SMTP_PASSWORD),
            settings.SMTP_FROM_EMAIL,
        )
        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            logger.warning(
                "SMTP_HOST is set but SMTP_USERNAME or SMTP_PASSWORD is missing - "
                "authentication will likely fail (username_set=%s, password_set=%s)",
                bool(settings.SMTP_USERNAME),
                bool(settings.SMTP_PASSWORD),
            )
        return SmtpEmailService()

    logger.warning("SMTP is disabled. Falling back to console logging.")
    return ConsoleEmailService()
