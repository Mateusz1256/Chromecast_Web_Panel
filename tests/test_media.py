from io import BytesIO

from app.services.media_service import MediaService, MediaValidationError
from app.services.settings_service import SettingsService


class FakeCastService:
    def __init__(self):
        self.show_image_calls = []
        self.play_media_calls = []
        self.set_volume_calls = []
        self.stop_calls = 0

    def get_status(self):
        return {
            "online": True,
            "volume_level": 0.33,
            "media": {},
        }

    def show_image(self, media_url, content_type):
        self.show_image_calls.append((media_url, content_type))
        return {
            "ok": True,
            "command": "show_image",
            "message": "Image sent to Cast device",
        }

    def play_media(self, media_url, content_type):
        self.play_media_calls.append((media_url, content_type))
        return {
            "ok": True,
            "command": "play_media",
            "message": "Media playback started",
        }

    def set_volume(self, level):
        self.set_volume_calls.append(level)
        return {"ok": True, "command": "set_volume", "message": "Volume command sent"}

    def stop(self):
        self.stop_calls += 1
        return {"ok": True, "command": "stop", "message": "Playback stopped"}


def login(app, client):
    app.extensions["user_store"].create_admin("admin", "secret-password")
    return client.post(
        "/login",
        data={"username": "admin", "password": "secret-password"},
        follow_redirects=True,
    )


def make_media_service(tmp_path):
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
    return MediaService(settings_service, base_directory=str(tmp_path))


def test_media_service_saves_sanitized_image(tmp_path):
    service = make_media_service(tmp_path)
    upload = _upload("My Image.png", png_bytes(), "image/png")

    saved = service.save_image(upload)

    assert saved["filename"] == "My_Image.png"
    assert (tmp_path / "media" / "My_Image.png").exists()


def test_media_service_rejects_unsupported_mime(tmp_path):
    service = make_media_service(tmp_path)
    upload = _upload("image.png", b"not-image", "text/plain")

    try:
        service.save_image(upload)
    except MediaValidationError as exc:
        assert str(exc) == "Unsupported media MIME type"
    else:
        raise AssertionError("Expected MediaValidationError")


def test_media_service_rejects_unsupported_extension(tmp_path):
    service = make_media_service(tmp_path)
    upload = _upload("movie.avi", b"data", "video/x-msvideo")

    try:
        service.save_media(upload)
    except MediaValidationError as exc:
        assert str(exc) == "Unsupported media extension"
    else:
        raise AssertionError("Expected MediaValidationError")


def test_media_service_saves_audio_and_video(tmp_path):
    service = make_media_service(tmp_path)

    audio = service.save_media(_upload("track.mp3", b"audio", "audio/mpeg"))
    video = service.save_media(_upload("clip.mp4", b"video", "video/mp4"))

    assert audio["media_type"] == "audio"
    assert video["media_type"] == "video"
    assert [item["filename"] for item in service.list_media()] == [
        "clip.mp4",
        "track.mp3",
    ]


def test_media_service_blocks_path_traversal(tmp_path):
    service = make_media_service(tmp_path)

    try:
        service.resolve_media_path("../secret.png")
    except MediaValidationError as exc:
        assert str(exc) == "Invalid media filename"
    else:
        raise AssertionError("Expected MediaValidationError")


def test_media_public_url_uses_lan_ip_and_port(tmp_path):
    service = make_media_service(tmp_path)
    service.save_image(_upload("image.webp", webp_bytes(), "image/webp"))

    url = service.public_url("image.webp")

    assert url == "http://192.168.0.10:5000/media/files/image.webp"


def test_media_library_requires_login(client):
    response = client.get("/media")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_media_upload_uses_stable_file_name_display(app, client):
    login(app, client)

    response = client.get("/media")

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'class="file-input"' in page
    assert "data-file-name" in page
    assert "Nie wybrano pliku" in page


def test_upload_lists_and_serves_image(app, client):
    login(app, client)

    upload_response = client.post(
        "/media",
        data={"image": (_bytes(png_bytes()), "photo.png", "image/png")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    file_response = client.get("/media/files/photo.png")

    assert upload_response.status_code == 200
    assert "photo.png" in upload_response.get_data(as_text=True)
    assert file_response.status_code == 200
    assert file_response.mimetype == "image/png"


def test_upload_accepts_audio_and_video(app, client):
    login(app, client)

    audio_response = client.post(
        "/media",
        data={"media": (_bytes(b"audio"), "track.mp3", "audio/mpeg")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    video_response = client.post(
        "/media",
        data={"media": (_bytes(b"video"), "clip.mp4", "video/mp4")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert audio_response.status_code == 200
    assert video_response.status_code == 200
    assert "track.mp3" in video_response.get_data(as_text=True)
    assert "clip.mp4" in video_response.get_data(as_text=True)


def test_media_file_endpoint_blocks_traversal(client):
    response = client.get("/media/files/../secret.png")

    assert response.status_code == 404


def test_show_image_calls_cast_service_with_public_url(app, client):
    login(app, client)
    fake_cast = FakeCastService()
    app.extensions["cast_service"] = fake_cast
    client.post(
        "/media",
        data={"image": (_bytes(jpeg_bytes()), "screen.jpg", "image/jpeg")},
        content_type="multipart/form-data",
    )

    response = client.post("/media/show/screen.jpg", follow_redirects=True)

    assert response.status_code == 200
    assert fake_cast.show_image_calls == [
        ("http://192.168.0.10:5000/media/files/screen.jpg", "image/jpeg")
    ]
    assert "Image sent to Cast device" in response.get_data(as_text=True)


def test_play_audio_sets_default_volume_and_remembers_previous(app, client):
    login(app, client)
    fake_cast = FakeCastService()
    app.extensions["cast_service"] = fake_cast
    client.post(
        "/media",
        data={"media": (_bytes(b"audio"), "track.mp3", "audio/mpeg")},
        content_type="multipart/form-data",
    )

    response = client.post("/media/play/track.mp3", follow_redirects=True)

    assert response.status_code == 200
    assert fake_cast.set_volume_calls == [0.2]
    assert fake_cast.play_media_calls == [
        ("http://192.168.0.10:5000/media/files/track.mp3", "audio/mpeg")
    ]
    with client.session_transaction() as flask_session:
        assert flask_session["previous_audio_volume"] == 0.33


def test_play_video_uses_default_media_receiver(app, client):
    login(app, client)
    fake_cast = FakeCastService()
    app.extensions["cast_service"] = fake_cast
    client.post(
        "/media",
        data={"media": (_bytes(b"video"), "clip.mp4", "video/mp4")},
        content_type="multipart/form-data",
    )

    response = client.post("/media/play/clip.mp4", follow_redirects=True)

    assert response.status_code == 200
    assert fake_cast.set_volume_calls == []
    assert fake_cast.play_media_calls == [
        ("http://192.168.0.10:5000/media/files/clip.mp4", "video/mp4")
    ]


def test_delete_removes_image(app, client):
    login(app, client)
    client.post(
        "/media",
        data={"image": (_bytes(png_bytes()), "delete-me.png", "image/png")},
        content_type="multipart/form-data",
    )

    response = client.post("/media/delete/delete-me.png", follow_redirects=True)

    assert response.status_code == 200
    assert client.get("/media/files/delete-me.png").status_code == 404


def test_stop_calls_cast_service(app, client):
    login(app, client)
    fake_cast = FakeCastService()
    app.extensions["cast_service"] = fake_cast

    response = client.post("/media/stop", follow_redirects=True)

    assert response.status_code == 200
    assert fake_cast.stop_calls == 1


def test_stop_restores_previous_audio_volume(app, client):
    login(app, client)
    fake_cast = FakeCastService()
    app.extensions["cast_service"] = fake_cast
    with client.session_transaction() as flask_session:
        flask_session["previous_audio_volume"] = 0.33

    response = client.post("/media/stop", follow_redirects=True)

    assert response.status_code == 200
    assert fake_cast.stop_calls == 1
    assert fake_cast.set_volume_calls == [0.33]


def _upload(filename, content, content_type):
    from werkzeug.datastructures import FileStorage

    return FileStorage(
        stream=_bytes(content),
        filename=filename,
        content_type=content_type,
    )


def _bytes(content):
    return BytesIO(content)


def png_bytes():
    return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"


def jpeg_bytes():
    return b"\xff\xd8\xff\xe0\x00\x10JFIF"


def webp_bytes():
    return b"RIFF\x00\x00\x00\x00WEBP"
