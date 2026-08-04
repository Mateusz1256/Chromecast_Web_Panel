import threading
import time

import pytest

from app.services.cast_service import (
    CastConnectionTimeout,
    CastDeviceUnavailable,
    CastService,
    CastUnsupportedCommand,
)


class FakeAdapter:
    def __init__(self):
        self.connect_calls = 0
        self.disconnect_calls = 0
        self.commands = []
        self.fail_status = False
        self.fail_connect = None
        self.lock_observed = []

    def connect(self, cast_ip, timeout):
        self.connect_calls += 1
        if self.fail_connect is not None:
            raise self.fail_connect
        return {"cast_ip": cast_ip, "timeout": timeout}

    def disconnect(self, handle):
        self.disconnect_calls += 1

    def get_status(self, handle):
        if self.fail_status:
            raise CastConnectionTimeout("timeout")
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
            "media": {"player_state": "PLAYING"},
            "message": None,
        }

    def play_media(self, handle, media_url, content_type, timeout):
        self.commands.append(("play_media", media_url, content_type, timeout))

    def pause(self, handle):
        self.commands.append(("pause",))

    def resume(self, handle):
        self.commands.append(("resume",))

    def stop(self, handle):
        self.commands.append(("stop",))

    def quit_app(self, handle):
        self.commands.append(("quit_app",))

    def seek(self, handle, seconds):
        self.commands.append(("seek", seconds))

    def set_volume(self, handle, level):
        self.commands.append(("set_volume", level))

    def mute(self, handle):
        self.commands.append(("mute",))

    def unmute(self, handle):
        self.commands.append(("unmute",))


class SlowAdapter(FakeAdapter):
    def pause(self, handle):
        self.lock_observed.append("start")
        time.sleep(0.02)
        self.lock_observed.append("end")


def test_get_status_returns_standard_dict():
    adapter = FakeAdapter()
    service = CastService("192.168.0.39", timeout_seconds=5, adapter=adapter)

    status = service.get_status()

    assert status["online"] is True
    assert status["name"] == "Play Box"
    assert status["app_id"] == "CC1AD845"
    assert status["media"] == {"player_state": "PLAYING"}
    assert adapter.connect_calls == 1


def test_missing_cast_ip_is_domain_error():
    service = CastService("", adapter=FakeAdapter())

    with pytest.raises(CastDeviceUnavailable, match="not configured"):
        service.get_status()


def test_connect_maps_adapter_unavailable_error():
    adapter = FakeAdapter()
    adapter.fail_connect = CastDeviceUnavailable("not found")
    service = CastService("192.168.0.39", adapter=adapter)

    with pytest.raises(CastDeviceUnavailable, match="not found"):
        service.connect()


def test_status_error_drops_connection_and_reconnects_next_time():
    adapter = FakeAdapter()
    service = CastService("192.168.0.39", adapter=adapter)

    service.connect()
    adapter.fail_status = True
    with pytest.raises(CastConnectionTimeout):
        service.get_status()

    adapter.fail_status = False
    service.get_status()

    assert adapter.connect_calls == 2


def test_media_command_returns_standard_result():
    adapter = FakeAdapter()
    service = CastService("192.168.0.39", timeout_seconds=7, adapter=adapter)

    result = service.play_media("http://nas/media/image.jpg", "image/jpeg")

    assert result == {
        "ok": True,
        "command": "play_media",
        "message": "Media playback started",
    }
    assert adapter.commands == [
        ("play_media", "http://nas/media/image.jpg", "image/jpeg", 7)
    ]


def test_volume_is_validated_before_command():
    adapter = FakeAdapter()
    service = CastService("192.168.0.39", adapter=adapter)

    with pytest.raises(CastUnsupportedCommand, match="between 0 and 1"):
        service.set_volume(1.1)

    assert adapter.commands == []


def test_quit_app_returns_standard_result():
    adapter = FakeAdapter()
    service = CastService("192.168.0.39", adapter=adapter)

    result = service.quit_app()

    assert result == {
        "ok": True,
        "command": "quit_app",
        "message": "Active Cast app closed",
    }
    assert adapter.commands == [("quit_app",)]


def test_commands_are_serialized_by_lock():
    adapter = SlowAdapter()
    service = CastService("192.168.0.39", adapter=adapter)

    first = threading.Thread(target=service.pause)
    second = threading.Thread(target=service.pause)

    first.start()
    second.start()
    first.join()
    second.join()

    assert adapter.lock_observed == ["start", "end", "start", "end"]
