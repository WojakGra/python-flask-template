# Contributing

Thanks for helping out. Bug reports, fixes and small improvements are all welcome.

## Before you start

- For anything bigger than a small fix, open an issue first so we can agree on the approach.
- Security problems go through [SECURITY.md](SECURITY.md), not public issues.
- By taking part you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Setup

You need [uv](https://docs.astral.sh/uv/getting-started/installation/). Then:

```sh
uv sync
uv run pre-commit install
uv run poe dev
```

See the [README](README.md) for Docker, mail and translations.

## Making a change

1. Fork the repo and create a branch from `master`.
2. Make the change. Add or update tests in `tests/` when behaviour changes.
3. If you changed models, add a migration: `uv run poe migration -m "short description"`.
4. If you added or changed user-facing text, run `uv run poe i18n-extract` and `uv run poe i18n-update`, then fill in the Polish translation.
5. Run the checks:

   ```sh
   uv run poe fmt     # fix lint issues and format
   uv run poe check   # ruff + mypy (strict)
   uv run poe test
   ```

6. Open a pull request and fill in the template.

## Commits and pull requests

- Keep each pull request to one topic.
- Write commit messages in the imperative mood: "Add password strength check", not "Added ...".
