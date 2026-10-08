import pytest
from flask import Flask

from app import create_app
from tests.conftest import MakeApp


def test_missing_secret_key_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FLASK_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="FLASK_SECRET_KEY"):
        create_app()


def test_security_headers(app: Flask) -> None:
    headers = app.test_client().get("/api/health").headers
    assert "cdn.jsdelivr.net" in headers["Content-Security-Policy"]
    assert headers["X-Frame-Options"] == "SAMEORIGIN"


def test_force_https_redirects(make_app: MakeApp) -> None:
    app = make_app(FORCE_HTTPS=True)
    response = app.test_client().get("/api/health")
    assert response.status_code == 302
    assert response.location.startswith("https://")


def test_shell_context(app: Flask) -> None:
    with app.app_context():
        context = app.make_shell_context()
    assert {"db", "sa", "User", "Item"} <= context.keys()
