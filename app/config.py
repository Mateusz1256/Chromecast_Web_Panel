import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class AppConfig:
    BASE_DIRECTORY = str(BASE_DIR)
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    APP_HOST = os.environ.get("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.environ.get("APP_PORT", "5000"))
    CAST_IP = os.environ.get("CAST_IP", "")
    CAST_TIMEOUT_SECONDS = float(os.environ.get("CAST_TIMEOUT_SECONDS", "10"))
    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH",
        str(BASE_DIR / "instance" / "app.sqlite3"),
    )
    SETTINGS_PATH = os.environ.get(
        "SETTINGS_PATH",
        str(BASE_DIR / "instance" / "config.json"),
    )

    MEDIA_DIRECTORY = os.environ.get(
        "MEDIA_DIRECTORY",
        str(BASE_DIR / "media"),
    )
    LOG_DIRECTORY = os.environ.get(
        "LOG_DIRECTORY",
        str(BASE_DIR / "logs"),
    )
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_MAX_BYTES = int(os.environ.get("LOG_MAX_BYTES", "1048576"))
    LOG_BACKUP_COUNT = int(os.environ.get("LOG_BACKUP_COUNT", "3"))

    JSON_SORT_KEYS = False


class TestConfig(AppConfig):
    TESTING = True
    CAST_IP = "192.168.0.39"
    SECRET_KEY = "test-secret-key"
    WTF_CSRF_ENABLED = False
