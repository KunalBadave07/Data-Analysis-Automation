from __future__ import annotations

import pandas as pd

from app.services.pipeline import data_pipeline
from app.services.pipeline_stub import start_pipeline


def test_run_pipeline_returns_processed_analysis(monkeypatch, tmp_path):
    source = tmp_path / "source.csv"
    pd.DataFrame(
        {
            "Order Date": ["2025-01-01", "2025-01-15", "2025-02-01"],
            "Product Line": ["A", "A", "B"],
            "State": ["North", "South", "North"],
            "Qty": [10, 20, 15],
            "Unit Price": [100, 110, 105],
        }
    ).to_csv(source, index=False)

    uploads = []
    monkeypatch.setattr(data_pipeline, "upload_file", lambda path, key: uploads.append((path, key)) or True)

    result = data_pipeline.run_pipeline(str(source), "business_analysis")

    assert result["metrics"]["total_metric"]["value"] == 45
    assert result["dashboard"]["trend"]["labels"]
    assert len(uploads) == 2


def test_start_pipeline_marks_failed_jobs(monkeypatch):
    monkeypatch.setattr("app.services.pipeline_stub.run_pipeline", lambda filename, operation: (_ for _ in ()).throw(ValueError("bad dataset")))

    job_id = start_pipeline("broken.csv", "business_analysis", "desc", "user-1")

    from app.services.pipeline_stub import JOBS

    assert JOBS[job_id]["status"] == "FAILED"
    assert "bad dataset" in JOBS[job_id]["result"]["description"]
