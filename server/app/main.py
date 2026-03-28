from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from app.config import settings
from app.routers import shops, lists

app = FastAPI(title="Shopping List API")

app.include_router(shops.router)
app.include_router(lists.router)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(key: str = Security(api_key_header)):
    if settings.api_key and key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/health")
async def health():
    return {"status": "ok"}
