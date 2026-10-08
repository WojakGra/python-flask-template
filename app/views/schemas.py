from flask_marshmallow.fields import URLFor
from flask_marshmallow.sqla import SQLAlchemyAutoSchema
from marshmallow import fields

from app.models import Item


class ItemSchema(SQLAlchemyAutoSchema):
    """JSON view of an Item. Loading accepts only `title`; the rest is read-only."""

    class Meta:
        model = Item
        include_fk = True
        dump_only = ("id", "created_at", "user_id")

    url = URLFor("api.get_item", values={"item_id": "<id>"}, dump_only=True)
    created_at = fields.AwareDateTime(dump_only=True)
