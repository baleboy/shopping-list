import json
from pathlib import Path
from typing import Optional, List, Dict
from anthropic import Anthropic
from app.config import settings
from app.models import ShopProfile, ShoppingItem, CategorizedSection, CategorizedList
from app.services.list_service import get_list


def _get_client() -> Anthropic:
    return Anthropic(api_key=settings.anthropic_api_key)


def _cache_path(list_name: str, shop_id: str) -> Path:
    cache_dir = settings.data_dir / "cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / f"{list_name}_{shop_id}.json"


def categorize_items(items: List[str], sections: List[str]) -> Dict[str, str]:
    client = _get_client()
    prompt = (
        f"Categorize each shopping item into exactly one of these shop sections: {sections}\n\n"
        f"Items: {items}\n\n"
        "Return ONLY a JSON object mapping each item to its section. "
        "Example: {\"milk\": \"dairy\", \"bananas\": \"produce\"}\n"
        "If an item doesn't fit any section well, assign it to the closest match."
    )
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return json.loads(response.content[0].text)


def get_or_create_categorized_list(list_name: str, shop: ShopProfile) -> Optional[CategorizedList]:
    cache = _cache_path(list_name, shop.id)

    if cache.exists():
        data = json.loads(cache.read_text())
        return CategorizedList(**data)

    items = get_list(list_name)
    if items is None:
        return None

    mapping = categorize_items(items, shop.sections)

    sections = []
    for section_name in shop.sections:
        section_items = [
            ShoppingItem(name=item)
            for item, assigned in mapping.items()
            if assigned == section_name
        ]
        if section_items:
            sections.append(CategorizedSection(name=section_name, items=section_items))

    result = CategorizedList(
        list_name=list_name,
        shop=shop.id,
        sections=sections
    )

    cache.write_text(result.model_dump_json(indent=2))
    return result
