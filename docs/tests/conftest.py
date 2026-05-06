from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.extensions import bcrypt
from app.services.auth_store import create_user, mark_user_verified
from app.services.pipeline_stub import JOBS


@pytest.fixture
def app(tmp_path):
    auth_db_path = tmp_path / "auth.db"
    app = create_app(
        {
            "TESTING": True,
            "AUTH_DB_PATH": str(auth_db_path),
            "OTP_RESEND_COOLDOWN_SECONDS": 0,
            "SECRET_KEY": "test-secret-key",
        }
    )
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def verified_user(app):
    with app.app_context():
        user = create_user(
            email="qa@example.com",
            password_hash=bcrypt.generate_password_hash("StrongPass123").decode("utf-8"),
        )
        mark_user_verified(user.id)
        return user


@pytest.fixture
def logged_in_client(client, verified_user):
    client.post(
        "/auth/login",
        data={"email": verified_user.email, "password": "StrongPass123"},
        follow_redirects=True,
    )
    return client


@pytest.fixture(autouse=True)
def clear_jobs():
    JOBS.clear()
    yield
    JOBS.clear()


@pytest.fixture
def sample_dataframe():
    return pd.DataFrame(
        {
            "order_date": pd.to_datetime(
                ["2025-01-01", "2025-01-15", "2025-02-01", "2025-02-15"]
            ),
            "product_line": ["A", "A", "B", "B"],
            "state": ["North", "South", "North", "South"],
            "qty": [10, 20, 15, 25],
            "unit_price": [100, 110, 105, 120],
        }
    )
