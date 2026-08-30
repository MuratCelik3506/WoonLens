from fastapi.testclient import TestClient

from woonlens.bootstrap.settings import Settings
from woonlens.entrypoints.api import create_app


def test_health_endpoint_reports_ready() -> None:
    app = create_app(Settings(environment="test"))

    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_documentation_is_disabled_in_production() -> None:
    app = create_app(Settings(environment="production"))

    with TestClient(app) as client:
        response = client.get("/docs")

    assert response.status_code == 404
