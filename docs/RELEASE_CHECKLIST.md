# Release Checklist

Use this checklist before tagging a release.

## Version

- App version is set in `app/version.py`.
- `CHANGELOG.md` has the release notes.
- Public documentation is current.

## Validation

```sh
python -m pytest
python -m ruff check .
python -m pip install --dry-run --ignore-installed --python-version 3.8 --only-binary=:all: -r requirements.txt
```

## Security

- `.env` is not committed.
- `SECRET_KEY` is not a placeholder.
- `SESSION_COOKIE_SECURE=1` is used when serving over HTTPS.
- The panel is kept on a trusted network or private VPN.
- `max_volume` is conservative.
- `monitor_app_changes` is enabled only if explicitly wanted.
- Audit logs do not contain passwords, tokens, cookies, full media URLs,
  media titles or `content_id`.

## Backup And Restore

```sh
scripts/backup.sh
scripts/restore.sh backups/<archive>.tar.gz
```

Restore should be tested on a separate copy of the application directory before
using it on the live instance.

## Dependencies And Licenses

- `requirements.txt` and `requirements-dev.txt` are pinned.
- `THIRD_PARTY_NOTICES.md` reflects the declared packages and licenses.

## Tag

```sh
git status --short
git tag -a v1.0.0 -m "v1.0.0"
```
