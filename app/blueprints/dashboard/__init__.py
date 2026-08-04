from flask import Blueprint, current_app, jsonify, render_template
from flask_login import login_required

from app.services.cast_service import CastServiceError

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/")
@login_required
def dashboard():
    settings = current_app.extensions["settings_service"].load()
    return render_template(
        "dashboard/index.html",
        status_refresh_seconds=settings["status_refresh_seconds"],
        max_volume=settings["max_volume"],
    )


@dashboard_bp.get("/status")
@login_required
def status():
    return jsonify(_safe_status())


def _safe_status():
    cast_service = current_app.extensions["cast_service"]
    try:
        status_payload = cast_service.get_status()
    except CastServiceError as exc:
        return {
            "ok": False,
            "status": _offline_status(str(exc)),
        }
    except Exception:
        current_app.logger.exception("Unexpected Cast status error")
        return {
            "ok": False,
            "status": _offline_status("Unexpected Cast status error"),
        }
    return {"ok": True, "status": status_payload}


def _offline_status(message):
    return {
        "online": False,
        "name": None,
        "model_name": None,
        "app_name": None,
        "app_id": None,
        "is_stand_by": None,
        "is_active_input": None,
        "volume_level": None,
        "volume_muted": None,
        "media": {},
        "message": message,
    }
