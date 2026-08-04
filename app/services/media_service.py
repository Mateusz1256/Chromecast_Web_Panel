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


class MediaValidationError(ValueError):
    pass


class MediaNotFoundError(FileNotFoundError):
    pass


@dataclass
class MediaFile:
    filename: str
    size_bytes: int
    content_type: str

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
        media_directory = self.media_directory
        media_directory.mkdir(parents=True, exist_ok=True)
        images = []
        paths = sorted(media_directory.iterdir(), key=lambda item: item.name.lower())
        for path in paths:
            if path.is_file() and path.suffix.lower() in ALLOWED_IMAGE_TYPES:
                images.append(
                    MediaFile(
                        filename=path.name,
                        size_bytes=path.stat().st_size,
                        content_type=self.content_type_for(path.name),
                    ).to_dict()
                )
        return images

    def save_image(self, uploaded_file: FileStorage) -> Dict[str, Any]:
        if not uploaded_file or not uploaded_file.filename:
            raise MediaValidationError("Choose an image file")

        filename = secure_filename(uploaded_file.filename)
        if not filename:
            raise MediaValidationError("Image filename is invalid")

        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_IMAGE_TYPES:
            raise MediaValidationError("Unsupported image extension")

        expected_content_type = ALLOWED_IMAGE_TYPES[suffix]
        if uploaded_file.mimetype != expected_content_type:
            raise MediaValidationError("Unsupported image MIME type")
        if self._detect_image_type(uploaded_file) != expected_content_type:
            raise MediaValidationError("Image content does not match its type")

        size_bytes = self._measure_upload(uploaded_file)
        max_bytes = int(self.settings["max_upload_mb"]) * 1024 * 1024
        if size_bytes > max_bytes:
            raise MediaValidationError("Image exceeds configured upload limit")

        media_directory = self.media_directory
        media_directory.mkdir(parents=True, exist_ok=True)
        target = self._unique_path(media_directory / filename)
        uploaded_file.save(str(target))
        return MediaFile(
            filename=target.name,
            size_bytes=target.stat().st_size,
            content_type=expected_content_type,
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
        if path.suffix.lower() not in ALLOWED_IMAGE_TYPES:
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
        if suffix in ALLOWED_IMAGE_TYPES:
            return ALLOWED_IMAGE_TYPES[suffix]
        guessed, _ = mimetypes.guess_type(filename)
        return guessed or "application/octet-stream"

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
