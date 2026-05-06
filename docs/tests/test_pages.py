from app import create_app


def test_home_page_loads():
    app = create_app()
    client = app.test_client()

    response = client.get("/")
    assert response.status_code == 200
    assert b"Upload once. Get insights" in response.data


def test_auth_pages_load():
    app = create_app()
    client = app.test_client()

    login_response = client.get("/auth/login")
    register_response = client.get("/auth/register")
    verify_response = client.get("/auth/verify")
    forgot_password_response = client.get("/auth/forgot-password")
    reset_password_response = client.get("/auth/reset-password")

    assert login_response.status_code == 200
    assert register_response.status_code == 200
    assert verify_response.status_code == 200
    assert forgot_password_response.status_code == 200
    assert reset_password_response.status_code == 200


def test_protected_page_redirects_to_login():
    app = create_app()
    client = app.test_client()

    response = client.get("/dataset/operation")
    assert response.status_code == 302
    assert "/auth/login" in response.headers.get("Location", "")
