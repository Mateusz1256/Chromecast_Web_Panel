#!/bin/sh
set -eu

APP_DIR="${APP_DIR:-/volume1/path-to-app}"
PID_FILE="${PID_FILE:-$APP_DIR/instance/cast-panel.pid}"
STOP_LOG="${STOP_LOG:-$APP_DIR/logs/start.log}"

log() {
    mkdir -p "$(dirname "$STOP_LOG")"
    printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$STOP_LOG"
}

if [ ! -f "$PID_FILE" ]; then
    log "PID file not found; nothing to stop"
    exit 0
fi

APP_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
if [ -z "$APP_PID" ]; then
    rm -f "$PID_FILE"
    log "PID file was empty"
    exit 0
fi

if ! kill -0 "$APP_PID" 2>/dev/null; then
    rm -f "$PID_FILE"
    log "Process $APP_PID is not running"
    exit 0
fi

log "Stopping process $APP_PID"
kill "$APP_PID"

for _ in 1 2 3 4 5 6 7 8 9 10; do
    if ! kill -0 "$APP_PID" 2>/dev/null; then
        rm -f "$PID_FILE"
        log "Stopped process $APP_PID"
        exit 0
    fi
    sleep 1
done

log "Process $APP_PID did not stop after 10 seconds"
exit 1
