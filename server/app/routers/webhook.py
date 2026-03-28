import hmac
import hashlib
from fastapi import APIRouter, Request, HTTPException
from app.config import settings
from app.services.git_sync import git_pull

router = APIRouter(tags=["webhook"])


@router.post("/webhook")
async def github_webhook(request: Request):
    body = await request.body()

    if settings.github_webhook_secret:
        signature = request.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + hmac.new(
            settings.github_webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=401, detail="Invalid signature")

    git_pull()
    return {"status": "ok"}
