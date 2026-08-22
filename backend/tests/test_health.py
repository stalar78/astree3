from fastapi.testclient import TestClient

from app.main import create_app


def test_app_can_be_created() -> None:
    app = create_app()
    assert app.title == "Astrea API"


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
