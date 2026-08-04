# Synology Deployment

This deployment path runs the Flask app directly with Waitress. It does not use
Docker, Apache or Nginx.

## Directory Layout

Recommended location:

```text
/volume1/path-to-app
```

Recommended support directories:

```text
/volume1/path-to-app/instance
/volume1/path-to-app/logs
/volume1/path-to-app/media
/volume1/path-to-app/backups
/volume1/tmp-pip
```

## Initial Install

```sh
cd /volume1/path-to-app
python3 -m venv .venv
. .venv/bin/activate

export TMPDIR=/volume1/tmp-pip
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

cp .env.example .env
```

Edit `.env` and set at least:

```text
SECRET_KEY
CAST_IP
APP_HOST
APP_PORT
DATABASE_PATH
SETTINGS_PATH
PRESETS_PATH
MEDIA_DIRECTORY
LOG_DIRECTORY
AUDIT_LOG_PATH
```

Create the first administrator account:

```sh
. .venv/bin/activate
flask --app wsgi:app init-admin
```

## Manual Start And Stop

```sh
chmod +x scripts/start.sh scripts/stop.sh scripts/backup.sh
APP_DIR=/volume1/path-to-app scripts/start.sh
APP_DIR=/volume1/path-to-app scripts/stop.sh
```

The start script:

- switches to the application directory;
- loads `.env` when present;
- activates `.venv`;
- exports `TMPDIR`;
- starts Waitress;
- writes startup output to `logs/start.log`;
- writes the process ID to `instance/cast-panel.pid`;
- refuses to start a second instance when the PID is still running.

## DSM Startup Task

In Synology DSM:

1. Open Control Panel.
2. Open Task Scheduler.
3. Create a Triggered Task.
4. Choose User-defined script.
5. Set Event to Boot-up.
6. Use a user that can read and write the application directory.
7. Use this script:

```sh
APP_DIR=/volume1/path-to-app /volume1/path-to-app/scripts/start.sh
```

Keep the panel available only on LAN or through Tailscale. Do not expose it to
the public internet.

## Backup

Run:

```sh
APP_DIR=/volume1/path-to-app scripts/backup.sh
```

The backup archive is written to `backups/` and includes existing configuration,
SQLite database and presets. Media files are not included because they can be
large; back them up separately if needed.

## Update

```sh
cd /volume1/path-to-app
scripts/backup.sh
scripts/stop.sh
git pull --ff-only
. .venv/bin/activate
export TMPDIR=/volume1/tmp-pip
python -m pip install -r requirements.txt
python -m pytest
scripts/start.sh
```

If tests cannot run on the NAS due to limited resources, at minimum verify:

```sh
curl http://127.0.0.1:5000/health
```

Expected response:

```json
{"status":"ok"}
```
