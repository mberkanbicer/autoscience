"""Email and in-app notification delivery."""

from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

import structlog

from app.config import get_settings

logger = structlog.get_logger()


def _send_smtp_sync(
    *,
    to_email: str,
    subject: str,
    body: str,
) -> None:
    settings = get_settings()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg.set_content(body)

    if settings.smtp_use_tls:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)


class NotificationService:
    """Optional SMTP notifications for collaboration events."""

    async def send_review_assignment(
        self,
        *,
        assignee_email: str,
        assignee_name: str,
        proposal_title: str,
        project_id: str,
        proposal_id: str,
        actor_name: str,
    ) -> bool:
        settings = get_settings()
        if not settings.notification_email_enabled or not settings.smtp_host:
            return False

        subject = f"[Autoscience] Review assigned: {proposal_title}"
        body = (
            f"Hi {assignee_name},\n\n"
            f"{actor_name} assigned you a review proposal:\n"
            f"  Title: {proposal_title}\n"
            f"  Project: {project_id}\n"
            f"  Proposal ID: {proposal_id}\n\n"
            f"Open your team page to respond.\n"
        )
        try:
            await asyncio.to_thread(
                _send_smtp_sync,
                to_email=assignee_email,
                subject=subject,
                body=body,
            )
            logger.info("review_assignment_email_sent", assignee=assignee_email)
            return True
        except smtplib.SMTPException as exc:
            logger.warning("review_assignment_email_smtp_error", error=str(exc))
            return False
        except (OSError, ConnectionError) as exc:
            logger.warning("review_assignment_email_network_error", error=str(exc))
            return False
        except Exception as exc:
            logger.warning("review_assignment_email_failed", error=str(exc))
            return False
