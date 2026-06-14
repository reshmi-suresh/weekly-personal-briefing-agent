"""Send weekly digest HTML via Gmail SMTP."""

from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger("weekly-briefing-agent")


def digest_subject(date: str | None = None) -> str:
    if date:
        return f"Weekly digest — {date}"
    from agent.prompt import email_subject

    return email_subject()


def send_email_smtp(html: str, recipient: str, subject: str) -> None:
    """Send HTML digest via Gmail SMTP using an App Password."""
    gmail_user = os.getenv("GMAIL_USER")
    app_password = os.getenv("GMAIL_APP_PASSWORD")
    if not gmail_user or not app_password:
        raise ValueError(
            "GMAIL_USER and GMAIL_APP_PASSWORD must be set in the environment"
        )

    log.info("Sending digest to %s via Gmail SMTP...", recipient)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = recipient
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, app_password.replace(" ", ""))
        server.sendmail(gmail_user, [recipient], msg.as_string())

    log.info("Email sent successfully.")
