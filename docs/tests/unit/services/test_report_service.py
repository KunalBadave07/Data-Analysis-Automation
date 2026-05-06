from __future__ import annotations

import pandas as pd

from app.services.report_service import build_report_context, generate_dashboard_data


def test_generate_dashboard_data_reads_real_dataset(tmp_path):
    csv_path = tmp_path / "dataset.csv"
    pd.DataFrame(
        {
            "date": ["2025-01-01", "2025-02-01"],
            "category": ["A", "B"],
            "region": ["North", "South"],
            "units_sold": [10, 20],
            "price": [100, 150],
        }
    ).to_csv(csv_path, index=False)

    dashboard = generate_dashboard_data(str(csv_path), "business_analysis")

    assert dashboard["kpis"]
    assert dashboard["trend"]["labels"]
    assert dashboard["category_chart"]["labels"] == ["B", "A"]


def test_build_report_context_uses_job_result():
    job = {
        "filename": "sample.csv",
        "operation": "business_analysis",
        "status": "SUCCEEDED",
        "result": {
            "summary": "Summary",
            "description": "Description",
            "dashboard": {"kpis": []},
            "report_sections": {"dataset_overview": []},
            "insights": ["Insight"],
            "recommendations": ["Recommendation"],
            "metrics": {"records": {"value": 1}},
        },
    }

    context = build_report_context(job)

    assert context["title"].startswith("Business Analytics Report")
    assert context["executive_summary"] == "Summary"
    assert context["insights"] == ["Insight"]
