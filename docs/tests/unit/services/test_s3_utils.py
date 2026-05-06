from __future__ import annotations

from app.services.pipeline import s3_utils


class _UploadOnceClient:
    def __init__(self):
        self.calls = 0

    def upload_file(self, local_path, bucket, key):
        self.calls += 1
        return None


class _RetryClient:
    def __init__(self):
        self.calls = 0

    def upload_file(self, local_path, bucket, key):
        self.calls += 1
        raise RuntimeError("boom")


def test_upload_file_returns_true_on_success(monkeypatch):
    client = _UploadOnceClient()
    monkeypatch.setattr(s3_utils, "s3_client", client)

    assert s3_utils.upload_file("a.csv", "raw/a.csv") is True
    assert client.calls == 1


def test_upload_file_retries_and_returns_false(monkeypatch):
    client = _RetryClient()
    monkeypatch.setattr(s3_utils, "s3_client", client)
    monkeypatch.setattr(s3_utils.time, "sleep", lambda _: None)

    assert s3_utils.upload_file("a.csv", "raw/a.csv", retries=2) is False
    assert client.calls == 2
