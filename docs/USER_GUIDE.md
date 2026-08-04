# User Guide

## First Run

1. Install dependencies.
2. Copy `.env.example` to `.env`.
3. Set `SECRET_KEY`, `CAST_IP`, host/port and paths.
4. Create the first admin account:

```sh
flask --app wsgi:app init-admin
```

5. Start the app and open it in a browser.

## Dashboard

The Status page shows the Cast device status, active app, standby/input state,
volume and available media metadata. Native apps may not expose standard media
status; in that case the panel shows a clear message instead of a traceback.

The Pilot page contains playback controls, volume controls, mute/unmute, seek
and a `Close Cast app` action. PyChromecast does not provide a stable physical
TV power on/off command, so the panel only closes the active Cast application
when the receiver supports it.

## Media

Upload media from `/media`, then use `Display` or `Play` to send it to the Cast
device. The receiver fetches files from:

```text
http://<host-lan-ip>:<app-port>/media/files/<filename>
```

Use a LAN IP address reachable by the Cast device.

## Presets And Queue

Select files in the media library to start a slideshow or queue. Presets are
stored in `instance/presets.json` and run only after an explicit user action.

## Logs

Open `/audit` to inspect recent panel operations and errors. Audit logs are
technical logs, not watch history.

## Backup

Run:

```sh
scripts/backup.sh
```

Restore on a separate copy first:

```sh
scripts/restore.sh backups/<archive>.tar.gz
```
