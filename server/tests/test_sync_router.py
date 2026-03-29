from unittest.mock import patch


def test_sync_success(client):
    with patch("app.routers.sync.git_push", return_value=True):
        response = client.post("/sync")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_sync_failure(client):
    with patch("app.routers.sync.git_push", return_value=False):
        response = client.post("/sync")
    assert response.status_code == 500
    assert "failed" in response.json()["detail"].lower()
