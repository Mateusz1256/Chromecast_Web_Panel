# Script-Based Deployment

This document describes running Cast Control Panel on a Unix-like host with the
provided shell scripts and Waitress.

## Directory Layout

Example location:

```text
/opt/cast-panel
```

Support directories:

```text
/opt/cast-panel/instance
/opt/cast-panel/logs
/opt/cast-panel/media
/opt/cast-panel/backups
/tmp/cast-panel-pip
```

## Initial Install

```sh
cd /opt/cast-panel
python3 -m venv .venv
. .venv/bin/activate

export TMPDIR=/tmp/cast-panel-pip
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
APP_DIR=/opt/cast-panel scripts/start.sh
APP_DIR=/opt/cast-panel scripts/stop.sh
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

## Autostart

Use your host's service manager or task scheduler to run:

```sh
APP_DIR=/opt/cast-panel /opt/cast-panel/scripts/start.sh
```

On shutdown, run:

```sh
APP_DIR=/opt/cast-panel /opt/cast-panel/scripts/stop.sh
```

Keep the panel available only on a trusted network or private VPN.

## Backup

Run:

```sh
APP_DIR=/opt/cast-panel scripts/backup.sh
```

The backup archive is written to `backups/` and includes existing configuration,
SQLite database and presets. Media files are not included because they can be
large; back them up separately if needed.

Restore to an application directory:

```sh
APP_DIR=/opt/cast-panel scripts/restore.sh backups/<archive>.tar.gz
```

## Update

```sh
cd /opt/cast-panel
scripts/backup.sh
scripts/stop.sh
git pull --ff-only
. .venv/bin/activate
export TMPDIR=/tmp/cast-panel-pip
python -m pip install -r requirements.txt
python -m pytest
scripts/start.sh
```

At minimum, verify:

```sh
curl http://127.0.0.1:5000/health
```

Expected response:

```json
{"status":"ok"}
```
