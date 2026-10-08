from typing import Any

from flask import Blueprint, current_app, request
from flask_login import current_user, login_required
from sqlalchemy import text

from app.extensions import db
from app.models import Item
from app.services.item_service import ItemService
from app.views.schemas import ItemSchema

bp = Blueprint("api", __name__, url_prefix="/api")
item_schema = ItemSchema()


@bp.get("/health")
def health() -> dict[str, str]:
    db.session.execute(text("SELECT 1"))
    return {"status": "ok"}


@bp.get("/items")
def list_items() -> dict[str, Any]:
    page = ItemService(db.session).page(
        request.args.get("page", 1, type=int), current_app.config["ITEMS_PER_PAGE"]
    )
    return {
        "items": item_schema.dump(page.items, many=True),
        "meta": {"page": page.page, "pages": page.pages, "total": page.total},
    }


@bp.get("/items/<int:item_id>")
def get_item(item_id: int) -> dict[str, Any]:
    data: dict[str, Any] = item_schema.dump(db.get_or_404(Item, item_id))
    return data


@bp.post("/items")
@login_required
def create_item() -> tuple[dict[str, Any], int]:
    # Raises marshmallow.ValidationError on bad input; controllers/errors.py turns it into a 400.
    data = item_schema.load(request.get_json())
    item = ItemService(db.session).create(data["title"], current_user)
    created: dict[str, Any] = item_schema.dump(item)
    return created, 201
