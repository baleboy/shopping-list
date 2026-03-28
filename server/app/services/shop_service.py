from typing import List, Optional

import yaml
from pathlib import Path
from app.config import settings
from app.models import ShopProfile


def _shops_dir() -> Path:
    return settings.data_dir / "shops"


def list_shops() -> List[ShopProfile]:
    shops_dir = _shops_dir()
    if not shops_dir.exists():
        return []
    profiles = []
    for f in sorted(shops_dir.glob("*.yaml")):
        data = yaml.safe_load(f.read_text())
        profiles.append(ShopProfile(
            id=f.stem,
            name=data["name"],
            sections=data.get("sections", [])
        ))
    return profiles


def get_shop(shop_id: str) -> Optional[ShopProfile]:
    path = _shops_dir() / f"{shop_id}.yaml"
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text())
    return ShopProfile(
        id=shop_id,
        name=data["name"],
        sections=data.get("sections", [])
    )
