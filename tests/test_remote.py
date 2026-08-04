from app.services.cast_service import CastUnsupportedCommand
from app.services.rate_limiter import CommandRateLimiter


class FakeRemoteCastService:
    def __init__(self):
        self.commands = []
        self.get_status_calls = 0
        self.pause_error = None

    def get_status(self):
        self.get_status_calls += 1
        return {
            "online": True,
            "name": "Play Box",
            "model_name": "Android TV",
            "app_name": "Default Media Receiver",
            "app_id": "CC1AD845",
            "is_stand_by": False,
            "is_active_input": True,
            "volume_level": 0.25,
            "volume_muted": False,
            "media": {"player_state": "PLAYING", "current_time": 10},
            "message": None,
        }

    def set_volume(self, level):
        self.commands.append(("set_volume", level))
        return {"ok": True, "command": "set_volume", "message": "Volume command sent"}

    def mute(self):
        self.commands.append(("mute",))
        return {"ok": True, "command": "mute", "message": "Device muted"}

    def unmute(self):
        self.commands.append(("unmute",))
        return {"ok": True, "command": "unmute", "message": "Device unmuted"}

    def pause(self):
        if self.pause_error is not None:
            raise self.pause_error
        self.commands.append(("pause",))
        return {"ok": True, "command": "pause", "message": "Playback paused"}

    def resume(self):
        self.commands.append(("resume",))
        return {"ok": True, "command": "resume", "message": "Playback resumed"}

    def stop(self):
        self.commands.append(("stop",))
        return {"ok": True, "command": "stop", "message": "Playback stopped"}

    def seek(self, seconds):
        self.commands.append(("seek", seconds))
        return {"ok": True, "command": "seek", "message": "Seek command sent"}


def login(app, client):
    app.extensions["user_store"].create_admin("admin", "secret-password")
    return client.post(
        "/login",
        data={"username": "admin", "password": "secret-password"},
        follow_redirects=True,
    )


def test_remote_requires_login(client):
    response = client.post("/remote/mute")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_volume_command_enforces_configured_max(app, client):
    fake_cast = FakeRemoteCastService()
    app.extensions["cast_service"] = fake_cast
    login(app, client)

    response = client.post("/remote/volume", json={"level": 0.8})

    assert response.status_code == 400
    assert response.get_json()["ok"] is False
    assert fake_cast.commands == []


def test_volume_command_returns_refreshed_status(app, client):
    fake_cast = FakeRemoteCastService()
    app.extensions["cast_service"] = fake_cast
    login(app, client)

    response = client.post("/remote/volume", json={"level": 0.4})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["status"]["name"] == "Play Box"
    assert fake_cast.commands == [("set_volume", 0.4)]
    assert fake_cast.get_status_calls == 1


def test_seek_rejects_negative_position(app, client):
    fake_cast = FakeRemoteCastService()
    app.extensions["cast_service"] = fake_cast
    login(app, client)

    response = client.post("/remote/seek", json={"seconds": -1})

    assert response.status_code == 400
    assert fake_cast.commands == []


def test_remote_maps_unsupported_command(app, client):
    fake_cast = FakeRemoteCastService()
    fake_cast.pause_error = CastUnsupportedCommand("pause is unsupported")
    app.extensions["cast_service"] = fake_cast
    login(app, client)

    response = client.post("/remote/pause")

    assert response.status_code == 400
    assert response.get_json()["message"] == "pause is unsupported"


def test_remote_rate_limits_repeated_command(app, client):
    fake_cast = FakeRemoteCastService()
    app.extensions["cast_service"] = fake_cast
    app.extensions["command_rate_limiter"] = CommandRateLimiter(60)
    login(app, client)

    first = client.post("/remote/mute")
    second = client.post("/remote/mute")

    assert first.status_code == 200
    assert second.status_code == 429
    assert fake_cast.commands == [("mute",)]
