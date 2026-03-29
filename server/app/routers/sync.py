from fastapi import APIRouter, HTTPException
from app.services.git_sync import git_push

router = APIRouter(tags=["sync"])


@router.post("/sync")
async def sync():
    if not git_push():
        raise HTTPException(status_code=500, detail="Git sync failed")
    return {"status": "ok"}
