from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from app.extensions import db
from app.services.auth_service import AuthService

EMAIL = "ann@example.com"
PASSWORD = "correct horse"


MakeApp = Callable[..., Flask]


@pytest.fixture
def make_app(tmp_path: Path) -> Iterator[MakeApp]:
    """App factory with test defaults and an empty SQLite schema.

    `make_app(KEY=value)` overrides config keys; `schema=False` leaves the database empty.
    """
    apps: list[Flask] = []

    def factory(schema: bool = True, **overrides: object) -> Flask:
        app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test",
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
                "WTF_CSRF_ENABLED": False,  # test_auth.py checks CSRF separately
                "RATELIMIT_ENABLED": False,  # test_auth.py checks the limiter separately
                **overrides,
            }
        )
        if schema:
            with app.app_context():
                db.create_all()
        apps.append(app)
        return app

    yield factory
    for app in apps:  # close pooled SQLite connections
        with app.app_context():
            db.engine.dispose()


@pytest.fixture
def app(make_app: MakeApp) -> Flask:
    return make_app()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture
def ctx(app: Flask) -> Iterator[None]:
    """Request context for calling services directly (they use url_for, gettext, templates)."""
    with app.test_request_context():
        yield


@pytest.fixture
def user(app: Flask) -> str:
    with app.test_request_context():
        AuthService(db.session).register(EMAIL, PASSWORD)
    return EMAIL


@pytest.fixture
def auth_client(client: FlaskClient, user: str) -> FlaskClient:
    client.post("/auth/login", data={"email": user, "password": PASSWORD})
    return client
