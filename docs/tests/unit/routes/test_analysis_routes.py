from __future__ import annotations

import pandas as pd

from app.services.pipeline_stub import JOBS


def _seed_job(tmp_path, user_id="test-user"):
    processed_path = tmp_path / "processed.csv"
    pd.DataFrame(
        {
            "date": ["2025-01-01", "2025-02-01"],
            "category": ["A", "B"],
            "region": ["North", "South"],
            "units_sold": [10, 20],
            "price": [100, 150],
        }
    ).to_csv(processed_path, index=False)

    JOBS["job-123"] = {
        "job_id": "job-123",
        "user_id": user_id,
        "filename": "sample.csv",
        "operation": "business_analysis",
        "status": "SUCCEEDED",
        "processed_path": str(processed_path),
        "result": {
            "processing_notes": {"duplicates_removed": 0, "date_columns": ["date"], "derived_features": []},
        },
    }


def test_results_route_renders_real_analysis(logged_in_client, verified_user, tmp_path):
    _seed_job(tmp_path, user_id=verified_user.id)

    response = logged_in_client.get("/analysis/results/job-123")

    assert response.status_code == 200
    assert b"Results Summary" in response.data
    assert b"Dataset Overview" in response.data


def test_dashboard_export_returns_json(logged_in_client, verified_user, tmp_path):
    _seed_job(tmp_path, user_id=verified_user.id)

    response = logged_in_client.get("/analysis/dashboard/job-123/export")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["job_id"] == "job-123"
    assert "dashboard" in payload


def test_report_route_renders_business_report(logged_in_client, verified_user, tmp_path):
    _seed_job(tmp_path, user_id=verified_user.id)

    response = logged_in_client.get("/analysis/report/job-123")

    assert response.status_code == 200
    assert b"Business Analytics Report" in response.data
