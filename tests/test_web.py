from flask.testing import FlaskClient

from tests.conftest import EMAIL, PASSWORD, MakeApp

HTMX = {"HX-Request": "true"}


def test_anonymous_index_has_no_form(client: FlaskClient) -> None:
    html = client.get("/").text
    assert "No items yet" in html
    assert 'name="title"' not in html


def test_htmx_create_returns_fragment(auth_client: FlaskClient) -> None:
    response = auth_client.post("/items", data={"title": "<b>first</b>"}, headers=HTMX)
    assert response.status_code == 200
    assert "<html" not in response.text  # just the #items fragment
    assert "&lt;b&gt;first&lt;/b&gt;" in response.text  # autoescaped
    assert "Item added" in response.text
    assert 'value="&lt;b&gt;first' not in response.text  # title input cleared


def test_htmx_invalid_create_shows_error(auth_client: FlaskClient) -> None:
    response = auth_client.post("/items", data={"title": "   "}, headers=HTMX)
    assert response.status_code == 400
    assert "invalid-feedback" in response.text


def test_plain_form_create_redirects(auth_client: FlaskClient) -> None:
    response = auth_client.post("/items", data={"title": "first"})
    assert response.status_code == 302
    assert "Item added" in auth_client.get("/").text


def test_create_requires_login(client: FlaskClient) -> None:
    response = client.post("/items", data={"title": "first"})
    assert response.status_code == 302
    assert response.location.startswith("/auth/login")


def test_pagination(make_app: MakeApp) -> None:
    client = make_app(ITEMS_PER_PAGE=2).test_client()
    client.post(
        "/auth/register", data={"email": EMAIL, "password": PASSWORD, "password2": PASSWORD}
    )
    for title in ["one", "two", "three"]:
        client.post("/items", data={"title": title})

    assert "one" not in client.get("/").text
    assert "one" in client.get("/?page=2").text


def test_404_page_uses_layout(client: FlaskClient) -> None:
    response = client.get("/nope")
    assert response.status_code == 404
    assert "navbar" in response.text


def test_language_from_header_and_switcher(client: FlaskClient) -> None:
    assert "Zaloguj" in client.get("/", headers={"Accept-Language": "pl"}).text

    client.get("/lang/pl")
    assert "Zaloguj" in client.get("/").text
    client.get("/lang/en")
    assert "Sign in" in client.get("/", headers={"Accept-Language": "pl"}).text


def test_language_switch_ignores_external_next(client: FlaskClient) -> None:
    response = client.get("/lang/pl", query_string={"next": "//evil.com"})
    assert response.location == "/"
