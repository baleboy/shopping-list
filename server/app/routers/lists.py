import json
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.services.list_service import list_lists, get_list, create_list
from app.services.shop_service import get_shop
from app.services.categorizer import get_or_create_categorized_list, _cache_path
from app.models import CategorizedList

router = APIRouter(prefix="/lists", tags=["lists"])


class CreateListRequest(BaseModel):
    name: str


class ListResponse(BaseModel):
    name: str
    items: List[str]


class ToggleResponse(BaseModel):
    name: str
    checked: bool


@router.get("", response_model=List[str])
async def get_lists():
    return list_lists()


@router.get("/{name}", response_model=ListResponse)
async def get_list_by_name(name: str):
    items = get_list(name)
    if items is None:
        raise HTTPException(status_code=404, detail="List not found")
    return ListResponse(name=name, items=items)


@router.post("", response_model=ListResponse, status_code=201)
async def create_new_list(
    body: CreateListRequest,
    from_param: Optional[str] = Query(None, alias="from")
):
    items = create_list(body.name, from_master=(from_param == "master"))
    return ListResponse(name=body.name, items=items)


@router.post("/{name}/prepare", response_model=CategorizedList)
async def prepare_list(name: str, shop: str = Query(...)):
    shop_profile = get_shop(shop)
    if shop_profile is None:
        raise HTTPException(status_code=404, detail="Shop not found")
    result = get_or_create_categorized_list(name, shop_profile)
    if result is None:
        raise HTTPException(status_code=404, detail="List not found")
    return result


@router.patch("/{name}/items/{item}", response_model=ToggleResponse)
async def toggle_item(name: str, item: str, shop: str = Query(...)):
    cache = _cache_path(name, shop)
    if not cache.exists():
        raise HTTPException(status_code=404, detail="Prepared list not found. Call /prepare first.")

    data = json.loads(cache.read_text())
    cat_list = CategorizedList(**data)

    found = False
    new_checked = False
    for section in cat_list.sections:
        for si in section.items:
            if si.name == item:
                si.checked = not si.checked
                new_checked = si.checked
                found = True
                break
        if found:
            break

    if not found:
        raise HTTPException(status_code=404, detail="Item not found")

    cache.write_text(cat_list.model_dump_json(indent=2))
    return ToggleResponse(name=item, checked=new_checked)
