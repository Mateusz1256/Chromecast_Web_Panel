
from app.services.settings_service import SettingsService


class FakeCastService:
    def __init__(self):
        self.connect_calls = 0

    def connect(self):
        self.connect_calls += 1
        return {"ok": True, "command": "connect", "message": "connected"}


def test_init_admin_cli_creates_hashed_user(app):
    runner = app.test_cli_runner()

    result = runner.invoke(
        args=[
            "init-admin",
            "--username",
            "admin",
            "--password",
            "secret-password",
        ]
    )

    assert result.exit_code == 0
    user = app.extensions["user_store"].get_by_username("admin")
    assert user is not None
    assert user.password_hash != "secret-password"


def test_init_admin_cli_refuses_second_admin(app):
    runner = app.test_cli_runner()
    runner.invoke(
        args=["init-admin", "--username", "admin", "--password", "secret-password"]
    )

    result = runner.invoke(
        args=["init-admin", "--username", "other", "--password", "secret-password"]
    )

    assert result.exit_code != 0
    assert "already exists" in result.output


def test_settings_requires_login(client):
    response = client.get("/settings")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_allows_access_to_settings(app, client):
    app.extensions["user_store"].create_admin("admin", "secret-password")

    login_response = client.post(
        "/login",
        data={"username": "admin", "password": "secret-password"},
        follow_redirects=True,
    )

    assert login_response.status_code == 200
    assert "Ustawienia" in login_response.get_data(as_text=True)


def test_invalid_login_is_rejected(app, client):
    app.extensions["user_store"].create_admin("admin", "secret-password")

    response = client.post(
        "/login",
        data={"username": "admin", "password": "wrong"},
        follow_redirects=True,
    )

    assert "Invalid username or password" in response.get_data(as_text=True)


def test_settings_service_rejects_invalid_ip_and_path(tmp_path):
    service = SettingsService(
        config_path=str(tmp_path / "config.json"),
        base_directory=str(tmp_path),
    )

    _, errors = service.validate(
        {
            "cast_ip": "999.1.1.1",
            "nas_lan_ip": "192.168.0.10",
            "media_directory": "../private",
        }
    )

    assert errors["cast_ip"] == "Enter a valid IP address"
    assert errors["media_directory"] == "Path traversal is not allowed"


def test_settings_service_rejects_path_outside_project(tmp_path):
    service = SettingsService(
        config_path=str(tmp_path / "config.json"),
        base_directory=str(tmp_path / "project"),
    )

    _, errors = service.validate(
        {
            "cast_ip": "192.168.0.39",
            "nas_lan_ip": "192.168.0.10",
            "media_directory": str(tmp_path / "outside"),
        }
    )

    assert errors["media_directory"] == "Media directory must be inside the project"


def test_settings_persist_after_save(tmp_path):
    config_path = tmp_path / "config.json"
    service = SettingsService(
        config_path=str(config_path),
        base_directory=str(tmp_path),
    )

    saved = service.save(
        {
            "cast_ip": "192.168.0.39",
            "nas_lan_ip": "192.168.0.10",
            "app_port": "5000",
            "media_directory": "media",
            "max_upload_mb": "50",
            "max_volume": "0.4",
            "default_audio_volume": "0.2",
            "cast_timeout_seconds": "8",
            "status_refresh_seconds": "5",
        }
    )
    reloaded = SettingsService(
        config_path=str(config_path),
        base_directory=str(tmp_path),
    ).load()

    assert saved == reloaded
    assert reloaded["media_directory"] == str((tmp_path / "media").resolve())


def test_import_rejects_secret_keys(app, client):
    app.extensions["user_store"].create_admin("admin", "secret-password")
    client.post(
        "/login",
        data={"username": "admin", "password": "secret-password"},
    )

    response = client.post(
        "/settings/import",
        json={
            "cast_ip": "192.168.0.39",
            "nas_lan_ip": "192.168.0.10",
            "secret_key": "must-not-persist",
        },
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert "secret_key" not in data["settings"]


def test_export_returns_public_settings_only(app, client):
    app.extensions["user_store"].create_admin("admin", "secret-password")
    client.post(
        "/login",
        data={"username": "admin", "password": "secret-password"},
    )
    app.extensions["settings_service"].save(
        {
            "cast_ip": "192.168.0.39",
            "nas_lan_ip": "192.168.0.10",
            "media_directory": "media",
        }
    )

    response = client.get("/settings/export")

    assert response.status_code == 200
    exported = response.get_json()
    assert "secret_key" not in exported
    assert exported["cast_ip"] == "192.168.0.39"


def test_test_cast_requires_login(client):
    response = client.post("/settings/test-cast")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_test_cast_uses_registered_service(app, client):
    app.extensions["user_store"].create_admin("admin", "secret-password")
    fake_cast_service = FakeCastService()
    app.extensions["cast_service"] = fake_cast_service
    client.post(
        "/login",
        data={"username": "admin", "password": "secret-password"},
    )

    response = client.post("/settings/test-cast")

    assert response.status_code == 200
    assert response.get_json()["ok"] is True
    assert fake_cast_service.connect_calls == 1
