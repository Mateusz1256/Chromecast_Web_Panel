# Changelog

All notable changes to this project are documented in this file.

The format is based on Keep a Changelog, and the project uses Semantic
Versioning.

## [Unreleased]

### Added

- Project documentation and staged implementation plan.
- Python 3.8 compatible Flask application bootstrap with `/health`.
- pytest, Ruff, rotated application logging and pinned dependency files.
- `THIRD_PARTY_NOTICES.md`.
- `CastService` with mockable adapter, timeout, reconnect, command lock,
  standardized status payloads and domain exceptions.
- Local administrator login with Flask-Login, `init-admin` CLI command, password
  hashing, CSRF and persistent settings in `instance/config.json`.
- Settings validation for IP addresses, ports, paths, upload limits, volume
  limits and timeouts, plus secret-free import/export.
- Authenticated Cast status dashboard with polling.
- Media library with upload, preview, deletion, safe public media endpoint,
  local Cast URL generation and image display.
- Remote controls with backend-enforced volume limits, mute/unmute, play, pause,
  stop, seek, refreshed status after commands and rate limiting.
- Audio and video upload/playback for MP3/AAC/M4A/OGG/WAV and MP4/WebM.
- Slideshow, media queue and presets with one active in-memory playback job.
- Rotated JSONL audit logs, recent-error panel and optional active app change
  monitoring disabled by default.
- Script-based deployment helpers for start, stop and backup.
- Version `1.0.0`, strong secret key validation, secure session defaults,
  versioned settings migration, secret-free diagnostics export, restore script,
  user guide, developer guide and release checklist.
- Sidebar-based Polish UI, separate Status and Pilot views, theme toggle and
  Cast app close command.
- English interface language option with client-side translations.

### Changed

- Public docs and descriptions are now English and platform-neutral.
- `.env.example` uses placeholders instead of host-specific paths or IPs.
- Local agent prompt files, task notes and diagnostics are ignored and no longer
  tracked.
- Status, media and settings screens use consistent Polish labels.
- Theme selection moved from the sidebar to Settings as a slider control.
- Selected upload file names now render on one line in the Media view.

### Fixed

- Load `.env` before application configuration reads environment variables.
- Settings form labels and loading/status messages now follow the selected
  interface language.
- Settings label now describes the media URL host as the server LAN IP address
  instead of a NAS-specific address.
