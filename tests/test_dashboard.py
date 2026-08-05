from app.services.cast_service import CastDeviceUnavailable


class FakeStatusCastService:
    def __init__(self, status=None, error=None):
        self.status = status or {
            "online": True,
            "name": "Play Box",
            "model_name": "Android TV",
            "app_name": "Netflix",
            "app_id": "native-app",
            "is_stand_by": False,
            "is_active_input": True,
            "volume_level": 0.35,
            "volume_muted": False,
            "media": {},
            "message": "Active application does not expose standard media status",
        }
        self.error = error
        self.get_status_calls = 0

    def get_status(self):
        self.get_status_calls += 1
        if self.error is not None:
            raise self.error
        return self.status


def login(app, client):
    app.extensions["user_store"].create_admin("admin", "secret-password")
    return client.post(
        "/login",
        data={"username": "admin", "password": "secret-password"},
        follow_redirects=True,
    )


def test_dashboard_requires_login(client):
    response = client.get("/")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_status_requires_login(client):
    response = client.get("/status")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_redirects_to_dashboard(app, client):
    response = login(app, client)

    assert response.status_code == 200
    assert "Urządzenie Cast" in response.get_data(as_text=True)
    assert 'data-i18n="status.loading"' in response.get_data(as_text=True)


def test_status_returns_cast_status(app, client):
    fake_service = FakeStatusCastService()
    app.extensions["cast_service"] = fake_service
    login(app, client)

    response = client.get("/status")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["status"]["name"] == "Play Box"
    assert payload["status"]["media"] == {}
    assert fake_service.get_status_calls == 1


def test_status_maps_cast_errors_to_offline_payload(app, client):
    fake_service = FakeStatusCastService(
        error=CastDeviceUnavailable("Configured Cast device was not found")
    )
    app.extensions["cast_service"] = fake_service
    login(app, client)

    response = client.get("/status")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is False
    assert payload["status"]["online"] is False
    assert payload["status"]["message"] == "Configured Cast device was not found"
