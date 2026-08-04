from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_login import current_user, login_required

from app.services.cast_service import CastServiceError
from app.services.media_service import MediaNotFoundError, MediaValidationError
from app.services.playback_service import (
    PlaybackJobAlreadyRunning,
    PlaybackJobNotRunning,
)

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
            saved_media = media_service.save_media(uploaded_file)
        except MediaValidationError as exc:
            _audit("media.upload", False, str(exc))
            flash(str(exc), "error")
        else:
            _audit(
                "media.upload",
                True,
                details={"media_type": saved_media["media_type"]},
            )
            flash("Media uploaded", "success")
        return redirect(url_for("media.library"))

    playback_service = current_app.extensions["playback_service"]
    return render_template(
        "media/library.html",
        media_files=media_service.list_media(),
        playback_status=playback_service.status(),
        presets=playback_service.load_presets(),
    )


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
        _audit("media.play", False, str(exc))
        flash(str(exc), "error")
    else:
        _audit("media.play", True, details={"media_type": media_type})
        flash(result["message"], "success")
    return redirect(url_for("media.library"))


@media_bp.post("/delete/<path:filename>")
@login_required
def delete(filename):
    media_service = current_app.extensions["media_service"]
    try:
        media_service.delete(filename)
    except (MediaValidationError, MediaNotFoundError) as exc:
        _audit("media.delete", False, str(exc))
        flash(str(exc), "error")
    else:
        _audit("media.delete", True)
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
        _audit("media.stop", False, str(exc))
        flash(str(exc), "error")
    else:
        _audit("media.stop", True)
        flash(result["message"], "success")
    return redirect(url_for("media.library"))


@media_bp.post("/slideshow/start")
@login_required
def start_slideshow():
    playback_service = current_app.extensions["playback_service"]
    filenames = request.form.getlist("filenames")
    try:
        slide_seconds = float(request.form.get("slide_seconds", "5"))
        playback_service.start_slideshow(filenames, slide_seconds)
    except (ValueError, MediaValidationError, PlaybackJobAlreadyRunning) as exc:
        _audit("job.slideshow.start", False, str(exc))
        flash(str(exc), "error")
    else:
        _audit("job.slideshow.start", True, details={"count": len(filenames)})
        flash("Slideshow started", "success")
    return redirect(url_for("media.library"))


@media_bp.post("/queue/start")
@login_required
def start_queue():
    playback_service = current_app.extensions["playback_service"]
    filenames = request.form.getlist("filenames")
    try:
        playback_service.start_queue(filenames)
    except (ValueError, MediaValidationError, PlaybackJobAlreadyRunning) as exc:
        _audit("job.queue.start", False, str(exc))
        flash(str(exc), "error")
    else:
        _audit("job.queue.start", True, details={"count": len(filenames)})
        flash("Queue started", "success")
    return redirect(url_for("media.library"))


@media_bp.post("/job/stop")
@login_required
def stop_job():
    playback_service = current_app.extensions["playback_service"]
    try:
        playback_service.stop()
    except PlaybackJobNotRunning as exc:
        _audit("job.stop", False, str(exc))
        flash(str(exc), "error")
    else:
        _audit("job.stop", True)
        flash("Playback job stopping", "success")
    return redirect(url_for("media.library"))


@media_bp.get("/job/status")
@login_required
def job_status():
    return jsonify(current_app.extensions["playback_service"].status())


@media_bp.post("/presets")
@login_required
def save_preset():
    playback_service = current_app.extensions["playback_service"]
    filename = request.form.get("filename", "")
    name = request.form.get("name", "")
    try:
        volume = _optional_float(request.form.get("volume"))
        stop_after_seconds = _optional_float(request.form.get("stop_after_seconds"))
        playback_service.save_preset(name, filename, volume, stop_after_seconds)
    except (ValueError, MediaValidationError) as exc:
        _audit("preset.save", False, str(exc))
        flash(str(exc), "error")
    else:
        _audit("preset.save", True)
        flash("Preset saved", "success")
    return redirect(url_for("media.library"))


@media_bp.post("/presets/<name>/run")
@login_required
def run_preset(name):
    playback_service = current_app.extensions["playback_service"]
    try:
        playback_service.run_preset(name)
    except (ValueError, MediaValidationError, PlaybackJobAlreadyRunning) as exc:
        _audit("preset.run", False, str(exc))
        flash(str(exc), "error")
    else:
        _audit("preset.run", True)
        flash("Preset started", "success")
    return redirect(url_for("media.library"))


@media_bp.post("/presets/<name>/delete")
@login_required
def delete_preset(name):
    current_app.extensions["playback_service"].delete_preset(name)
    _audit("preset.delete", True)
    flash("Preset deleted", "success")
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


def _optional_float(value):
    if value is None or value == "":
        return None
    return float(value)


def _audit(command, ok, error="", details=None):
    current_app.extensions["audit_service"].record(
        user=current_user.get_id(),
        command=command,
        ok=ok,
        error=error,
        details=details,
    )
