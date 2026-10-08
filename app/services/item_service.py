from flask_babel import gettext as _
from flask_sqlalchemy.pagination import Pagination, SelectPagination
from sqlalchemy import select

from app.models import Item, User
from app.services import DbSession, ValidationError


class ItemService:
    def __init__(self, session: DbSession) -> None:
        self.session = session

    def page(self, page: int, per_page: int) -> Pagination:
        """Items newest first. Out-of-range pages are empty instead of 404."""
        query = select(Item).order_by(Item.id.desc())
        return SelectPagination(
            select=query, session=self.session, page=page, per_page=per_page, error_out=False
        )

    def create(self, title: str, author: User) -> Item:
        title = title.strip()
        if not title or len(title) > 200:
            raise ValidationError(_("Title must be 1 to 200 characters long."))

        item = Item(title=title, author=author)
        self.session.add(item)
        self.session.commit()
        return item
