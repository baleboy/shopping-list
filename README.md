# Shopping List Manager

Write your shopping list at home in markdown. See it on your phone sorted by aisle. Check off items as you shop.

## How It Works

1. **At home** — edit your shopping list in the web app (or markdown if you prefer)
2. **Sync** — hit Sync in the web app, or `git push`; a webhook keeps the server in sync
3. **In the shop** — open the iOS app, pick your shop, and see items sorted by section
4. **Shop** — tap items to check them off as you go

An LLM (Claude) automatically categorizes items into shop sections — no manual tagging needed.

## Project Structure

```
server/          # Python/FastAPI backend
ios/             # SwiftUI iOS app
lists/           # Shopping list markdown files (sample data)
shops/           # Shop profile YAML files (sample data)
docs/            # Design spec and implementation plan
```

## Setup

### Prerequisites

- Python 3.9+
- Xcode 26+
- A [Fly.io](https://fly.io) account
- An [Anthropic API key](https://console.anthropic.com)
- An Apple Developer account (for TestFlight)

### Data Repo

Create a separate GitHub repo for your shopping data with this structure:

```
lists/
  master.md       # Your recurring shopping list
shops/
  my-shop.yaml    # One file per shop
```

**Shopping list** (`lists/master.md`):
```markdown
# Weekly Shopping
- milk
- bananas
- chicken breast
- sourdough bread
```

**Shop profile** (`shops/my-shop.yaml`):
```yaml
name: "My Local Shop"
sections:
  - produce
  - bakery
  - dairy
  - meat
  - frozen
  - household
```

Section order should match the physical layout of the shop.

### Backend

```bash
cd server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Run locally:**
```bash
SHOPPING_DATA_DIR=/path/to/your/data-repo SHOPPING_ANTHROPIC_API_KEY=your-key uvicorn app.main:app --reload --port 8080
```

**Deploy to Fly.io:**

```bash
fly launch
fly volumes create shopping_data -r REGION -n 1
fly secrets set SHOPPING_ANTHROPIC_API_KEY=your-anthropic-key
fly secrets set SHOPPING_API_KEY=your-password
fly secrets set SHOPPING_GITHUB_WEBHOOK_SECRET=$(openssl rand -hex 32)
fly deploy
```

Then set up a GitHub webhook on your data repo:
- **URL:** `https://your-app.fly.dev/webhook`
- **Content type:** `application/json`
- **Secret:** same value as `SHOPPING_GITHUB_WEBHOOK_SECRET`
- **Events:** Just `push`

### iOS App

1. Copy the config example:
   ```bash
   cp ios/ShoppingList/ShoppingList/Services/AppConfig.swift.example \
      ios/ShoppingList/ShoppingList/Services/AppConfig.swift
   ```
2. Edit `AppConfig.swift` with your Fly URL and API key
3. Open `ios/ShoppingList/ShoppingList.xcodeproj` in Xcode
4. Build and run on simulator or device
5. Distribute to household members via TestFlight

### Running Tests

**Backend:**
```bash
cd server && source venv/bin/activate && pytest tests/ -v
```

**iOS:**
```bash
cd ios/ShoppingList && xcodebuild test -scheme ShoppingList -destination 'platform=iOS Simulator,name=iPhone 17 Pro'
```

## Architecture

- **Backend:** Python/FastAPI with file-based storage (no database). Markdown lists and YAML shop profiles on disk, cached categorization results as JSON.
- **iOS App:** SwiftUI with four screens (shop picker, shop editor, list picker, shopping list). Offline caching for use without connectivity.
- **Shop Management:** Shops can be created, edited (sections reordered), and deleted from the iOS app. Changes are stored server-side and take priority over git-synced YAML profiles.
- **LLM Integration:** Claude API categorizes items into shop sections. Results are cached server-side so subsequent requests are instant.
- **Web Frontend:** Single-page app served at `/` for managing lists in the browser. Password-protected using the API key. No build step — just a single HTML file with inline CSS/JS.
- **Sync:** Git-based. Push lists from home (or hit Sync in the web app), webhook triggers server pull. Check-off state stored server-side and shared across household devices.
