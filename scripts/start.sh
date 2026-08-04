#!/bin/sh
set -eu

APP_DIR="${APP_DIR:-/volume1/path-to-app}"
VENV_DIR="${VENV_DIR:-$APP_DIR/.venv}"
TMPDIR="${TMPDIR:-/volume1/tmp-pip}"
PID_FILE="${PID_FILE:-$APP_DIR/instance/cast-panel.pid}"
START_LOG="${START_LOG:-$APP_DIR/logs/start.log}"
HOST="${APP_HOST:-0.0.0.0}"
PORT="${APP_PORT:-5000}"

mkdir -p "$APP_DIR/instance" "$APP_DIR/logs" "$TMPDIR"

log() {
    printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$START_LOG"
}

if [ -f "$PID_FILE" ]; then
    OLD_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        log "Already running with PID $OLD_PID"
        exit 0
    fi
    rm -f "$PID_FILE"
fi

cd "$APP_DIR"

if [ -f "$APP_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$APP_DIR/.env"
    set +a
fi

if [ -f "$VENV_DIR/bin/activate" ]; then
    # shellcheck disable=SC1091
    . "$VENV_DIR/bin/activate"
else
    log "Virtual environment not found: $VENV_DIR"
    exit 1
fi

export TMPDIR

log "Starting Cast Control Panel on $HOST:$PORT"
nohup waitress-serve \
    --host="$HOST" \
    --port="$PORT" \
    wsgi:app >> "$START_LOG" 2>&1 &

APP_PID="$!"
printf '%s\n' "$APP_PID" > "$PID_FILE"
log "Started with PID $APP_PID"
