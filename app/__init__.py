import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from flask import Flask
from flask_babel import get_locale
from werkzeug.middleware.proxy_fix import ProxyFix

from app import extensions
from app.config import Config
from app.controllers import api, auth, cli, errors, web
from app.extensions import db
from app.models import Item, User


def create_app(test_config: Mapping[str, Any] | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True, template_folder="views/templates")
    app.config.from_object(Config)
    # FLASK_SECRET_KEY -> SECRET_KEY, FLASK_SQLALCHEMY_DATABASE_URI -> SQLALCHEMY_DATABASE_URI, ...
    app.config.from_prefixed_env()
    if test_config:
        app.config.from_mapping(test_config)
    if not app.config["SECRET_KEY"]:
        raise RuntimeError("FLASK_SECRET_KEY is not set (see .env.example)")
    if not app.config["SQLALCHEMY_DATABASE_URI"]:
        Path(app.instance_path).mkdir(exist_ok=True)
        db_path = (Path(app.instance_path) / "app.db").as_posix()
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["REMEMBER_COOKIE_SECURE"] = app.config["FORCE_HTTPS"]

    if proxies := app.config["PROXY_COUNT"]:
        app.wsgi_app = ProxyFix(  # type: ignore[method-assign]
            app.wsgi_app, x_for=proxies, x_proto=proxies, x_host=proxies, x_prefix=proxies
        )
    if not app.debug and not app.testing:
        app.logger.setLevel(logging.INFO)

    extensions.init_app(app)
    for controller in (web, auth, api, errors, cli):
        app.register_blueprint(controller.bp)

    app.context_processor(lambda: {"current_locale": get_locale})
    app.shell_context_processor(lambda: {"sa": sa, "db": db, "User": User, "Item": Item})
    return app
