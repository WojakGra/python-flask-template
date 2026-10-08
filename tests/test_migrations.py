from pathlib import Path

import flask_migrate
import pytest

from tests.conftest import MakeApp

VERSIONS = Path(__file__).parents[1] / "migrations" / "versions"


@pytest.mark.skipif(
    not any(VERSIONS.glob("*.py")),
    reason='no migrations yet, run: uv run poe db-init, then uv run poe migration -m "init"',
)
def test_migrations_apply_and_match_models(make_app: MakeApp) -> None:
    app = make_app(schema=False)
    with app.app_context():
        flask_migrate.upgrade()
        flask_migrate.check()  # exits non-zero if models changed without a migration
        flask_migrate.downgrade(revision="base")
