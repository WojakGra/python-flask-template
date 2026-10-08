from typing import Any

from sqlalchemy.orm import Session, scoped_session

# Services take the session in their constructor: db.session in the app, any session in tests.
DbSession = Session | scoped_session[Any]


class ValidationError(ValueError):
    """Invalid input rejected by a service.

    Controllers turn it into a 400 response or a form error.
    """
