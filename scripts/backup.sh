#!/bin/sh
set -eu

APP_DIR="${APP_DIR:-/volume1/path-to-app}"
BACKUP_DIR="${BACKUP_DIR:-$APP_DIR/backups}"
STAMP="$(date '+%Y%m%d-%H%M%S')"
ARCHIVE="$BACKUP_DIR/cast-panel-config-$STAMP.tar.gz"

mkdir -p "$BACKUP_DIR"
cd "$APP_DIR"

FILES=""
for candidate in .env instance/config.json instance/app.sqlite3 instance/presets.json; do
    if [ -e "$candidate" ]; then
        FILES="$FILES $candidate"
    fi
done

if [ -z "$FILES" ]; then
    echo "Nothing to back up. Configuration files do not exist yet." >&2
    exit 1
fi

# shellcheck disable=SC2086
tar -czf "$ARCHIVE" $FILES

echo "$ARCHIVE"
