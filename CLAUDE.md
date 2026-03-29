# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Shopping list manager: write markdown lists at home, see them sorted by store aisle on your phone. An LLM (Claude Haiku) auto-categorizes items into shop sections.

## Commands

### Backend (server/)

```bash
cd server && source venv/bin/activate

# Run locally
SHOPPING_DATA_DIR=/path/to/data-repo SHOPPING_ANTHROPIC_API_KEY=your-key uvicorn app.main:app --reload --port 8080

# Run all tests
pytest tests/ -v

# Run a single test file
pytest tests/test_categorizer.py -v

# Run a single test
pytest tests/test_categorizer.py::test_function_name -v
```

### iOS (ios/ShoppingList/)

```bash
cd ios/ShoppingList

# Build
xcodebuild build -scheme ShoppingList -destination 'platform=iOS Simulator,name=iPhone 17 Pro'

# Run tests
xcodebuild test -scheme ShoppingList -destination 'platform=iOS Simulator,name=iPhone 17 Pro'
```

### Deploy backend to Fly.io

```bash
cd server && fly deploy
```

## Architecture

### Backend (Python/FastAPI)

- **Entry point:** `app/main.py` — FastAPI app with API key auth (X-API-Key header) on all routes except `/webhook` and `/health`
- **Config:** `app/config.py` — Pydantic settings, all env vars prefixed with `SHOPPING_` (data_dir, api_key, anthropic_api_key, github_webhook_secret)
- **Routers:** `app/routers/` — shops (CRUD), lists (get/categorize), webhook (GitHub push sync)
- **Services:**
  - `categorizer.py` — calls Claude Haiku to map items to shop sections; caches results as JSON in `{data_dir}/cache/`
  - `shop_service.py` — manages shop profiles (YAML on disk, with server-side overrides)
  - `list_service.py` — parses markdown lists from `{data_dir}/lists/`
  - `git_sync.py` — pulls data repo on webhook trigger
- **Storage:** File-based, no database. Lists as markdown, shops as YAML, cache as JSON. All under `SHOPPING_DATA_DIR`.

### iOS App (SwiftUI)

- **MVVM pattern:** Views in `Views/`, ViewModels in `ViewModels/`, Models in `Models/`
- **Screens:** ShopPicker → ShopEditor (edit sections), ListPicker → ShoppingList (tap to check off)
- **Networking:** `Services/APIClient.swift` talks to the FastAPI backend
- **Config:** `Services/AppConfig.swift` (gitignored) — holds server URL and API key. Copy from `.example` file.

### Data Flow

1. User edits `lists/master.md` → git push → GitHub webhook → server pulls via git_sync
2. App requests categorized list → server checks cache → if miss, calls Claude Haiku to categorize → caches result
3. Cache is invalidated when webhook receives a push (new list content)
