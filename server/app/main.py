from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.routers import shops, lists, webhook, sync

app = FastAPI(title="Shopping List API")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(key: str = Security(api_key_header)):
    if settings.api_key and key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


app.include_router(shops.router, dependencies=[Depends(verify_api_key)])
app.include_router(lists.router, dependencies=[Depends(verify_api_key)])
app.include_router(webhook.router)
app.include_router(sync.router, dependencies=[Depends(verify_api_key)])

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def serve_frontend():
    return FileResponse(static_dir / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}
