# python-flask-template

A batteries-included Flask starter: login, registration and password reset, an HTML UI with Bootstrap and htmx, a JSON API, Polish and English, migrations, and Docker Compose with Postgres and a mail catcher. It runs on Linux and Windows.

Stack: Python 3.14, Flask 3.1, SQLAlchemy 2.1, uv, Poe the Poet, pytest, ruff, mypy (strict), pre-commit.

## Quick start

Install [uv](https://docs.astral.sh/uv/getting-started/installation/):

```sh
# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then, the same in bash and PowerShell:

```sh
uv sync                          # .venv with app + dev dependencies
uv run poe db-init               # once per project: creates migrations/
uv run poe migration -m "init"   # first migration from the models
uv run poe dev                   # creates .env, migrates, serves http://127.0.0.1:5000 with auto-reload
```

Local runs use SQLite in `instance/app.db`. The debug toolbar shows up on every page in dev mode.

To see password reset emails, start Mailpit (needs Docker) and open http://localhost:8025:

```sh
uv run poe mail
```

## Docker

```sh
uv run poe up     # docker compose up --build, app on http://localhost:8000
uv run poe down
```

Run `db-init` and the first `migration` before the first `up`. The image runs whatever is in `migrations/versions/`.

Compose starts:

| service   | what it does                                     |
| --------- | ------------------------------------------------ |
| `db`      | Postgres 18, also on `localhost:5432`            |
| `mailpit` | catches all mail, inbox on http://localhost:8025 |
| `migrate` | runs `flask db upgrade` once and exits           |
| `web`     | gunicorn, starts after `migrate` succeeds        |

`FLASK_SECRET_KEY` comes from `.env`. The Postgres credentials in `compose.yaml` (`app`/`app`) are for local use only. Set the gunicorn worker count with `WEB_CONCURRENCY`.

To run the app locally against the compose database, start `docker compose up -d db` and set `FLASK_SQLALCHEMY_DATABASE_URI=postgresql+psycopg://app:app@localhost:5432/app` in `.env`.

## Commands

Every task runs as `uv run poe <task>`. Poe the Poet is a dev dependency, so nothing else needs installing, and the tasks work the same on Linux and Windows. `uv run poe` with no task lists them all.

| task                                                             | runs                                                 |
| ---------------------------------------------------------------- | ---------------------------------------------------- |
| `dev`                                                            | `prepare`, then `flask run --debug`                  |
| `prepare`                                                        | `setup`, `migrate`                                   |
| `setup`                                                          | copies `.env.example` to `.env` if `.env` is missing |
| `test`                                                           | `pytest`                                             |
| `check`                                                          | `ruff check .`, `ruff format --check .`, `mypy`      |
| `fmt`                                                            | `ruff check --fix .`, `ruff format .`                |
| `db-init`                                                        | `flask db init` (once per project)                   |
| `migration -m "..."`                                             | `flask db migrate -m "..."`                          |
| `migrate`                                                        | `flask db upgrade`                                   |
| `i18n-extract`, `i18n-update`, `i18n-compile`, `i18n-init -l xx` | translation workflow, see below                      |
| `mail`                                                           | `docker compose up -d mailpit`                       |
| `up` / `down`                                                    | `docker compose up --build` / `docker compose down`  |

Other useful commands: `uv run flask shell` (has `db`, `sa`, `User`, `Item` loaded), `uv run flask routes`, `uv run flask create-user EMAIL`, `uv add <package>`, `uv lock --upgrade`.

VS Code: accept the recommended extensions when prompted. Python files get ruff on save, mypy and pytest show up in the editor and the Testing panel, and F5 ("Flask") runs `prepare` and then the app under the debugger, breakpoints in templates included.

Enable the git hooks once per clone with `uv run pre-commit install`. They run `uv lock --check`, ruff and mypy through `uv run`, so tool versions come from `uv.lock`.

## Configuration

Defaults live in `app/config.py`. Every `FLASK_<KEY>` environment variable overrides config key `<KEY>`, and values are parsed as JSON where possible (`true`, `5`, `["a"]`). The `flask` CLI loads `.env`. Gunicorn does not, so in production set real environment variables.

| variable                                                           | default                     | notes                                                                  |
| ------------------------------------------------------------------ | --------------------------- | ---------------------------------------------------------------------- |
| `FLASK_SECRET_KEY`                                                 | none                        | Required. The app refuses to start without it.                         |
| `FLASK_SQLALCHEMY_DATABASE_URI`                                    | SQLite in `instance/app.db` | e.g. `postgresql+psycopg://user:pass@host/db`                          |
| `FLASK_MAIL_SERVER`, `_PORT`, `_USE_TLS`, `_USERNAME`, `_PASSWORD` | Mailpit on `localhost:1025` | Flask-Mail settings                                                    |
| `FLASK_FORCE_HTTPS`                                                | `false`                     | Redirect to HTTPS, secure cookies. Use behind a TLS proxy.             |
| `FLASK_PROXY_COUNT`                                                | `0`                         | Number of proxies in front of the app (enables `ProxyFix`)             |
| `FLASK_CORS_ORIGINS`                                               | `[]`                        | Browser origins allowed to call `/api/*`                               |
| `FLASK_RATELIMIT_STORAGE_URI`                                      | `memory://`                 | Use `redis://...` with several workers, `memory://` counts per process |
| `FLASK_ITEMS_PER_PAGE`                                             | `10`                        |                                                                        |

## Architecture

The code is split into Model, View, Controller and Service layers, plus forms. A request goes from a controller to a service to the models, and the controller hands the result to a view.

```
app/
  __init__.py        create_app(): config, extensions, controllers, shell context
  config.py          defaults for every config key
  extensions.py      all Flask extensions in one place, init_app(), locale selection
  models/            Model: SQLAlchemy tables (User, Item)
  services/          Service: business rules, queries, commits, emails
  forms/             WTForms: HTML form fields and validation
  controllers/       Controller: blueprints (web, auth, api, errors, cli)
  views/
    schemas.py       JSON views (marshmallow)
    templates/       HTML views (Jinja + Bootstrap-Flask macros)
  translations/      Polish catalog (.po source, compiled .mo)
tests/               one file per layer
```

| layer      | does                                                              | does not                           |
| ---------- | ----------------------------------------------------------------- | ---------------------------------- |
| Controller | reads the request, calls a service, picks a view, sets the status | run queries or hold business rules |
| Service    | enforces rules, queries, commits, sends mail                      | touch `request` or build responses |
| Model      | defines tables and relationships                                  | know about JSON or HTML            |
| View       | turns models into HTML or JSON                                    | change data                        |
| Form       | checks the shape of HTML input, renders fields                    | hold business rules                |

Services take the session in their constructor (`ItemService(db.session)`), so tests can call them without HTTP. A service raises `ValidationError` for bad input. Controllers show it as a form error, and anything uncaught becomes a 400 (JSON under `/api/`, an HTML page elsewhere).

Models inherit from `Base` in `app/extensions.py`. It shares its registry with `db.Model`, so `db.session`, `db.paginate` and Flask-Migrate work the same, but mypy can see the model types.

`User` and `Item` are working examples that go through every layer. Replace `Item` with your own resources.

### Adding a resource

1. Model: `app/models/order.py`, then import it in `app/models/__init__.py`. Flask-Migrate only sees models imported there.
2. Service: `app/services/order_service.py` with an `OrderService(session)` class.
3. Form: `app/forms/order.py` if there is an HTML form.
4. Views: a schema in `app/views/schemas.py`, templates in `app/views/templates/orders/`.
5. Controller: routes in `controllers/web.py` / `controllers/api.py`, or a new blueprint added to the loop in `create_app()`.
6. `uv run poe migration -m "add orders"`, review the file, `uv run poe migrate`.
7. Tests: `tests/test_order_service.py` for the rules, `tests/test_api.py` / `tests/test_web.py` for HTTP.

## Migrations

The template ships without a `migrations/` folder. Create it and the first migration yourself:

```sh
uv run poe db-init
uv run poe migration -m "init"
```

Commit `migrations/` in your project, including every file in `migrations/versions/`. Migrations are the shared history of the schema. Every developer, the tests and production apply the same files, and the `migrate` container runs exactly what is committed. If each developer generated their own, revision IDs would differ and databases would drift apart.

After changing models, run `uv run poe migration -m "describe the change"`, review the generated file, and commit it. `tests/test_migrations.py` applies all migrations to an empty database and fails when the models have changes that no migration covers. It is skipped until the first migration exists.

Ruff skips `migrations/` because the files are generated. SQLite needs batch mode for `ALTER TABLE`, which `app/extensions.py` enables.

## Auth and security

- Login, registration, logout and password reset are in `controllers/auth.py` and `services/auth_service.py`. Passwords are hashed with Werkzeug (scrypt).
- Reset links expire after 30 minutes and stop working once the password changes. The reset page shows the same message whether or not the email exists.
- `next=` redirects after login only go to paths on this site.
- Every POST needs a CSRF token. Forms include it, htmx sends it from `hx-headers` on `<body>`, and JSON clients send it as `X-CSRFToken`. Logout is POST only.
- The API uses the login session. `POST /api/items` returns 401 without it.
- Auth form submissions are limited to 10 per minute per IP (Flask-Limiter).
- Talisman sets a Content-Security-Policy (scripts and styles only from this site and jsDelivr), `X-Frame-Options`, `X-Content-Type-Options` and `Referrer-Policy`. CSP is off in debug mode because the debug toolbar injects inline scripts.
- In production behind a TLS proxy, set `FLASK_FORCE_HTTPS=true` and `FLASK_PROXY_COUNT=1`.

## Translations

The UI detects the language from the browser and has a switcher in the navbar. Mark strings with `_()` in templates and services and `_l()` in forms, then:

```sh
uv run poe i18n-extract    # scan code into messages.pot
uv run poe i18n-update     # merge into app/translations/*/messages.po
# translate the new entries in the .po files
uv run poe i18n-compile    # build .mo files (commit them too)
```

Add a language with `uv run poe i18n-init -l de` and add `"de"` to `LANGUAGES` in `app/config.py`.

## Testing

`uv run poe test`. Each test gets its own SQLite file. The `make_app(KEY=value)` fixture builds an app with overridden config, which the tests use for CSRF, rate limits, CORS and HTTPS. Mail is never sent in tests: `mail.record_messages()` collects it instead. Warnings fail the run, except two known ones from Flask-Login and the generated `env.py`, listed in `pyproject.toml`.

## Why these extensions

Checked against PyPI and GitHub in October 2026.

| extension                                  | status                                                                                               | here                                                                                                                           |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Flask-SQLAlchemy 3.1                       | maintenance mode, last release 2023. Breaks with SQLAlchemy 2.1 only for `MappedAsDataclass` (#1420) | used, tested on SQLAlchemy 2.1. Don't use `MappedAsDataclass`. Flask-SQLAlchemy-Lite is the maintainer's recommended successor |
| Flask-Migrate                              | maintained                                                                                           | used                                                                                                                           |
| WTForms + Flask-WTF                        | active                                                                                               | used for forms and CSRF                                                                                                        |
| Flask-Login 0.6.3                          | last release 2023, works, emits a `utcnow()` deprecation warning                                     | used (Flask-Security builds on it too)                                                                                         |
| Flask-Mail                                 | maintained                                                                                           | used for reset emails                                                                                                          |
| Flask-Marshmallow + marshmallow-sqlalchemy | active                                                                                               | used for API schemas and input validation                                                                                      |
| Bootstrap-Flask                            | active                                                                                               | used for form, flash and pagination macros                                                                                     |
| Flask-Babel 4.0                            | last release 2023, works                                                                             | used                                                                                                                           |
| Flask-Cors, Flask-Compress, Flask-Limiter  | active                                                                                               | used                                                                                                                           |
| Flask-Talisman 1.1                         | no release since 2023, only sets headers                                                             | used, replaces Flask-SSLify                                                                                                    |
| Flask-DebugToolbar                         | maintained                                                                                           | dev dependency, debug mode only                                                                                                |
| Flask-Security                             | active                                                                                               | not used: the custom auth here is smaller. Switch to it for roles, 2FA or email confirmation                                   |
| Flask-SSLify                               | dead since 2015                                                                                      | replaced by Talisman + ProxyFix                                                                                                |
| Flask-Bcrypt                               | dead, breaks with bcrypt 5                                                                           | not needed: Werkzeug hashes with scrypt                                                                                        |
| Flask-Testing                              | dead, live server broken since Werkzeug 2.1                                                          | not needed: pytest + `app.test_client()`                                                                                       |
| Flask-Assets, Flask-Static-Compress        | dead or nearly                                                                                       | not needed: Bootstrap and htmx load from a CDN with SRI, Flask-Compress handles compression                                    |

## Using this as a template

1. Change `name` and `description` in `pyproject.toml`, then `uv lock`.
2. Change `image:` in `compose.yaml` and `MAIL_DEFAULT_SENDER` in `app/config.py`.
3. Replace the `Item` example (model, service, form, schema, templates, routes, tests).
4. `uv run poe db-init`, `uv run poe migration -m "init"`, commit `migrations/`.

The package is named `app`, so no imports need renaming.
