# Shopping List Manager — Design Spec

## Overview

A system for managing weekly shopping lists. Lists are written at home as plain markdown files, pushed via git to a backend server, and viewed on an iOS app in the shop — sorted by aisle order using LLM-based categorization. Multiple household members can share lists and check off items in real time.

## Components

### 1. Shopping List Files (Markdown)

Edited at home in any text editor. Plain format:

```markdown
# Weekly Shopping
- milk
- bananas
- chicken breast
- sourdough bread
- cheddar cheese
- olive oil
- tomatoes
```

- **Master list** (`master.md`): recurring items, kept long-term. Can be used directly for shopping.
- **Session lists** (any name, e.g., `2026-03-28.md`, `party-supplies.md`, `weekly.md`): optional — copy from master and adjust, or create from scratch. List names are freeform.
- You can shop with any list — master or session.
- Stored in a private GitHub repo

### 2. Shop Profiles (YAML)

Edited at home, stored in the same git repo under a `shops/` directory:

```yaml
name: "Lidl Main Street"
sections:
  - produce
  - bakery
  - dairy
  - meat
  - canned goods
  - oils & condiments
  - frozen
  - household
```

The section order matches the physical layout of the shop. One file per shop (e.g., `shops/lidl-main-street.yaml`).

### 3. Backend Server (Python/FastAPI)

A lightweight server deployed on Fly.io.

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/lists` | List available session lists |
| `GET` | `/lists/{name}` | Get a raw list |
| `POST` | `/lists?from=master` | Create a new session list (copies master if `from=master` param is set, otherwise creates empty) |
| `PUT` | `/lists/{name}` | Update a list |
| `GET` | `/shops` | List available shop profiles |
| `GET` | `/shops/{id}` | Get a shop profile |
| `POST` | `/lists/{name}/prepare?shop={id}` | Categorize & sort list for a shop |
| `PATCH` | `/lists/{name}/items/{item}` | Toggle item checked/unchecked |
| `POST` | `/webhook` | GitHub webhook to trigger git pull |

**Storage:** Files on disk — markdown lists, YAML profiles, and a JSON file per session for categorized/checked state. No database.

**Sync:** The server's data directory is a clone of the GitHub repo. A GitHub webhook triggers `git pull` when changes are pushed.

**Authentication:** Shared API key/token in request headers.

**LLM Integration:** When `/prepare` is called, the server sends the item list and shop sections to the Claude API. Prompt: "Given these shop sections: [...], categorize each item: [...]. Return JSON mapping each item to its section." The result is cached as a JSON file so subsequent requests don't re-call the LLM. The response is parsed with markdown code block stripping, since LLMs may wrap JSON in ` ```json ``` ` blocks. Items that the LLM assigns to a section not in the shop profile are collected into an "Other" catch-all section at the bottom of the list.

**Categorized list format (JSON):**

```json
{
  "session": "2026-03-28",
  "shop": "lidl-main-street",
  "sections": [
    {
      "name": "produce",
      "items": [
        { "name": "bananas", "checked": false },
        { "name": "tomatoes", "checked": false }
      ]
    },
    {
      "name": "bakery",
      "items": [
        { "name": "sourdough bread", "checked": false }
      ]
    }
  ]
}
```

### 4. iOS App (SwiftUI)

Three screens:

**Shop Picker (launch screen):**
- Lists available shops from `GET /shops`
- Tap to select; remembers last-used shop

**Shopping List:**
- Fetches categorized list from backend
- Items grouped by section in shop-walk order
- Tap to check off (strikes through / grays out)
- Check-off syncs to backend in real time
- Pull-to-refresh for list changes
- Badge showing items remaining

**List Picker:**
- Shows all available lists (master and session lists)
- Option to create new list from master

**Offline:** Caches the last-fetched categorized list locally. Syncs checkmarks when connectivity returns.

**No list editing in the app** — that happens at home in the text editor.

### 5. Deployment

| Component | Platform | Cost |
|-----------|----------|------|
| Backend | Fly.io (free tier or ~$5/mo) | Free–$5/mo |
| Data/lists | GitHub repo (can be public) | Free |
| LLM | Claude API | ~cents/month |
| iOS app | TestFlight (household distribution) | $99/year (Apple Developer) |

**Server deployment:**
1. `cd server && fly launch` — creates the app and `fly.toml`
2. Configure `fly.toml`: set `SHOPPING_DATA_DIR = "/data"` env var, add a `[mounts]` section for persistent volume
3. `fly volumes create shopping_data -r REGION -n 1` — persistent volume for data + cache
4. Set secrets (names must match `SHOPPING_` env prefix):
   ```
   fly secrets set SHOPPING_ANTHROPIC_API_KEY=...
   fly secrets set SHOPPING_API_KEY=...
   fly secrets set SHOPPING_GITHUB_WEBHOOK_SECRET=...
   ```
5. `fly deploy` — builds and deploys; `start.sh` clones the data repo into `/data` on first boot, pulls on subsequent boots
6. GitHub webhook on the data repo: Settings → Webhooks → Add webhook, payload URL `https://your-app.fly.dev/webhook`, content type `application/json`, secret matching `SHOPPING_GITHUB_WEBHOOK_SECRET`
7. Update iOS `APIClient.swift` with the Fly URL (`https://your-app.fly.dev`, no port) and the `SHOPPING_API_KEY` value

**Important notes:**
- Fly serves on standard HTTPS (port 443), not 8080 — the internal port is only used inside the container
- The data repo can be public (webhook secret ensures only genuine GitHub payloads trigger pulls)
- `start.sh` handles the case where the volume mount directory already exists (non-empty) by cloning to a temp dir and moving files

## Workflow

1. **At home:** Edit `master.md`, copy to `2026-03-28.md`, adjust, `git push`
2. **Webhook fires:** Server does `git pull`, picks up changes
3. **In the shop:** Open iOS app, pick shop, app calls `/prepare` to categorize the list
4. **Shopping:** Walk the aisles, tap items to check them off
5. **Household:** Others open the same list, see real-time check-off state
