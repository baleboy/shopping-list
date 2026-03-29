import json
import re
from typing import List, Optional
from pathlib import Path

import yaml
from app.config import settings
from app.models import ShopProfile


DEFAULT_SECTIONS = [
    "produce",
    "bakery",
    "dairy & eggs",
    "meat & fish",
    "pasta & grains",
    "canned goods",
    "oils & condiments",
    "frozen",
    "household",
]


def _shops_dir() -> Path:
    return settings.data_dir / "shops"


def _cache_shops_dir() -> Path:
    d = settings.data_dir / "cache" / "shops"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _slugify(name: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return slug


def _load_yaml_shops() -> dict:
    shops_dir = _shops_dir()
    result = {}
    if not shops_dir.exists():
        return result
    for f in sorted(shops_dir.glob("*.yaml")):
        data = yaml.safe_load(f.read_text())
        shop_id = f.stem
        result[shop_id] = ShopProfile(
            id=shop_id,
            name=data["name"],
            sections=data.get("sections", [])
        )
    return result


def _load_cached_shops() -> dict:
    cache_dir = _cache_shops_dir()
    result = {}
    for f in sorted(cache_dir.glob("*.json")):
        data = json.loads(f.read_text())
        shop_id = f.stem
        if data.get("_deleted"):
            result[shop_id] = None
        else:
            result[shop_id] = ShopProfile(**data)
    return result


def _save_cached_shop(shop: ShopProfile) -> None:
    path = _cache_shops_dir() / f"{shop.id}.json"
    path.write_text(json.dumps(shop.model_dump(), indent=2))


def _invalidate_categorized_cache(shop_id: str) -> None:
    cache_dir = settings.data_dir / "cache"
    if not cache_dir.exists():
        return
    for f in cache_dir.glob(f"*_{shop_id}.json"):
        f.unlink()


def list_shops() -> List[ShopProfile]:
    yaml_shops = _load_yaml_shops()
    cached_shops = _load_cached_shops()
    merged = {}
    merged.update(yaml_shops)
    for shop_id, shop in cached_shops.items():
        if shop is None:
            merged.pop(shop_id, None)
        else:
            merged[shop_id] = shop
    return sorted(merged.values(), key=lambda s: s.name)


def get_shop(shop_id: str) -> Optional[ShopProfile]:
    cache_path = _cache_shops_dir() / f"{shop_id}.json"
    if cache_path.exists():
        data = json.loads(cache_path.read_text())
        if data.get("_deleted"):
            return None
        return ShopProfile(**data)
    yaml_path = _shops_dir() / f"{shop_id}.yaml"
    if not yaml_path.exists():
        return None
    data = yaml.safe_load(yaml_path.read_text())
    return ShopProfile(
        id=shop_id,
        name=data["name"],
        sections=data.get("sections", [])
    )


def create_shop(name: str) -> ShopProfile:
    slug = _slugify(name)
    shop_id = slug
    existing_ids = {s.id for s in list_shops()}
    if shop_id in existing_ids:
        counter = 2
        while f"{slug}-{counter}" in existing_ids:
            counter += 1
        shop_id = f"{slug}-{counter}"
    shop = ShopProfile(id=shop_id, name=name, sections=DEFAULT_SECTIONS.copy())
    _save_cached_shop(shop)
    return shop


def update_shop(shop_id: str, name: str, sections: List[str]) -> Optional[ShopProfile]:
    existing = get_shop(shop_id)
    if existing is None:
        return None
    old_sections = existing.sections
    updated = ShopProfile(id=shop_id, name=name, sections=sections)
    _save_cached_shop(updated)
    if old_sections != sections:
        _invalidate_categorized_cache(shop_id)
    return updated


def delete_shop(shop_id: str) -> bool:
    existing = get_shop(shop_id)
    if existing is None:
        return False
    cache_path = _cache_shops_dir() / f"{shop_id}.json"
    yaml_path = _shops_dir() / f"{shop_id}.yaml"
    if yaml_path.exists():
        cache_path.write_text(json.dumps({"_deleted": True}))
    else:
        if cache_path.exists():
            cache_path.unlink()
    _invalidate_categorized_cache(shop_id)
    return True
