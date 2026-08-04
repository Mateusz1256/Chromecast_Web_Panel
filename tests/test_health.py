def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_app_registers_cast_service(app):
    service = app.extensions["cast_service"]

    assert service.cast_ip == "192.168.0.39"
    assert service.timeout_seconds == 10
