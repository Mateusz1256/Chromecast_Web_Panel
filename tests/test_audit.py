from app.services.audit_service import AuditService


class FakeCastStatusService:
    def __init__(self, app_id="APP1"):
        self.app_id = app_id

    def get_status(self):
        return {
            "online": True,
            "name": "Play Box",
            "model_name": "Android TV",
            "app_name": "Native App",
            "app_id": self.app_id,
            "is_stand_by": False,
            "is_active_input": True,
            "volume_level": 0.2,
            "volume_muted": False,
            "media": {"title": "should-not-be-audited"},
            "message": None,
        }


class FakeRemoteCastService(FakeCastStatusService):
    def mute(self):
        return {"ok": True, "command": "mute", "message": "Device muted"}


def login(app, client):
    app.extensions["user_store"].create_admin("admin", "secret-password")
    return client.post(
        "/login",
        data={"username": "admin", "password": "secret-password"},
        follow_redirects=True,
    )


def test_audit_service_redacts_sensitive_details(tmp_path):
    service = AuditService(
        log_path=str(tmp_path / "audit.log"),
        max_bytes=1024,
        backup_count=1,
        logger_name="audit-test-redact",
    )

    service.record(
        user="1",
        command="login",
        ok=False,
        details={
            "password": "secret",
            "csrf_token": "token",
            "safe": "value",
            "nested": {"title": "private title"},
        },
    )

    entry = service.recent_entries()[0]
    assert entry["details"]["password"] == "[redacted]"
    assert entry["details"]["csrf_token"] == "[redacted]"
    assert entry["details"]["nested"]["title"] == "[redacted]"
    assert entry["details"]["safe"] == "value"


def test_audit_service_keeps_recent_errors(tmp_path):
    service = AuditService(
        log_path=str(tmp_path / "audit.log"),
        max_bytes=1024,
        backup_count=1,
        logger_name="audit-test-errors",
    )

    service.record("1", "ok-command", True)
    service.record("1", "bad-command", False, error="failed")

    errors = service.recent_entries(errors_only=True)
    assert len(errors) == 1
    assert errors[0]["command"] == "bad-command"


def test_remote_command_writes_audit_entry(app, client):
    app.extensions["cast_service"] = FakeRemoteCastService()
    login(app, client)

    response = client.post("/remote/mute")

    assert response.status_code == 200
    entry = app.extensions["audit_service"].recent_entries()[0]
    assert entry["command"] == "remote.mute"
    assert entry["ok"] is True


def test_app_change_monitoring_is_disabled_by_default(app, client):
    app.extensions["cast_service"] = FakeCastStatusService()
    login(app, client)

    response = client.get("/status")

    assert response.status_code == 200
    assert app.extensions["audit_service"].recent_entries() == []


def test_app_change_monitoring_requires_explicit_setting(app, client):
    app.extensions["cast_service"] = FakeCastStatusService(app_id="APP2")
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
            "monitor_app_changes": True,
        }
    )
    login(app, client)

    response = client.get("/status")

    assert response.status_code == 200
    entry = app.extensions["audit_service"].recent_entries()[0]
    assert entry["command"] == "app_change"
    assert "title" not in entry["details"]


def test_audit_panel_requires_login(client):
    response = client.get("/audit")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
