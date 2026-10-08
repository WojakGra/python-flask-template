import pytest
from flask.testing import FlaskClient

from app.extensions import limiter, mail
from tests.conftest import EMAIL, PASSWORD, MakeApp


def test_register_logs_in(client: FlaskClient) -> None:
    response = client.post(
        "/auth/register",
        data={"email": EMAIL, "password": PASSWORD, "password2": PASSWORD},
        follow_redirects=True,
    )
    assert EMAIL in response.text


def test_register_duplicate_email_shows_form_error(client: FlaskClient, user: str) -> None:
    response = client.post(
        "/auth/register", data={"email": user, "password": PASSWORD, "password2": PASSWORD}
    )
    assert "already registered" in response.text


def test_login_rejects_wrong_password(client: FlaskClient, user: str) -> None:
    response = client.post("/auth/login", data={"email": user, "password": "nope"})
    assert "Invalid email or password" in response.text


@pytest.mark.parametrize(
    ("next_url", "expected"),
    [
        ("/items?page=2", "/items?page=2"),
        ("//evil.com", "/"),
        ("/\\evil.com", "/"),
        ("https://evil.com/", "/"),
    ],
)
def test_login_redirects_only_to_local_next(
    client: FlaskClient, user: str, next_url: str, expected: str
) -> None:
    response = client.post(
        "/auth/login", query_string={"next": next_url}, data={"email": user, "password": PASSWORD}
    )
    assert response.status_code == 302
    assert response.location == expected


def test_logout(auth_client: FlaskClient) -> None:
    assert (
        auth_client.get("/auth/logout").status_code == 405
    )  # POST only, so links can't log you out
    auth_client.post("/auth/logout")
    assert EMAIL not in auth_client.get("/").text


def test_password_reset_flow(client: FlaskClient, user: str) -> None:
    with mail.record_messages() as outbox:
        client.post("/auth/reset", data={"email": user})
    reset_path = str(outbox[0].body).split("http://localhost", 1)[1].split()[0]

    assert client.get(reset_path).status_code == 200
    client.post(reset_path, data={"password": "brand new pass", "password2": "brand new pass"})

    response = client.post("/auth/login", data={"email": user, "password": "brand new pass"})
    assert response.status_code == 302
    assert client.get(reset_path).status_code == 302  # link is single-use


def test_unknown_email_gets_same_reset_message(client: FlaskClient) -> None:
    response = client.post(
        "/auth/reset", data={"email": "nobody@example.com"}, follow_redirects=True
    )
    assert "If that email is registered" in response.text


def test_csrf_is_enforced(make_app: MakeApp) -> None:
    app = make_app(WTF_CSRF_ENABLED=True)
    response = app.test_client().post("/auth/login", data={"email": EMAIL, "password": PASSWORD})
    assert response.status_code == 400
    assert "CSRF" in response.text


def test_login_is_rate_limited(make_app: MakeApp) -> None:
    app = make_app(RATELIMIT_ENABLED=True)
    with app.app_context():
        limiter.reset()
    client = app.test_client()
    codes = [
        client.post("/auth/login", data={"email": EMAIL, "password": "x"}).status_code
        for _ in range(11)
    ]
    assert codes[-1] == 429
    assert 429 not in codes[:10]


def test_remember_me_sets_cookie(client: FlaskClient, user: str) -> None:
    client.post("/auth/login", data={"email": user, "password": PASSWORD, "remember_me": "y"})
    assert client.get_cookie("remember_token") is not None
