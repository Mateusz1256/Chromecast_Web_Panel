from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_login import login_required

from app.services.cast_service import CastServiceError
from app.services.media_service import MediaNotFoundError, MediaValidationError

media_bp = Blueprint("media", __name__, url_prefix="/media")


@media_bp.route("", methods=["GET", "POST"])
@login_required
def library():
    media_service = current_app.extensions["media_service"]

    if request.method == "POST":
        max_upload_mb = media_service.settings["max_upload_mb"]
        max_bytes = int(max_upload_mb) * 1024 * 1024
        if request.content_length and request.content_length > max_bytes:
            flash("Media exceeds configured upload limit", "error")
            return redirect(url_for("media.library"))

        try:
            uploaded_file = request.files.get("media") or request.files.get("image")
            media_service.save_media(uploaded_file)
        except MediaValidationError as exc:
            flash(str(exc), "error")
        else:
            flash("Media uploaded", "success")
        return redirect(url_for("media.library"))

    return render_template("media/library.html", media_files=media_service.list_media())


@media_bp.get("/files/<path:filename>")
def file(filename):
    media_service = current_app.extensions["media_service"]
    try:
        path = media_service.resolve_media_path(filename)
    except MediaValidationError:
        return ("Not found", 404)
    if not path.exists() or not path.is_file():
        return ("Not found", 404)
    return send_file(path, mimetype=media_service.content_type_for(path.name))


@media_bp.post("/show/<path:filename>")
@login_required
def show(filename):
    return _play(filename)


@media_bp.post("/play/<path:filename>")
@login_required
def play(filename):
    return _play(filename)


def _play(filename):
    media_service = current_app.extensions["media_service"]
    cast_service = current_app.extensions["cast_service"]
    try:
        media_url = media_service.public_url(filename)
        content_type = media_service.content_type_for(filename)
        media_type = media_service.media_type_for(filename)
        if media_type == "image":
            result = cast_service.show_image(media_url, content_type)
        else:
            if media_type == "audio":
                _set_default_audio_volume(cast_service)
            result = cast_service.play_media(media_url, content_type)
    except (MediaValidationError, MediaNotFoundError, CastServiceError) as exc:
        flash(str(exc), "error")
    else:
        flash(result["message"], "success")
    return redirect(url_for("media.library"))


@media_bp.post("/delete/<path:filename>")
@login_required
def delete(filename):
    media_service = current_app.extensions["media_service"]
    try:
        media_service.delete(filename)
    except (MediaValidationError, MediaNotFoundError) as exc:
        flash(str(exc), "error")
    else:
        flash("Image deleted", "success")
    return redirect(url_for("media.library"))


@media_bp.post("/stop")
@login_required
def stop():
    cast_service = current_app.extensions["cast_service"]
    try:
        result = cast_service.stop()
        _restore_previous_volume(cast_service)
    except CastServiceError as exc:
        flash(str(exc), "error")
    else:
        flash(result["message"], "success")
    return redirect(url_for("media.library"))


def _set_default_audio_volume(cast_service):
    settings = current_app.extensions["settings_service"].load()
    status = cast_service.get_status()
    previous_volume = status.get("volume_level")
    if previous_volume is not None:
        session["previous_audio_volume"] = previous_volume
    target_volume = min(
        float(settings["default_audio_volume"]),
        float(settings["max_volume"]),
    )
    cast_service.set_volume(target_volume)


def _restore_previous_volume(cast_service):
    previous_volume = session.pop("previous_audio_volume", None)
    if previous_volume is not None:
        cast_service.set_volume(float(previous_volume))
