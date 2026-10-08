from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_babel import gettext as _
from flask_login import current_user, login_user, logout_user
from werkzeug.wrappers import Response

from app.controllers import safe_next_url
from app.extensions import db, limiter, login_manager
from app.forms.auth import LoginForm, RegisterForm, ResetPasswordForm, ResetRequestForm
from app.models import User
from app.services import ValidationError
from app.services.auth_service import AuthService

bp = Blueprint("auth", __name__, url_prefix="/auth")
# Brute-force protection on every form POST in this blueprint.
limiter.limit("10 per minute", methods=["POST"])(bp)

login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"
login_manager.localize_callback = _


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    return db.session.get(User, int(user_id))


@login_manager.unauthorized_handler
def unauthorized() -> Response:
    if request.path.startswith("/api/"):
        abort(401)
    flash(_("Please log in to access this page."), "info")
    return redirect(url_for("auth.login", next=request.full_path))


@bp.route("/login", methods=["GET", "POST"])
def login() -> str | Response:
    if current_user.is_authenticated:
        return redirect(url_for("web.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = AuthService(db.session).authenticate(form.email.data, form.password.data)
        if user is None:
            flash(_("Invalid email or password."), "danger")
        else:
            login_user(user, remember=form.remember_me.data)
            return redirect(safe_next_url(request.args.get("next")) or url_for("web.index"))
    return render_template("auth/login.html", form=form)


@bp.post("/logout")
def logout() -> Response:
    logout_user()
    return redirect(url_for("web.index"))


@bp.route("/register", methods=["GET", "POST"])
def register() -> str | Response:
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            user = AuthService(db.session).register(form.email.data, form.password.data)
        except ValidationError as e:
            form.email.errors = [str(e)]
        else:
            login_user(user)
            flash(_("Welcome! Your account is ready."), "success")
            return redirect(url_for("web.index"))
    return render_template("auth/form.html", form=form, title=_("Register"))


@bp.route("/reset", methods=["GET", "POST"])
def reset_request() -> str | Response:
    form = ResetRequestForm()
    if form.validate_on_submit():
        AuthService(db.session).send_password_reset(form.email.data)
        flash(_("If that email is registered, a reset link is on its way."), "info")
        return redirect(url_for(".login"))
    return render_template("auth/form.html", form=form, title=_("Reset password"))


@bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token: str) -> str | Response:
    service = AuthService(db.session)
    user = service.user_from_reset_token(token)
    if user is None:
        flash(_("This reset link is invalid or has expired."), "danger")
        return redirect(url_for(".reset_request"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        try:
            service.reset_password(user, form.password.data)
        except ValidationError as e:
            form.password.errors = [str(e)]
        else:
            flash(_("Password changed. You can sign in now."), "success")
            return redirect(url_for(".login"))
    return render_template("auth/form.html", form=form, title=_("Set a new password"))
