# Shop Management from iOS App — Design Spec

## Overview

Add the ability to create, edit, and delete shop profiles directly from the iOS app. Shop changes are stored server-side (not pushed to git). Shops edited via the app take priority over git-synced YAML files.

## Server Changes

### New Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/shops` | Create a new shop with default sections |
| `PUT` | `/shops/{id}` | Update shop name and/or sections (including order) |
| `DELETE` | `/shops/{id}` | Delete a shop |

### Storage

App-edited shops are saved as JSON files in `{data_dir}/cache/shops/` — outside the git-synced `shops/` directory. When listing or getting shops:

1. Load all YAML files from `{data_dir}/shops/` (git-synced)
2. Load all JSON files from `{data_dir}/cache/shops/` (app-edited)
3. App-edited shops override git-synced shops with the same ID
4. Merge both sets, return sorted by name

New shops created from the app are stored only in `cache/shops/`. Editing a git-synced shop creates an override in `cache/shops/`.

### Default Sections

New shops are created with these default sections:

```
produce, bakery, dairy & eggs, meat & fish, pasta & grains,
canned goods, oils & condiments, frozen, household
```

### Cache Invalidation

When a shop's sections change (via `PUT`), any cached categorized lists for that shop are deleted from `{data_dir}/cache/`. This forces re-categorization on the next `/prepare` call so items are assigned to the updated sections.

### Request/Response Formats

**POST /shops**
```json
// Request
{ "name": "My New Shop" }

// Response (201)
{ "id": "my-new-shop", "name": "My New Shop", "sections": ["produce", "bakery", ...] }
```

**PUT /shops/{id}**
```json
// Request
{ "name": "Updated Name", "sections": ["dairy & eggs", "produce", "bakery"] }

// Response (200)
{ "id": "my-shop", "name": "Updated Name", "sections": ["dairy & eggs", "produce", "bakery"] }
```

**DELETE /shops/{id}**
```json
// Response (200)
{ "status": "ok" }
```

## iOS Changes

### Shop Picker Screen (modified)

- **Add button** (+) in the top-right toolbar — shows an alert with a text field for the shop name, creates the shop with default sections via `POST /shops`
- **Swipe left** on any shop reveals two actions:
  - **Edit** (blue) — navigates to the Shop Editor screen
  - **Delete** (red) — confirms with an alert, then calls `DELETE /shops/{id}`
- Existing behavior (tap to select shop) is unchanged

### Shop Editor Screen (new)

- **Shop name** — editable text field at the top
- **Sections list** — displays current sections in order, supports drag-to-reorder via `.onMove`
- **Add section** — text field and "Add" button below the list
- **Swipe to delete** on individual sections
- **Save** — navigation bar button that calls `PUT /shops/{id}` with the updated name and section list, then pops back to the shop picker
- **Cancel** — discard changes and pop back

### API Client Additions

```
POST   /shops              → createShop(name:)
PUT    /shops/{id}         → updateShop(id:name:sections:)
DELETE /shops/{id}         → deleteShop(id:)
```

### No Changes To

- ListPickerView
- ShoppingListView
- ShoppingListViewModel
- Models (ShopProfile already has id, name, sections)
