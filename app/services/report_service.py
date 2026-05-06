from __future__ import annotations

import pandas as pd

from app.services.analytics_service import generate_analysis


def generate_dashboard_data(file_path: str, operation: str) -> dict:
    df = pd.read_csv(file_path)
    analysis = generate_analysis(df, operation)
    return analysis["dashboard"]


def build_report_context(job: dict) -> dict:
    result = job.get("result", {})
    report_sections = result.get("report_sections", {})
    schema = result.get("schema", {})
    processing_notes = result.get("processing_notes", {})

    return {
        "title": f"Business Analytics Report: {job.get('filename', 'dataset')}",
        "executive_summary": result.get("summary", "Dataset analysis completed."),
        "description": result.get("description", ""),
        "operation": job.get("operation", "").replace("_", " ").title(),
        "status": job.get("status", "UNKNOWN"),
        "schema": schema,
        "processing_notes": processing_notes,
        "dashboard": result.get("dashboard", {}),
        "sections": report_sections,
        "insights": result.get("insights", []),
        "insight_cards": result.get("insight_cards", []),
        "recommendations": result.get("recommendations", []),
        "business_actions": result.get("business_actions", []),
        "metrics": result.get("metrics", {}),
        "mode_details": result.get("mode_details", {}),
        "schema_health": result.get("schema_health", {}),
    }
