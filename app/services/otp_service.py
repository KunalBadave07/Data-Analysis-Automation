from __future__ import annotations

import hashlib
import hmac
import random
import smtplib
from email.message import EmailMessage

from flask import current_app


def generate_otp_code() -> str:
    return f"{random.SystemRandom().randint(0, 999999):06d}"


def hash_otp(code: str) -> str:
    secret = current_app.config["SECRET_KEY"].encode("utf-8")
    return hmac.new(secret, code.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_otp(code: str, expected_hash: str) -> bool:
    candidate = hash_otp(code)
    return hmac.compare_digest(candidate, expected_hash)


def send_otp_email(email: str, code: str) -> tuple[bool, str]:
    smtp_host = current_app.config["SMTP_HOST"]
    smtp_username = current_app.config["SMTP_USERNAME"]
    smtp_password = current_app.config["SMTP_PASSWORD"]
    smtp_sender = current_app.config["SMTP_SENDER"]
    smtp_port = current_app.config["SMTP_PORT"]

    if not smtp_host or not smtp_username or not smtp_password:
        return (
            False,
            "SMTP is not configured. Please set SMTP credentials and try again.",
        )

    message = EmailMessage()
    message["Subject"] = "Your Data Automation OTP Verification Code"
    message["From"] = smtp_sender
    message["To"] = email
    message.set_content(
        f"Your verification code is {code}. "
        f"It expires in {current_app.config['OTP_EXPIRY_MINUTES']} minutes."
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
    except smtplib.SMTPAuthenticationError:
        return (
            False,
            "SMTP authentication failed. Please check SMTP username and app password.",
        )
    except (smtplib.SMTPException, OSError, TimeoutError):
        return (
            False,
            "Unable to send OTP email right now. Please try again shortly.",
        )

    return True, "OTP email sent successfully."
