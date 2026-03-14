# Sample App Flow

A minimal end-to-end demonstration connecting a Telegram bot, an internal write
API, a SQLite database, and a browser-facing read UI.

---

## Overview

The sample app runs as **three separate processes**:

| Process | Entry point | Bind address | Exposed publicly |
|---|---|---|---|
| Telegram bot | `scratch_space/feature_sample/sample_bot.py` | n/a (polling) | No |
| Frontend webapp | `tg_central_hub_bot.webapp.app:app` | `0.0.0.0:8000` | Yes - via Cloudflare Tunnel |
| Backend service | `tg_central_hub_bot.webapp.backend_app:backend_app` | `127.0.0.1:8001` | Never |

**Data flow:**

```
User sends /add <text> to the Telegram bot
  │
  ▼
Bot calls POST http://127.0.0.1:8001/internal/entries
  with Authorization: Bearer <BOT_API_KEY>
  │
  ▼
Backend validates key, inserts row into SQLite (data/sample.db)
Returns {"id": 1, "text": "...", "created_at": "..."}
  │
  ▼
Bot replies "Saved entry #1: <text>"

Meanwhile, in the browser:
User visits https://entries.pitrified.qzz.io/entries  (Google login required)
  │
  ▼
Page loads; HTMX polls GET /pages/partials/entries-table every 5 seconds
  │
  ▼
Frontend reads the same SQLite file (read-only) and renders the table
```

**Network exposure model:**

```
internet
  │
  ▼
Cloudflare Zero Trust (Google Auth gate)
  │                         │
  ▼                         ▼
bot.pitrified.qzz.io    entries.pitrified.qzz.io
(Telegram IP bypass)    (Google OAuth required)
  │                         │
  ▼                         ▼
Cloudflare Tunnel (single outbound connection from the Linux box)
  │                         │
  ▼                         ▼
localhost:5000          localhost:8000
PTB webhook server      Frontend FastAPI app
       │                    │
       └──────────┬─────────┘
                  ▼
          localhost:8001
          Backend FastAPI app  ──▶  data/sample.db
          (127.0.0.1 only,
           not in tunnel ingress)
```

---

## Setup guide

### 1 - Required environment variables

Add all of the following to `~/cred/tg-central-hub-bot/.env`:

```dotenv
# --- Always required ---
BOT_TOKEN=<token from BotFather>

# --- Sample app ---
BOT_API_KEY=<64-char hex, e.g.: python -c "import secrets; print(secrets.token_hex(32))">
SAMPLE_DB_PATH=data/sample.db     # optional, this is the default

# --- Google OAuth (frontend webapp) ---
GOOGLE_CLIENT_ID=<your OAuth client ID>
GOOGLE_CLIENT_SECRET=<your OAuth client secret>
SESSION_SECRET_KEY=<64-char hex>  # required in prod; auto-generated in dev

# --- Cloudflare / proxy (prod only) ---
TRUSTED_HOSTS=entries.pitrified.qzz.io,bot.pitrified.qzz.io,localhost,127.0.0.1
PUBLIC_BASE_URL=https://entries.pitrified.qzz.io

# --- Environment ---
ENV_STAGE_TYPE=dev      # dev (default) or prod
ENV_LOCATION_TYPE=local # local (default) or render
```

#### Dev vs prod differences

| Variable / behaviour | `dev` | `prod` |
|---|---|---|
| `SESSION_SECRET_KEY` | Auto-generated at startup (sufficient for local testing) | Must be set manually; startup fails without it |
| `TrustedHostMiddleware` | Allows all hosts (`*`) - test client and `localhost` work without extra config | Enforces `TRUSTED_HOSTS` list; rejects requests with an unexpected `Host` header |
| Swagger UI / ReDoc | Self-hosted at `/docs` and `/redoc` (no CDN) | Hidden (`docs_url=None`) |
| `PUBLIC_BASE_URL` | Not needed - OAuth redirect uses `http://localhost:8000` | Should be set to the public Cloudflare domain so OAuth redirects point to the correct URL |
| `GOOGLE_REDIRECT_URI` | Can be left unset (defaults to `http://localhost:8000/auth/google/callback`) | Derived from `PUBLIC_BASE_URL` at request time; `GOOGLE_REDIRECT_URI` is used as fallback only |

### 2 - Start the backend service

The backend binds exclusively to `127.0.0.1` and is never added to the Cloudflare
tunnel ingress. It handles writes from the bot only.

```bash
source ~/cred/tg-central-hub-bot/.env
uv run uvicorn tg_central_hub_bot.webapp.backend_app:backend_app \
  --host 127.0.0.1 --port 8001
```

SQLite table is created automatically on first startup (`data/sample.db`).

### 3 - Start the frontend webapp

```bash
source ~/cred/tg-central-hub-bot/.env
uv run uvicorn tg_central_hub_bot.webapp.app:app \
  --host 0.0.0.0 --port 8000
```

- Local: `http://localhost:8000`
- Via Cloudflare Tunnel: `https://entries.pitrified.qzz.io`

### 4 - Run the sample bot

The sample bot uses **polling** (no webhook required for local dev):

```bash
source ~/cred/tg-central-hub-bot/.env
uv run python scratch_space/feature_sample/sample_bot.py
```

Send `/start` to see instructions, then `/add hello world` to create an entry.

### 5 - Verify with curl

```bash
# Create an entry (201)
curl -s -X POST http://127.0.0.1:8001/internal/entries \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BOT_API_KEY" \
  -d '{"text": "test"}' | python -m json.tool

# Wrong key → 403
curl -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:8001/internal/entries \
  -H "Authorization: Bearer wrong" -d '{"text": "x"}'

# No auth header → 401
curl -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:8001/internal/entries \
  -d '{"text": "x"}'
```

### 6 - Run tests

```bash
BOT_TOKEN=fake uv run pytest \
  tests/config/test_sample_app_config.py \
  tests/params/test_sample_app_params.py \
  tests/webapp/test_bot_auth.py \
  tests/webapp/test_entries_service.py -v
```

---

## Technical deep dive

### Config and params layer

The sample app follows the same config/params split as the rest of the project:

- `src/tg_central_hub_bot/config/sample_app_config.py` - `SampleAppConfig(BaseModelKwargs)` holds `db_path: Path` and `bot_api_key: SecretStr`. It is a pure Pydantic model; it never reads env vars.
- `src/tg_central_hub_bot/params/sample_app_params.py` - `SampleAppParams` reads `BOT_API_KEY` and `SAMPLE_DB_PATH` from the environment. Raises `MissingBotApiKeyError` (not bare `ValueError`) if the key is absent. The raw key is stored as `SecretStr` and is fully masked in `__str__` / `__repr__`.
- `SampleAppParams` is **optional** in the singleton: `TgCentralHubBotParams` only instantiates it when `BOT_API_KEY` is present in the environment. When the variable is absent, `params.sample_app` is `None` and the rest of the app works unchanged.

```python
# tg_central_hub_bot_params.py (relevant excerpt)
if os.getenv("BOT_API_KEY"):
    self.sample_app = SampleAppParams(env_type=self.env_type)
else:
    self.sample_app = None
```

### Bot-to-backend authentication

The bot is a trusted internal caller on the same machine. Authentication uses a
**pre-shared API key** rather than OAuth:

- `BOT_API_KEY` - a 64-char random hex string, stored only in `.env`.
- The bot sends `Authorization: Bearer <BOT_API_KEY>` on every request.
- The backend validates it in `src/tg_central_hub_bot/webapp/core/bot_auth.py` using `hmac.compare_digest` for constant-time comparison, preventing timing-based side-channel attacks.
- The expected key is stored as raw bytes in `app.state.bot_api_key` during lifespan startup.

```python
# bot_auth.py (simplified)
def verify_bot_api_key(credentials, request) -> None:
    expected: bytes = request.app.state.bot_api_key
    provided: bytes = credentials.credentials.encode()
    if not hmac.compare_digest(expected, provided):
        raise HTTPException(status_code=403, detail="Forbidden")
```

### EntriesService and SQLite

`src/tg_central_hub_bot/webapp/services/entries_service.py` wraps stdlib `sqlite3`
with `asyncio.to_thread` to avoid blocking the event loop - no extra async SQLite
dependency needed. All queries use parameterised statements (no string interpolation).

Schema (created automatically on first `init_db()` call):

```sql
CREATE TABLE IF NOT EXISTS entries (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    text       TEXT    NOT NULL,
    created_at TEXT    NOT NULL
);
```

Both the backend app and the frontend app share the **same SQLite file**. The
backend has write access; the frontend reads via `list_entries()` (newest first)
through the same `EntriesService` instance wired into `app.state`.

### Router separation

| Router | Mount | Auth | Process |
|---|---|---|---|
| `webapp/internal/entries_router.py` | `POST /internal/entries` | `verify_bot_api_key` (Bearer token) | Backend only (`127.0.0.1:8001`) |
| `webapp/api/v1/entries_router.py` | `GET /api/v1/entries/` | Google OAuth session (`get_current_user`) | Frontend webapp (`:8000`) |
| `webapp/routers/pages_router.py` | `GET /entries` | Google OAuth session | Frontend webapp (`:8000`) |
| `webapp/routers/pages_router.py` | `GET /pages/partials/entries-table` | Google OAuth session | Frontend webapp (`:8000`) |

The internal router is mounted **only** on the backend app factory (`create_backend_app()`). It is never registered with the frontend app.

### HTMX polling

`templates/pages/entries.html` renders a `<div>` that instructs HTMX to:

- Fetch `GET /pages/partials/entries-table` on page load, then every 5 seconds.
- Swap the response HTML into `innerHTML` of the div.

`templates/partials/entries_table.html` returns a Bulma table fragment. If the
`EntriesService` is not configured on app state (e.g., `BOT_API_KEY` was never
set) the partial returns an empty table gracefully - no 500 error.

### Cloudflare Tunnel and proxy headers

**Tunnel ingress** (in `~/.cloudflared/config.yml`) lists only `:5000` (PTB webhook)
and `:8000` (frontend). The backend on `:8001` is simply absent from ingress, making
it unreachable from outside the machine. It also binds to `127.0.0.1`, so it is
not reachable from the local network either.

**Proxy headers** - `cloudflared` connects to the app from localhost and forwards:

- `X-Forwarded-Proto` - the public scheme (`https`).
- `X-Forwarded-Host` - the public hostname (`entries.pitrified.qzz.io`).

Two middlewares are added in `create_app()`:

1. `ProxyHeadersMiddleware(trusted_hosts=["127.0.0.1", "::1"])` - reads and promotes the forwarded headers, but only when the actual TCP connection originates from localhost. External callers cannot spoof these headers because they cannot send requests from those addresses.
2. `TrustedHostMiddleware` - in `prod` mode, enforces the `TRUSTED_HOSTS` list and rejects requests with unexpected `Host` headers. In `dev` mode (or `debug=True`) it allows all hosts so the test client and `localhost` work without configuration.

### OAuth redirect URI derivation

Behind Cloudflare, the local app sees `http://localhost:8000` but the browser
lives at `https://entries.pitrified.qzz.io`. The redirect URI sent to Google must
match the public URL exactly.

`src/tg_central_hub_bot/webapp/utils/url_utils.py` provides `get_public_base_url(request, override)`:

```
Resolution order:
1. override  - explicit PUBLIC_BASE_URL env var, if set
2. X-Forwarded-Proto + X-Forwarded-Host headers (trusted proxy only)
3. Raw request scheme + netloc (local / direct access)
```

Both `google_login` and `google_callback` handlers call `get_public_base_url` and
build the redirect URI dynamically, ensuring the same URL is sent to Google at
login initiation and at token exchange (Google validates that they match).

### Backend app factory

`src/tg_central_hub_bot/webapp/backend_app.py` exports a `create_backend_app(config?)` factory and a module-level `backend_app` instance. Key details:

- Swagger UI, ReDoc, and the OpenAPI schema are all disabled (`docs_url=None`, `redoc_url=None`, `openapi_url=None`). The backend is an internal service; it does not need a public API browser.
- The lifespan handler initialises `EntriesService`, calls `init_db()`, and stores both the service and the raw API key bytes in `app.state`. Handlers retrieve them via `request.app.state`.
- The module-level `backend_app = create_backend_app()` call reads `BOT_API_KEY` and `SAMPLE_DB_PATH` from the environment at import time, which is what uvicorn picks up via the `module:attr` entry point.
