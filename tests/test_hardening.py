import pytest

from app import create_app
from app.config import AppConfig
from app.version import __version__


class WeakSecretConfig(AppConfig):
    TESTING = False
    SECRET_KEY = "dev-only-change-me"
    REQUIRE_STRONG_SECRET = True


def login(app, client):
    app.extensions["user_store"].create_admin("admin", "secret-password")
    return client.post(
        "/login",
        data={"username": "admin", "password": "secret-password"},
        follow_redirects=True,
    )


def test_version_is_1_0_0():
    assert __version__ == "1.0.0"


def test_app_refuses_placeholder_secret_key():
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(WeakSecretConfig)


def test_diagnostics_export_requires_login(client):
    response = client.get("/diagnostics/export")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_diagnostics_export_omits_secrets_and_full_paths(app, client):
    app.extensions["settings_service"].save(
        {
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
    )
    login(app, client)

    response = client.get("/diagnostics/export")

    assert response.status_code == 200
    data = response.get_json()
    assert data["app_version"] == "1.0.0"
    assert "SECRET_KEY" not in str(data)
    assert "password" not in str(data).lower()
    assert "media_directory" not in data["settings"]
    assert data["settings"]["media_directory_configured"] is True
