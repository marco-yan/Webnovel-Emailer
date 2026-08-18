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


def send_gmail(recipients: list[str], subject: str, body: str) -> None:
    sender = os.environ.get("GMAIL_ADDRESS")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    if not sender or not password:
        raise RuntimeError("GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set")
    if not recipients:
        raise RuntimeError("At least one recipient is required")

    # Send one message per recipient so addresses are never exposed to one another.
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(sender, password)
        for recipient in recipients:
            smtp.send_message(build_message(sender, recipient, subject, body))
