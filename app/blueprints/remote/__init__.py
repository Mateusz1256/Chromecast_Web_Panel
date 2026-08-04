from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import current_user, login_required

from app.blueprints.dashboard import _safe_status
from app.services.cast_service import CastServiceError, CastUnsupportedCommand
from app.services.rate_limiter import RateLimitExceeded

remote_bp = Blueprint("remote", __name__, url_prefix="/remote")


@remote_bp.get("/")
@login_required
def remote_panel():
    settings = current_app.extensions["settings_service"].load()
    return render_template(
        "dashboard/remote.html",
        status_refresh_seconds=settings["status_refresh_seconds"],
        max_volume=settings["max_volume"],
    )


@remote_bp.post("/volume")
@login_required
def volume():
    payload = request.get_json(silent=True) or {}
    try:
        level = float(payload.get("level"))
    except (TypeError, ValueError):
        return _error_response("Volume level must be a number", 400)

    settings = current_app.extensions["settings_service"].load()
    max_volume = float(settings["max_volume"])
    if level < 0 or level > max_volume:
        return _error_response(
            "Volume level must be between 0 and configured max volume",
            400,
        )

    return _run_command(
        "set_volume",
        lambda cast_service: cast_service.set_volume(level),
    )


@remote_bp.post("/mute")
@login_required
def mute():
    return _run_command("mute", lambda cast_service: cast_service.mute())


@remote_bp.post("/unmute")
@login_required
def unmute():
    return _run_command("unmute", lambda cast_service: cast_service.unmute())


@remote_bp.post("/pause")
@login_required
def pause():
    return _run_command("pause", lambda cast_service: cast_service.pause())


@remote_bp.post("/resume")
@login_required
def resume():
    return _run_command("resume", lambda cast_service: cast_service.resume())


@remote_bp.post("/stop")
@login_required
def stop():
    return _run_command("stop", lambda cast_service: cast_service.stop())


@remote_bp.post("/quit-app")
@login_required
def quit_app():
    return _run_command("quit_app", lambda cast_service: cast_service.quit_app())


@remote_bp.post("/seek")
@login_required
def seek():
    payload = request.get_json(silent=True) or {}
    try:
        seconds = float(payload.get("seconds"))
    except (TypeError, ValueError):
        return _error_response("Seek position must be a number", 400)
    if seconds < 0:
        return _error_response("Seek position cannot be negative", 400)
    return _run_command("seek", lambda cast_service: cast_service.seek(seconds))


def _run_command(command_name, command):
    try:
        _check_rate_limit(command_name)
        result = command(current_app.extensions["cast_service"])
    except RateLimitExceeded as exc:
        _audit(command_name, False, str(exc))
        return _error_response(str(exc), 429)
    except CastUnsupportedCommand as exc:
        _audit(command_name, False, str(exc))
        return _error_response(str(exc), 400)
    except CastServiceError as exc:
        _audit(command_name, False, str(exc))
        return _error_response(str(exc), 503)

    status_payload = _safe_status()
    _audit(command_name, True)
    return jsonify({"ok": True, "result": result, "status": status_payload["status"]})


def _check_rate_limit(command_name):
    user_id = current_user.get_id() or "anonymous"
    key = f"{user_id}:{command_name}"
    current_app.extensions["command_rate_limiter"].check(key)


def _error_response(message, status_code):
    return jsonify(
        {
            "ok": False,
            "message": message,
            "status": _safe_status()["status"],
        }
    ), status_code


def _audit(command_name, ok, error=""):
    current_app.extensions["audit_service"].record(
        user=current_user.get_id(),
        command=f"remote.{command_name}",
        ok=ok,
        error=error,
    )
