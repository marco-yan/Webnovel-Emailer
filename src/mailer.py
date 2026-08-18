from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def build_message(sender: str, recipient: str, subject: str, body: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)
    return msg


def _credentials() -> tuple[str, str]:
    sender = (os.environ.get("GMAIL_ADDRESS") or "").strip()
    password = (os.environ.get("GMAIL_APP_PASSWORD") or "").strip()
    if not sender or not password:
        raise RuntimeError("GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set")
    return sender, password


def send_gmail(recipients: list[str], subject: str, body: str) -> None:
    send_gmail_batches(recipients, [(subject, body)])


def send_gmail_batches(recipients: list[str], messages: list[tuple[str, str]]) -> None:
    """Send many reading batches through one SMTP session.

    Each recipient receives an individual message so recipient addresses are not exposed.
    """
    if not recipients:
        raise RuntimeError("At least one recipient is required")
    if not messages:
        raise RuntimeError("At least one message is required")

    sender, password = _credentials()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(sender, password)
        for subject, body in messages:
            for recipient in recipients:
                smtp.send_message(build_message(sender, recipient, subject, body))
