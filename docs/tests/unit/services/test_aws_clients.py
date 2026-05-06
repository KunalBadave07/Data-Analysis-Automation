from __future__ import annotations

from app.services import aws_clients


class _FakeSession:
    def __init__(self):
        self.client_calls = []
        self.resource_calls = []

    def client(self, name):
        self.client_calls.append(name)
        return f"client:{name}"

    def resource(self, name):
        self.resource_calls.append(name)
        return f"resource:{name}"


def test_get_clients_returns_expected_service_map(app, monkeypatch):
    fake_session = _FakeSession()
    monkeypatch.setattr(aws_clients, "create_session", lambda: fake_session)

    with app.app_context():
        clients = aws_clients.get_clients()

    assert clients["s3"] == "client:s3"
    assert clients["dynamodb"] == "resource:dynamodb"
    assert clients["athena"] == "client:athena"
    assert "quicksight" in clients
