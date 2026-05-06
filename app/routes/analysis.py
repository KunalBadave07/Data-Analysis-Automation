from __future__ import annotations

import os
from functools import lru_cache

import pandas as pd
from flask import Blueprint, abort, jsonify, make_response, render_template, request
from flask_login import login_required

from app.services.analytics_service import build_metric_destinations, generate_analysis
from app.services.pipeline_stub import get_job, list_jobs
from app.services.report_service import build_report_context, generate_dashboard_data

analysis_bp = Blueprint("analysis", __name__, url_prefix="/analysis")


@lru_cache(maxsize=16)
def _load_processed_frame(processed_path: str, modified_time: float) -> pd.DataFrame:
    return pd.read_csv(processed_path)


def _refresh_job_analysis(
    job: dict,
    operation: str,
    category: str = "all",
    region: str = "all",
    year: str = "all",
    product: str = "all",
) -> dict:
    processed_path = job.get("processed_path")
    if not processed_path or not os.path.exists(processed_path):
        raise FileNotFoundError("Processed data not found")

    modified_time = os.path.getmtime(processed_path)
    cache_key = f"{operation}:{category}:{region}:{year}:{product}"
    cached_analysis = job.setdefault("analysis_cache", {}).get(cache_key)
    if cached_analysis:
        return cached_analysis

    df = _load_processed_frame(processed_path, modified_time).copy()
    analysis = generate_analysis(
        df,
        operation,
        category=category,
        region=region,
        year=year,
        product=product,
        processing_notes=job.get("result", {}).get("processing_notes", {}),
    )
    analysis["metric_destinations"] = build_metric_destinations(job["job_id"], analysis)
    job["result"].update(analysis)
    job["analysis_cache"][cache_key] = analysis
    return analysis


@analysis_bp.route("/dashboard/<job_id>")
@login_required
def dashboard(job_id: str):
    job = get_job(job_id)
    if not job:
        abort(404)
    if job.get("status") != "SUCCEEDED":
        return render_template("dashboard.html", job=job, chart_data=None, error=job["result"]["description"])

    mode = request.args.get("mode", job.get("operation", "business_analysis"))
    category = request.args.get("category", "all")
    region = request.args.get("region", "all")
    year = request.args.get("year", "all")
    product = request.args.get("product", "all")
    analysis = _refresh_job_analysis(
        job,
        mode,
        category=category,
        region=region,
        year=year,
        product=product,
    )
    chart_data = analysis["dashboard"]
    job["result"]["dashboard"] = chart_data
    return render_template("dashboard.html", job=job, chart_data=chart_data, analysis=analysis)


@analysis_bp.route("/dashboard/<job_id>/export")
@login_required
def dashboard_export(job_id: str):
    job = get_job(job_id)
    if not job:
        abort(404)
    if job.get("status") != "SUCCEEDED":
        abort(400, description="Dashboard export is available only for successful jobs.")
    mode = request.args.get("mode", job.get("operation", "business_analysis"))
    category = request.args.get("category", "all")
    region = request.args.get("region", "all")
    year = request.args.get("year", "all")
    product = request.args.get("product", "all")
    analysis = _refresh_job_analysis(job, mode, category=category, region=region, year=year, product=product)
    chart_data = analysis["dashboard"]
    export_format = request.args.get("format", "json")
    if export_format == "powerbi_html":
        response = make_response(
            render_template("dashboard_export.html", job=job, chart_data=chart_data, analysis=analysis)
        )
        safe_name = os.path.splitext(job.get("filename", "dashboard"))[0].replace(" ", "_")
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        response.headers["Content-Disposition"] = f'attachment; filename="{safe_name}_powerbi_dashboard.html"'
        return response
    return jsonify(
        {
            "job_id": job_id,
            "filename": job.get("filename"),
            "dashboard": chart_data,
            "schema": analysis.get("schema", {}),
        }
    )


@analysis_bp.route("/processing/<job_id>")
@login_required
def processing_status(job_id: str):
    job = get_job(job_id)
    if not job:
        abort(404)
    return render_template("processing.html", job=job)


@analysis_bp.route("/results/<job_id>")
@login_required
def results(job_id: str):
    job = get_job(job_id)
    if not job:
        abort(404)
    if job.get("status") == "FAILED":
        return render_template("results.html", job=job, error=job["result"]["description"])

    category = request.args.get("category", "all")
    region = request.args.get("region", "all")
    year = request.args.get("year", "all")
    mode = request.args.get("mode", job.get("operation", "business_analysis"))
    product = request.args.get("product", "all")
    try:
        analysis = _refresh_job_analysis(job, mode, category=category, region=region, year=year, product=product)
    except FileNotFoundError as error:
        return render_template("results.html", job=job, error=str(error))

    return render_template("results.html", job=job, analysis=analysis)


@analysis_bp.route("/metric/<job_id>/<metric_key>")
@login_required
def metric_detail(job_id: str, metric_key: str):
    job = get_job(job_id)
    if not job:
        abort(404)
    if job.get("status") != "SUCCEEDED":
        abort(400, description="Metric details are available only for successful jobs.")

    category = request.args.get("category", "all")
    region = request.args.get("region", "all")
    year = request.args.get("year", "all")
    mode = request.args.get("mode", job.get("operation", "business_analysis"))
    product = request.args.get("product", "all")
    analysis = _refresh_job_analysis(job, mode, category=category, region=region, year=year, product=product)
    metric = analysis.get("metrics", {}).get(metric_key)
    if not metric:
        abort(404)

    return render_template(
        "results.html",
        job=job,
        analysis=analysis,
        focus_metric=metric_key,
        focus_message=f"{metric['label']} opens its related analytical section below.",
    )


@analysis_bp.route("/report/<job_id>")
@login_required
def report(job_id: str):
    job = get_job(job_id)
    if not job:
        abort(404)
    if job.get("status") == "SUCCEEDED" and job.get("processed_path"):
        _refresh_job_analysis(job, job.get("operation", "business_analysis"))
    report_context = build_report_context(job)
    return render_template("report.html", job=job, report=report_context)


@analysis_bp.route("/history")
@login_required
def history():
    from flask_login import current_user

    jobs = list_jobs(user_id=current_user.get_id())
    return render_template("history.html", jobs=jobs)
