# Sample app to integrate telegram bot and frontend/backend

## overview

1. user sends message to bot
2. bot calls backend endpoint
3. backend processes request and updates some basic database (sqlite)
4. bot sends back some ack to user
5. user visits frontend page to see updated database state

notes and questions:

q1:
frontend endpoint is tunneled via cloudflare as specified in
/home/pmn/repos/linux-box-cloudflare/docs/01_box_setup.md
only the frontend page should be exposed to the internet,
the backend should be accessible only from the local network

q2:
endpoints in the sample app are authenticated with google oauth,
but the bot should be able to call the backend endpoint without going through oauth flow,
since it's a trusted internal service;
we can setup some way to authenticate the bot's requests even if backend and bot are on the same machine

## Plan

### Component overview

```
internet
  │
  ▼
Cloudflare edge (Zero Trust Google Auth gate)
  │                          │
  ▼                          ▼
bot.pitrified.qzz.io    app.pitrified.qzz.io
(Telegram IP bypass)    (Google OAuth required)
  │                          │
  ▼                          ▼
Cloudflare Tunnel (single outbound connection from Linux box)
  │                          │
  ▼                          ▼
localhost:5000           localhost:8000
PTB webhook server       Frontend FastAPI app
        │                    │
        │ POST               │ READ
        ▼                    ▼
localhost:8001           SQLite DB (data/sample.db)
Backend FastAPI app ─────────────────────────▶ (shared file)
(NOT in tunnel ingress,
 binds to 127.0.0.1 only)
```

Three separate processes:

1. **Bot** - PTB webhook server on `:5000`, handles Telegram messages, calls backend
2. **Frontend webapp** - FastAPI on `:8000`, serves HTML pages + HTMX read API
3. **Backend service** - FastAPI on `:8001`, internal write API for bot, never tunneled

---

### Q1: Exposure model

The Cloudflare tunnel ingress only lists `:5000` and `:8000`. The backend on `:8001` simply never appears in `config.yml`, so it is unreachable from outside the machine regardless of any auth policy. Additionally, bind the backend to `127.0.0.1:8001` (not `0.0.0.0`) so it is only reachable on loopback even from the local network.

Updated `~/.cloudflared/config.yml` snippet:

```yaml
ingress:
  - hostname: pitrified.qzz.io
    service: http://localhost:8090 # nginx landing page (existing)

  - hostname: bot.pitrified.qzz.io
    service: http://localhost:5000 # PTB webhook

  - hostname: app.pitrified.qzz.io
    service: http://localhost:8000 # frontend FastAPI

  # backend on :8001 intentionally absent - local only
  - service: http_status:404
```

Cloudflare Zero Trust protects `app.pitrified.qzz.io` with the existing Google Auth policy.
The `bot.pitrified.qzz.io/webhook` path has a Bypass policy for Telegram IP ranges (see Phase 7 of `01_box_setup.md`).

---

### Q2: Bot-to-backend authentication

The bot is a trusted internal caller on the same machine. Use a **pre-shared API key** stored in `.env`:

- `BOT_API_KEY` - random 64-char hex (`secrets.token_hex(32)`)
- Bot sends `Authorization: Bearer <BOT_API_KEY>` on every request to backend
- Backend has a FastAPI dependency `verify_bot_api_key` that extracts and compares the key using `hmac.compare_digest` to prevent timing attacks
- The key never leaves the machine (backend is not tunneled, and `.env` is not committed)

---

### Data flow

1. User sends `/add hello` to the bot
2. PTB webhook receives at `bot.pitrified.qzz.io/webhook` (Telegram IP bypass lets it through Cloudflare Zero Trust)
3. Bot command handler calls `POST http://127.0.0.1:8001/internal/entries` with header `Authorization: Bearer <BOT_API_KEY>` and body `{"text": "hello"}`
4. Backend validates key with `hmac.compare_digest`, inserts row into SQLite, returns `{"id": 1, "text": "hello", "created_at": "..."}`
5. Bot sends "Saved entry #1: hello" back to the user
6. User visits `https://app.pitrified.qzz.io/entries` - Cloudflare Zero Trust prompts Google login
7. Frontend page loads; HTMX polls `GET /api/v1/entries` every 5 seconds
8. Frontend reads SQLite (same file, read-only) and renders the updated table

---

### New files

| Path                                                        | Purpose                                                                             |
| ----------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `src/tg_central_hub_bot/config/sample_app_config.py`        | `SampleAppConfig(BaseModelKwargs)` - db_path, bot_api_key (`SecretStr`)             |
| `src/tg_central_hub_bot/params/sample_app_params.py`        | `SampleAppParams` - loads `BOT_API_KEY` and `SAMPLE_DB_PATH` from env               |
| `src/tg_central_hub_bot/webapp/backend_app.py`              | `create_backend_app()` factory - mounts only the internal router                    |
| `src/tg_central_hub_bot/webapp/internal/`                   | Internal router package                                                             |
| `src/tg_central_hub_bot/webapp/internal/entries_router.py`  | `POST /internal/entries` protected by `verify_bot_api_key` dependency               |
| `src/tg_central_hub_bot/webapp/core/bot_auth.py`            | `verify_bot_api_key` FastAPI dependency using `hmac.compare_digest`                 |
| `src/tg_central_hub_bot/webapp/api/v1/entries_router.py`    | `GET /api/v1/entries` - OAuth-protected, returns entry list for HTMX                |
| `src/tg_central_hub_bot/webapp/services/entries_service.py` | SQLite CRUD (stdlib `sqlite3` with `aiosqlite` for async, or sync with thread pool) |
| `src/tg_central_hub_bot/webapp/schemas/entry_schemas.py`    | `EntryCreate`, `EntryRead` Pydantic models                                          |
| `templates/pages/entries.html`                              | HTMX table that polls `GET /api/v1/entries` every 5s                                |
| `scratch_space/feature_sample/sample_bot.py`                | PTB bot: `/add <text>` command, calls backend via httpx                             |

### Existing files to extend

| File                                                         | Change                                                |
| ------------------------------------------------------------ | ----------------------------------------------------- |
| `src/tg_central_hub_bot/params/tg_central_hub_bot_params.py` | Wire `SampleAppParams` into the main params singleton |
| `src/tg_central_hub_bot/webapp/api/v1/api_router.py`         | Include `entries_router`                              |
| `src/tg_central_hub_bot/webapp/routers/pages_router.py`      | Add `GET /entries` route rendering `entries.html`     |
| `.env` template / `README.md`                                | Document `BOT_API_KEY` and `SAMPLE_DB_PATH`           |

---

### Config / params design

Following the existing pattern:

```python
# config/sample_app_config.py
class SampleAppConfig(BaseModelKwargs):
    db_path: Path
    bot_api_key: SecretStr

# params/sample_app_params.py
class MissingBotApiKeyError(Exception): ...

class SampleAppParams:
    def __init__(self, env_type: EnvType) -> None:
        self.env_type = env_type
        key = os.getenv("BOT_API_KEY")
        if not key:
            raise MissingBotApiKeyError("BOT_API_KEY is not set")
        self._bot_api_key = SecretStr(key)
        raw_db = os.getenv("SAMPLE_DB_PATH", "data/sample.db")
        self.db_path = Path(raw_db)

    def to_config(self) -> SampleAppConfig:
        return SampleAppConfig(db_path=self.db_path, bot_api_key=self._bot_api_key)
```

---

### Bot auth dependency

```python
# webapp/core/bot_auth.py
import hmac
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer()

def verify_bot_api_key(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(_bearer)],
    request: Request,
) -> None:
    expected = request.app.state.bot_api_key  # set during lifespan
    provided = credentials.credentials.encode()
    if not hmac.compare_digest(expected, provided):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
```

---

### Webhook security

PTB supports a `secret_token` parameter when registering the webhook:

```python
await app.bot.set_webhook(
    url="https://bot.pitrified.qzz.io/webhook",
    secret_token=os.getenv("WEBHOOK_SECRET_TOKEN"),  # random hex, stored in .env
)
```

PTB then validates the `X-Telegram-Bot-Api-Secret-Token` header on every incoming update automatically.

---

### New env vars

| Variable               | Required     | Default          | Description                                                 |
| ---------------------- | ------------ | ---------------- | ----------------------------------------------------------- |
| `BOT_API_KEY`          | yes (sample) | -                | Pre-shared key for bot-to-backend auth (64-char hex)        |
| `SAMPLE_DB_PATH`       | no           | `data/sample.db` | Path to the SQLite database file                            |
| `WEBHOOK_SECRET_TOKEN` | no           | -                | Optional Telegram webhook secret token for extra validation |

---

### Security notes

- Backend binds to `127.0.0.1:8001` - not reachable from LAN, only loopback
- API key comparison uses `hmac.compare_digest` - constant-time, no timing leak
- SQLite queries use parameterized statements - no SQL injection
- Webhook secret token validates Telegram origin at the application layer (on top of IP-range bypass)
- `BOT_API_KEY` stored in `.env` at `~/cred/tg-central-hub-bot/.env`, never committed
- Frontend only gets read access to SQLite; write path is exclusively through the authenticated backend

---

### Implementation order

1. `SampleAppConfig` + `SampleAppParams` (config/params layer)
2. `entries_service.py` + SQLite schema (create table on startup)
3. `entry_schemas.py` (Pydantic models)
4. `bot_auth.py` (verify_bot_api_key dependency)
5. `internal/entries_router.py` + `backend_app.py`
6. `api/v1/entries_router.py` (read endpoint for HTMX)
7. `entries.html` template + pages router update
8. `sample_bot.py` (PTB bot in scratch_space)
9. Tests for auth dependency, entries service, and entry router
10. Update cloudflared `config.yml` snippet in docs

## Follow up questions

### webhook registration

in
/home/pmn/repos/linux-box-cloudflare/docs/01_box_setup.md
Phase 7: Telegram Bot Integration (Webhook Bypass)

we register the webhook with Telegram using a curl command that points to the Cloudflare edge:

```bash
curl -F "url=https://bot.pitrified.qzz.io/webhook" \
  https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook
```

how does this differ from `await app.bot.set_webhook(` using PTB?

**Answer:**

They do the exact same thing - both call the Telegram Bot API's `setWebhook` method. The `curl` command is a manual one-off shell invocation. `await app.bot.set_webhook(url=...)` is the PTB wrapper that makes the same HTTPS call to `api.telegram.org` from Python code. The PTB version additionally accepts a `secret_token` keyword argument (and other options like `allowed_updates`, `max_connections`, `certificate`) which are simply passed as extra form fields in the same API call. For the sample app, calling `set_webhook` from the bot startup code is cleaner because it keeps the registration co-located with the bot's startup logic and can include the `secret_token` for validation.

---

### bot registration polling vs webhook

in sample bot
/home/pmn/repos/tg-central-hub-bot/scratch_space/tg_central_hub_bot_sample/tutorial_bot.py
who is "registering" the bot running in this box to telegram?

how does that sample tutorial differs from the webhook approach?

if we register the webhook, and do not run `app.run_polling()`,
will the bot still work and receive updates via the webhook?
do they receive the same set of updates (at different times),
or are there differences in behavior when using webhook vs polling?

will the webhook be triggered even if the bot process is not running,
or does it require the bot to be active to receive updates?

**Answer:**

**Who registers the polling bot?**

Nobody registers the tutorial bot with Telegram in any persistent way. `app.run_polling()` opens a long-lived loop that repeatedly calls `getUpdates` on the Telegram API (short-polling or long-polling). Telegram just sees ordinary API calls from the bot token - there is no "registration". When the script exits, updates simply queue up at Telegram's servers until the next `getUpdates` call. The bot token is the only identity - whoever holds it can call the API.

**Polling vs webhook differences:**

|                     | Polling (`run_polling`)                                        | Webhook                                                     |
| ------------------- | -------------------------------------------------------------- | ----------------------------------------------------------- |
| Direction           | Bot pulls Telegram                                             | Telegram pushes bot                                         |
| Registration        | None - just start calling `getUpdates`                         | One-time call to `setWebhook` with a public HTTPS URL       |
| Requires public URL | No - works behind CGNAT, firewall, locally                     | Yes - the URL must be reachable by Telegram's servers       |
| Updates received    | Same set of updates                                            | Same set of updates                                         |
| Timing              | Slight delay (poll interval, typically 0-1s)                   | Near-instant push                                           |
| Mutual exclusivity  | Yes - Telegram will refuse `getUpdates` while a webhook is set | Yes - must call `deleteWebhook` before switching to polling |

Both modes receive the same kinds of updates (messages, callbacks, etc.). Telegram does not differentiate what it delivers based on the mode - it is purely a delivery mechanism difference.

**Running webhook without `run_polling()`:**

Yes, the bot works without `run_polling()`. In webhook mode you run PTB using `app.run_webhook(...)` (or wire it into an existing ASGI app using `app.update_queue`). PTB provides a built-in webhook server via `Application.run_webhook()`, or you can integrate with FastAPI/Starlette by feeding raw update JSON into `app.update_queue.put()`. The key point: `run_polling()` and `run_webhook()` are alternate entry points. Use exactly one of them.

**Does the webhook fire when the bot process is not running?**

No. If the bot process is down, Telegram sends the POST to the webhook URL and gets a non-2xx response (connection refused, 502, etc.). Telegram will retry a fixed number of times with exponential backoff. If retries are exhausted, that update is dropped. Telegram does NOT queue updates indefinitely for a webhook - it queues them briefly while retrying, then discards them. This is the main operational difference: polling picks up queued updates whenever the bot restarts; a webhook that was down long enough will lose updates. For the sample app this is acceptable, but it is worth knowing.

## Final implementation recap

### Files created

| Path | Description |
|---|---|
| `src/tg_central_hub_bot/config/sample_app_config.py` | `SampleAppConfig(BaseModelKwargs)` - `db_path: Path`, `bot_api_key: SecretStr` |
| `src/tg_central_hub_bot/params/sample_app_params.py` | `SampleAppParams` - reads `BOT_API_KEY` / `SAMPLE_DB_PATH` from env; raises `MissingBotApiKeyError` |
| `src/tg_central_hub_bot/webapp/core/bot_auth.py` | `verify_bot_api_key` FastAPI dependency; constant-time `hmac.compare_digest` comparison |
| `src/tg_central_hub_bot/webapp/internal/__init__.py` | Internal package init |
| `src/tg_central_hub_bot/webapp/internal/entries_router.py` | `POST /internal/entries` - bot auth protected; 201 on success |
| `src/tg_central_hub_bot/webapp/backend_app.py` | `create_backend_app()` factory; `backend_app` entry point for uvicorn on `127.0.0.1:8001` |
| `src/tg_central_hub_bot/webapp/api/v1/entries_router.py` | `GET /api/v1/entries/` - OAuth protected; returns `list[EntryRead]` for HTMX |
| `src/tg_central_hub_bot/webapp/schemas/entry_schemas.py` | `EntryCreate`, `EntryRead` Pydantic models |
| `src/tg_central_hub_bot/webapp/services/entries_service.py` | `EntriesService` - async SQLite CRUD via `asyncio.to_thread`; parameterised statements |
| `templates/pages/entries.html` | Full page - HTMX polls `/pages/partials/entries-table` every 5 s |
| `templates/partials/entries_table.html` | Bulma table fragment swapped by HTMX |
| `scratch_space/feature_sample/sample_bot.py` | PTB bot - `/start`, `/add <text>`; calls backend via httpx with Bearer auth |
| `tests/config/test_sample_app_config.py` | Config model tests |
| `tests/params/test_sample_app_params.py` | Params loading, error, masking tests |
| `tests/webapp/test_bot_auth.py` | Bot auth dependency: valid key, wrong key, missing header, empty body |
| `tests/webapp/test_entries_service.py` | SQLite CRUD: create, list (newest first), empty DB |

### Files modified

| Path | Change |
|---|---|
| `src/tg_central_hub_bot/params/tg_central_hub_bot_params.py` | Added `os` import; wired `SampleAppParams` as optional `sample_app` attribute; added `get_sample_app_params()` accessor |
| `src/tg_central_hub_bot/webapp/api/v1/api_router.py` | Included `entries_router` under `/api/v1/entries` |
| `src/tg_central_hub_bot/webapp/main.py` | Added `SampleAppConfig` import and `EntriesService`; extended `create_app()` signature with `sample_app_config` kwarg; extended lifespan to init `EntriesService` when configured |
| `src/tg_central_hub_bot/webapp/app.py` | Reads `sample_app` from params singleton and passes config to `create_app()` |
| `src/tg_central_hub_bot/webapp/routers/pages_router.py` | Added `GET /entries` page route and `GET /pages/partials/entries-table` partial route |

### Key design decisions

- `SampleAppParams` is **optional** in the singleton - only instantiated when `BOT_API_KEY` is present. The rest of the app works unchanged without it.
- `EntriesService` uses `asyncio.to_thread` over stdlib `sqlite3` - no extra dependency, no blocking of the event loop.
- The backend app (`backend_app.py`) is a **separate process** bound to `127.0.0.1:8001`. It never appears in the Cloudflare tunnel ingress config.
- The frontend app reads entries via the same `EntriesService` instance; when `sample_app_config` is not supplied to `create_app()` the service is simply absent and the HTMX partial returns an empty table gracefully.

---

## Manual testing steps

### Prerequisites

1. Add to `~/cred/tg-central-hub-bot/.env`:
   ```
   BOT_API_KEY=<output of `python -c "import secrets; print(secrets.token_hex(32))"`>
   SAMPLE_DB_PATH=data/sample.db
   ```
2. Ensure `BOT_TOKEN`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` are also set.

### 1 - Unit tests (no external services needed)

```bash
BOT_TOKEN=fake uv run pytest tests/config/test_sample_app_config.py \
  tests/params/test_sample_app_params.py \
  tests/webapp/test_bot_auth.py \
  tests/webapp/test_entries_service.py -v
# Expected: all pass
```

### 2 - Start the backend service

```bash
source ~/cred/tg-central-hub-bot/.env
uv run uvicorn tg_central_hub_bot.webapp.backend_app:backend_app \
  --host 127.0.0.1 --port 8001
```

### 3 - Verify the bot auth endpoint directly

```bash
# Should create an entry (201)
curl -s -X POST http://127.0.0.1:8001/internal/entries \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BOT_API_KEY" \
  -d '{"text": "manual test entry"}' | python -m json.tool

# Should return 403
curl -s -o /dev/null -w "%{http_code}" \
  -X POST http://127.0.0.1:8001/internal/entries \
  -H "Authorization: Bearer wrongkey" \
  -d '{"text": "bad auth"}'
# Expected: 403

# Should return 401 (no auth header)
curl -s -o /dev/null -w "%{http_code}" \
  -X POST http://127.0.0.1:8001/internal/entries \
  -d '{"text": "no auth"}'
# Expected: 401
```

### 4 - Start the frontend webapp

```bash
source ~/cred/tg-central-hub-bot/.env
uv run uvicorn tg_central_hub_bot.webapp.app:app \
  --host 0.0.0.0 --port 8000
```

<!-- source ~/cred/tg-central-hub-bot/.env && uv run uvicorn tg_central_hub_bot.webapp.app:app --host 0.0.0.0 --port 8000 -->

### 5 - Visit the entries page in a browser

1. Navigate to `http://localhost:8000` and complete Google login.
2. Navigate to `http://localhost:8000/entries`.
3. The page loads and renders existing entries (or "No entries yet" if empty).
4. The table auto-refreshes every 5 seconds via HTMX.

### 6 - Run the sample bot and test end-to-end

```bash
source ~/cred/tg-central-hub-bot/.env
uv run python scratch_space/feature_sample/sample_bot.py
```

<!-- source ~/cred/tg-central-hub-bot/.env && uv run python scratch_space/feature_sample/sample_bot.py -->

In Telegram:
- Send `/start` - bot replies with welcome message.
- Send `/add hello from bot` - bot replies "Saved entry #N: hello from bot".
- Refresh `http://localhost:8000/entries` - the new entry appears (or wait 5 s for HTMX poll).

### 7 - Verify backend is not reachable from outside loopback

```bash
# From another machine on the same LAN (replace 192.168.x.x with box IP):
curl -s -o /dev/null -w "%{http_code}" \
  http://192.168.x.x:8001/internal/entries
# Expected: connection refused (port only bound to 127.0.0.1)
```

### 8 - Run full verification suite

```bash
BOT_TOKEN=fake uv run pytest && uv run ruff check . && uv run pyright
# New test failures: none
# Pre-existing failures (static assets not present): 8 in tests/webapp/test_pages.py
```

