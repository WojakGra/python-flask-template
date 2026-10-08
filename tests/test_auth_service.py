import pytest

from app.extensions import db, mail
from app.services import ValidationError
from app.services.auth_service import AuthService
from tests.conftest import EMAIL, PASSWORD

pytestmark = pytest.mark.usefixtures("ctx")


def test_register_normalizes_email_and_hashes_password() -> None:
    user = AuthService(db.session).register("  Ann@Example.COM ", PASSWORD)
    assert user.email == EMAIL
    assert user.password_hash != PASSWORD
    assert user.check_password(PASSWORD)


def test_register_rejects_duplicate_email() -> None:
    service = AuthService(db.session)
    service.register(EMAIL, PASSWORD)
    with pytest.raises(ValidationError):
        service.register(EMAIL.upper(), PASSWORD)


def test_register_rejects_short_password() -> None:
    with pytest.raises(ValidationError):
        AuthService(db.session).register(EMAIL, "short")


def test_authenticate() -> None:
    service = AuthService(db.session)
    user = service.register(EMAIL, PASSWORD)
    assert service.authenticate(EMAIL, PASSWORD) == user
    assert service.authenticate(EMAIL, "wrong password") is None
    assert service.authenticate("nobody@example.com", PASSWORD) is None


def test_reset_token_works_once() -> None:
    service = AuthService(db.session)
    user = service.register(EMAIL, PASSWORD)
    token = service._serializer().dumps(service._token_payload(user))

    assert service.user_from_reset_token(token) == user
    service.reset_password(user, "new password")
    assert service.user_from_reset_token(token) is None  # old hash no longer matches
    assert service.user_from_reset_token(token + "x") is None


def test_send_password_reset_mails_only_existing_users() -> None:
    service = AuthService(db.session)
    service.register(EMAIL, PASSWORD)
    with mail.record_messages() as outbox:
        service.send_password_reset("nobody@example.com")
        service.send_password_reset(EMAIL)

    assert [m.recipients for m in outbox] == [[EMAIL]]
    assert "/auth/reset/" in str(outbox[0].body)
