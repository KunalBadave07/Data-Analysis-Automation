from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from flask import current_app
from flask_login import UserMixin


@dataclass
class AuthUser(UserMixin):
    id: str
    email: str
    password_hash: str
    is_verified: bool

    def get_id(self) -> str:
        return self.id


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


@contextmanager
def _connect():
    db_path = current_app.config["AUTH_DB_PATH"]
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _row_to_user(row: sqlite3.Row | None) -> AuthUser | None:
    if not row:
        return None
    return AuthUser(
        id=row["id"],
        email=row["email"],
        password_hash=row["password_hash"],
        is_verified=bool(row["is_verified"]),
    )


def init_auth_db() -> None:
    db_path = Path(current_app.config["AUTH_DB_PATH"])
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_verified INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS otp_codes (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                otp_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                consumed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_otp_user ON otp_codes(user_id)")
        conn.commit()
    finally:
        conn.close()


def create_user(email: str, password_hash: str) -> AuthUser | None:
    now = _utcnow_iso()
    user_id = str(uuid4())

    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO users(id, email, password_hash, is_verified, created_at, updated_at)
                VALUES (?, ?, ?, 0, ?, ?)
                """,
                (user_id, email, password_hash, now, now),
            )
            conn.commit()
    except sqlite3.IntegrityError:
        return None

    return get_user_by_id(user_id)


def get_user_by_id(user_id: str) -> AuthUser | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _row_to_user(row)


def get_user_by_email(email: str) -> AuthUser | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return _row_to_user(row)


def mark_user_verified(user_id: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET is_verified = 1, updated_at = ? WHERE id = ?",
            (_utcnow_iso(), user_id),
        )
        conn.commit()


def update_user_password(user_id: str, password_hash: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
            (password_hash, _utcnow_iso(), user_id),
        )
        conn.commit()


def create_otp(user_id: str, otp_hash: str, expires_at: str) -> str:
    otp_id = str(uuid4())
    now = _utcnow_iso()

    with _connect() as conn:
        conn.execute(
            "UPDATE otp_codes SET consumed = 1 WHERE user_id = ? AND consumed = 0",
            (user_id,),
        )
        conn.execute(
            """
            INSERT INTO otp_codes(id, user_id, otp_hash, expires_at, consumed, created_at)
            VALUES (?, ?, ?, ?, 0, ?)
            """,
            (otp_id, user_id, otp_hash, expires_at, now),
        )
        conn.commit()
    return otp_id


def get_latest_active_otp(user_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM otp_codes
            WHERE user_id = ? AND consumed = 0
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

    if not row:
        return None

    expires_at = datetime.fromisoformat(row["expires_at"])
    if datetime.now(UTC) >= expires_at:
        mark_otp_consumed(row["id"])
        return None

    return dict(row)


def mark_otp_consumed(otp_id: str) -> None:
    with _connect() as conn:
        conn.execute("UPDATE otp_codes SET consumed = 1 WHERE id = ?", (otp_id,))
        conn.commit()


def has_recent_otp(user_id: str, window_seconds: int) -> bool:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT created_at FROM otp_codes
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

    if not row:
        return False

    created_at = datetime.fromisoformat(row["created_at"])
    elapsed_seconds = (datetime.now(UTC) - created_at).total_seconds()
    return elapsed_seconds < window_seconds
