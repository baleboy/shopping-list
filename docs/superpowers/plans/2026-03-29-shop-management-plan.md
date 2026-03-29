# Shop Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add CRUD for shop profiles from the iOS app, with server-side storage that overrides git-synced YAML files.

**Architecture:** Extend shop_service with a cache layer (`cache/shops/`) that stores app-edited shops as JSON, taking priority over YAML files. Add POST/PUT/DELETE endpoints. Add iOS Shop Editor screen and update Shop Picker with add/swipe actions. Invalidate categorized list cache when shop sections change.

**Tech Stack:** Python/FastAPI, pytest. Swift, SwiftUI.

---

## File Structure

### Backend

```
server/
  app/
    services/
      shop_service.py    # (modify) Add cache layer, create/update/delete, default sections
    routers/
      shops.py           # (modify) Add POST, PUT, DELETE endpoints
    models.py            # (modify) Add CreateShopRequest, UpdateShopRequest
  tests/
    test_shop_service.py # (modify) Add tests for cache layer, CRUD
    test_shops_router.py # (modify) Add tests for new endpoints
```

### iOS

```
ios/ShoppingList/ShoppingList/
  Services/
    APIClient.swift            # (modify) Add createShop, updateShop, deleteShop
  Views/
    ShopPickerView.swift       # (modify) Add toolbar +, swipe actions
    ShopEditorView.swift       # (create) Edit name, reorder/add/delete sections
  ViewModels/
    ShopPickerViewModel.swift  # (modify) Add create, delete, reload
    ShopEditorViewModel.swift  # (create) Edit state, save
```

---

## Phase 1: Backend

### Task 1: Extend shop_service with cache layer and CRUD

**Files:**
- Modify: `server/app/services/shop_service.py`
- Modify: `server/tests/test_shop_service.py`

- [ ] **Step 1: Write tests for cache-aware listing and getting**

Add to `server/tests/test_shop_service.py`:

```python
import json
import yaml
from app.services.shop_service import list_shops, get_shop, create_shop, update_shop, delete_shop


def test_list_shops_merges_yaml_and_cache(tmp_data_dir):
    # YAML shop
    shop_data = {"name": "YAML Shop", "sections": ["produce", "dairy"]}
    (tmp_data_dir / "shops" / "yaml-shop.yaml").write_text(yaml.dump(shop_data))
    # Cached shop
    cache_dir = tmp_data_dir / "cache" / "shops"
    cache_dir.mkdir(parents=True)
    cached = {"id": "cached-shop", "name": "Cached Shop", "sections": ["frozen"]}
    (cache_dir / "cached-shop.json").write_text(json.dumps(cached))
    shops = list_shops()
    names = [s.name for s in shops]
    assert "YAML Shop" in names
    assert "Cached Shop" in names


def test_cached_shop_overrides_yaml(tmp_data_dir):
    shop_data = {"name": "Original", "sections": ["produce"]}
    (tmp_data_dir / "shops" / "my-shop.yaml").write_text(yaml.dump(shop_data))
    cache_dir = tmp_data_dir / "cache" / "shops"
    cache_dir.mkdir(parents=True)
    cached = {"id": "my-shop", "name": "Updated", "sections": ["dairy", "produce"]}
    (cache_dir / "my-shop.json").write_text(json.dumps(cached))
    shop = get_shop("my-shop")
    assert shop.name == "Updated"
    assert shop.sections == ["dairy", "produce"]


def test_create_shop(tmp_data_dir):
    shop = create_shop("My New Shop")
    assert shop.id == "my-new-shop"
    assert shop.name == "My New Shop"
    assert len(shop.sections) > 0
    # Verify it's persisted in cache
    assert get_shop("my-new-shop") is not None


def test_create_shop_generates_unique_id(tmp_data_dir):
    create_shop("Test Shop")
    shop2 = create_shop("Test Shop")
    assert shop2.id != "test-shop"


def test_update_shop(tmp_data_dir):
    create_shop("Original")
    updated = update_shop("original", name="Renamed", sections=["frozen", "dairy"])
    assert updated.name == "Renamed"
    assert updated.sections == ["frozen", "dairy"]
    # Verify persisted
    fetched = get_shop("original")
    assert fetched.name == "Renamed"


def test_update_shop_not_found(tmp_data_dir):
    result = update_shop("nonexistent", name="X", sections=["a"])
    assert result is None


def test_delete_shop_cached(tmp_data_dir):
    create_shop("To Delete")
    assert delete_shop("to-delete") is True
    assert get_shop("to-delete") is None


def test_delete_shop_yaml(tmp_data_dir):
    shop_data = {"name": "YAML Shop", "sections": ["produce"]}
    (tmp_data_dir / "shops" / "yaml-shop.yaml").write_text(yaml.dump(shop_data))
    # Deleting a YAML shop creates a "tombstone" in cache
    assert delete_shop("yaml-shop") is True
    assert get_shop("yaml-shop") is None


def test_delete_shop_not_found(tmp_data_dir):
    assert delete_shop("nonexistent") is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/baleboy/Projects/shopping-list/server && source venv/bin/activate && pytest tests/test_shop_service.py -v`
Expected: FAIL (ImportError for new functions)

- [ ] **Step 3: Implement updated shop_service.py**

Replace `server/app/services/shop_service.py`:

```python
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
    """Load shops from git-synced YAML files. Returns {id: ShopProfile}."""
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
    """Load shops from app-edited cache. Returns {id: ShopProfile or None (tombstone)}."""
    cache_dir = _cache_shops_dir()
    result = {}
    for f in sorted(cache_dir.glob("*.json")):
        data = json.loads(f.read_text())
        shop_id = f.stem
        if data.get("_deleted"):
            result[shop_id] = None  # tombstone
        else:
            result[shop_id] = ShopProfile(**data)
    return result


def _save_cached_shop(shop: ShopProfile) -> None:
    path = _cache_shops_dir() / f"{shop.id}.json"
    path.write_text(json.dumps(shop.model_dump(), indent=2))


def _invalidate_categorized_cache(shop_id: str) -> None:
    """Delete cached categorized lists for this shop."""
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
            merged.pop(shop_id, None)  # tombstone removes YAML shop
        else:
            merged[shop_id] = shop
    return sorted(merged.values(), key=lambda s: s.name)


def get_shop(shop_id: str) -> Optional[ShopProfile]:
    # Check cache first (includes tombstones)
    cache_path = _cache_shops_dir() / f"{shop_id}.json"
    if cache_path.exists():
        data = json.loads(cache_path.read_text())
        if data.get("_deleted"):
            return None
        return ShopProfile(**data)
    # Fall back to YAML
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
    # Ensure unique ID
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
        # Write tombstone so YAML shop stays hidden
        cache_path.write_text(json.dumps({"_deleted": True}))
    else:
        # Pure cache shop — just delete the file
        if cache_path.exists():
            cache_path.unlink()
    _invalidate_categorized_cache(shop_id)
    return True
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/baleboy/Projects/shopping-list/server && source venv/bin/activate && pytest tests/test_shop_service.py -v`
Expected: ALL PASS

- [ ] **Step 5: Run full test suite**

Run: `cd /Users/baleboy/Projects/shopping-list/server && pytest tests/ -v`
Expected: ALL PASS (existing tests should still work since list_shops/get_shop signatures unchanged)

- [ ] **Step 6: Commit**

```bash
git add server/app/services/shop_service.py server/tests/test_shop_service.py
git commit -m "feat: extend shop service with cache layer and CRUD operations"
```

---

### Task 2: Add shop CRUD endpoints

**Files:**
- Modify: `server/app/routers/shops.py`
- Modify: `server/app/models.py`
- Modify: `server/tests/test_shops_router.py`

- [ ] **Step 1: Add request models to models.py**

Add to `server/app/models.py`:

```python
class CreateShopRequest(BaseModel):
    name: str


class UpdateShopRequest(BaseModel):
    name: str
    sections: list[str]
```

- [ ] **Step 2: Write tests for new endpoints**

Add to `server/tests/test_shops_router.py`:

```python
def test_create_shop(client):
    response = client.post("/shops", json={"name": "New Shop"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Shop"
    assert data["id"] == "new-shop"
    assert len(data["sections"]) > 0


def test_update_shop(client, tmp_data_dir):
    # Create first
    client.post("/shops", json={"name": "Test Shop"})
    response = client.put("/shops/test-shop", json={
        "name": "Renamed",
        "sections": ["frozen", "dairy"]
    })
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"
    assert response.json()["sections"] == ["frozen", "dairy"]


def test_update_shop_not_found(client):
    response = client.put("/shops/nonexistent", json={
        "name": "X",
        "sections": ["a"]
    })
    assert response.status_code == 404


def test_delete_shop(client):
    client.post("/shops", json={"name": "To Delete"})
    response = client.delete("/shops/to-delete")
    assert response.status_code == 200
    # Verify gone
    response = client.get("/shops/to-delete")
    assert response.status_code == 404


def test_delete_shop_not_found(client):
    response = client.delete("/shops/nonexistent")
    assert response.status_code == 404
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /Users/baleboy/Projects/shopping-list/server && source venv/bin/activate && pytest tests/test_shops_router.py -v`
Expected: FAIL (405 Method Not Allowed for POST/PUT/DELETE)

- [ ] **Step 4: Implement new endpoints in shops router**

Replace `server/app/routers/shops.py`:

```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/baleboy/Projects/shopping-list/server && source venv/bin/activate && pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add server/app/routers/shops.py server/app/models.py server/tests/test_shops_router.py
git commit -m "feat: add POST/PUT/DELETE endpoints for shop management"
```

---

## Phase 2: iOS App

### Task 3: Add API client methods for shop CRUD

**Files:**
- Modify: `ios/ShoppingList/ShoppingList/Services/APIClient.swift`

- [ ] **Step 1: Add createShop, updateShop, deleteShop methods**

Add to `APIClient` class before the closing brace:

```swift
    func createShop(name: String) async throws -> ShopProfile {
        let body = try JSONEncoder().encode(["name": name])
        let data = try await request("/shops", method: "POST", body: body)
        return try JSONDecoder().decode(ShopProfile.self, from: data)
    }

    func updateShop(id: String, name: String, sections: [String]) async throws -> ShopProfile {
        let payload: [String: Any] = ["name": name, "sections": sections]
        let body = try JSONSerialization.data(withJSONObject: payload)
        let data = try await request("/shops/\(id)", method: "PUT", body: body)
        return try JSONDecoder().decode(ShopProfile.self, from: data)
    }

    func deleteShop(id: String) async throws {
        _ = try await request("/shops/\(id)", method: "DELETE")
    }
```

- [ ] **Step 2: Build to verify**

Run:
```bash
cd /Users/baleboy/Projects/shopping-list/ios/ShoppingList
xcodebuild build -scheme ShoppingList -destination 'platform=iOS Simulator,name=iPhone 17 Pro' 2>&1 | tail -5
```
Expected: BUILD SUCCEEDED

- [ ] **Step 3: Commit**

```bash
git add ios/
git commit -m "feat: add shop CRUD methods to API client"
```

---

### Task 4: Update ShopPickerViewModel with create, delete, reload

**Files:**
- Modify: `ios/ShoppingList/ShoppingList/ViewModels/ShopPickerViewModel.swift`

- [ ] **Step 1: Update ShopPickerViewModel**

Replace `ios/ShoppingList/ShoppingList/ViewModels/ShopPickerViewModel.swift`:

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

    func loadShops(forceRefresh: Bool = false) async {
        guard forceRefresh || shops.isEmpty else { return }
        isLoading = shops.isEmpty
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

    func createShop(name: String) async -> ShopProfile? {
        do {
            let shop = try await APIClient.shared.createShop(name: name)
            await loadShops(forceRefresh: true)
            return shop
        } catch {
            errorMessage = "Failed to create shop: \(error.localizedDescription)"
            return nil
        }
    }

    func deleteShop(_ shop: ShopProfile) async {
        do {
            try await APIClient.shared.deleteShop(id: shop.id)
            await loadShops(forceRefresh: true)
        } catch {
            errorMessage = "Failed to delete shop: \(error.localizedDescription)"
        }
    }
}
```

- [ ] **Step 2: Build to verify**

Run:
```bash
cd /Users/baleboy/Projects/shopping-list/ios/ShoppingList
xcodebuild build -scheme ShoppingList -destination 'platform=iOS Simulator,name=iPhone 17 Pro' 2>&1 | tail -5
```
Expected: BUILD SUCCEEDED

- [ ] **Step 3: Commit**

```bash
git add ios/
git commit -m "feat: add create and delete to ShopPickerViewModel"
```

---

### Task 5: Create ShopEditorView and ViewModel

**Files:**
- Create: `ios/ShoppingList/ShoppingList/ViewModels/ShopEditorViewModel.swift`
- Create: `ios/ShoppingList/ShoppingList/Views/ShopEditorView.swift`

- [ ] **Step 1: Create ShopEditorViewModel**

Create `ios/ShoppingList/ShoppingList/ViewModels/ShopEditorViewModel.swift`:

```swift
import Foundation

@Observable
class ShopEditorViewModel {
    var name: String
    var sections: [String]
    var newSectionName = ""
    var isSaving = false
    var errorMessage: String?

    let shopId: String

    init(shop: ShopProfile) {
        self.shopId = shop.id
        self.name = shop.name
        self.sections = shop.sections
    }

    func addSection() {
        let trimmed = newSectionName.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return }
        sections.append(trimmed)
        newSectionName = ""
    }

    func deleteSection(at offsets: IndexSet) {
        sections.remove(atOffsets: offsets)
    }

    func moveSection(from source: IndexSet, to destination: Int) {
        sections.move(fromOffsets: source, toOffset: destination)
    }

    func save() async -> ShopProfile? {
        isSaving = true
        errorMessage = nil
        do {
            let updated = try await APIClient.shared.updateShop(id: shopId, name: name, sections: sections)
            isSaving = false
            return updated
        } catch {
            errorMessage = "Failed to save: \(error.localizedDescription)"
            isSaving = false
            return nil
        }
    }
}
```

- [ ] **Step 2: Create ShopEditorView**

Create `ios/ShoppingList/ShoppingList/Views/ShopEditorView.swift`:

```swift
import SwiftUI

struct ShopEditorView: View {
    @State private var viewModel: ShopEditorViewModel
    @Environment(\.dismiss) private var dismiss
    var onSave: (() -> Void)?

    init(shop: ShopProfile, onSave: (() -> Void)? = nil) {
        self._viewModel = State(initialValue: ShopEditorViewModel(shop: shop))
        self.onSave = onSave
    }

    var body: some View {
        Form {
            Section("Shop Name") {
                TextField("Name", text: $viewModel.name)
            }

            Section("Sections (drag to reorder)") {
                List {
                    ForEach(viewModel.sections, id: \.self) { section in
                        Text(section)
                    }
                    .onMove { viewModel.moveSection(from: $0, to: $1) }
                    .onDelete { viewModel.deleteSection(at: $0) }
                }

                HStack {
                    TextField("New section", text: $viewModel.newSectionName)
                    Button("Add") {
                        viewModel.addSection()
                    }
                    .disabled(viewModel.newSectionName.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }

            if let error = viewModel.errorMessage {
                Section {
                    Text(error)
                        .foregroundStyle(.red)
                }
            }
        }
        .navigationTitle("Edit Shop")
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button("Save") {
                    Task {
                        if await viewModel.save() != nil {
                            onSave?()
                            dismiss()
                        }
                    }
                }
                .disabled(viewModel.name.trimmingCharacters(in: .whitespaces).isEmpty || viewModel.isSaving)
            }
        }
        .environment(\.editMode, .constant(.active))
    }
}

#Preview {
    NavigationStack {
        ShopEditorView(shop: ShopProfile(
            id: "lidl",
            name: "Lidl Main Street",
            sections: ["produce", "dairy", "bakery", "frozen"]
        ))
    }
}
```

- [ ] **Step 3: Build to verify**

Run:
```bash
cd /Users/baleboy/Projects/shopping-list/ios/ShoppingList
xcodebuild build -scheme ShoppingList -destination 'platform=iOS Simulator,name=iPhone 17 Pro' 2>&1 | tail -5
```
Expected: BUILD SUCCEEDED

- [ ] **Step 4: Commit**

```bash
git add ios/
git commit -m "feat: add shop editor screen with drag-to-reorder sections"
```

---

### Task 6: Update ShopPickerView with add, swipe edit/delete

**Files:**
- Modify: `ios/ShoppingList/ShoppingList/Views/ShopPickerView.swift`

- [ ] **Step 1: Update ShopPickerView**

Replace `ios/ShoppingList/ShoppingList/Views/ShopPickerView.swift`:

```swift
import SwiftUI

struct ShopPickerView: View {
    @State private var viewModel: ShopPickerViewModel
    @Binding var selectedShop: ShopProfile?
    @State private var showingAddAlert = false
    @State private var newShopName = ""
    @State private var shopToEdit: ShopProfile?
    @State private var showingDeleteConfirm = false
    @State private var shopToDelete: ShopProfile?

    init(selectedShop: Binding<ShopProfile?>, viewModel: ShopPickerViewModel = ShopPickerViewModel()) {
        self._selectedShop = selectedShop
        self._viewModel = State(initialValue: viewModel)
    }

    var body: some View {
        Group {
            if viewModel.isLoading {
                ProgressView("Loading shops...")
            } else if let error = viewModel.errorMessage {
                VStack(spacing: 16) {
                    Text(error)
                        .foregroundStyle(.secondary)
                    Button("Retry") {
                        Task { await viewModel.loadShops(forceRefresh: true) }
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
                    .swipeActions(edge: .trailing) {
                        Button(role: .destructive) {
                            shopToDelete = shop
                            showingDeleteConfirm = true
                        } label: {
                            Label("Delete", systemImage: "trash")
                        }
                        Button {
                            shopToEdit = shop
                        } label: {
                            Label("Edit", systemImage: "pencil")
                        }
                        .tint(.blue)
                    }
                }
            }
        }
        .navigationTitle("Select Shop")
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    newShopName = ""
                    showingAddAlert = true
                } label: {
                    Image(systemName: "plus")
                }
            }
        }
        .alert("New Shop", isPresented: $showingAddAlert) {
            TextField("Shop name", text: $newShopName)
            Button("Cancel", role: .cancel) {}
            Button("Add") {
                Task { await viewModel.createShop(name: newShopName) }
            }
        }
        .alert("Delete Shop?", isPresented: $showingDeleteConfirm) {
            Button("Cancel", role: .cancel) {}
            Button("Delete", role: .destructive) {
                if let shop = shopToDelete {
                    Task { await viewModel.deleteShop(shop) }
                }
            }
        } message: {
            if let shop = shopToDelete {
                Text("Delete \"\(shop.name)\"? This cannot be undone.")
            }
        }
        .navigationDestination(item: $shopToEdit) { shop in
            ShopEditorView(shop: shop) {
                Task { await viewModel.loadShops(forceRefresh: true) }
            }
        }
        .task { await viewModel.loadShops() }
    }
}

#Preview {
    let viewModel = ShopPickerViewModel()
    viewModel.shops = [
        ShopProfile(id: "lidl", name: "Lidl Main Street", sections: ["produce", "dairy", "bakery"]),
        ShopProfile(id: "tesco", name: "Tesco Express", sections: ["fruit & veg", "dairy", "meat"]),
    ]
    return NavigationStack {
        ShopPickerView(selectedShop: .constant(nil), viewModel: viewModel)
    }
}
```

- [ ] **Step 2: Build to verify**

Run:
```bash
cd /Users/baleboy/Projects/shopping-list/ios/ShoppingList
xcodebuild build -scheme ShoppingList -destination 'platform=iOS Simulator,name=iPhone 17 Pro' 2>&1 | tail -5
```
Expected: BUILD SUCCEEDED

- [ ] **Step 3: Commit**

```bash
git add ios/
git commit -m "feat: add shop create, edit, and delete to shop picker"
```

---

### Task 7: Run all tests and update ContentView navigation

**Files:**
- Modify: `ios/ShoppingList/ShoppingList/ContentView.swift` (may need update if ShopPickerView init changed)

- [ ] **Step 1: Run backend tests**

```bash
cd /Users/baleboy/Projects/shopping-list/server && source venv/bin/activate && pytest tests/ -v
```
Expected: ALL PASS

- [ ] **Step 2: Run iOS tests**

```bash
cd /Users/baleboy/Projects/shopping-list/ios/ShoppingList
xcodebuild test -scheme ShoppingList -destination 'platform=iOS Simulator,name=iPhone 17 Pro' 2>&1 | tail -20
```
Expected: ALL PASS

- [ ] **Step 3: Verify ContentView still works**

Read `ContentView.swift` — the `ShopPickerView` init signature hasn't changed (still takes `selectedShop` binding and optional viewModel), so no changes needed. But the `.navigationDestination(item: $selectedShop)` for ListPickerView is in ContentView, while `.navigationDestination(item: $shopToEdit)` for ShopEditorView is in ShopPickerView. Verify no conflicts.

- [ ] **Step 4: Commit (if any fixes needed)**

```bash
git add ios/
git commit -m "fix: verify navigation works with shop editor"
```

---

### Task 8: Update docs

**Files:**
- Modify: `docs/superpowers/specs/2026-03-28-shopping-list-design.md`
- Modify: `README.md`

- [ ] **Step 1: Update main design spec**

In the **Endpoints** table in `docs/superpowers/specs/2026-03-28-shopping-list-design.md`, add:

```
| `POST` | `/shops` | Create a new shop with default sections |
| `PUT` | `/shops/{id}` | Update shop name and sections |
| `DELETE` | `/shops/{id}` | Delete a shop |
```

In the **iOS App** section, update the Shop Picker description:

```
**Shop Picker (launch screen):**
- Lists available shops from `GET /shops`
- Tap to select; remembers last-used shop
- Add new shops via + button (creates with default sections)
- Swipe left to edit (opens Shop Editor) or delete

**Shop Editor:**
- Edit shop name
- Drag to reorder sections
- Add or delete sections
- Saves to server via `PUT /shops/{id}`
```

Add a note about storage:

```
**Shop storage:** Shops edited from the app are stored server-side in `cache/shops/` as JSON,
separate from git-synced YAML files. App edits take priority over YAML. New shops are stored
only in the cache. Deleting a git-synced shop creates a tombstone in the cache.
```

- [ ] **Step 2: Update README**

In the **Architecture** section of `README.md`, add a bullet:

```
- **Shop Management:** Shops can be created, edited (sections reordered), and deleted from the iOS app. Changes are stored server-side and take priority over git-synced YAML profiles.
```

- [ ] **Step 3: Commit**

```bash
git add docs/ README.md
git commit -m "docs: update spec and README with shop management feature"
```
