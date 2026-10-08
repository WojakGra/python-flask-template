from typing import ClassVar


class Config:
    """Defaults. Override any key with a FLASK_<KEY> environment variable (see .env.example)."""

    SECRET_KEY: str | None = None  # required, no default on purpose
    SQLALCHEMY_DATABASE_URI: str | None = None  # None: SQLite in instance/app.db
    LANGUAGES: ClassVar[list[str]] = ["en", "pl"]
    ITEMS_PER_PAGE = 10
    PASSWORD_RESET_MAX_AGE = 30 * 60  # seconds

    # Mailpit from compose.yaml catches mail locally: http://localhost:8025
    MAIL_SERVER = "localhost"
    MAIL_PORT = 1025
    MAIL_DEFAULT_SENDER = "noreply@example.com"

    # Origins allowed to call /api/* from a browser, e.g. ["https://app.example.com"].
    CORS_ORIGINS: ClassVar[list[str]] = []
    # Behind a TLS-terminating proxy: FORCE_HTTPS=true and PROXY_COUNT=<number of proxies>.
    FORCE_HTTPS = False
    PROXY_COUNT = 0

    # memory:// counts per process. With several gunicorn workers use redis://...
    RATELIMIT_STORAGE_URI = "memory://"
    DEBUG_TB_INTERCEPT_REDIRECTS = False
