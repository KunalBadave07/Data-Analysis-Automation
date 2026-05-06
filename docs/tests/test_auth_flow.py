from pathlib import Path
from uuid import uuid4

from app import create_app


def _build_test_app(monkeypatch):
    db_dir = Path("instance/test_dbs")
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / f"auth_test_{uuid4().hex}.db"

    app = create_app(
        {
            "TESTING": True,
            "AUTH_DB_PATH": str(db_path),
            "OTP_RESEND_COOLDOWN_SECONDS": 0,
        }
    )
    monkeypatch.setattr("app.routes.auth.generate_otp_code", lambda: "123456")
    monkeypatch.setattr(
        "app.routes.auth.send_otp_email",
        lambda email, code: (True, "OTP email sent successfully."),
    )
    return app, db_path


def test_register_login_verify_flow(monkeypatch):
    app, _ = _build_test_app(monkeypatch)
    client = app.test_client()

    register_response = client.post(
        "/auth/register",
        data={"email": "phase3@example.com", "password": "StrongPass123"},
        follow_redirects=True,
    )
    assert register_response.status_code == 200
    assert b"Verify your email" in register_response.data

    login_before_verify = client.post(
        "/auth/login",
        data={"email": "phase3@example.com", "password": "StrongPass123"},
        follow_redirects=True,
    )
    assert b"Please verify your email before login." in login_before_verify.data

    verify_response = client.post(
        "/auth/verify",
        data={"email": "phase3@example.com", "otp": "123456"},
        follow_redirects=True,
    )
    assert b"Email verified successfully. You are now logged in." in verify_response.data


def test_invalid_otp_rejected(monkeypatch):
    app, _ = _build_test_app(monkeypatch)
    client = app.test_client()

    client.post(
        "/auth/register",
        data={"email": "wrongotp@example.com", "password": "StrongPass123"},
        follow_redirects=True,
    )
    verify_response = client.post(
        "/auth/verify",
        data={"email": "wrongotp@example.com", "otp": "000000"},
        follow_redirects=True,
    )
    assert b"Invalid OTP code." in verify_response.data


def test_forgot_password_reset_flow(monkeypatch):
    app, _ = _build_test_app(monkeypatch)
    client = app.test_client()

    client.post(
        "/auth/register",
        data={"email": "reset@example.com", "password": "OldPass123"},
        follow_redirects=True,
    )
    client.post(
        "/auth/verify",
        data={"email": "reset@example.com", "otp": "123456"},
        follow_redirects=True,
    )
    client.post("/auth/logout", follow_redirects=True)

    forgot_response = client.post(
        "/auth/forgot-password",
        data={"email": "reset@example.com"},
        follow_redirects=True,
    )
    assert b"Password reset OTP generated." in forgot_response.data

    reset_response = client.post(
        "/auth/reset-password",
        data={
            "email": "reset@example.com",
            "otp": "123456",
            "new_password": "NewPass123",
            "confirm_password": "NewPass123",
        },
        follow_redirects=True,
    )
    assert b"Password reset successful. You are now logged in." in reset_response.data
