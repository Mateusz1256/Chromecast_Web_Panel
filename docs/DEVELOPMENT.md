# Development

## Setup

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

## Test And Lint

```sh
python -m pytest
python -m ruff check .
```

The automated tests use mocks for Cast access and do not require a physical
device.

## Python Compatibility

The project targets Python 3.8 compatible syntax and pinned dependencies.
Avoid:

- `str | None`;
- `match`;
- unpinned dependency upgrades without checking Python 3.8 support.

## Architecture

- `app/services/cast_service.py` isolates `pychromecast`.
- `app/services/media_service.py` validates and serves local media.
- `app/services/settings_service.py` owns persisted user settings.
- `app/services/playback_service.py` owns in-memory slideshow/queue jobs.
- `app/services/audit_service.py` writes sanitized JSONL audit entries.
- Blueprints expose authenticated UI and JSON endpoints.

## Security Review Notes

- User-supplied filenames are sanitized and resolved under the media directory.
- Shell scripts do not consume browser/user request data.
- CSRF is enabled for forms and JSON commands.
- A placeholder `SECRET_KEY` is rejected when `REQUIRE_STRONG_SECRET=1`.
- Audit logs redact sensitive keys and avoid media titles/content IDs.

