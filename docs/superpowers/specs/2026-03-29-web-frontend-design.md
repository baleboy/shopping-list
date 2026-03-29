# Web Frontend for List Management

## Overview

A browser-based frontend for managing shopping lists, served from the existing FastAPI backend on Fly.io. Allows family members to create, edit, and delete lists without needing git or markdown knowledge.

## Architecture

- Single `index.html` file with inline CSS and JS in `server/static/`
- Served by FastAPI's `StaticFiles` at `/`
- No build step, no framework, no external dependencies
- Same deployment as the backend (`fly deploy`)

## Backend Changes

### New Endpoints

**`PUT /lists/{name}`** — Update list content
- Request: `{"items": ["milk", "eggs", "bananas"]}`
- Converts items to markdown format (`- item` per line) and writes to `{data_dir}/lists/{name}.md`
- Returns: `ListResponse(name, items)`

**`DELETE /lists/{name}`** — Delete a list
- Deletes `{data_dir}/lists/{name}.md` and any associated cache files in `{data_dir}/cache/`
- Returns: `{"status": "ok"}`

**`POST /sync`** — Push changes to git
- Runs `git add .`, `git commit -m "Update lists"`, `git push` in the data directory
- Returns: `{"status": "ok"}` or error message
- Protected by the same API key auth as other endpoints

### Modified Endpoints

**`POST /lists`** — Add optional `items` field
- `CreateListRequest(name, items: list[str] | None = None)`
- If items provided, writes them immediately; otherwise creates an empty list

### Static File Serving

- Mount `StaticFiles` at `/static` in `main.py`
- Serve `index.html` at `/` as a catch-all HTML response

## Frontend Design

### Authentication

- On first load, show a centered password input
- Password is sent as `X-API-Key` header on all API calls
- Stored in `localStorage` to persist across sessions
- On 401 response, clear stored password and re-prompt

### Layout

Sidebar + editor, responsive:

- **Desktop (>=768px):** Side-by-side panels
- **Mobile (<768px):** Sidebar collapses, hamburger menu to toggle

### Sidebar

- List of list names, click to select
- Selected list visually highlighted
- "+ New list" button at bottom
- Small delete button per list (with browser `confirm()` dialog)

### Editor Panel

- List name displayed as heading at top
- Plain textarea, one item per line (no `- ` prefix needed)
- "Save" button — sends items array to `PUT /lists/{name}`
- "Sync" button — calls `POST /sync` to push changes to GitHub
- Unsaved changes indicator (visual cue on save button or subtle text)

### Behavior

- Switching lists with unsaved changes shows a discard confirmation
- "New list" prompts for a name, then opens empty editor
- Delete shows `confirm()` dialog, then calls `DELETE /lists/{name}`
- Save: splits textarea by newlines, filters empty lines, sends as items array
- On load: fetches list names via `GET /lists`, selects the first one, fetches its items via `GET /lists/{name}`

## Data Flow

1. User edits list in browser → Save → `PUT /lists/{name}` → server writes markdown to disk
2. User clicks Sync → `POST /sync` → server commits and pushes to GitHub
3. GitHub webhook fires → other server instances pull changes
4. iOS app requests categorized list → server reads updated markdown → categorizes

## What's NOT in scope

- No real user accounts or session management
- No offline/PWA support
- No drag-and-drop reordering
- No real-time collaboration
- No shop management from the web (iOS app handles that)
