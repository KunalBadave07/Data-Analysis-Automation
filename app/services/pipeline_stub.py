from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.services.analytics_service import build_metric_destinations
from app.services.pipeline.data_pipeline import run_pipeline

JOBS: dict[str, dict] = {}


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def start_pipeline(filename: str, operation: str, description: str, user_id: str) -> str:
    job_id = str(uuid4())
    created_at = _utcnow_iso()
    processed_path = None

    try:
        pipeline_output = run_pipeline(filename, operation)
        processed_path = pipeline_output.get("processed_path")
        result = {
            "summary": pipeline_output.get("summary", "Pipeline executed successfully."),
            "description": description or "Analytics were generated from the uploaded dataset.",
            "metrics": pipeline_output.get("metrics", {}),
            "insights": pipeline_output.get("insights", []),
            "insight_cards": pipeline_output.get("insight_cards", []),
            "recommendations": pipeline_output.get("recommendations", []),
            "business_actions": pipeline_output.get("business_actions", []),
            "dashboard": pipeline_output.get("dashboard", {}),
            "report_sections": pipeline_output.get("report_sections", {}),
            "schema": pipeline_output.get("schema", {}),
            "schema_health": pipeline_output.get("schema_health", {}),
            "breakdowns": pipeline_output.get("breakdowns", {}),
            "filters": pipeline_output.get("filters", {}),
            "filter_lists": pipeline_output.get("filter_lists", {}),
            "processing_notes": pipeline_output.get("processing_notes", {}),
            "mode_details": pipeline_output.get("mode_details", {}),
        }
        result["metric_destinations"] = build_metric_destinations(job_id, pipeline_output)
        status = "SUCCEEDED"
    except Exception as e:
        result = {
            "summary": "Pipeline execution failed.",
            "description": str(e),
            "metrics": {},
            "insights": [],
            "insight_cards": [],
            "recommendations": [],
            "business_actions": [],
            "dashboard": {},
            "report_sections": {},
            "schema": {},
            "schema_health": {},
            "breakdowns": {},
            "filters": {},
            "filter_lists": {"category_list": [], "region_list": [], "year_list": []},
            "processing_notes": {},
            "mode_details": {},
            "metric_destinations": {},
        }
        status = "FAILED"

    JOBS[job_id] = {
        "job_id": job_id,
        "user_id": user_id,
        "filename": filename,
        "operation": operation,
        "description": description,
        "status": status,
        "created_at": created_at,
        "updated_at": _utcnow_iso(),
        "result": result,
        "processed_path": processed_path,
    }
    return job_id


def get_job(job_id: str) -> dict | None:
    return JOBS.get(job_id)


def list_jobs(user_id: str) -> list[dict]:
    jobs = [job for job in JOBS.values() if job["user_id"] == user_id]
    return sorted(jobs, key=lambda item: item["created_at"], reverse=True)
