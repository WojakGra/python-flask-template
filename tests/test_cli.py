from flask import Flask

from app.extensions import db
from app.models import User


def test_create_user(app: Flask) -> None:
    runner = app.test_cli_runner()
    args = ["create-user", "cli@example.com", "--password", "long enough"]

    result = runner.invoke(args=args)
    assert result.exit_code == 0, result.output
    with app.app_context():
        assert db.session.query(User).filter_by(email="cli@example.com").count() == 1

    duplicate = runner.invoke(args=args)
    assert duplicate.exit_code == 1
    assert "already registered" in duplicate.output
