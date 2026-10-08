import pytest
from flask.testing import FlaskClient

from tests.conftest import MakeApp


def test_health(client: FlaskClient) -> None:
    response = client.get("/api/health")
    assert response.json == {"status": "ok"}


def test_create_requires_login(client: FlaskClient) -> None:
    response = client.post("/api/items", json={"title": "x"})
    assert response.status_code == 401
    assert response.json is not None
    assert response.json["error"] == "Unauthorized"


def test_create_get_and_list(auth_client: FlaskClient) -> None:
    response = auth_client.post("/api/items", json={"title": " Buy milk "})
    assert response.status_code == 201
    item = response.json
    assert item is not None
    assert item["title"] == "Buy milk"
    assert item["url"] == f"/api/items/{item['id']}"

    assert auth_client.get(item["url"]).json == item
    listing = auth_client.get("/api/items").json
    assert listing == {"items": [item], "meta": {"page": 1, "pages": 1, "total": 1}}


def test_missing_title_lists_field_errors(auth_client: FlaskClient) -> None:
    response = auth_client.post("/api/items", json={})
    assert response.status_code == 400
    assert response.json is not None
    assert "title" in response.json["fields"]


@pytest.mark.parametrize("payload", [{"title": "   "}, {"title": "x" * 201}, {"title": 5}])
def test_invalid_title_is_400(auth_client: FlaskClient, payload: object) -> None:
    assert auth_client.post("/api/items", json=payload).status_code == 400


def test_non_json_is_415(auth_client: FlaskClient) -> None:
    assert auth_client.post("/api/items", data="title=x").status_code == 415


def test_unknown_item_is_json_404(client: FlaskClient) -> None:
    response = client.get("/api/items/999")
    assert response.status_code == 404
    assert response.json is not None


def test_cors_only_for_configured_origins(make_app: MakeApp, client: FlaskClient) -> None:
    origin = {"Origin": "https://app.example.com"}
    assert "Access-Control-Allow-Origin" not in client.get("/api/health", headers=origin).headers

    app = make_app(CORS_ORIGINS=["https://app.example.com"])
    response = app.test_client().get("/api/health", headers=origin)
    assert response.headers["Access-Control-Allow-Origin"] == "https://app.example.com"
