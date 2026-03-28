# Shopping List Manager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a backend API + iOS app that lets you write shopping lists as markdown at home and view them sorted by shop aisle order on your phone, with LLM-based item categorization and real-time check-off.

**Architecture:** Python/FastAPI backend serving a REST API, with file-based storage (markdown lists, YAML shop profiles, JSON cached state). Git-synced data directory. SwiftUI iOS app with three screens (shop picker, list picker, shopping list). Claude API for item categorization.

**Tech Stack:** Python 3.12, FastAPI, uvicorn, anthropic SDK, pyyaml, pytest. Swift, SwiftUI, Swift Testing.

---

## File Structure

### Backend (`server/`)

```
server/
  app/
    __init__.py
    main.py              # FastAPI app, middleware, startup
    config.py            # Settings (env vars)
    routers/
      __init__.py
      lists.py           # /lists endpoints
      shops.py           # /shops endpoints
      webhook.py         # /webhook endpoint
    services/
      __init__.py
      list_service.py    # List CRUD, markdown parsing
      shop_service.py    # Shop profile loading
      categorizer.py     # LLM categorization logic
      git_sync.py        # Git pull logic
    models.py            # Pydantic models (shared)
  tests/
    __init__.py
    conftest.py          # Fixtures (tmp data dirs, test client)
    test_list_service.py
    test_shop_service.py
    test_categorizer.py
    test_lists_router.py
    test_shops_router.py
    test_webhook_router.py
  requirements.txt
  Dockerfile
```

### iOS App (`ios/ShoppingList/ShoppingList/`)

```
ShoppingList/
  ShoppingListApp.swift        # (exists) App entry point
  ContentView.swift            # (exists) Replace with navigation root
  Models/
    ShopProfile.swift          # Shop model + Codable
    ShoppingItem.swift         # Item model + Codable
    CategorizedList.swift      # Categorized list model + Codable
  Services/
    APIClient.swift            # HTTP client for backend API
  Views/
    ShopPickerView.swift       # Shop selection screen
    ListPickerView.swift       # List selection screen
    ShoppingListView.swift     # Main shopping screen with sections
  ViewModels/
    ShopPickerViewModel.swift  # Shop picker state
    ListPickerViewModel.swift  # List picker state
    ShoppingListViewModel.swift # Shopping list state + check-off
```

### Data (separate git repo)

```
lists/
  master.md
shops/
  lidl-main-street.yaml
```

---

## Phase 1: Backend

### Task 1: Project scaffolding and config

**Files:**
- Create: `server/requirements.txt`
- Create: `server/app/__init__.py`
- Create: `server/app/config.py`
- Create: `server/app/main.py`
- Create: `server/tests/__init__.py`
- Create: `server/tests/conftest.py`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.115.0
uvicorn==0.30.0
pyyaml==6.0.2
anthropic==0.40.0
pytest==8.3.0
httpx==0.27.0
```

- [ ] **Step 2: Create virtual environment and install**

Run:
```bash
cd server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 3: Create config.py**

```python
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_dir: Path = Path("data")
    api_key: str = ""
    anthropic_api_key: str = ""
    github_webhook_secret: str = ""

    model_config = {"env_prefix": "SHOPPING_"}


settings = Settings()
```

- [ ] **Step 4: Create main.py with health check**

```python
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from app.config import settings

app = FastAPI(title="Shopping List API")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(key: str = Security(api_key_header)):
    if settings.api_key and key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Create conftest.py with test fixtures**

```python
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.config import settings
from app.main import app


@pytest.fixture
def tmp_data_dir(tmp_path):
    lists_dir = tmp_path / "lists"
    lists_dir.mkdir()
    shops_dir = tmp_path / "shops"
    shops_dir.mkdir()
    original = settings.data_dir
    settings.data_dir = tmp_path
    yield tmp_path
    settings.data_dir = original


@pytest.fixture
def client(tmp_data_dir):
    settings.api_key = ""
    return TestClient(app)
```

- [ ] **Step 6: Create empty __init__.py files**

Create empty `server/app/__init__.py` and `server/tests/__init__.py`.

- [ ] **Step 7: Verify health endpoint**

Run:
```bash
cd server
source venv/bin/activate
pytest tests/ -v
```

Create a quick smoke test first in `server/tests/test_health.py`:

```python
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add server/
git commit -m "feat: backend scaffolding with FastAPI, config, and health endpoint"
```

---

### Task 2: Pydantic models

**Files:**
- Create: `server/app/models.py`
- Create: `server/tests/test_models.py`

- [ ] **Step 1: Write tests for models**

Create `server/tests/test_models.py`:

```python
from app.models import ShopProfile, ShoppingItem, CategorizedSection, CategorizedList


def test_shop_profile():
    shop = ShopProfile(id="lidl", name="Lidl Main Street", sections=["produce", "dairy"])
    assert shop.id == "lidl"
    assert shop.sections == ["produce", "dairy"]


def test_shopping_item_defaults_unchecked():
    item = ShoppingItem(name="milk")
    assert item.checked is False


def test_categorized_list_structure():
    lst = CategorizedList(
        list_name="weekly",
        shop="lidl",
        sections=[
            CategorizedSection(
                name="dairy",
                items=[ShoppingItem(name="milk")]
            )
        ]
    )
    assert lst.sections[0].items[0].name == "milk"
    assert lst.sections[0].items[0].checked is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd server && pytest tests/test_models.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Create models.py**

```python
from pydantic import BaseModel


class ShopProfile(BaseModel):
    id: str
    name: str
    sections: list[str]


class ShoppingItem(BaseModel):
    name: str
    checked: bool = False


class CategorizedSection(BaseModel):
    name: str
    items: list[ShoppingItem]


class CategorizedList(BaseModel):
    list_name: str
    shop: str
    sections: list[CategorizedSection]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd server && pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/app/models.py server/tests/test_models.py
git commit -m "feat: add Pydantic models for shop profiles, items, and categorized lists"
```

---

### Task 3: Shop service

**Files:**
- Create: `server/app/services/__init__.py`
- Create: `server/app/services/shop_service.py`
- Create: `server/tests/test_shop_service.py`

- [ ] **Step 1: Write tests**

Create `server/tests/test_shop_service.py`:

```python
import yaml
from app.services.shop_service import list_shops, get_shop


def test_list_shops_empty(tmp_data_dir):
    assert list_shops() == []


def test_list_shops_finds_yaml(tmp_data_dir):
    shop_data = {"name": "Test Shop", "sections": ["produce", "dairy"]}
    (tmp_data_dir / "shops" / "test-shop.yaml").write_text(yaml.dump(shop_data))
    shops = list_shops()
    assert len(shops) == 1
    assert shops[0].id == "test-shop"
    assert shops[0].name == "Test Shop"


def test_get_shop(tmp_data_dir):
    shop_data = {"name": "Test Shop", "sections": ["produce", "dairy"]}
    (tmp_data_dir / "shops" / "test-shop.yaml").write_text(yaml.dump(shop_data))
    shop = get_shop("test-shop")
    assert shop is not None
    assert shop.sections == ["produce", "dairy"]


def test_get_shop_not_found(tmp_data_dir):
    assert get_shop("nonexistent") is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd server && pytest tests/test_shop_service.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement shop_service.py**

Create empty `server/app/services/__init__.py`.

Create `server/app/services/shop_service.py`:

```python
import yaml
from pathlib import Path
from app.config import settings
from app.models import ShopProfile


def _shops_dir() -> Path:
    return settings.data_dir / "shops"


def list_shops() -> list[ShopProfile]:
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


def get_shop(shop_id: str) -> ShopProfile | None:
    path = _shops_dir() / f"{shop_id}.yaml"
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text())
    return ShopProfile(
        id=shop_id,
        name=data["name"],
        sections=data.get("sections", [])
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd server && pytest tests/test_shop_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/app/services/ server/tests/test_shop_service.py
git commit -m "feat: add shop service for loading YAML shop profiles"
```

---

### Task 4: List service

**Files:**
- Create: `server/app/services/list_service.py`
- Create: `server/tests/test_list_service.py`

- [ ] **Step 1: Write tests**

Create `server/tests/test_list_service.py`:

```python
from app.services.list_service import list_lists, get_list, create_list, parse_items


def test_parse_items_from_markdown():
    md = "# Shopping\n- milk\n- bananas\n- chicken breast\n"
    assert parse_items(md) == ["milk", "bananas", "chicken breast"]


def test_parse_items_ignores_non_list_lines():
    md = "# Title\nSome text\n- item one\n\n- item two\n"
    assert parse_items(md) == ["item one", "item two"]


def test_list_lists_empty(tmp_data_dir):
    assert list_lists() == []


def test_list_lists_finds_md(tmp_data_dir):
    (tmp_data_dir / "lists" / "master.md").write_text("- milk\n")
    (tmp_data_dir / "lists" / "weekly.md").write_text("- bread\n")
    names = list_lists()
    assert "master" in names
    assert "weekly" in names


def test_get_list(tmp_data_dir):
    (tmp_data_dir / "lists" / "master.md").write_text("- milk\n- bread\n")
    items = get_list("master")
    assert items == ["milk", "bread"]


def test_get_list_not_found(tmp_data_dir):
    assert get_list("nonexistent") is None


def test_create_list_from_master(tmp_data_dir):
    (tmp_data_dir / "lists" / "master.md").write_text("- milk\n- bread\n")
    create_list("monday", from_master=True)
    assert get_list("monday") == ["milk", "bread"]


def test_create_list_empty(tmp_data_dir):
    create_list("tuesday", from_master=False)
    content = (tmp_data_dir / "lists" / "tuesday.md").read_text()
    assert content == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd server && pytest tests/test_list_service.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement list_service.py**

```python
import shutil
from pathlib import Path
from app.config import settings


def _lists_dir() -> Path:
    return settings.data_dir / "lists"


def parse_items(markdown: str) -> list[str]:
    items = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
    return items


def list_lists() -> list[str]:
    lists_dir = _lists_dir()
    if not lists_dir.exists():
        return []
    return sorted(f.stem for f in lists_dir.glob("*.md"))


def get_list(name: str) -> list[str] | None:
    path = _lists_dir() / f"{name}.md"
    if not path.exists():
        return None
    return parse_items(path.read_text())


def create_list(name: str, from_master: bool = False) -> list[str]:
    lists_dir = _lists_dir()
    target = lists_dir / f"{name}.md"
    if from_master:
        master = lists_dir / "master.md"
        shutil.copy2(master, target)
        return parse_items(target.read_text())
    else:
        target.write_text("")
        return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd server && pytest tests/test_list_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/app/services/list_service.py server/tests/test_list_service.py
git commit -m "feat: add list service for markdown list parsing and CRUD"
```

---

### Task 5: Categorizer service

**Files:**
- Create: `server/app/services/categorizer.py`
- Create: `server/tests/test_categorizer.py`

- [ ] **Step 1: Write tests**

Create `server/tests/test_categorizer.py`:

```python
import json
from unittest.mock import patch, MagicMock
from app.services.categorizer import categorize_items, get_or_create_categorized_list
from app.models import ShopProfile


def test_categorize_items_calls_llm():
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = json.dumps({
        "milk": "dairy",
        "bananas": "produce"
    })

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("app.services.categorizer._get_client", return_value=mock_client):
        result = categorize_items(
            items=["milk", "bananas"],
            sections=["produce", "dairy", "bakery"]
        )

    assert result == {"milk": "dairy", "bananas": "produce"}
    mock_client.messages.create.assert_called_once()


def test_get_or_create_categorized_list_caches(tmp_data_dir):
    shop = ShopProfile(id="test-shop", name="Test", sections=["produce", "dairy"])
    (tmp_data_dir / "lists" / "weekly.md").write_text("- milk\n- bananas\n")

    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = json.dumps({
        "milk": "dairy",
        "bananas": "produce"
    })
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("app.services.categorizer._get_client", return_value=mock_client):
        result1 = get_or_create_categorized_list("weekly", shop)
        result2 = get_or_create_categorized_list("weekly", shop)

    # LLM called only once — second call uses cache
    assert mock_client.messages.create.call_count == 1
    assert result1.list_name == "weekly"
    assert result1.shop == "test-shop"
    assert len(result1.sections) == 2


def test_get_or_create_categorized_list_structure(tmp_data_dir):
    shop = ShopProfile(id="test-shop", name="Test", sections=["produce", "dairy"])
    (tmp_data_dir / "lists" / "weekly.md").write_text("- milk\n- bananas\n")

    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = json.dumps({
        "milk": "dairy",
        "bananas": "produce"
    })
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("app.services.categorizer._get_client", return_value=mock_client):
        result = get_or_create_categorized_list("weekly", shop)

    section_names = [s.name for s in result.sections]
    assert "produce" in section_names
    assert "dairy" in section_names
    dairy = next(s for s in result.sections if s.name == "dairy")
    assert dairy.items[0].name == "milk"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd server && pytest tests/test_categorizer.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement categorizer.py**

```python
import json
from pathlib import Path
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


def categorize_items(items: list[str], sections: list[str]) -> dict[str, str]:
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


def get_or_create_categorized_list(list_name: str, shop: ShopProfile) -> CategorizedList | None:
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd server && pytest tests/test_categorizer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/app/services/categorizer.py server/tests/test_categorizer.py
git commit -m "feat: add LLM-based item categorizer with caching"
```

---

### Task 6: Shops router

**Files:**
- Create: `server/app/routers/__init__.py`
- Create: `server/app/routers/shops.py`
- Create: `server/tests/test_shops_router.py`

- [ ] **Step 1: Write tests**

Create `server/tests/test_shops_router.py`:

```python
import yaml


def test_get_shops_empty(client):
    response = client.get("/shops")
    assert response.status_code == 200
    assert response.json() == []


def test_get_shops(client, tmp_data_dir):
    shop_data = {"name": "Test Shop", "sections": ["produce", "dairy"]}
    (tmp_data_dir / "shops" / "test-shop.yaml").write_text(yaml.dump(shop_data))
    response = client.get("/shops")
    assert response.status_code == 200
    shops = response.json()
    assert len(shops) == 1
    assert shops[0]["id"] == "test-shop"


def test_get_shop_by_id(client, tmp_data_dir):
    shop_data = {"name": "Test Shop", "sections": ["produce", "dairy"]}
    (tmp_data_dir / "shops" / "test-shop.yaml").write_text(yaml.dump(shop_data))
    response = client.get("/shops/test-shop")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Shop"


def test_get_shop_not_found(client):
    response = client.get("/shops/nonexistent")
    assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd server && pytest tests/test_shops_router.py -v`
Expected: FAIL

- [ ] **Step 3: Implement shops router**

Create empty `server/app/routers/__init__.py`.

Create `server/app/routers/shops.py`:

```python
from fastapi import APIRouter, HTTPException
from app.models import ShopProfile
from app.services.shop_service import list_shops, get_shop

router = APIRouter(prefix="/shops", tags=["shops"])


@router.get("", response_model=list[ShopProfile])
async def get_shops():
    return list_shops()


@router.get("/{shop_id}", response_model=ShopProfile)
async def get_shop_by_id(shop_id: str):
    shop = get_shop(shop_id)
    if shop is None:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop
```

- [ ] **Step 4: Register router in main.py**

Add to `server/app/main.py` after the app is created:

```python
from app.routers import shops

app.include_router(shops.router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd server && pytest tests/test_shops_router.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add server/app/routers/ server/tests/test_shops_router.py server/app/main.py
git commit -m "feat: add /shops endpoints"
```

---

### Task 7: Lists router

**Files:**
- Create: `server/app/routers/lists.py`
- Create: `server/tests/test_lists_router.py`

- [ ] **Step 1: Write tests**

Create `server/tests/test_lists_router.py`:

```python
import json
from unittest.mock import patch, MagicMock
import yaml


def test_get_lists_empty(client):
    response = client.get("/lists")
    assert response.status_code == 200
    assert response.json() == []


def test_get_lists(client, tmp_data_dir):
    (tmp_data_dir / "lists" / "master.md").write_text("- milk\n")
    response = client.get("/lists")
    assert response.status_code == 200
    assert "master" in response.json()


def test_get_list_by_name(client, tmp_data_dir):
    (tmp_data_dir / "lists" / "weekly.md").write_text("- milk\n- bread\n")
    response = client.get("/lists/weekly")
    assert response.status_code == 200
    assert response.json() == {"name": "weekly", "items": ["milk", "bread"]}


def test_get_list_not_found(client):
    response = client.get("/lists/nonexistent")
    assert response.status_code == 404


def test_create_list_empty(client, tmp_data_dir):
    response = client.post("/lists", json={"name": "tuesday"})
    assert response.status_code == 201
    assert response.json() == {"name": "tuesday", "items": []}


def test_create_list_from_master(client, tmp_data_dir):
    (tmp_data_dir / "lists" / "master.md").write_text("- milk\n- bread\n")
    response = client.post("/lists?from=master", json={"name": "monday"})
    assert response.status_code == 201
    assert response.json()["items"] == ["milk", "bread"]


def test_prepare_list(client, tmp_data_dir):
    (tmp_data_dir / "lists" / "weekly.md").write_text("- milk\n- bananas\n")
    shop_data = {"name": "Test Shop", "sections": ["produce", "dairy"]}
    (tmp_data_dir / "shops" / "test-shop.yaml").write_text(yaml.dump(shop_data))

    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = json.dumps({
        "milk": "dairy",
        "bananas": "produce"
    })
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("app.services.categorizer._get_client", return_value=mock_client):
        response = client.post("/lists/weekly/prepare?shop=test-shop")

    assert response.status_code == 200
    data = response.json()
    assert data["list_name"] == "weekly"
    assert data["shop"] == "test-shop"


def test_toggle_item(client, tmp_data_dir):
    (tmp_data_dir / "lists" / "weekly.md").write_text("- milk\n- bananas\n")
    shop_data = {"name": "Test Shop", "sections": ["produce", "dairy"]}
    (tmp_data_dir / "shops" / "test-shop.yaml").write_text(yaml.dump(shop_data))

    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = json.dumps({
        "milk": "dairy",
        "bananas": "produce"
    })
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("app.services.categorizer._get_client", return_value=mock_client):
        client.post("/lists/weekly/prepare?shop=test-shop")

    response = client.patch("/lists/weekly/items/milk?shop=test-shop")
    assert response.status_code == 200
    assert response.json()["checked"] is True

    response = client.patch("/lists/weekly/items/milk?shop=test-shop")
    assert response.status_code == 200
    assert response.json()["checked"] is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd server && pytest tests/test_lists_router.py -v`
Expected: FAIL

- [ ] **Step 3: Implement lists router**

Create `server/app/routers/lists.py`:

```python
import json
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
    items: list[str]


class ToggleResponse(BaseModel):
    name: str
    checked: bool


@router.get("", response_model=list[str])
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
    from_param: str | None = Query(None, alias="from")
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
```

- [ ] **Step 4: Register router in main.py**

Add to `server/app/main.py`:

```python
from app.routers import lists

app.include_router(lists.router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd server && pytest tests/test_lists_router.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add server/app/routers/lists.py server/tests/test_lists_router.py server/app/main.py
git commit -m "feat: add /lists endpoints with prepare and toggle"
```

---

### Task 8: Webhook and git sync

**Files:**
- Create: `server/app/services/git_sync.py`
- Create: `server/app/routers/webhook.py`
- Create: `server/tests/test_webhook_router.py`

- [ ] **Step 1: Write tests**

Create `server/tests/test_webhook_router.py`:

```python
import hmac
import hashlib
import json
from unittest.mock import patch
from app.config import settings


def test_webhook_triggers_git_pull(client):
    settings.github_webhook_secret = ""
    with patch("app.routers.webhook.git_pull") as mock_pull:
        mock_pull.return_value = True
        response = client.post("/webhook", json={"ref": "refs/heads/main"})
    assert response.status_code == 200
    mock_pull.assert_called_once()


def test_webhook_validates_signature(client):
    settings.github_webhook_secret = "test-secret"
    payload = json.dumps({"ref": "refs/heads/main"}).encode()
    sig = "sha256=" + hmac.new(b"test-secret", payload, hashlib.sha256).hexdigest()

    with patch("app.routers.webhook.git_pull") as mock_pull:
        mock_pull.return_value = True
        response = client.post(
            "/webhook",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": sig
            }
        )
    assert response.status_code == 200
    settings.github_webhook_secret = ""


def test_webhook_rejects_bad_signature(client):
    settings.github_webhook_secret = "test-secret"
    response = client.post(
        "/webhook",
        json={"ref": "refs/heads/main"},
        headers={"X-Hub-Signature-256": "sha256=bad"}
    )
    assert response.status_code == 401
    settings.github_webhook_secret = ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd server && pytest tests/test_webhook_router.py -v`
Expected: FAIL

- [ ] **Step 3: Implement git_sync.py**

```python
import subprocess
from app.config import settings


def git_pull() -> bool:
    try:
        subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=settings.data_dir,
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError:
        return False
```

- [ ] **Step 4: Implement webhook router**

Create `server/app/routers/webhook.py`:

```python
import hmac
import hashlib
from fastapi import APIRouter, Request, HTTPException
from app.config import settings
from app.services.git_sync import git_pull

router = APIRouter(tags=["webhook"])


@router.post("/webhook")
async def github_webhook(request: Request):
    body = await request.body()

    if settings.github_webhook_secret:
        signature = request.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + hmac.new(
            settings.github_webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=401, detail="Invalid signature")

    git_pull()
    return {"status": "ok"}
```

- [ ] **Step 5: Register router in main.py**

Add to `server/app/main.py`:

```python
from app.routers import webhook

app.include_router(webhook.router)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd server && pytest tests/test_webhook_router.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add server/app/services/git_sync.py server/app/routers/webhook.py server/tests/test_webhook_router.py server/app/main.py
git commit -m "feat: add webhook endpoint and git sync"
```

---

### Task 9: Auth middleware

**Files:**
- Modify: `server/app/main.py`
- Modify: `server/tests/conftest.py`
- Create: `server/tests/test_auth.py`

- [ ] **Step 1: Write tests**

Create `server/tests/test_auth.py`:

```python
from fastapi.testclient import TestClient
from app.config import settings
from app.main import app


def test_protected_endpoint_rejects_without_key(tmp_data_dir):
    settings.api_key = "secret123"
    client = TestClient(app)
    response = client.get("/shops")
    assert response.status_code == 401
    settings.api_key = ""


def test_protected_endpoint_accepts_valid_key(tmp_data_dir):
    settings.api_key = "secret123"
    client = TestClient(app)
    response = client.get("/shops", headers={"X-API-Key": "secret123"})
    assert response.status_code == 200
    settings.api_key = ""


def test_health_is_public(tmp_data_dir):
    settings.api_key = "secret123"
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    settings.api_key = ""


def test_webhook_is_public(tmp_data_dir):
    settings.api_key = "secret123"
    client = TestClient(app)
    response = client.post("/webhook", json={})
    assert response.status_code == 200
    settings.api_key = ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd server && pytest tests/test_auth.py -v`
Expected: some FAIL (no auth enforcement yet)

- [ ] **Step 3: Add auth dependency to protected routers**

Update `server/app/main.py` to apply the `verify_api_key` dependency to the shops and lists routers:

```python
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from app.config import settings
from app.routers import shops, lists, webhook

app = FastAPI(title="Shopping List API")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(key: str = Security(api_key_header)):
    if settings.api_key and key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


app.include_router(shops.router, dependencies=[Depends(verify_api_key)])
app.include_router(lists.router, dependencies=[Depends(verify_api_key)])
app.include_router(webhook.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Run all tests to verify they pass**

Run: `cd server && pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add server/app/main.py server/tests/test_auth.py
git commit -m "feat: add API key auth to protected endpoints"
```

---

### Task 10: Dockerfile and run script

**Files:**
- Create: `server/Dockerfile`
- Create: `server/run.sh`

- [ ] **Step 1: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

- [ ] **Step 2: Create run.sh for local development**

```bash
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
uvicorn app.main:app --reload --port 8080
```

- [ ] **Step 3: Make run.sh executable and test Docker build**

Run:
```bash
cd server
chmod +x run.sh
docker build -t shopping-list-server .
```

Expected: successful build

- [ ] **Step 4: Commit**

```bash
git add server/Dockerfile server/run.sh
git commit -m "feat: add Dockerfile and local run script"
```

---

## Phase 2: iOS App

### Task 11: iOS models

**Files:**
- Create: `ios/ShoppingList/ShoppingList/Models/ShopProfile.swift`
- Create: `ios/ShoppingList/ShoppingList/Models/ShoppingItem.swift`
- Create: `ios/ShoppingList/ShoppingList/Models/CategorizedList.swift`
- Modify: `ios/ShoppingList/ShoppingListTests/ShoppingListTests.swift`

- [ ] **Step 1: Write tests for models**

Replace `ios/ShoppingList/ShoppingListTests/ShoppingListTests.swift`:

```swift
import Testing
import Foundation
@testable import ShoppingList

struct ShoppingListTests {

    @Test func shopProfileDecodesFromJSON() throws {
        let json = """
        {"id": "lidl", "name": "Lidl Main Street", "sections": ["produce", "dairy"]}
        """.data(using: .utf8)!
        let shop = try JSONDecoder().decode(ShopProfile.self, from: json)
        #expect(shop.id == "lidl")
        #expect(shop.name == "Lidl Main Street")
        #expect(shop.sections == ["produce", "dairy"])
    }

    @Test func shoppingItemDecodesWithCheckedState() throws {
        let json = """
        {"name": "milk", "checked": true}
        """.data(using: .utf8)!
        let item = try JSONDecoder().decode(ShoppingItem.self, from: json)
        #expect(item.name == "milk")
        #expect(item.checked == true)
    }

    @Test func categorizedListDecodesFullStructure() throws {
        let json = """
        {
            "list_name": "weekly",
            "shop": "lidl",
            "sections": [
                {
                    "name": "dairy",
                    "items": [{"name": "milk", "checked": false}]
                }
            ]
        }
        """.data(using: .utf8)!
        let list = try JSONDecoder().decode(CategorizedList.self, from: json)
        #expect(list.listName == "weekly")
        #expect(list.shop == "lidl")
        #expect(list.sections.count == 1)
        #expect(list.sections[0].items[0].name == "milk")
    }
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd ios/ShoppingList
xcodebuild test -scheme ShoppingList -destination 'platform=iOS Simulator,name=iPhone 16' 2>&1 | tail -20
```
Expected: FAIL (types not defined)

- [ ] **Step 3: Create ShopProfile.swift**

```swift
import Foundation

struct ShopProfile: Codable, Identifiable {
    let id: String
    let name: String
    let sections: [String]
}
```

- [ ] **Step 4: Create ShoppingItem.swift**

```swift
import Foundation

struct ShoppingItem: Codable, Identifiable {
    var id: String { name }
    let name: String
    var checked: Bool
}
```

- [ ] **Step 5: Create CategorizedList.swift**

```swift
import Foundation

struct CategorizedSection: Codable, Identifiable {
    var id: String { name }
    let name: String
    var items: [ShoppingItem]
}

struct CategorizedList: Codable {
    let listName: String
    let shop: String
    var sections: [CategorizedSection]

    enum CodingKeys: String, CodingKey {
        case listName = "list_name"
        case shop
        case sections
    }
}
```

- [ ] **Step 6: Run tests to verify they pass**

Run:
```bash
cd ios/ShoppingList
xcodebuild test -scheme ShoppingList -destination 'platform=iOS Simulator,name=iPhone 16' 2>&1 | tail -20
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add ios/
git commit -m "feat: add iOS data models with Codable conformance"
```

---

### Task 12: API client

**Files:**
- Create: `ios/ShoppingList/ShoppingList/Services/APIClient.swift`

- [ ] **Step 1: Create APIClient.swift**

```swift
import Foundation

class APIClient {
    static let shared = APIClient()

    // TODO during deployment: move to a config or environment variable
    private var baseURL = URL(string: "http://localhost:8080")!
    private var apiKey = ""

    func configure(baseURL: URL, apiKey: String) {
        self.baseURL = baseURL
        self.apiKey = apiKey
    }

    private func request(_ path: String, method: String = "GET", body: Data? = nil, query: [String: String] = [:]) async throws -> Data {
        var components = URLComponents(url: baseURL.appendingPathComponent(path), resolvingAgainstBaseURL: false)!
        if !query.isEmpty {
            components.queryItems = query.map { URLQueryItem(name: $0.key, value: $0.value) }
        }
        var request = URLRequest(url: components.url!)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if !apiKey.isEmpty {
            request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        }
        request.httpBody = body
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200...299).contains(http.statusCode) else {
            let http = response as? HTTPURLResponse
            throw APIError.httpError(statusCode: http?.statusCode ?? 0)
        }
        return data
    }

    func getShops() async throws -> [ShopProfile] {
        let data = try await request("/shops")
        return try JSONDecoder().decode([ShopProfile].self, from: data)
    }

    func getLists() async throws -> [String] {
        let data = try await request("/lists")
        return try JSONDecoder().decode([String].self, from: data)
    }

    func prepareList(name: String, shop: String) async throws -> CategorizedList {
        let data = try await request("/lists/\(name)/prepare", method: "POST", query: ["shop": shop])
        return try JSONDecoder().decode(CategorizedList.self, from: data)
    }

    func toggleItem(listName: String, item: String, shop: String) async throws {
        _ = try await request("/lists/\(listName)/items/\(item)", method: "PATCH", query: ["shop": shop])
    }
}

enum APIError: Error {
    case httpError(statusCode: Int)
}
```

- [ ] **Step 2: Commit**

```bash
git add ios/
git commit -m "feat: add API client for backend communication"
```

---

### Task 13: Shop Picker screen

**Files:**
- Create: `ios/ShoppingList/ShoppingList/ViewModels/ShopPickerViewModel.swift`
- Create: `ios/ShoppingList/ShoppingList/Views/ShopPickerView.swift`
- Modify: `ios/ShoppingList/ShoppingList/ContentView.swift`
- Modify: `ios/ShoppingList/ShoppingList/ShoppingListApp.swift`

- [ ] **Step 1: Create ShopPickerViewModel**

```swift
import Foundation

@Observable
class ShopPickerViewModel {
    var shops: [ShopProfile] = []
    var isLoading = false
    var errorMessage: String?

    private let lastShopKey = "lastSelectedShop"

    var lastSelectedShopId: String? {
        get { UserDefaults.standard.string(forKey: lastShopKey) }
        set { UserDefaults.standard.set(newValue, forKey: lastShopKey) }
    }

    func loadShops() async {
        isLoading = true
        errorMessage = nil
        do {
            shops = try await APIClient.shared.getShops()
        } catch {
            errorMessage = "Failed to load shops: \(error.localizedDescription)"
        }
        isLoading = false
    }

    func selectShop(_ shop: ShopProfile) {
        lastSelectedShopId = shop.id
    }
}
```

- [ ] **Step 2: Create ShopPickerView**

```swift
import SwiftUI

struct ShopPickerView: View {
    @State private var viewModel = ShopPickerViewModel()
    @Binding var selectedShop: ShopProfile?

    var body: some View {
        Group {
            if viewModel.isLoading {
                ProgressView("Loading shops...")
            } else if let error = viewModel.errorMessage {
                VStack(spacing: 16) {
                    Text(error)
                        .foregroundStyle(.secondary)
                    Button("Retry") {
                        Task { await viewModel.loadShops() }
                    }
                }
            } else {
                List(viewModel.shops) { shop in
                    Button {
                        viewModel.selectShop(shop)
                        selectedShop = shop
                    } label: {
                        HStack {
                            Text(shop.name)
                            Spacer()
                            if shop.id == viewModel.lastSelectedShopId {
                                Image(systemName: "clock")
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle("Select Shop")
        .task { await viewModel.loadShops() }
    }
}
```

- [ ] **Step 3: Update ContentView as navigation root**

Replace `ios/ShoppingList/ShoppingList/ContentView.swift`:

```swift
import SwiftUI

struct ContentView: View {
    @State private var selectedShop: ShopProfile?

    var body: some View {
        NavigationStack {
            ShopPickerView(selectedShop: $selectedShop)
                .navigationDestination(item: $selectedShop) { shop in
                    ListPickerView(shop: shop)
                }
        }
    }
}
```

- [ ] **Step 4: Build to verify**

Run:
```bash
cd ios/ShoppingList
xcodebuild build -scheme ShoppingList -destination 'platform=iOS Simulator,name=iPhone 16' 2>&1 | tail -5
```
Expected: BUILD SUCCEEDED (ListPickerView doesn't exist yet, so create a placeholder)

Create a placeholder `ios/ShoppingList/ShoppingList/Views/ListPickerView.swift`:

```swift
import SwiftUI

struct ListPickerView: View {
    let shop: ShopProfile

    var body: some View {
        Text("Lists for \(shop.name)")
            .navigationTitle("Select List")
    }
}
```

- [ ] **Step 5: Commit**

```bash
git add ios/
git commit -m "feat: add shop picker screen with navigation"
```

---

### Task 14: List Picker screen

**Files:**
- Create: `ios/ShoppingList/ShoppingList/ViewModels/ListPickerViewModel.swift`
- Modify: `ios/ShoppingList/ShoppingList/Views/ListPickerView.swift`

- [ ] **Step 1: Create ListPickerViewModel**

```swift
import Foundation

@Observable
class ListPickerViewModel {
    var lists: [String] = []
    var isLoading = false
    var errorMessage: String?

    func loadLists() async {
        isLoading = true
        errorMessage = nil
        do {
            lists = try await APIClient.shared.getLists()
        } catch {
            errorMessage = "Failed to load lists: \(error.localizedDescription)"
        }
        isLoading = false
    }
}
```

- [ ] **Step 2: Update ListPickerView**

Replace `ios/ShoppingList/ShoppingList/Views/ListPickerView.swift`:

```swift
import SwiftUI

struct ListPickerView: View {
    let shop: ShopProfile
    @State private var viewModel = ListPickerViewModel()
    @State private var selectedList: String?

    var body: some View {
        Group {
            if viewModel.isLoading {
                ProgressView("Loading lists...")
            } else if let error = viewModel.errorMessage {
                VStack(spacing: 16) {
                    Text(error)
                        .foregroundStyle(.secondary)
                    Button("Retry") {
                        Task { await viewModel.loadLists() }
                    }
                }
            } else {
                List(viewModel.lists, id: \.self) { listName in
                    Button(listName) {
                        selectedList = listName
                    }
                }
            }
        }
        .navigationTitle("Select List")
        .navigationDestination(item: $selectedList) { listName in
            ShoppingListView(listName: listName, shop: shop)
        }
        .task { await viewModel.loadLists() }
    }
}
```

- [ ] **Step 3: Create placeholder ShoppingListView**

Create `ios/ShoppingList/ShoppingList/Views/ShoppingListView.swift`:

```swift
import SwiftUI

struct ShoppingListView: View {
    let listName: String
    let shop: ShopProfile

    var body: some View {
        Text("Shopping: \(listName) at \(shop.name)")
            .navigationTitle(listName)
    }
}
```

- [ ] **Step 4: Build to verify**

Run:
```bash
cd ios/ShoppingList
xcodebuild build -scheme ShoppingList -destination 'platform=iOS Simulator,name=iPhone 16' 2>&1 | tail -5
```
Expected: BUILD SUCCEEDED

- [ ] **Step 5: Commit**

```bash
git add ios/
git commit -m "feat: add list picker screen"
```

---

### Task 15: Shopping List screen (main shopping experience)

**Files:**
- Create: `ios/ShoppingList/ShoppingList/ViewModels/ShoppingListViewModel.swift`
- Modify: `ios/ShoppingList/ShoppingList/Views/ShoppingListView.swift`

- [ ] **Step 1: Create ShoppingListViewModel**

```swift
import Foundation

@Observable
class ShoppingListViewModel {
    var categorizedList: CategorizedList?
    var isLoading = false
    var errorMessage: String?

    let listName: String
    let shop: ShopProfile

    init(listName: String, shop: ShopProfile) {
        self.listName = listName
        self.shop = shop
    }

    var itemsRemaining: Int {
        guard let list = categorizedList else { return 0 }
        return list.sections.flatMap(\.items).filter { !$0.checked }.count
    }

    func loadList() async {
        isLoading = true
        errorMessage = nil
        do {
            categorizedList = try await APIClient.shared.prepareList(name: listName, shop: shop.id)
        } catch {
            errorMessage = "Failed to load list: \(error.localizedDescription)"
        }
        isLoading = false
    }

    func toggleItem(_ item: ShoppingItem, inSection section: CategorizedSection) async {
        guard var list = categorizedList,
              let sectionIndex = list.sections.firstIndex(where: { $0.id == section.id }),
              let itemIndex = list.sections[sectionIndex].items.firstIndex(where: { $0.id == item.id }) else {
            return
        }

        // Optimistic update
        list.sections[sectionIndex].items[itemIndex].checked.toggle()
        categorizedList = list

        do {
            try await APIClient.shared.toggleItem(listName: listName, item: item.name, shop: shop.id)
        } catch {
            // Revert on failure
            list.sections[sectionIndex].items[itemIndex].checked.toggle()
            categorizedList = list
        }
    }
}
```

- [ ] **Step 2: Implement ShoppingListView**

Replace `ios/ShoppingList/ShoppingList/Views/ShoppingListView.swift`:

```swift
import SwiftUI

struct ShoppingListView: View {
    let listName: String
    let shop: ShopProfile
    @State private var viewModel: ShoppingListViewModel

    init(listName: String, shop: ShopProfile) {
        self.listName = listName
        self.shop = shop
        self._viewModel = State(initialValue: ShoppingListViewModel(listName: listName, shop: shop))
    }

    var body: some View {
        Group {
            if viewModel.isLoading {
                ProgressView("Preparing list...")
            } else if let error = viewModel.errorMessage {
                VStack(spacing: 16) {
                    Text(error)
                        .foregroundStyle(.secondary)
                    Button("Retry") {
                        Task { await viewModel.loadList() }
                    }
                }
            } else if let list = viewModel.categorizedList {
                List {
                    ForEach(list.sections) { section in
                        Section(section.name.capitalized) {
                            ForEach(section.items) { item in
                                Button {
                                    Task { await viewModel.toggleItem(item, inSection: section) }
                                } label: {
                                    HStack {
                                        Image(systemName: item.checked ? "checkmark.circle.fill" : "circle")
                                            .foregroundStyle(item.checked ? .green : .primary)
                                        Text(item.name)
                                            .strikethrough(item.checked)
                                            .foregroundStyle(item.checked ? .secondary : .primary)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle("\(listName) (\(viewModel.itemsRemaining) left)")
        .refreshable { await viewModel.loadList() }
        .task { await viewModel.loadList() }
    }
}
```

- [ ] **Step 3: Build to verify**

Run:
```bash
cd ios/ShoppingList
xcodebuild build -scheme ShoppingList -destination 'platform=iOS Simulator,name=iPhone 16' 2>&1 | tail -5
```
Expected: BUILD SUCCEEDED

- [ ] **Step 4: Commit**

```bash
git add ios/
git commit -m "feat: add shopping list screen with section grouping and check-off"
```

---

### Task 16: Offline caching

**Files:**
- Modify: `ios/ShoppingList/ShoppingList/ViewModels/ShoppingListViewModel.swift`

- [ ] **Step 1: Add local cache to ShoppingListViewModel**

Add these methods to `ShoppingListViewModel`:

```swift
private var cacheURL: URL {
    let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    return docs.appendingPathComponent("cache_\(listName)_\(shop.id).json")
}

private func saveToCache(_ list: CategorizedList) {
    if let data = try? JSONEncoder().encode(list) {
        try? data.write(to: cacheURL)
    }
}

private func loadFromCache() -> CategorizedList? {
    guard let data = try? Data(contentsOf: cacheURL) else { return nil }
    return try? JSONDecoder().decode(CategorizedList.self, from: data)
}
```

Update `loadList()` to use the cache:

```swift
func loadList() async {
    isLoading = categorizedList == nil
    errorMessage = nil
    do {
        let list = try await APIClient.shared.prepareList(name: listName, shop: shop.id)
        categorizedList = list
        saveToCache(list)
    } catch {
        if categorizedList == nil {
            categorizedList = loadFromCache()
        }
        if categorizedList == nil {
            errorMessage = "Failed to load list: \(error.localizedDescription)"
        }
    }
    isLoading = false
}
```

Also update `toggleItem` to save cache after toggling:

```swift
// After the optimistic update line:
saveToCache(list)
```

- [ ] **Step 2: Build to verify**

Run:
```bash
cd ios/ShoppingList
xcodebuild build -scheme ShoppingList -destination 'platform=iOS Simulator,name=iPhone 16' 2>&1 | tail -5
```
Expected: BUILD SUCCEEDED

- [ ] **Step 3: Commit**

```bash
git add ios/
git commit -m "feat: add offline caching for shopping lists"
```

---

### Task 17: Sample data and end-to-end test

**Files:**
- Create: `lists/master.md`
- Create: `shops/lidl-main-street.yaml`

- [ ] **Step 1: Create sample master list**

Create `lists/master.md`:

```markdown
# Weekly Shopping
- milk
- eggs
- bananas
- chicken breast
- sourdough bread
- cheddar cheese
- olive oil
- tomatoes
- onions
- pasta
- tinned tomatoes
- frozen peas
- kitchen roll
```

- [ ] **Step 2: Create sample shop profile**

Create `shops/lidl-main-street.yaml`:

```yaml
name: "Lidl Main Street"
sections:
  - produce
  - bakery
  - dairy & eggs
  - meat & fish
  - pasta & grains
  - canned goods
  - oils & condiments
  - frozen
  - household
```

- [ ] **Step 3: Run backend locally and test**

```bash
cd server
SHOPPING_DATA_DIR=../  SHOPPING_ANTHROPIC_API_KEY=your-key-here source venv/bin/activate && uvicorn app.main:app --port 8080
```

In another terminal:
```bash
# List shops
curl http://localhost:8080/shops | python3 -m json.tool

# List lists
curl http://localhost:8080/lists | python3 -m json.tool

# Prepare a list
curl -X POST "http://localhost:8080/lists/master/prepare?shop=lidl-main-street" | python3 -m json.tool

# Toggle an item
curl -X PATCH "http://localhost:8080/lists/master/items/milk?shop=lidl-main-street" | python3 -m json.tool
```

Expected: all return valid JSON responses with correct data

- [ ] **Step 4: Run iOS app in simulator and verify end-to-end**

Open Xcode, run the app in a simulator. Should see:
1. Shop picker with "Lidl Main Street"
2. Tap → list picker with "master"
3. Tap → categorized shopping list sorted by sections
4. Tap items to check them off

- [ ] **Step 5: Commit**

```bash
git add lists/ shops/
git commit -m "feat: add sample data for end-to-end testing"
```

---

### Task 18: Run all backend tests

- [ ] **Step 1: Run full test suite**

```bash
cd server
source venv/bin/activate
pytest tests/ -v
```

Expected: ALL PASS

- [ ] **Step 2: Run iOS tests**

```bash
cd ios/ShoppingList
xcodebuild test -scheme ShoppingList -destination 'platform=iOS Simulator,name=iPhone 16' 2>&1 | tail -20
```

Expected: ALL PASS
