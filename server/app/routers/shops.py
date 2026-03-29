from typing import List
from fastapi import APIRouter, HTTPException
from app.models import ShopProfile, CreateShopRequest, UpdateShopRequest
from app.services.shop_service import list_shops, get_shop, create_shop, update_shop, delete_shop

router = APIRouter(prefix="/shops", tags=["shops"])


@router.get("", response_model=List[ShopProfile])
async def get_shops():
    return list_shops()


@router.get("/{shop_id}", response_model=ShopProfile)
async def get_shop_by_id(shop_id: str):
    shop = get_shop(shop_id)
    if shop is None:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop


@router.post("", response_model=ShopProfile, status_code=201)
async def create_new_shop(body: CreateShopRequest):
    return create_shop(body.name)


@router.put("/{shop_id}", response_model=ShopProfile)
async def update_existing_shop(shop_id: str, body: UpdateShopRequest):
    result = update_shop(shop_id, body.name, body.sections)
    if result is None:
        raise HTTPException(status_code=404, detail="Shop not found")
    return result


@router.delete("/{shop_id}")
async def delete_existing_shop(shop_id: str):
    if not delete_shop(shop_id):
        raise HTTPException(status_code=404, detail="Shop not found")
    return {"status": "ok"}
