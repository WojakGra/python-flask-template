from flask import Flask, current_app, has_request_context, request, session
from flask_babel import Babel
from flask_bootstrap import Bootstrap5
from flask_compress import Compress
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_mail import Mail
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from flask_wtf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base for models. Shares registry and metadata with db.Model, but type checkers can see it."""


db = SQLAlchemy(model_class=Base)
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
babel = Babel()
mail = Mail()
ma = Marshmallow()
cors = CORS()
compress = Compress()
limiter = Limiter(get_remote_address)
talisman = Talisman()
bootstrap = Bootstrap5()

# Bootstrap and htmx load from jsDelivr with SRI hashes (see base.html).
CSP = {
    "default-src": "'self'",
    "script-src": ["'self'", "https://cdn.jsdelivr.net"],
    "style-src": ["'self'", "https://cdn.jsdelivr.net"],
    "img-src": ["'self'", "data:"],
}


def select_locale() -> str | None:
    if not has_request_context():  # CLI, background code: default locale
        return None
    languages: list[str] = current_app.config["LANGUAGES"]
    if session.get("lang") in languages:
        return str(session["lang"])
    return request.accept_languages.best_match(languages)


def init_app(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)  # batch mode: ALTER TABLE works on SQLite
    login_manager.init_app(app)
    csrf.init_app(app)
    babel.init_app(app, locale_selector=select_locale)
    mail.init_app(app)
    ma.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    compress.init_app(app)
    limiter.init_app(app)
    bootstrap.init_app(app)
    force_https = app.config["FORCE_HTTPS"]
    talisman.init_app(
        app,
        force_https=force_https,
        session_cookie_secure=force_https,
        # The debug toolbar injects inline scripts, so CSP is off in debug mode only.
        content_security_policy=None if app.debug else CSP,
    )

    if app.debug:
        try:
            from flask_debugtoolbar import DebugToolbarExtension
        except ImportError:  # dev dependency, absent in the production image
            pass
        else:
            DebugToolbarExtension(app)
