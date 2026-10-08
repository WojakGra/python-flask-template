from typing import Any

import marshmallow
from flask import Blueprint, render_template, request
from werkzeug.exceptions import BadRequest, HTTPException

from app.extensions import db
from app.services import ValidationError

bp = Blueprint("errors", __name__)


@bp.app_errorhandler(HTTPException)
def http_error(e: HTTPException) -> tuple[str | dict[str, Any], int]:
    code = e.code or 500
    if code >= 500:
        db.session.rollback()
    if request.path.startswith("/api/"):
        return {"error": e.name, "message": e.description}, code
    return render_template("errors/error.html", error=e), code


@bp.app_errorhandler(ValidationError)
def validation_error(e: ValidationError) -> tuple[str | dict[str, Any], int]:
    return http_error(BadRequest(str(e)))


@bp.app_errorhandler(marshmallow.ValidationError)
def schema_error(e: marshmallow.ValidationError) -> tuple[str | dict[str, Any], int]:
    response, code = http_error(BadRequest())
    if isinstance(response, dict):
        response["fields"] = e.messages
    return response, code
