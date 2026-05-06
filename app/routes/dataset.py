import os
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.services.pipeline_stub import start_pipeline

dataset_bp = Blueprint("dataset", __name__, url_prefix="/dataset")


@dataset_bp.route("/operation")
@login_required
def operation_selection():
    return render_template("operation_select.html")


@dataset_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_dataset():
    default_operation = request.args.get("operation", "")

    if request.method == "POST":
        uploaded_file = request.files.get("dataset")
        operation = request.form.get("operation", "").strip()
        description = request.form.get("description", "").strip()

        if not uploaded_file or uploaded_file.filename == "":
            flash("Please choose a dataset file.", "error")
            return redirect(url_for("dataset.upload_dataset"))

        if not operation:
            flash("Please select an operation.", "error")
            return redirect(url_for("dataset.upload_dataset"))

        UPLOAD_FOLDER = "data/raw"

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        safe_filename = secure_filename(uploaded_file.filename or "")
        if not safe_filename:
            flash("The uploaded file name is invalid.", "error")
            return redirect(url_for("dataset.upload_dataset"))

        allowed_extensions = {".csv", ".xlsx", ".xls"}
        extension = os.path.splitext(safe_filename)[1].lower()
        if extension not in allowed_extensions:
            flash("Please upload a CSV or Excel retail dataset.", "error")
            return redirect(url_for("dataset.upload_dataset"))

        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)

        uploaded_file.save(file_path)

        job_id = start_pipeline(
            filename=file_path,   # pass full path now
            operation=operation,
            description=description,
            user_id=current_user.get_id(),
        )

        flash("Dataset accepted. Analytics pipeline started.", "success")
        return redirect(url_for("analysis.processing_status", job_id=job_id))

    return render_template("upload.html", default_operation=default_operation)
