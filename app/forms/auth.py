from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

from app.services.auth_service import MIN_PASSWORD_LENGTH


class LoginForm(FlaskForm):
    email = EmailField(_l("Email"), validators=[DataRequired(), Email()])
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    remember_me = BooleanField(_l("Remember me"))
    submit = SubmitField(_l("Sign in"))


class RegisterForm(FlaskForm):
    email = EmailField(_l("Email"), validators=[DataRequired(), Email(), Length(max=254)])
    password = PasswordField(
        _l("Password"), validators=[DataRequired(), Length(min=MIN_PASSWORD_LENGTH)]
    )
    password2 = PasswordField(
        _l("Repeat password"), validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField(_l("Register"))


class ResetRequestForm(FlaskForm):
    email = EmailField(_l("Email"), validators=[DataRequired(), Email()])
    submit = SubmitField(_l("Send reset link"))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        _l("New password"), validators=[DataRequired(), Length(min=MIN_PASSWORD_LENGTH)]
    )
    password2 = PasswordField(
        _l("Repeat password"), validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField(_l("Set password"))
