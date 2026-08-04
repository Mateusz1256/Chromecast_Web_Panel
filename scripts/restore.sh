#!/bin/sh
set -eu

APP_DIR="${APP_DIR:-/volume1/path-to-app}"
ARCHIVE="${1:-}"

if [ -z "$ARCHIVE" ]; then
    echo "Usage: APP_DIR=/path/to/app scripts/restore.sh /path/to/backup.tar.gz" >&2
    exit 1
fi

if [ ! -f "$ARCHIVE" ]; then
    echo "Backup archive not found: $ARCHIVE" >&2
    exit 1
fi

mkdir -p "$APP_DIR"
cd "$APP_DIR"

tar -tzf "$ARCHIVE" | while IFS= read -r entry; do
    case "$entry" in
        .env|instance/config.json|instance/app.sqlite3|instance/presets.json)
            ;;
        *)
            echo "Unsafe backup entry: $entry" >&2
            exit 1
            ;;
    esac
done

tar -xzf "$ARCHIVE"
echo "Restored $ARCHIVE into $APP_DIR"
