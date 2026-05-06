from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from app.services.pipeline_stub import list_jobs

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    return render_template("home.html")


@main_bp.route("/health")
def health():
    return jsonify({"status": "ok", "phase": 3})


@main_bp.route("/user")
@login_required
def user_portal():
    jobs = list_jobs(user_id=current_user.get_id())
    user_key = f"user_settings_{current_user.get_id()}"
    settings = session.get(
        user_key,
        {
            "display_name": "",
            "default_operation": "forecasting",
            "start_page": "home",
            "email_notifications": True,
            "pipeline_alerts": True,
        },
    )
    return render_template("user.html", jobs=jobs, total_jobs=len(jobs), settings=settings)


@main_bp.route("/user/preferences", methods=["POST"])
@login_required
def update_preferences():
    user_key = f"user_settings_{current_user.get_id()}"
    existing_settings = session.get(
        user_key,
        {
            "display_name": "",
            "default_operation": "forecasting",
            "start_page": "home",
            "email_notifications": True,
            "pipeline_alerts": True,
        },
    )

    section = request.form.get("section", "")
    if section == "profile":
        existing_settings["display_name"] = request.form.get("display_name", "").strip()
        existing_settings["default_operation"] = request.form.get(
            "default_operation", "forecasting"
        )
        existing_settings["start_page"] = request.form.get("start_page", "home")
    elif section == "notifications":
        existing_settings["email_notifications"] = bool(request.form.get("email_notifications"))
        existing_settings["pipeline_alerts"] = bool(request.form.get("pipeline_alerts"))
    else:
        flash("Unknown settings section.", "error")
        return redirect(url_for("main.user_portal"))

    session[user_key] = existing_settings
    session.modified = True
    flash("Settings updated.", "success")
    return redirect(url_for("main.user_portal"))


@main_bp.route("/about")
@login_required
def about():
    return render_template("about.html")
