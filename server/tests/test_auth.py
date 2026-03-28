from fastapi.testclient import TestClient
from app.config import settings
from app.main import app


def test_protected_endpoint_rejects_without_key(tmp_data_dir):
    settings.api_key = "secret123"
    client = TestClient(app)
    response = client.get("/shops")
    assert response.status_code == 401
    settings.api_key = ""


def test_protected_endpoint_accepts_valid_key(tmp_data_dir):
    settings.api_key = "secret123"
    client = TestClient(app)
    response = client.get("/shops", headers={"X-API-Key": "secret123"})
    assert response.status_code == 200
    settings.api_key = ""


def test_health_is_public(tmp_data_dir):
    settings.api_key = "secret123"
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    settings.api_key = ""


def test_webhook_is_public(tmp_data_dir):
    settings.api_key = "secret123"
    client = TestClient(app)
    response = client.post("/webhook", json={})
    assert response.status_code == 200
    settings.api_key = ""
