from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required

from app.forms import SettingsForm
from app.services.cast_service import CastServiceError
from app.services.settings_service import SettingsValidationError

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("", methods=["GET", "POST"])
@login_required
def settings():
    settings_service = current_app.extensions["settings_service"]
    current_settings = settings_service.load()
    form = SettingsForm(data=current_settings)

    if form.validate_on_submit():
        submitted = _form_to_settings(form)
        try:
            saved_settings = settings_service.save(submitted)
        except SettingsValidationError as exc:
            for field_name, message in exc.errors.items():
                getattr(form, field_name).errors.append(message)
        else:
            _refresh_cast_service(saved_settings)
            flash("Settings saved", "success")
            return redirect(url_for("settings.settings"))

    return render_template("settings/index.html", form=form)


@settings_bp.get("/export")
@login_required
def export_settings():
    settings_service = current_app.extensions["settings_service"]
    return jsonify(settings_service.export())


@settings_bp.post("/import")
@login_required
def import_settings():
    settings_service = current_app.extensions["settings_service"]
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"ok": False, "errors": {"json": "Expected JSON object"}}), 400
    try:
        settings = settings_service.import_settings(payload)
    except SettingsValidationError as exc:
        return jsonify({"ok": False, "errors": exc.errors}), 400
    _refresh_cast_service(settings)
    return jsonify({"ok": True, "settings": settings})


@settings_bp.post("/test-cast")
@login_required
def test_cast():
    cast_service = current_app.extensions["cast_service"]
    try:
        result = cast_service.connect()
    except CastServiceError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 503
    return jsonify(result)


def _form_to_settings(form):
    return {
        "cast_ip": form.cast_ip.data,
        "nas_lan_ip": form.nas_lan_ip.data,
        "app_port": form.app_port.data,
        "media_directory": form.media_directory.data,
        "max_upload_mb": form.max_upload_mb.data,
        "max_volume": form.max_volume.data,
        "default_audio_volume": form.default_audio_volume.data,
        "cast_timeout_seconds": form.cast_timeout_seconds.data,
        "status_refresh_seconds": form.status_refresh_seconds.data,
        "monitor_app_changes": form.monitor_app_changes.data,
    }


def _refresh_cast_service(settings):
    cast_service = current_app.extensions["cast_service"]
    cast_service.cast_ip = settings["cast_ip"]
    cast_service.timeout_seconds = settings["cast_timeout_seconds"]
