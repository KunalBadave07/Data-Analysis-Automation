from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import bcrypt, login_manager
from app.services.auth_store import (
    create_otp,
    create_user,
    get_latest_active_otp,
    get_user_by_email,
    get_user_by_id,
    has_recent_otp,
    mark_otp_consumed,
    mark_user_verified,
    update_user_password,
)
from app.services.otp_service import generate_otp_code, hash_otp, send_otp_email, verify_otp

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@login_manager.user_loader
def load_user(user_id: str):
    return get_user_by_id(user_id)


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _issue_verification_otp(user) -> tuple[bool, str]:
    code = generate_otp_code()
    expires_at = (
        datetime.now(UTC) + timedelta(minutes=current_app.config["OTP_EXPIRY_MINUTES"])
    ).isoformat()
    delivered, message = send_otp_email(user.email, code)
    if delivered:
        create_otp(user_id=user.id, otp_hash=hash_otp(code), expires_at=expires_at)
    return delivered, message


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        email = _normalize_email(request.form.get("email", ""))
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "error")
            return redirect(url_for("auth.register"))

        if not EMAIL_PATTERN.match(email):
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("auth.register"))

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return redirect(url_for("auth.register"))

        existing_user = get_user_by_email(email)
        if existing_user:
            if existing_user.is_verified:
                flash("Account already exists. Please login.", "warning")
                return redirect(url_for("auth.login"))

            cooldown = current_app.config["OTP_RESEND_COOLDOWN_SECONDS"]
            if has_recent_otp(existing_user.id, cooldown):
                flash("OTP already sent recently. Please wait and check your email.", "warning")
            else:
                delivered, msg = _issue_verification_otp(existing_user)
                flash(msg, "success" if delivered else "info")

            flash("Account exists but is not verified yet.", "warning")
            return redirect(url_for("auth.verify_otp_page", email=email))

        user = create_user(
            email=email,
            password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
        )
        if not user:
            flash("Unable to create account right now.", "error")
            return redirect(url_for("auth.register"))

        delivered, msg = _issue_verification_otp(user)
        flash(
            "Registration successful. Verify your email with the OTP code.",
            "success",
        )
        flash(msg, "success" if delivered else "info")
        return redirect(url_for("auth.verify_otp_page", email=email))

    return render_template("auth/register.html")


@auth_bp.route("/verify", methods=["GET", "POST"])
def verify_otp_page():
    if current_user.is_authenticated and getattr(current_user, "is_verified", False):
        return redirect(url_for("main.home"))

    email = _normalize_email(request.values.get("email", ""))

    if request.method == "POST":
        otp = request.form.get("otp", "").strip()

        if not email or not otp:
            flash("Email and OTP are required.", "error")
            return redirect(url_for("auth.verify_otp_page", email=email))

        user = get_user_by_email(email)
        if not user:
            flash("Account not found.", "error")
            return redirect(url_for("auth.register"))

        if user.is_verified:
            flash("Email is already verified. Please login.", "info")
            return redirect(url_for("auth.login"))

        latest_otp = get_latest_active_otp(user.id)
        if not latest_otp:
            flash("OTP expired or unavailable. Please request a new code.", "warning")
            return redirect(url_for("auth.verify_otp_page", email=email))

        if not verify_otp(otp, latest_otp["otp_hash"]):
            flash("Invalid OTP code.", "error")
            return redirect(url_for("auth.verify_otp_page", email=email))

        mark_otp_consumed(latest_otp["id"])
        mark_user_verified(user.id)
        verified_user = get_user_by_id(user.id)
        login_user(verified_user)
        flash("Email verified successfully. You are now logged in.", "success")
        return redirect(url_for("main.home"))

    return render_template("auth/verify_otp.html", email=email)


@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    email = _normalize_email(request.form.get("email", ""))
    if not email:
        flash("Email is required to resend OTP.", "error")
        return redirect(url_for("auth.verify_otp_page"))

    user = get_user_by_email(email)
    if not user:
        flash("Account not found.", "error")
        return redirect(url_for("auth.register"))

    if user.is_verified:
        flash("Account already verified. Please login.", "info")
        return redirect(url_for("auth.login"))

    cooldown = current_app.config["OTP_RESEND_COOLDOWN_SECONDS"]
    if has_recent_otp(user.id, cooldown):
        flash("Please wait before requesting another OTP.", "warning")
        return redirect(url_for("auth.verify_otp_page", email=email))

    delivered, msg = _issue_verification_otp(user)
    flash("New OTP generated.", "success")
    flash(msg, "success" if delivered else "info")
    return redirect(url_for("auth.verify_otp_page", email=email))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        email = _normalize_email(request.form.get("email", ""))
        password = request.form.get("password", "")
        user = get_user_by_email(email)

        if not user or not bcrypt.check_password_hash(user.password_hash, password):
            flash("Invalid credentials.", "error")
            return redirect(url_for("auth.login"))

        if not user.is_verified:
            flash("Please verify your email before login.", "warning")
            return redirect(url_for("auth.verify_otp_page", email=email))

        login_user(user)
        flash("Logged in successfully.", "success")
        return redirect(url_for("main.home"))

    return render_template("auth/login.html")


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    email = _normalize_email(request.values.get("email", ""))

    if request.method == "POST":
        if not email:
            flash("Email is required.", "error")
            return redirect(url_for("auth.forgot_password"))

        if not EMAIL_PATTERN.match(email):
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("auth.forgot_password", email=email))

        user = get_user_by_email(email)
        if not user:
            flash("Account not found.", "error")
            return redirect(url_for("auth.register"))

        if not user.is_verified:
            flash("Please verify your email before resetting password.", "warning")
            return redirect(url_for("auth.verify_otp_page", email=email))

        cooldown = current_app.config["OTP_RESEND_COOLDOWN_SECONDS"]
        if has_recent_otp(user.id, cooldown):
            flash("OTP already sent recently. Please wait and check your email.", "warning")
            return redirect(url_for("auth.reset_password", email=email))

        delivered, msg = _issue_verification_otp(user)
        if delivered:
            flash("Password reset OTP generated.", "success")
            flash(msg, "success")
            return redirect(url_for("auth.reset_password", email=email))

        flash(msg, "error")
        return redirect(url_for("auth.forgot_password", email=email))

    return render_template("auth/forgot_password.html", email=email)


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    email = _normalize_email(request.values.get("email", ""))

    if request.method == "POST":
        otp = request.form.get("otp", "").strip()
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not email or not otp or not new_password or not confirm_password:
            flash("Email, OTP, and both password fields are required.", "error")
            return redirect(url_for("auth.reset_password", email=email))

        if new_password != confirm_password:
            flash("New password and confirmation do not match.", "error")
            return redirect(url_for("auth.reset_password", email=email))

        if len(new_password) < 8:
            flash("New password must be at least 8 characters.", "error")
            return redirect(url_for("auth.reset_password", email=email))

        user = get_user_by_email(email)
        if not user:
            flash("Account not found.", "error")
            return redirect(url_for("auth.register"))

        if not user.is_verified:
            flash("Please verify your email before resetting password.", "warning")
            return redirect(url_for("auth.verify_otp_page", email=email))

        latest_otp = get_latest_active_otp(user.id)
        if not latest_otp:
            flash("OTP expired or unavailable. Please request a new code.", "warning")
            return redirect(url_for("auth.forgot_password", email=email))

        if not verify_otp(otp, latest_otp["otp_hash"]):
            flash("Invalid OTP code.", "error")
            return redirect(url_for("auth.reset_password", email=email))

        mark_otp_consumed(latest_otp["id"])
        update_user_password(
            user_id=user.id,
            password_hash=bcrypt.generate_password_hash(new_password).decode("utf-8"),
        )

        updated_user = get_user_by_id(user.id)
        login_user(updated_user)
        flash("Password reset successful. You are now logged in.", "success")
        return redirect(url_for("main.home"))

    return render_template("auth/reset_password.html", email=email)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("main.home"))


@auth_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_password or not new_password or not confirm_password:
        flash("All password fields are required.", "error")
        return redirect(url_for("main.user_portal"))

    if new_password != confirm_password:
        flash("New password and confirmation do not match.", "error")
        return redirect(url_for("main.user_portal"))

    if len(new_password) < 8:
        flash("New password must be at least 8 characters.", "error")
        return redirect(url_for("main.user_portal"))

    if not bcrypt.check_password_hash(current_user.password_hash, current_password):
        flash("Current password is incorrect.", "error")
        return redirect(url_for("main.user_portal"))

    update_user_password(
        user_id=current_user.get_id(),
        password_hash=bcrypt.generate_password_hash(new_password).decode("utf-8"),
    )
    flash("Password updated successfully.", "success")
    return redirect(url_for("main.user_portal"))
