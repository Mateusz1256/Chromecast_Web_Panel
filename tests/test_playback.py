import time
from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from app.services.media_service import MediaService
from app.services.playback_service import PlaybackJobAlreadyRunning, PlaybackService
from app.services.settings_service import SettingsService


class FakeCastService:
    def __init__(self):
        self.commands = []

    def show_image(self, media_url, content_type):
        self.commands.append(("show_image", media_url, content_type))
        return {"ok": True, "command": "show_image", "message": "Image sent"}

    def play_media(self, media_url, content_type):
        self.commands.append(("play_media", media_url, content_type))
        return {"ok": True, "command": "play_media", "message": "Media started"}

    def set_volume(self, level):
        self.commands.append(("set_volume", level))
        return {"ok": True, "command": "set_volume", "message": "Volume set"}

    def stop(self):
        self.commands.append(("stop",))
        return {"ok": True, "command": "stop", "message": "Stopped"}


def make_playback_service(tmp_path):
    settings_service = SettingsService(
        config_path=str(tmp_path / "config.json"),
        base_directory=str(tmp_path),
    )
    settings_service.save(
        {
            "cast_ip": "192.168.0.39",
            "nas_lan_ip": "192.168.0.10",
            "app_port": 5000,
            "media_directory": "media",
            "max_upload_mb": 1,
            "max_volume": 0.5,
            "default_audio_volume": 0.2,
            "cast_timeout_seconds": 10,
            "status_refresh_seconds": 5,
        }
    )
    media_service = MediaService(settings_service, base_directory=str(tmp_path))
    media_service.save_media(_upload("one.png", png_bytes(), "image/png"))
    media_service.save_media(_upload("two.png", png_bytes(), "image/png"))
    media_service.save_media(_upload("track.mp3", b"audio", "audio/mpeg"))
    cast_service = FakeCastService()
    playback_service = PlaybackService(
        media_service=media_service,
        cast_service=cast_service,
        presets_path=str(tmp_path / "presets.json"),
    )
    return playback_service, cast_service


def test_slideshow_rejects_parallel_job(tmp_path):
    playback_service, _ = make_playback_service(tmp_path)

    playback_service.start_slideshow(["one.png", "two.png"], slide_seconds=5)
    with pytest.raises(PlaybackJobAlreadyRunning):
        playback_service.start_slideshow(["one.png"], slide_seconds=5)

    playback_service.stop()


def test_stop_marks_active_job_for_stopping(tmp_path):
    playback_service, _ = make_playback_service(tmp_path)

    playback_service.start_slideshow(["one.png"], slide_seconds=5)
    status = playback_service.stop()

    assert status["active"] is True
    assert status["message"] == "Stopping job"


def test_restart_does_not_resume_active_job(tmp_path):
    playback_service, _ = make_playback_service(tmp_path)
    playback_service.start_slideshow(["one.png"], slide_seconds=5)

    fresh_service, _ = make_playback_service(tmp_path)

    assert fresh_service.status()["active"] is False
    playback_service.stop()


def test_presets_are_persisted_and_can_run(tmp_path):
    playback_service, cast_service = make_playback_service(tmp_path)

    preset = playback_service.save_preset("Morning", "track.mp3", volume=0.3)
    fresh_service, fresh_cast = make_playback_service(tmp_path)

    assert preset["name"] == "Morning"
    assert fresh_service.load_presets()[0]["filename"] == "track.mp3"
    fresh_service.run_preset("Morning")
    _wait_until_finished(fresh_service)

    assert fresh_cast.commands[:2] == [
        ("set_volume", 0.3),
        ("play_media", "http://192.168.0.10:5000/media/files/track.mp3", "audio/mpeg"),
    ]
    assert cast_service.commands == []


def test_preset_volume_respects_configured_limit(tmp_path):
    playback_service, _ = make_playback_service(tmp_path)

    with pytest.raises(ValueError, match="configured max volume"):
        playback_service.save_preset("Too loud", "track.mp3", volume=0.8)


def test_job_status_endpoint_requires_login(client):
    response = client.get("/media/job/status")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def _wait_until_finished(playback_service):
    for _ in range(20):
        if not playback_service.status()["active"]:
            return
        time.sleep(0.01)
    raise AssertionError("Playback job did not finish")


def _upload(filename, content, content_type):
    return FileStorage(
        stream=BytesIO(content),
        filename=filename,
        content_type=content_type,
    )


def png_bytes():
    return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
