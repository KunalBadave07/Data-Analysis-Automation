import smtplib
from pathlib import Path
from uuid import uuid4

from app import create_app
from app.services.otp_service import send_otp_email


class _AuthFailureSMTP:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def starttls(self):
        return None

    def login(self, username, password):
        raise smtplib.SMTPAuthenticationError(535, b"Bad credentials")

    def send_message(self, message):
        return None


def test_send_otp_email_handles_smtp_auth_failure(monkeypatch):
    db_dir = Path("instance/test_dbs")
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / f"otp_auth_fail_{uuid4().hex}.db"

    app = create_app(
        {
            "TESTING": True,
            "AUTH_DB_PATH": str(db_path),
            "SMTP_HOST": "smtp.gmail.com",
            "SMTP_PORT": 587,
            "SMTP_USERNAME": "wrong-user",
            "SMTP_PASSWORD": "wrong-password",
            "SMTP_SENDER": "no-reply@example.com",
        }
    )
    monkeypatch.setattr("app.services.otp_service.smtplib.SMTP", _AuthFailureSMTP)

    with app.app_context():
        delivered, msg = send_otp_email("user@example.com", "123456")

    assert delivered is False
    assert "authentication failed" in msg.lower()


def test_send_otp_email_exposes_dev_otp_when_smtp_not_configured(monkeypatch):
    db_dir = Path("instance/test_dbs")
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / f"otp_dev_fallback_{uuid4().hex}.db"

    app = create_app(
        {
            "TESTING": True,
            "AUTH_DB_PATH": str(db_path),
            "SMTP_HOST": "",
            "SMTP_PORT": 587,
            "SMTP_USERNAME": "",
            "SMTP_PASSWORD": "",
            "SMTP_SENDER": "no-reply@example.com",
        }
    )

    with app.app_context():
        delivered, msg = send_otp_email("user@example.com", "654321")

    assert delivered is False
    assert "smtp is not configured" in msg.lower()
