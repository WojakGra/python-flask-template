from flask import current_app, render_template, url_for
from flask_babel import gettext as _
from flask_mail import Message
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy import select

from app.extensions import mail
from app.models import User
from app.services import DbSession, ValidationError

MIN_PASSWORD_LENGTH = 8


def _check_password(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            _("Password must be at least %(n)d characters.", n=MIN_PASSWORD_LENGTH)
        )


class AuthService:
    def __init__(self, session: DbSession) -> None:
        self.session = session

    def register(self, email: str, password: str) -> User:
        email = email.strip().lower()
        _check_password(password)
        if self._find(email):
            raise ValidationError(_("This email is already registered."))

        user = User(email=email)
        user.set_password(password)
        self.session.add(user)
        self.session.commit()
        return user

    def authenticate(self, email: str, password: str) -> User | None:
        user = self._find(email.strip().lower())
        return user if user and user.check_password(password) else None

    def send_password_reset(self, email: str) -> None:
        """Mail a reset link if the account exists.

        Returns nothing either way, so callers can't probe which emails exist.
        """
        user = self._find(email.strip().lower())
        if user is None:
            return
        token = self._serializer().dumps(self._token_payload(user))
        url = url_for("auth.reset_password", token=token, _external=True)
        message = Message(
            subject=_("Reset your password"),
            recipients=[user.email],
            body=render_template("email/reset_password.txt", url=url),
            html=render_template("email/reset_password.html", url=url),
        )
        try:
            mail.send(message)
        except OSError:  # SMTP down: log it, keep the response identical
            current_app.logger.exception("Could not send password reset email")

    def user_from_reset_token(self, token: str) -> User | None:
        try:
            max_age = current_app.config["PASSWORD_RESET_MAX_AGE"]
            data = self._serializer().loads(token, max_age=max_age)
            user = self.session.get(User, data["id"])
        except BadSignature, KeyError, TypeError:
            return None
        # The token carries part of the old hash, so it stops working once the password changes.
        if user is None or data.get("h") != self._token_payload(user)["h"]:
            return None
        return user

    def reset_password(self, user: User, password: str) -> None:
        _check_password(password)
        user.set_password(password)
        self.session.commit()

    def _find(self, email: str) -> User | None:
        return self.session.scalar(select(User).filter_by(email=email))

    @staticmethod
    def _token_payload(user: User) -> dict[str, object]:
        return {"id": user.id, "h": user.password_hash[-16:]}

    @staticmethod
    def _serializer() -> URLSafeTimedSerializer:
        return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="password-reset")
