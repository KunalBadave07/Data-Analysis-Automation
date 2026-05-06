from __future__ import annotations

from io import BytesIO

from app.services.pipeline_stub import JOBS


def test_local_user_flow_upload_to_results_dashboard_report(logged_in_client, monkeypatch):
    monkeypatch.setattr("app.services.pipeline.data_pipeline.upload_file", lambda path, key: True)

    dataset_bytes = (
        b"date,category,region,units_sold,price\n"
        b"2025-01-01,Electronics,North,10,100\n"
        b"2025-02-01,Electronics,South,20,120\n"
        b"2025-03-01,Fashion,South,15,90\n"
    )

    upload_response = logged_in_client.post(
        "/dataset/upload",
        data={
            "operation": "business_analysis",
            "description": "System flow test",
            "dataset": (BytesIO(dataset_bytes), "system.csv"),
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )

    assert upload_response.status_code == 302
    assert JOBS
    job_id = next(iter(JOBS))

    processing_response = logged_in_client.get(f"/analysis/processing/{job_id}")
    results_response = logged_in_client.get(f"/analysis/results/{job_id}")
    dashboard_response = logged_in_client.get(f"/analysis/dashboard/{job_id}")
    report_response = logged_in_client.get(f"/analysis/report/{job_id}")

    assert processing_response.status_code == 200
    assert results_response.status_code == 200
    assert dashboard_response.status_code == 200
    assert report_response.status_code == 200
    assert b"Results Summary" in results_response.data
    assert b"Dashboard Preview" in dashboard_response.data
    assert b"Business Analytics Report" in report_response.data
