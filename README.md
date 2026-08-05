# Cast Control Panel

A lightweight Flask web panel for controlling a local Google Cast or Android TV
device. It focuses on local media playback, device status, basic remote
controls, safe upload handling and a small admin UI.

## Features

- Device status dashboard with online/offline state, active app, volume, mute
  state and media status when the receiver exposes it.
- Local administrator account with hashed password, Flask sessions and CSRF.
- Persistent settings in `instance/config.json`.
- Image upload and casting for JPG/JPEG, PNG and WebP.
- Audio upload and playback for MP3, AAC/M4A, OGG and WAV.
- Video upload and playback for MP4 and WebM.
- Basic remote controls: volume, mute/unmute, play, pause, stop and seek.
- Slideshow, queue and presets.
- Rotated application logs and sanitized audit logs.
- Simple WSGI deployment with Waitress.

## Requirements

- Python 3.8 compatible runtime.
- `pip`.
- Network access from the host running the app to the Cast device, usually TCP
  8009.
- A LAN address for the app host that the Cast device can reach.
- A configured Cast device IP address. The app can connect with
  `known_hosts=[CAST_IP]` and does not rely only on mDNS.

## Installation

```bash
cd /path/to/cast-panel

python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set at least:

- `SECRET_KEY`
- `CAST_IP`
- `APP_HOST`
- `APP_PORT`
- `MEDIA_DIRECTORY`
- `LOG_DIRECTORY`
- `AUDIT_LOG_PATH`

Create the first administrator account:

```bash
flask --app wsgi:app init-admin
```

There is no default username or password.

## Run

Development:

```bash
python run.py
```

Local production-style run:

```bash
waitress-serve --host=0.0.0.0 --port=5000 wsgi:app
```

Health check:

```text
GET /health
```

Expected response:

```json
{"status": "ok"}
```

## Configuration

User-editable settings are stored in:

```text
instance/config.json
```

The local admin account is stored in SQLite:

```text
instance/app.sqlite3
```

Secrets and password hashes must not be committed.

Example settings:

```json
{
  "cast_ip": "192.168.1.50",
  "nas_lan_ip": "192.168.1.10",
  "app_port": 5000,
  "media_directory": "/path/to/cast-panel/media",
  "max_upload_mb": 100,
  "max_volume": 0.5,
  "default_audio_volume": 0.2,
  "cast_timeout_seconds": 10,
  "status_refresh_seconds": 5,
  "monitor_app_changes": false
}
```

Settings validation covers IP addresses, ports, media directory, upload limit,
volume limits and Cast timeout. The media directory must stay within the project
base directory.

## Dashboard

After login, `/` shows the device status:

- online/offline;
- device name and model;
- active app and `app_id`;
- standby and active input;
- volume and mute;
- media status when available.

`GET /status` returns the same status as JSON. Cast errors are mapped to an
offline payload without exposing tracebacks. The frontend polls this endpoint and
keeps only one active status request.

The dashboard also includes basic remote controls. Backend validation enforces
`max_volume`, so the frontend cannot accidentally set 100%. Successful commands
return a refreshed device status. `COMMAND_RATE_LIMIT_SECONDS` limits repeated
control commands.

## Media Library

`/media` lets an authenticated admin upload, preview, play and delete media.

Supported images:

- JPG/JPEG;
- PNG;
- WebP.

Supported audio:

- MP3;
- AAC/M4A;
- OGG;
- WAV.

Supported video:

- MP4;
- WebM.

Uploads validate extension, MIME type, image signatures where applicable, file
size and sanitized filenames. Files are stored only in the configured media
directory.

The app does not transcode media and does not promise arbitrary codec support.
For video, MP4 with H.264 video and AAC audio is recommended for best Cast
compatibility.

Public media endpoint:

```text
GET /media/files/<filename>
```

This endpoint is intentionally accessible without a Flask session because the
Cast device must fetch media without login cookies. Access is still limited to
the media directory, blocks path traversal and serves only supported media
types.

The URL sent to Cast is built from the configured local host IP and app port:

```text
http://<server_lan_ip>:<app_port>/media/files/<filename>
```

In the settings file this value is still stored as `nas_lan_ip` for backward
compatibility, but it means the LAN IP address of the server running this app.

For audio playback, the app can apply `default_audio_volume`, capped by
`max_volume`, and restore the previous volume after `Stop`.

## Slideshow, Queue And Presets

The media library supports:

- image slideshows with configurable slide duration;
- queues of selected media;
- presets stored in `instance/presets.json`.

Only one playback job can run at a time. Active jobs live only in memory, so a
process restart never resumes commands automatically. Presets persist across
restarts, but running them always requires an explicit user action.

## Logs And Audit

The app writes rotated logs:

- `app.log` for Flask/application diagnostics;
- `audit.log` as JSONL for panel operations.

`LOG_MAX_BYTES` and `LOG_BACKUP_COUNT` control rotation. `/audit` shows recent
operations and recent errors.

Audit entries store the user, command name, result, error and limited technical
details. Passwords, tokens, cookies, headers, full media URLs, titles and
`content_id` are redacted or not sent to audit at all. The audit log is not a
watch history.

Active app change monitoring is optional and disabled by default:

```json
{
  "monitor_app_changes": false
}
```

When enabled, only technical app change data such as `app_id` and app name is
recorded.

## Deployment

For a simple Unix-like host, the repository includes:

```text
scripts/start.sh
scripts/stop.sh
scripts/backup.sh
scripts/restore.sh
```

The scripts set the working directory, load `.env`, activate `.venv`, start
Waitress, write startup logs and use a PID file to avoid a second instance.

Detailed script-based deployment notes are in
`docs/SCRIPT_DEPLOYMENT.md`.

Release validation steps are tracked in `docs/RELEASE_CHECKLIST.md`.

Additional documentation:

- `docs/USER_GUIDE.md`
- `docs/DEVELOPMENT.md`

## Security Notes

- Keep the panel on a trusted network or behind a private VPN.
- Use a strong admin password.
- Do not commit `.env`, `instance/`, `logs/` or uploaded media.
- Configure a conservative `max_volume`.
- Configure Cast and host LAN IPs explicitly.
- Keep CSRF enabled.
- Do not use this as a public internet-facing service without additional
  hardening.

## Credits

Third-party packages are listed in `THIRD_PARTY_NOTICES.md`.
