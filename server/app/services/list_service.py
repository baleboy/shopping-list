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
