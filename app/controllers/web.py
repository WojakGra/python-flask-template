from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_babel import gettext as _
from flask_login import current_user, login_required
from flask_sqlalchemy.pagination import Pagination
from werkzeug.wrappers import Response

from app.controllers import safe_next_url
from app.extensions import db
from app.forms.item import ItemForm
from app.services import ValidationError
from app.services.item_service import ItemService

bp = Blueprint("web", __name__)


def _items_page() -> Pagination:
    page = request.args.get("page", 1, type=int)
    return ItemService(db.session).page(page, current_app.config["ITEMS_PER_PAGE"])


@bp.get("/")
def index() -> str:
    return render_template("items/index.html", items=_items_page(), form=ItemForm())


@bp.post("/items")
@login_required
def create_item() -> str | Response | tuple[str, int]:
    form = ItemForm()
    if form.validate_on_submit():
        try:
            ItemService(db.session).create(form.title.data, current_user)
        except ValidationError as e:
            form.title.errors = [str(e)]
        else:
            flash(_("Item added."), "success")
            if request.headers.get("HX-Request"):
                # htmx swaps #items with this fragment: flash + empty form + updated list.
                # formdata=None: Flask-WTF would otherwise refill the form from the POST.
                return render_template(
                    "items/_list.html", items=_items_page(), form=ItemForm(formdata=None)
                )
            return redirect(url_for(".index"))

    template = "items/_list.html" if request.headers.get("HX-Request") else "items/index.html"
    return render_template(template, items=_items_page(), form=form), 400


@bp.get("/lang/<code>")
def set_language(code: str) -> Response:
    if code in current_app.config["LANGUAGES"]:
        session["lang"] = code
    return redirect(safe_next_url(request.args.get("next")) or url_for(".index"))
