import shutil
from pathlib import Path
from typing import Optional, List
from app.config import settings


def _lists_dir() -> Path:
    return settings.data_dir / "lists"


def parse_items(markdown: str) -> List[str]:
    items = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
    return items


def list_lists() -> List[str]:
    lists_dir = _lists_dir()
    if not lists_dir.exists():
        return []
    return sorted(f.stem for f in lists_dir.glob("*.md"))


def get_list(name: str) -> Optional[List[str]]:
    path = _lists_dir() / f"{name}.md"
    if not path.exists():
        return None
    return parse_items(path.read_text())


def items_to_markdown(items: List[str]) -> str:
    return "".join(f"- {item}\n" for item in items)


def update_list(name: str, items: List[str]) -> Optional[List[str]]:
    path = _lists_dir() / f"{name}.md"
    if not path.exists():
        return None
    path.write_text(items_to_markdown(items))
    return items


def delete_list(name: str) -> bool:
    path = _lists_dir() / f"{name}.md"
    if not path.exists():
        return False
    path.unlink()
    cache_dir = settings.data_dir / "cache"
    if cache_dir.exists():
        for cache_file in cache_dir.glob(f"{name}_*.json"):
            cache_file.unlink()
    return True


def create_list(name: str, from_master: bool = False) -> List[str]:
    lists_dir = _lists_dir()
    target = lists_dir / f"{name}.md"
    if from_master:
        master = lists_dir / "master.md"
        shutil.copy2(master, target)
        return parse_items(target.read_text())
    else:
        target.write_text("")
        return []
