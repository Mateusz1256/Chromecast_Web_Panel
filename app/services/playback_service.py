import json
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.cast_service import CastService
from app.services.media_service import MediaService, MediaValidationError


class PlaybackJobAlreadyRunning(ValueError):
    pass


class PlaybackJobNotRunning(ValueError):
    pass


@dataclass
class Preset:
    name: str
    filename: str
    media_type: str
    volume: Optional[float] = None
    stop_after_seconds: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PlaybackService:
    def __init__(
        self,
        media_service: MediaService,
        cast_service: CastService,
        presets_path: str,
    ):
        self.media_service = media_service
        self.cast_service = cast_service
        self.presets_path = Path(presets_path)
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None
        self._status = {
            "active": False,
            "kind": None,
            "current": None,
            "message": "No active job",
        }

    def start_slideshow(
        self,
        filenames: List[str],
        slide_seconds: float,
    ) -> Dict[str, Any]:
        if slide_seconds < 1:
            raise ValueError("Slide time must be at least 1 second")
        image_files = self._validate_files(filenames, expected_type="image")
        return self._start_job(
            kind="slideshow",
            target=self._run_slideshow,
            args=(image_files, slide_seconds),
        )

    def start_queue(self, filenames: List[str]) -> Dict[str, Any]:
        media_files = self._validate_files(filenames)
        return self._start_job(
            kind="queue",
            target=self._run_queue,
            args=(media_files,),
        )

    def stop(self) -> Dict[str, Any]:
        with self._lock:
            if not self._status["active"]:
                raise PlaybackJobNotRunning("No active job")
            self._stop_event.set()
            self._status["message"] = "Stopping job"
            return dict(self._status)

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._status)

    def load_presets(self) -> List[Dict[str, Any]]:
        if not self.presets_path.exists():
            return []
        with self.presets_path.open("r", encoding="utf-8") as presets_file:
            data = json.load(presets_file)
        if not isinstance(data, list):
            return []
        return [item for item in data if isinstance(item, dict)]

    def save_preset(
        self,
        name: str,
        filename: str,
        volume: Optional[float] = None,
        stop_after_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        name = name.strip()
        if not name:
            raise ValueError("Preset name is required")
        if volume is not None:
            max_volume = float(self.media_service.settings["max_volume"])
            if volume < 0 or volume > max_volume:
                raise ValueError("Preset volume exceeds configured max volume")
        if stop_after_seconds is not None and stop_after_seconds < 1:
            raise ValueError("Stop time must be at least 1 second")
        media_type = self._media_file(filename)["media_type"]
        preset = Preset(
            name=name,
            filename=filename,
            media_type=media_type,
            volume=volume,
            stop_after_seconds=stop_after_seconds,
        ).to_dict()
        presets = [item for item in self.load_presets() if item.get("name") != name]
        presets.append(preset)
        self._write_presets(presets)
        return preset

    def delete_preset(self, name: str) -> None:
        presets = [item for item in self.load_presets() if item.get("name") != name]
        self._write_presets(presets)

    def run_preset(self, name: str) -> Dict[str, Any]:
        preset = self._find_preset(name)
        return self._start_job(
            kind="preset",
            target=self._run_preset,
            args=(preset,),
        )

    def _start_job(self, kind: str, target, args) -> Dict[str, Any]:
        with self._lock:
            if self._status["active"]:
                raise PlaybackJobAlreadyRunning("A playback job is already active")
            self._stop_event = threading.Event()
            self._status = {
                "active": True,
                "kind": kind,
                "current": None,
                "message": f"Starting {kind}",
            }
            self._thread = threading.Thread(target=target, args=args, daemon=True)
            self._thread.start()
            return dict(self._status)

    def _run_slideshow(self, media_files, slide_seconds: float) -> None:
        try:
            for media_file in media_files:
                if self._stop_event.is_set():
                    break
                self._play_media_file(media_file)
                self._set_current(media_file["filename"], "Showing slide")
                self._stop_event.wait(slide_seconds)
        finally:
            self._finish_job("Slideshow stopped")

    def _run_queue(self, media_files) -> None:
        try:
            for media_file in media_files:
                if self._stop_event.is_set():
                    break
                self._play_media_file(media_file)
                self._set_current(media_file["filename"], "Playing queued media")
        finally:
            self._finish_job("Queue finished")

    def _run_preset(self, preset: Dict[str, Any]) -> None:
        try:
            if preset.get("volume") is not None:
                self.cast_service.set_volume(float(preset["volume"]))
            media_file = self._media_file(preset["filename"])
            self._play_media_file(media_file)
            self._set_current(preset["filename"], "Running preset")
            stop_after = preset.get("stop_after_seconds")
            if stop_after:
                if not self._stop_event.wait(float(stop_after)):
                    self.cast_service.stop()
        finally:
            self._finish_job("Preset finished")

    def _play_media_file(self, media_file: Dict[str, Any]) -> None:
        filename = media_file["filename"]
        media_url = self.media_service.public_url(filename)
        content_type = media_file["content_type"]
        if media_file["media_type"] == "image":
            self.cast_service.show_image(media_url, content_type)
        else:
            self.cast_service.play_media(media_url, content_type)

    def _set_current(self, filename: str, message: str) -> None:
        with self._lock:
            self._status["current"] = filename
            self._status["message"] = message

    def _finish_job(self, message: str) -> None:
        with self._lock:
            self._status = {
                "active": False,
                "kind": None,
                "current": None,
                "message": message,
            }

    def _validate_files(
        self,
        filenames: List[str],
        expected_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not filenames:
            raise ValueError("Choose at least one media file")
        media_files = []
        for filename in filenames:
            media_file = self._media_file(filename)
            if expected_type and media_file["media_type"] != expected_type:
                raise MediaValidationError("Only images can be used in slideshow")
            media_files.append(media_file)
        return media_files

    def _media_file(self, filename: str) -> Dict[str, Any]:
        path = self.media_service.resolve_media_path(filename)
        if not path.exists() or not path.is_file():
            raise MediaValidationError("Media file does not exist")
        return {
            "filename": path.name,
            "size_bytes": path.stat().st_size,
            "content_type": self.media_service.content_type_for(path.name),
            "media_type": self.media_service.media_type_for(path.name),
        }

    def _find_preset(self, name: str) -> Dict[str, Any]:
        for preset in self.load_presets():
            if preset.get("name") == name:
                return preset
        raise ValueError("Preset does not exist")

    def _write_presets(self, presets: List[Dict[str, Any]]) -> None:
        self.presets_path.parent.mkdir(parents=True, exist_ok=True)
        with self.presets_path.open("w", encoding="utf-8") as presets_file:
            json.dump(presets, presets_file, indent=2, sort_keys=True)
