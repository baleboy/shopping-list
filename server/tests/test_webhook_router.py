import hmac
import hashlib
import json
from unittest.mock import patch
from app.config import settings


def test_webhook_triggers_git_pull(client):
    settings.github_webhook_secret = ""
    with patch("app.routers.webhook.git_pull") as mock_pull:
        mock_pull.return_value = True
        response = client.post("/webhook", json={"ref": "refs/heads/main"})
    assert response.status_code == 200
    mock_pull.assert_called_once()


def test_webhook_validates_signature(client):
    settings.github_webhook_secret = "test-secret"
    payload = json.dumps({"ref": "refs/heads/main"}).encode()
    sig = "sha256=" + hmac.new(b"test-secret", payload, hashlib.sha256).hexdigest()

    with patch("app.routers.webhook.git_pull") as mock_pull:
        mock_pull.return_value = True
        response = client.post(
            "/webhook",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": sig
            }
        )
    assert response.status_code == 200
    settings.github_webhook_secret = ""


def test_webhook_rejects_bad_signature(client):
    settings.github_webhook_secret = "test-secret"
    response = client.post(
        "/webhook",
        json={"ref": "refs/heads/main"},
        headers={"X-Hub-Signature-256": "sha256=bad"}
    )
    assert response.status_code == 401
    settings.github_webhook_secret = ""
