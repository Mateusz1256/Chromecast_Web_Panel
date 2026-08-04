import mimetypes
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

ALLOWED_IMAGE_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

ALLOWED_AUDIO_TYPES = {
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".aac": "audio/aac",
    ".ogg": "audio/ogg",
    ".wav": "audio/wav",
}

ALLOWED_VIDEO_TYPES = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
}

ALLOWED_MEDIA_TYPES = {}
ALLOWED_MEDIA_TYPES.update(ALLOWED_IMAGE_TYPES)
ALLOWED_MEDIA_TYPES.update(ALLOWED_AUDIO_TYPES)
ALLOWED_MEDIA_TYPES.update(ALLOWED_VIDEO_TYPES)


class MediaValidationError(ValueError):
    pass


class MediaNotFoundError(FileNotFoundError):
    pass


@dataclass
class MediaFile:
    filename: str
    size_bytes: int
    content_type: str
    media_type: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MediaService:
    def __init__(
        self,
        settings_service,
        base_directory: str,
        fallback_media_directory: str = "",
    ):
        self.settings_service = settings_service
        self.base_directory = Path(base_directory).resolve()
        self.fallback_media_directory = fallback_media_directory

    def list_images(self) -> List[Dict[str, Any]]:
        return self.list_media("image")

    def list_media(self, media_type: str = "all") -> List[Dict[str, Any]]:
        media_directory = self.media_directory
        media_directory.mkdir(parents=True, exist_ok=True)
        media_files = []
        paths = sorted(media_directory.iterdir(), key=lambda item: item.name.lower())
        for path in paths:
            if not path.is_file():
                continue
            current_type = self.media_type_for(path.name)
            if current_type == "unknown":
                continue
            if media_type != "all" and current_type != media_type:
                continue
            media_files.append(
                MediaFile(
                    filename=path.name,
                    size_bytes=path.stat().st_size,
                    content_type=self.content_type_for(path.name),
                    media_type=current_type,
                ).to_dict()
            )
        return media_files

    def save_image(self, uploaded_file: FileStorage) -> Dict[str, Any]:
        return self.save_media(uploaded_file, expected_media_type="image")

    def save_media(
        self,
        uploaded_file: FileStorage,
        expected_media_type: str = "all",
    ) -> Dict[str, Any]:
        if not uploaded_file or not uploaded_file.filename:
            raise MediaValidationError("Choose a media file")

        filename = secure_filename(uploaded_file.filename)
        if not filename:
            raise MediaValidationError("Media filename is invalid")

        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_MEDIA_TYPES:
            raise MediaValidationError("Unsupported media extension")

        media_type = self.media_type_for(filename)
        if expected_media_type != "all" and media_type != expected_media_type:
            raise MediaValidationError("Unsupported media type for this upload")

        expected_content_type = ALLOWED_MEDIA_TYPES[suffix]
        accepted_mime_types = self.accepted_mime_types_for(suffix)
        if uploaded_file.mimetype not in accepted_mime_types:
            raise MediaValidationError("Unsupported media MIME type")
        self._validate_signature(uploaded_file, media_type, expected_content_type)

        size_bytes = self._measure_upload(uploaded_file)
        max_bytes = int(self.settings["max_upload_mb"]) * 1024 * 1024
        if size_bytes > max_bytes:
            raise MediaValidationError("Media exceeds configured upload limit")

        media_directory = self.media_directory
        media_directory.mkdir(parents=True, exist_ok=True)
        target = self._unique_path(media_directory / filename)
        uploaded_file.save(str(target))
        return MediaFile(
            filename=target.name,
            size_bytes=target.stat().st_size,
            content_type=expected_content_type,
            media_type=media_type,
        ).to_dict()

    def delete(self, filename: str) -> None:
        path = self.resolve_media_path(filename)
        if not path.exists() or not path.is_file():
            raise MediaNotFoundError(filename)
        path.unlink()

    def resolve_media_path(self, filename: str) -> Path:
        if not filename or "/" in filename or "\\" in filename:
            raise MediaValidationError("Invalid media filename")
        if Path(filename).name != filename:
            raise MediaValidationError("Invalid media filename")
        path = (self.media_directory / filename).resolve()
        try:
            path.relative_to(self.media_directory)
        except ValueError as exc:
            raise MediaValidationError("Path traversal is not allowed") from exc
        if path.suffix.lower() not in ALLOWED_MEDIA_TYPES:
            raise MediaValidationError("Unsupported media type")
        return path

    def public_url(self, filename: str) -> str:
        self.resolve_media_path(filename)
        settings = self.settings
        return "http://{}:{}/media/files/{}".format(
            settings["nas_lan_ip"],
            settings["app_port"],
            filename,
        )

    def content_type_for(self, filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix in ALLOWED_MEDIA_TYPES:
            return ALLOWED_MEDIA_TYPES[suffix]
        guessed, _ = mimetypes.guess_type(filename)
        return guessed or "application/octet-stream"

    def media_type_for(self, filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix in ALLOWED_IMAGE_TYPES:
            return "image"
        if suffix in ALLOWED_AUDIO_TYPES:
            return "audio"
        if suffix in ALLOWED_VIDEO_TYPES:
            return "video"
        return "unknown"

    def accepted_mime_types_for(self, suffix: str) -> List[str]:
        content_type = ALLOWED_MEDIA_TYPES[suffix]
        aliases = {
            ".m4a": ["audio/mp4", "audio/x-m4a"],
            ".aac": ["audio/aac", "audio/aacp", "audio/mp4"],
            ".ogg": ["audio/ogg", "application/ogg"],
            ".wav": ["audio/wav", "audio/x-wav"],
        }
        return aliases.get(suffix, [content_type])

    @property
    def media_directory(self) -> Path:
        raw_path = Path(str(self.settings["media_directory"]))
        if not raw_path.is_absolute():
            raw_path = self.base_directory / raw_path
        resolved = raw_path.resolve()
        try:
            resolved.relative_to(self.base_directory)
        except ValueError as exc:
            raise MediaValidationError(
                "Media directory must be inside the project"
            ) from exc
        return resolved

    @property
    def settings(self) -> Dict[str, Any]:
        settings = self.settings_service.load()
        use_fallback_directory = (
            not self.settings_service.config_path.exists()
            and self.fallback_media_directory
        )
        if use_fallback_directory:
            settings["media_directory"] = self.fallback_media_directory
        return settings

    def _measure_upload(self, uploaded_file: FileStorage) -> int:
        stream = uploaded_file.stream
        current_position = stream.tell()
        stream.seek(0, 2)
        size_bytes = stream.tell()
        stream.seek(current_position)
        return size_bytes

    def _detect_image_type(self, uploaded_file: FileStorage) -> str:
        stream = uploaded_file.stream
        current_position = stream.tell()
        header = stream.read(16)
        stream.seek(current_position)

        if header.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
            return "image/webp"
        return ""

    def _validate_signature(
        self,
        uploaded_file: FileStorage,
        media_type: str,
        expected_content_type: str,
    ) -> None:
        if media_type != "image":
            return
        if self._detect_image_type(uploaded_file) != expected_content_type:
            raise MediaValidationError("Image content does not match its type")

    def _unique_path(self, target: Path) -> Path:
        if not target.exists():
            return target

        stem = target.stem
        suffix = target.suffix
        for index in range(1, 1000):
            candidate = target.with_name(f"{stem}-{index}{suffix}")
            if not candidate.exists():
                return candidate
        raise MediaValidationError("Could not create a unique filename")
