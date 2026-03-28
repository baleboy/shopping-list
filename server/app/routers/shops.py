from typing import List
from fastapi import APIRouter, HTTPException
from app.models import ShopProfile
from app.services.shop_service import list_shops, get_shop

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
