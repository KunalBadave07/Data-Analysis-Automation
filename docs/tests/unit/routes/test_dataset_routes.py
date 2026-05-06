from __future__ import annotations


def test_upload_page_requires_login(client):
    response = client.get("/dataset/upload")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_upload_starts_pipeline_for_authenticated_user(logged_in_client, monkeypatch, tmp_path):
    called = {}

    def fake_start_pipeline(filename, operation, description, user_id):
        called["filename"] = filename
        called["operation"] = operation
        called["description"] = description
        called["user_id"] = user_id
        return "job-001"

    monkeypatch.setattr("app.routes.dataset.start_pipeline", fake_start_pipeline)

    dataset = tmp_path / "upload.csv"
    dataset.write_text("date,units_sold\n2025-01-01,10\n", encoding="utf-8")

    with dataset.open("rb") as handle:
        response = logged_in_client.post(
            "/dataset/upload",
            data={
                "operation": "business_analysis",
                "description": "Test upload",
                "dataset": (handle, "upload.csv"),
            },
            content_type="multipart/form-data",
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/analysis/processing/job-001")
    assert called["operation"] == "business_analysis"


def test_upload_rejects_missing_file(logged_in_client):
    response = logged_in_client.post(
        "/dataset/upload",
        data={"operation": "business_analysis", "description": "No file"},
        follow_redirects=True,
    )

    assert b"Please choose a dataset file." in response.data
