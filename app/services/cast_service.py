import threading
from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, Optional


class CastServiceError(Exception):
    """Base exception for Cast domain errors."""


class CastDeviceUnavailable(CastServiceError):
    """Raised when the configured Cast device cannot be found."""


class CastConnectionTimeout(CastServiceError):
    """Raised when a Cast operation exceeds its timeout."""


class CastUnsupportedCommand(CastServiceError):
    """Raised when a command is not supported by the current Cast state."""


class CastMediaLaunchFailed(CastServiceError):
    """Raised when Default Media Receiver cannot launch media."""


@dataclass
class CastCommandResult:
    ok: bool
    command: str
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CastStatus:
    online: bool
    name: Optional[str]
    model_name: Optional[str]
    app_name: Optional[str]
    app_id: Optional[str]
    is_stand_by: Optional[bool]
    is_active_input: Optional[bool]
    volume_level: Optional[float]
    volume_muted: Optional[bool]
    media: Dict[str, Any]
    message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PyChromecastAdapter:
    def connect(self, cast_ip: str, timeout: float) -> Any:
        try:
            import pychromecast  # type: ignore
        except ImportError as exc:
            raise CastDeviceUnavailable("pychromecast is not installed") from exc

        try:
            chromecasts, browser = pychromecast.get_chromecasts(
                known_hosts=[cast_ip],
                timeout=timeout,
            )
        except TimeoutError as exc:
            raise CastConnectionTimeout("Cast connection timed out") from exc
        except Exception as exc:
            raise CastDeviceUnavailable("Cast device is unavailable") from exc

        if not chromecasts:
            self._stop_discovery(browser)
            raise CastDeviceUnavailable("Configured Cast device was not found")

        cast = chromecasts[0]
        try:
            cast.wait(timeout=timeout)
        except TimeoutError as exc:
            self._stop_discovery(browser)
            raise CastConnectionTimeout("Cast connection timed out") from exc
        except Exception as exc:
            self._stop_discovery(browser)
            raise CastDeviceUnavailable("Cast device is unavailable") from exc

        return {"cast": cast, "browser": browser}

    def disconnect(self, handle: Any) -> None:
        cast = handle.get("cast") if isinstance(handle, dict) else None
        browser = handle.get("browser") if isinstance(handle, dict) else None
        if cast is not None and hasattr(cast, "disconnect"):
            cast.disconnect()
        self._stop_discovery(browser)

    def get_status(self, handle: Any) -> Dict[str, Any]:
        cast = handle["cast"]
        return _status_from_cast(cast).to_dict()

    def play_media(
        self,
        handle: Any,
        media_url: str,
        content_type: str,
        timeout: float,
    ) -> None:
        cast = handle["cast"]
        media_controller = getattr(cast, "media_controller", None)
        if media_controller is None:
            raise CastUnsupportedCommand("Media controller is unavailable")

        try:
            media_controller.play_media(media_url, content_type)
            media_controller.block_until_active(timeout=timeout)
        except TimeoutError as exc:
            raise CastConnectionTimeout("Media launch timed out") from exc
        except Exception as exc:
            raise CastMediaLaunchFailed("Media launch failed") from exc

    def pause(self, handle: Any) -> None:
        self._media_command(handle, "pause")

    def resume(self, handle: Any) -> None:
        self._media_command(handle, "play")

    def stop(self, handle: Any) -> None:
        self._media_command(handle, "stop")

    def quit_app(self, handle: Any) -> None:
        cast = handle["cast"]
        command = getattr(cast, "quit_app", None)
        try:
            if command is not None:
                command()
                return
            receiver_controller = getattr(cast, "receiver_controller", None)
            stop_app = getattr(receiver_controller, "stop_app", None)
            if stop_app is None:
                raise CastUnsupportedCommand("Closing the active app is unsupported")
            stop_app()
        except CastUnsupportedCommand:
            raise
        except Exception as exc:
            raise CastUnsupportedCommand(
                "Closing the active app is unsupported"
            ) from exc

    def seek(self, handle: Any, seconds: float) -> None:
        media_controller = self._media_controller(handle)
        try:
            media_controller.seek(seconds)
        except Exception as exc:
            raise CastUnsupportedCommand("Seek is unsupported") from exc

    def set_volume(self, handle: Any, level: float) -> None:
        cast = handle["cast"]
        try:
            cast.set_volume(level)
        except Exception as exc:
            raise CastUnsupportedCommand("Volume command is unsupported") from exc

    def mute(self, handle: Any) -> None:
        self._set_muted(handle, True)

    def unmute(self, handle: Any) -> None:
        self._set_muted(handle, False)

    def _media_controller(self, handle: Any) -> Any:
        media_controller = getattr(handle["cast"], "media_controller", None)
        if media_controller is None:
            raise CastUnsupportedCommand("Media controller is unavailable")
        return media_controller

    def _media_command(self, handle: Any, command_name: str) -> None:
        media_controller = self._media_controller(handle)
        command = getattr(media_controller, command_name, None)
        if command is None:
            raise CastUnsupportedCommand(f"{command_name} is unsupported")
        try:
            command()
        except Exception as exc:
            raise CastUnsupportedCommand(f"{command_name} is unsupported") from exc

    def _set_muted(self, handle: Any, muted: bool) -> None:
        cast = handle["cast"]
        try:
            cast.set_volume_muted(muted)
        except Exception as exc:
            raise CastUnsupportedCommand("Mute command is unsupported") from exc

    def _stop_discovery(self, browser: Any) -> None:
        if browser is not None and hasattr(browser, "stop_discovery"):
            browser.stop_discovery()


class CastService:
    def __init__(
        self,
        cast_ip: str,
        timeout_seconds: float = 10,
        adapter: Optional[Any] = None,
    ):
        self.cast_ip = cast_ip
        self.timeout_seconds = timeout_seconds
        self.adapter = adapter or PyChromecastAdapter()
        self._lock = threading.RLock()
        self._handle = None

    def connect(self) -> Dict[str, Any]:
        self._require_cast_ip()
        with self._lock:
            self._replace_connection()
        return CastCommandResult(
            ok=True,
            command="connect",
            message="Connected to Cast device",
        ).to_dict()

    def disconnect(self) -> Dict[str, Any]:
        with self._lock:
            if self._handle is not None:
                self.adapter.disconnect(self._handle)
                self._handle = None
        return CastCommandResult(
            ok=True,
            command="disconnect",
            message="Disconnected from Cast device",
        ).to_dict()

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            handle = self._ensure_connected()
            try:
                return self.adapter.get_status(handle)
            except CastServiceError:
                self._handle = None
                raise

    def play_media(self, media_url: str, content_type: str) -> Dict[str, Any]:
        self._run_connected_command(
            lambda handle: self.adapter.play_media(
                handle,
                media_url,
                content_type,
                self.timeout_seconds,
            )
        )
        return CastCommandResult(
            ok=True,
            command="play_media",
            message="Media playback started",
        ).to_dict()

    def show_image(self, media_url: str, content_type: str) -> Dict[str, Any]:
        result = self.play_media(media_url, content_type)
        result["command"] = "show_image"
        result["message"] = "Image sent to Cast device"
        return result

    def pause(self) -> Dict[str, Any]:
        self._run_connected_command(self.adapter.pause)
        return self._command_result("pause", "Playback paused")

    def resume(self) -> Dict[str, Any]:
        self._run_connected_command(self.adapter.resume)
        return self._command_result("resume", "Playback resumed")

    def stop(self) -> Dict[str, Any]:
        self._run_connected_command(self.adapter.stop)
        return self._command_result("stop", "Playback stopped")

    def quit_app(self) -> Dict[str, Any]:
        self._run_connected_command(self.adapter.quit_app)
        return self._command_result("quit_app", "Active Cast app closed")

    def seek(self, seconds: float) -> Dict[str, Any]:
        if seconds < 0:
            raise CastUnsupportedCommand("Seek position cannot be negative")
        self._run_connected_command(lambda handle: self.adapter.seek(handle, seconds))
        return self._command_result("seek", "Seek command sent")

    def set_volume(self, level: float) -> Dict[str, Any]:
        if level < 0 or level > 1:
            raise CastUnsupportedCommand("Volume level must be between 0 and 1")
        self._run_connected_command(
            lambda handle: self.adapter.set_volume(handle, level)
        )
        return self._command_result("set_volume", "Volume command sent")

    def mute(self) -> Dict[str, Any]:
        self._run_connected_command(self.adapter.mute)
        return self._command_result("mute", "Device muted")

    def unmute(self) -> Dict[str, Any]:
        self._run_connected_command(self.adapter.unmute)
        return self._command_result("unmute", "Device unmuted")

    def _run_connected_command(self, command: Callable[[Any], None]) -> None:
        with self._lock:
            handle = self._ensure_connected()
            try:
                command(handle)
            except CastServiceError:
                self._handle = None
                raise

    def _ensure_connected(self) -> Any:
        self._require_cast_ip()
        if self._handle is None:
            self._handle = self.adapter.connect(self.cast_ip, self.timeout_seconds)
        return self._handle

    def _replace_connection(self) -> None:
        if self._handle is not None:
            self.adapter.disconnect(self._handle)
            self._handle = None
        self._handle = self.adapter.connect(self.cast_ip, self.timeout_seconds)

    def _require_cast_ip(self) -> None:
        if not self.cast_ip:
            raise CastDeviceUnavailable("Cast IP is not configured")

    def _command_result(self, command: str, message: str) -> Dict[str, Any]:
        return CastCommandResult(
            ok=True,
            command=command,
            message=message,
        ).to_dict()


def _status_from_cast(cast: Any) -> CastStatus:
    status = getattr(cast, "status", None)
    media_controller = getattr(cast, "media_controller", None)
    media_status = getattr(media_controller, "status", None)
    media = _media_status_to_dict(media_status)

    message = None
    if not media:
        message = "Active application does not expose standard media status"

    return CastStatus(
        online=True,
        name=getattr(cast, "name", None),
        model_name=getattr(cast, "model_name", None),
        app_name=getattr(status, "display_name", None),
        app_id=getattr(status, "app_id", None),
        is_stand_by=getattr(status, "is_stand_by", None),
        is_active_input=getattr(status, "is_active_input", None),
        volume_level=getattr(status, "volume_level", None),
        volume_muted=getattr(status, "volume_muted", None),
        media=media,
        message=message,
    )


def _media_status_to_dict(media_status: Any) -> Dict[str, Any]:
    if media_status is None:
        return {}

    interesting_fields = (
        "player_state",
        "title",
        "content_id",
        "content_type",
        "duration",
        "current_time",
    )
    media = {}
    for field in interesting_fields:
        value = getattr(media_status, field, None)
        if value is not None:
            media[field] = value
    return media
