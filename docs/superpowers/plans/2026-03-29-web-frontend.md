# Web Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a browser-based shopping list editor served from the existing FastAPI backend, with create/edit/delete and git sync.

**Architecture:** Single `index.html` with inline CSS/JS, served by FastAPI's StaticFiles. Three new backend endpoints (`PUT /lists/{name}`, `DELETE /lists/{name}`, `POST /sync`) plus a modification to the existing `POST /lists`. Password auth via the existing `X-API-Key` mechanism.

**Tech Stack:** Python/FastAPI (backend), vanilla HTML/CSS/JS (frontend)

---

## File Structure

- **Create:** `server/app/static/index.html` — the entire web frontend (HTML + inline CSS + inline JS)
- **Create:** `server/app/routers/sync.py` — sync router with `POST /sync` endpoint
- **Modify:** `server/app/services/list_service.py` — add `update_list()`, `delete_list()`, `create_list()` changes
- **Modify:** `server/app/routers/lists.py` — add `PUT` and `DELETE` endpoints, modify `POST` to accept items
- **Modify:** `server/app/services/git_sync.py` — add `git_push()` function
- **Modify:** `server/app/main.py` — mount static files, add sync router
- **Modify:** `server/Dockerfile` — copy `static/` directory
- **Create:** `server/tests/test_list_update_delete.py` — tests for new list service functions and router endpoints
- **Create:** `server/tests/test_sync_router.py` — tests for sync endpoint

---

### Task 1: Add `update_list()` and `delete_list()` to list service

**Files:**
- Modify: `server/app/services/list_service.py`
- Create: `server/tests/test_list_update_delete.py`

- [ ] **Step 1: Write failing tests for `update_list` and `delete_list`**

In `server/tests/test_list_update_delete.py`:

```python
from app.services.list_service import update_list, delete_list, get_list


def test_update_list(tmp_data_dir):
    (tmp_data_dir / "lists" / "weekly.md").write_text("- milk\n")
    update_list("weekly", ["eggs", "bread", "butter"])
    assert get_list("weekly") == ["eggs", "bread", "butter"]


def test_update_list_writes_markdown(tmp_data_dir):
    (tmp_data_dir / "lists" / "weekly.md").write_text("")
    update_list("weekly", ["eggs", "bread"])
    content = (tmp_data_dir / "lists" / "weekly.md").read_text()
    assert content == "- eggs\n- bread\n"


def test_update_list_not_found(tmp_data_dir):
    result = update_list("nonexistent", ["eggs"])
    assert result is None


def test_delete_list(tmp_data_dir):
    (tmp_data_dir / "lists" / "weekly.md").write_text("- milk\n")
    assert delete_list("weekly") is True
    assert get_list("weekly") is None


def test_delete_list_not_found(tmp_data_dir):
    assert delete_list("nonexistent") is False


def test_delete_list_removes_cache(tmp_data_dir):
    (tmp_data_dir / "lists" / "weekly.md").write_text("- milk\n")
    cache_dir = tmp_data_dir / "cache"
    cache_dir.mkdir()
    (cache_dir / "weekly_test-shop.json").write_text("{}")
    delete_list("weekly")
    assert not (cache_dir / "weekly_test-shop.json").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd server && source venv/bin/activate && pytest tests/test_list_update_delete.py -v`
Expected: FAIL — `ImportError: cannot import name 'update_list'`

- [ ] **Step 3: Implement `update_list` and `delete_list`**

Add to `server/app/services/list_service.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd server && pytest tests/test_list_update_delete.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Run full test suite**

Run: `cd server && pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add server/app/services/list_service.py server/tests/test_list_update_delete.py
git commit -m "feat: add update_list and delete_list to list service"
```

---

### Task 2: Add PUT and DELETE endpoints to lists router

**Files:**
- Modify: `server/app/routers/lists.py`
- Modify: `server/tests/test_list_update_delete.py` (add router tests)

- [ ] **Step 1: Write failing tests for the new endpoints**

Append to `server/tests/test_list_update_delete.py`:

```python
def test_put_list(client, tmp_data_dir):
    (tmp_data_dir / "lists" / "weekly.md").write_text("- milk\n")
    response = client.put("/lists/weekly", json={"items": ["eggs", "bread"]})
    assert response.status_code == 200
    assert response.json() == {"name": "weekly", "items": ["eggs", "bread"]}


def test_put_list_not_found(client):
    response = client.put("/lists/nonexistent", json={"items": ["eggs"]})
    assert response.status_code == 404


def test_delete_list_endpoint(client, tmp_data_dir):
    (tmp_data_dir / "lists" / "weekly.md").write_text("- milk\n")
    response = client.delete("/lists/weekly")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert client.get("/lists/weekly").status_code == 404


def test_delete_list_endpoint_not_found(client):
    response = client.delete("/lists/nonexistent")
    assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd server && pytest tests/test_list_update_delete.py::test_put_list tests/test_list_update_delete.py::test_delete_list_endpoint -v`
Expected: FAIL — 405 Method Not Allowed

- [ ] **Step 3: Implement PUT and DELETE endpoints**

Add to `server/app/routers/lists.py`:

Add import at top:
```python
from app.services.list_service import list_lists, get_list, create_list, update_list, delete_list
```

Add request model:
```python
class UpdateListRequest(BaseModel):
    items: List[str]
```

Add endpoints:
```python
@router.put("/{name}", response_model=ListResponse)
async def update_list_by_name(name: str, body: UpdateListRequest):
    items = update_list(name, body.items)
    if items is None:
        raise HTTPException(status_code=404, detail="List not found")
    return ListResponse(name=name, items=items)


@router.delete("/{name}")
async def delete_list_by_name(name: str):
    if not delete_list(name):
        raise HTTPException(status_code=404, detail="List not found")
    return {"status": "ok"}
```

- [ ] **Step 4: Modify `POST /lists` to accept optional items**

Update `CreateListRequest` in `server/app/routers/lists.py`:

```python
class CreateListRequest(BaseModel):
    name: str
    items: list[str] | None = None
```

Update `create_new_list` handler:
```python
@router.post("", response_model=ListResponse, status_code=201)
async def create_new_list(
    body: CreateListRequest,
    from_param: Optional[str] = Query(None, alias="from")
):
    items = create_list(body.name, from_master=(from_param == "master"))
    if body.items is not None:
        items = update_list(body.name, body.items)
    return ListResponse(name=body.name, items=items)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd server && pytest tests/test_list_update_delete.py -v`
Expected: All tests PASS

- [ ] **Step 6: Run full test suite**

Run: `cd server && pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add server/app/routers/lists.py server/tests/test_list_update_delete.py
git commit -m "feat: add PUT and DELETE endpoints for lists"
```

---

### Task 3: Add git push and sync endpoint

**Files:**
- Modify: `server/app/services/git_sync.py`
- Create: `server/app/routers/sync.py`
- Create: `server/tests/test_sync_router.py`
- Modify: `server/app/main.py`

- [ ] **Step 1: Add `git_push()` to git_sync service**

Add to `server/app/services/git_sync.py`:

```python
def git_push(message: str = "Update lists") -> bool:
    try:
        subprocess.run(
            ["git", "add", "."],
            cwd=settings.data_dir,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=settings.data_dir,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "push"],
            cwd=settings.data_dir,
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError:
        return False
```

- [ ] **Step 2: Write failing test for sync endpoint**

In `server/tests/test_sync_router.py`:

```python
from unittest.mock import patch


def test_sync_success(client):
    with patch("app.routers.sync.git_push", return_value=True):
        response = client.post("/sync")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_sync_failure(client):
    with patch("app.routers.sync.git_push", return_value=False):
        response = client.post("/sync")
    assert response.status_code == 500
    assert "failed" in response.json()["detail"].lower()
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd server && pytest tests/test_sync_router.py -v`
Expected: FAIL — 404 (route doesn't exist yet)

- [ ] **Step 4: Create sync router**

Create `server/app/routers/sync.py`:

```python
from fastapi import APIRouter, HTTPException
from app.services.git_sync import git_push

router = APIRouter(tags=["sync"])


@router.post("/sync")
async def sync():
    if not git_push():
        raise HTTPException(status_code=500, detail="Git sync failed")
    return {"status": "ok"}
```

- [ ] **Step 5: Register sync router in main.py**

In `server/app/main.py`, add import:
```python
from app.routers import shops, lists, webhook, sync
```

Add after the webhook router line:
```python
app.include_router(sync.router, dependencies=[Depends(verify_api_key)])
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd server && pytest tests/test_sync_router.py -v`
Expected: All 2 tests PASS

- [ ] **Step 7: Run full test suite**

Run: `cd server && pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 8: Commit**

```bash
git add server/app/services/git_sync.py server/app/routers/sync.py server/tests/test_sync_router.py server/app/main.py
git commit -m "feat: add POST /sync endpoint for git push"
```

---

### Task 4: Mount static files and update Dockerfile

**Files:**
- Modify: `server/app/main.py`
- Modify: `server/Dockerfile`
- Create: `server/app/static/` (directory)

- [ ] **Step 1: Create static directory with a placeholder**

```bash
mkdir -p server/app/static
```

- [ ] **Step 2: Mount static files in main.py**

Add import at top of `server/app/main.py`:
```python
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
```

Add after router registrations:
```python
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def serve_frontend():
    return FileResponse(static_dir / "index.html")
```

- [ ] **Step 3: Update Dockerfile to copy static directory**

In `server/Dockerfile`, after the `COPY app/ app/` line, add:
```dockerfile
COPY app/static/ app/static/
```

Note: This is actually redundant since `COPY app/ app/` already copies `app/static/`, but keeping it explicit makes the intent clear. Alternatively, just verify `COPY app/ app/` handles it (it does — `static/` is inside `app/`).

On second thought, since `static/` is inside `app/`, the existing `COPY app/ app/` already includes it. No Dockerfile change needed.

- [ ] **Step 4: Run full test suite**

Run: `cd server && pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add server/app/main.py
git commit -m "feat: mount static files and serve frontend at /"
```

---

### Task 5: Build the web frontend

**Files:**
- Create: `server/app/static/index.html`

This is the largest task. The file contains all HTML, CSS, and JS inline.

- [ ] **Step 1: Create `index.html` with the complete frontend**

Create `server/app/static/index.html` with the following structure:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shopping Lists</title>
    <style>
        /* Reset */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; color: #333; height: 100vh; display: flex; flex-direction: column; }

        /* Password screen */
        #login { display: flex; align-items: center; justify-content: center; height: 100vh; }
        #login form { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        #login input { display: block; width: 100%; padding: 0.5rem; margin: 0.5rem 0; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem; }
        #login button { width: 100%; padding: 0.5rem; background: #4a9eff; color: white; border: none; border-radius: 4px; font-size: 1rem; cursor: pointer; }
        #login .error { color: #e44; font-size: 0.85rem; margin-top: 0.5rem; display: none; }

        /* App layout */
        #app { display: none; height: 100vh; }
        .header { background: white; border-bottom: 1px solid #e0e0e0; padding: 0.75rem 1rem; display: flex; align-items: center; gap: 0.75rem; }
        .header h1 { font-size: 1.1rem; flex: 1; }
        .hamburger { display: none; background: none; border: none; font-size: 1.5rem; cursor: pointer; }
        .sync-btn { padding: 0.4rem 0.8rem; background: #4a9eff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.85rem; }
        .sync-btn:disabled { opacity: 0.5; }

        .main { display: flex; flex: 1; overflow: hidden; }

        /* Sidebar */
        .sidebar { width: 220px; background: white; border-right: 1px solid #e0e0e0; display: flex; flex-direction: column; overflow-y: auto; }
        .sidebar-list { flex: 1; padding: 0.5rem; }
        .sidebar-item { display: flex; align-items: center; padding: 0.5rem 0.75rem; border-radius: 4px; cursor: pointer; margin-bottom: 2px; }
        .sidebar-item:hover { background: #f0f0f0; }
        .sidebar-item.active { background: #e8f0fe; color: #1a73e8; }
        .sidebar-item span { flex: 1; }
        .sidebar-item .delete-btn { display: none; background: none; border: none; color: #999; cursor: pointer; font-size: 1.1rem; }
        .sidebar-item:hover .delete-btn { display: block; }
        .sidebar-footer { padding: 0.5rem; border-top: 1px solid #e0e0e0; }
        .new-btn { width: 100%; padding: 0.5rem; background: none; border: 1px dashed #ccc; border-radius: 4px; cursor: pointer; color: #666; font-size: 0.9rem; }
        .new-btn:hover { border-color: #999; color: #333; }

        /* Editor */
        .editor { flex: 1; display: flex; flex-direction: column; padding: 1rem; }
        .editor-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; }
        .editor-header h2 { font-size: 1.2rem; }
        .unsaved { font-size: 0.75rem; color: #e44; }
        .editor textarea { flex: 1; width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem; font-family: inherit; line-height: 1.6; resize: none; }
        .editor-footer { margin-top: 0.75rem; display: flex; gap: 0.5rem; }
        .save-btn { padding: 0.5rem 1.5rem; background: #4a9eff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9rem; }
        .save-btn:disabled { opacity: 0.5; }
        .empty-state { flex: 1; display: flex; align-items: center; justify-content: center; color: #999; }

        /* Mobile */
        @media (max-width: 768px) {
            .hamburger { display: block; }
            .sidebar { position: fixed; left: -260px; top: 0; bottom: 0; z-index: 10; width: 260px; transition: left 0.2s; box-shadow: 2px 0 8px rgba(0,0,0,0.1); }
            .sidebar.open { left: 0; }
            .overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.3); z-index: 9; }
            .overlay.open { display: block; }
        }
    </style>
</head>
<body>

<!-- Password screen -->
<div id="login">
    <form onsubmit="return handleLogin(event)">
        <h2>Shopping Lists</h2>
        <input type="password" id="password" placeholder="Password" autofocus>
        <button type="submit">Enter</button>
        <div class="error" id="login-error">Wrong password</div>
    </form>
</div>

<!-- App -->
<div id="app">
    <div class="header">
        <button class="hamburger" onclick="toggleSidebar()">&#9776;</button>
        <h1>Shopping Lists</h1>
        <button class="sync-btn" onclick="syncToGit()">Sync</button>
    </div>
    <div class="overlay" onclick="toggleSidebar()"></div>
    <div class="main">
        <div class="sidebar">
            <div class="sidebar-list" id="sidebar-list"></div>
            <div class="sidebar-footer">
                <button class="new-btn" onclick="createNewList()">+ New list</button>
            </div>
        </div>
        <div class="editor" id="editor">
            <div class="empty-state">Select or create a list</div>
        </div>
    </div>
</div>

<script>
    let apiKey = localStorage.getItem("apiKey") || "";
    let lists = [];
    let currentList = null;
    let originalContent = "";

    // --- API helpers ---
    async function api(method, path, body) {
        const opts = { method, headers: { "X-API-Key": apiKey, "Content-Type": "application/json" } };
        if (body) opts.body = JSON.stringify(body);
        const res = await fetch(path, opts);
        if (res.status === 401) { logout(); throw new Error("Unauthorized"); }
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    }

    // --- Auth ---
    function handleLogin(e) {
        e.preventDefault();
        apiKey = document.getElementById("password").value;
        localStorage.setItem("apiKey", apiKey);
        init();
        return false;
    }

    function logout() {
        apiKey = "";
        localStorage.removeItem("apiKey");
        document.getElementById("app").style.display = "none";
        document.getElementById("login").style.display = "flex";
        document.getElementById("login-error").style.display = "block";
    }

    // --- Init ---
    async function init() {
        try {
            lists = await api("GET", "/lists");
            document.getElementById("login").style.display = "none";
            document.getElementById("app").style.display = "flex";
            renderSidebar();
            if (lists.length > 0) selectList(lists[0]);
        } catch (e) { /* login screen stays visible */ }
    }

    // --- Sidebar ---
    function renderSidebar() {
        const el = document.getElementById("sidebar-list");
        el.innerHTML = lists.map(name => `
            <div class="sidebar-item ${name === currentList ? 'active' : ''}" onclick="selectList('${name}')">
                <span>${name}</span>
                <button class="delete-btn" onclick="event.stopPropagation(); deleteList('${name}')">&times;</button>
            </div>
        `).join("");
    }

    // --- List operations ---
    function hasUnsavedChanges() {
        const ta = document.querySelector("#editor textarea");
        return ta && ta.value !== originalContent;
    }

    async function selectList(name) {
        if (hasUnsavedChanges() && !confirm("You have unsaved changes. Discard them?")) return;
        currentList = name;
        renderSidebar();
        const data = await api("GET", `/lists/${encodeURIComponent(name)}`);
        originalContent = data.items.join("\n");
        renderEditor(name, originalContent);
        closeSidebar();
    }

    function renderEditor(name, content) {
        document.getElementById("editor").innerHTML = `
            <div class="editor-header">
                <h2>${name}</h2>
                <span class="unsaved" id="unsaved" style="display:none">unsaved</span>
            </div>
            <textarea oninput="checkUnsaved()">${content}</textarea>
            <div class="editor-footer">
                <button class="save-btn" onclick="saveList()">Save</button>
            </div>
        `;
    }

    function checkUnsaved() {
        const ta = document.querySelector("#editor textarea");
        const indicator = document.getElementById("unsaved");
        if (indicator) indicator.style.display = ta.value !== originalContent ? "inline" : "none";
    }

    async function saveList() {
        const ta = document.querySelector("#editor textarea");
        const items = ta.value.split("\n").filter(line => line.trim() !== "");
        await api("PUT", `/lists/${encodeURIComponent(currentList)}`, { items });
        originalContent = items.join("\n");
        ta.value = originalContent;
        checkUnsaved();
    }

    async function createNewList() {
        const name = prompt("List name:");
        if (!name) return;
        await api("POST", "/lists", { name });
        lists.push(name);
        lists.sort();
        renderSidebar();
        await selectList(name);
    }

    async function deleteList(name) {
        if (!confirm(`Delete "${name}"?`)) return;
        await api("DELETE", `/lists/${encodeURIComponent(name)}`);
        lists = lists.filter(n => n !== name);
        renderSidebar();
        if (currentList === name) {
            currentList = null;
            document.getElementById("editor").innerHTML = '<div class="empty-state">Select or create a list</div>';
        }
    }

    async function syncToGit() {
        const btn = document.querySelector(".sync-btn");
        btn.disabled = true;
        btn.textContent = "Syncing...";
        try {
            await api("POST", "/sync");
            btn.textContent = "Synced!";
            setTimeout(() => { btn.textContent = "Sync"; btn.disabled = false; }, 2000);
        } catch (e) {
            btn.textContent = "Failed";
            setTimeout(() => { btn.textContent = "Sync"; btn.disabled = false; }, 2000);
        }
    }

    // --- Mobile sidebar ---
    function toggleSidebar() {
        document.querySelector(".sidebar").classList.toggle("open");
        document.querySelector(".overlay").classList.toggle("open");
    }
    function closeSidebar() {
        document.querySelector(".sidebar").classList.remove("open");
        document.querySelector(".overlay").classList.remove("open");
    }

    // --- Boot ---
    if (apiKey) init();
</script>
</body>
</html>
```

- [ ] **Step 2: Test manually in browser**

Run: `cd server && source venv/bin/activate && SHOPPING_DATA_DIR=/path/to/data-repo SHOPPING_ANTHROPIC_API_KEY=your-key uvicorn app.main:app --reload --port 8080`

Open `http://localhost:8080`. Verify:
- Password screen appears
- After entering API key, lists load in sidebar
- Clicking a list shows items in textarea
- Editing and saving works
- Creating a new list works
- Deleting a list works
- Sync button works
- Mobile hamburger menu works (resize browser)
- Unsaved changes warning works when switching lists

- [ ] **Step 3: Commit**

```bash
git add server/app/static/index.html
git commit -m "feat: add web frontend for list management"
```

---

### Task 6: Final integration test

**Files:**
- No new files — verify everything works together

- [ ] **Step 1: Run full test suite**

Run: `cd server && pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 2: Test deploy locally with Docker**

```bash
cd server && docker build -t shopping-list . && docker run --rm -p 8080:8080 -e SHOPPING_API_KEY=test shopping-list
```

Verify `http://localhost:8080` serves the frontend.

- [ ] **Step 3: Commit any final fixes if needed**

- [ ] **Step 4: Deploy to Fly.io**

```bash
cd server && fly deploy
```
