import pytest

from app.extensions import db
from app.models import User
from app.services import ValidationError
from app.services.auth_service import AuthService
from app.services.item_service import ItemService
from tests.conftest import EMAIL, PASSWORD

pytestmark = pytest.mark.usefixtures("ctx")


@pytest.fixture
def author() -> User:
    return AuthService(db.session).register(EMAIL, PASSWORD)


def test_create_strips_title_and_sets_author(author: User) -> None:
    item = ItemService(db.session).create("  Buy milk  ", author)
    assert item.id is not None
    assert item.title == "Buy milk"
    assert item.author == author


@pytest.mark.parametrize("title", ["", "   ", "x" * 201])
def test_create_rejects_invalid_title(author: User, title: str) -> None:
    with pytest.raises(ValidationError):
        ItemService(db.session).create(title, author)


def test_page_is_newest_first(author: User) -> None:
    service = ItemService(db.session)
    for title in ["first", "second", "third"]:
        service.create(title, author)

    page = service.page(1, per_page=2)
    assert [item.title for item in page.items] == ["third", "second"]
    assert page.pages == 2
    assert service.page(9, per_page=2).items == []  # out of range: empty, not 404
