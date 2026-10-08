import click
from flask import Blueprint

from app.extensions import db
from app.services import ValidationError
from app.services.auth_service import AuthService

# cli_group=None: commands appear at the top level, e.g. `flask create-user`.
bp = Blueprint("cli", __name__, cli_group=None)


@bp.cli.command("create-user")
@click.argument("email")
@click.password_option()
def create_user(email: str, password: str) -> None:
    """Create a user account."""
    try:
        user = AuthService(db.session).register(email, password)
    except ValidationError as e:
        raise click.ClickException(str(e)) from e
    click.echo(f"Created user {user.email}")
