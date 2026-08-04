import pytest

from app import create_app
from app.config import TestConfig


@pytest.fixture()
def app(tmp_path):
    class RuntimeTestConfig(TestConfig):
        BASE_DIRECTORY = str(tmp_path)
        DATABASE_PATH = str(tmp_path / "instance" / "app.sqlite3")
        MEDIA_DIRECTORY = str(tmp_path / "media")
        LOG_DIRECTORY = str(tmp_path / "logs")
        PRESETS_PATH = str(tmp_path / "instance" / "presets.json")
        SETTINGS_PATH = str(tmp_path / "instance" / "config.json")

    return create_app(RuntimeTestConfig)


@pytest.fixture()
def client(app):
    return app.test_client()
