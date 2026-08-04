import ipaddress
import json
from pathlib import Path
from typing import Any, Dict, Tuple

DEFAULT_SETTINGS = {
    "cast_ip": "192.168.0.39",
    "nas_lan_ip": "192.168.0.10",
    "app_port": 5000,
    "media_directory": "media",
    "max_upload_mb": 100,
    "max_volume": 0.5,
    "default_audio_volume": 0.2,
    "cast_timeout_seconds": 10,
    "status_refresh_seconds": 5,
    "monitor_app_changes": False,
}


class SettingsValidationError(ValueError):
    def __init__(self, errors: Dict[str, str]):
        super().__init__("Settings validation failed")
        self.errors = errors


class SettingsService:
    def __init__(self, config_path: str, base_directory: str):
        self.config_path = Path(config_path)
        self.base_directory = Path(base_directory).resolve()

    def load(self) -> Dict[str, Any]:
        settings = dict(DEFAULT_SETTINGS)
        if self.config_path.exists():
            with self.config_path.open("r", encoding="utf-8") as config_file:
                loaded = json.load(config_file)
            if isinstance(loaded, dict):
                settings.update(_public_settings(loaded))
        return settings

    def save(self, values: Dict[str, Any]) -> Dict[str, Any]:
        settings, errors = self.validate(values)
        if errors:
            raise SettingsValidationError(errors)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w", encoding="utf-8") as config_file:
            json.dump(settings, config_file, indent=2, sort_keys=True)
        return settings

    def export(self) -> Dict[str, Any]:
        return _public_settings(self.load())

    def import_settings(self, values: Dict[str, Any]) -> Dict[str, Any]:
        return self.save(_public_settings(values))

    def validate(self, values: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
        settings = dict(DEFAULT_SETTINGS)
        settings.update(_public_settings(values))
        errors = {}

        _validate_ip(settings, errors, "cast_ip")
        _validate_ip(settings, errors, "nas_lan_ip")
        _validate_int_range(settings, errors, "app_port", 1, 65535)
        _validate_int_range(settings, errors, "max_upload_mb", 1, 2048)
        _validate_float_range(settings, errors, "max_volume", 0.01, 1)
        _validate_float_range(settings, errors, "default_audio_volume", 0, 1)
        _validate_float_range(settings, errors, "cast_timeout_seconds", 1, 60)
        _validate_float_range(settings, errors, "status_refresh_seconds", 1, 120)
        settings["monitor_app_changes"] = _coerce_bool(
            settings["monitor_app_changes"]
        )
        _validate_media_directory(settings, errors, self.base_directory)

        if (
            "max_volume" not in errors
            and "default_audio_volume" not in errors
            and settings["default_audio_volume"] > settings["max_volume"]
        ):
            errors["default_audio_volume"] = (
                "Default audio volume cannot exceed max volume"
            )

        return settings, errors


def _public_settings(values: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: values[key]
        for key in DEFAULT_SETTINGS
        if key in values
    }


def _validate_ip(settings: Dict[str, Any], errors: Dict[str, str], key: str) -> None:
    try:
        settings[key] = str(ipaddress.ip_address(str(settings[key])))
    except ValueError:
        errors[key] = "Enter a valid IP address"


def _validate_int_range(
    settings: Dict[str, Any],
    errors: Dict[str, str],
    key: str,
    minimum: int,
    maximum: int,
) -> None:
    try:
        value = int(settings[key])
    except (TypeError, ValueError):
        errors[key] = "Enter a whole number"
        return
    if value < minimum or value > maximum:
        errors[key] = f"Enter a value between {minimum} and {maximum}"
        return
    settings[key] = value


def _validate_float_range(
    settings: Dict[str, Any],
    errors: Dict[str, str],
    key: str,
    minimum: float,
    maximum: float,
) -> None:
    try:
        value = float(settings[key])
    except (TypeError, ValueError):
        errors[key] = "Enter a number"
        return
    if value < minimum or value > maximum:
        errors[key] = f"Enter a value between {minimum} and {maximum}"
        return
    settings[key] = value


def _validate_media_directory(
    settings: Dict[str, Any],
    errors: Dict[str, str],
    base_directory: Path,
) -> None:
    raw_path = str(settings["media_directory"]).strip()
    if not raw_path:
        errors["media_directory"] = "Media directory is required"
        return

    media_path = Path(raw_path)
    if not media_path.is_absolute():
        media_path = base_directory / media_path

    try:
        resolved = media_path.resolve()
    except OSError:
        errors["media_directory"] = "Media directory path is invalid"
        return

    if ".." in Path(raw_path).parts:
        errors["media_directory"] = "Path traversal is not allowed"
        return

    try:
        resolved.relative_to(base_directory)
    except ValueError:
        errors["media_directory"] = "Media directory must be inside the project"
        return

    settings["media_directory"] = str(resolved)


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return bool(value)
