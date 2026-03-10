# tg-central-hub-bot - Copilot Instructions

## Project overview

`tg-central-hub-bot` is a Telegram bot project with an optional FastAPI webapp. It uses `python-telegram-bot` (PTB v22+, ApplicationBuilder pattern) for the bot layer, an optional FastAPI webapp (Google OAuth, session management, CORS, rate limiting, Jinja2 templates, HTMX), a Singleton params system, and full dev tooling (uv, ruff, pyright, pytest, pre-commit, MkDocs). Python 3.14, managed with **uv**.

The package name is `tg_central_hub_bot`.

## Running & tooling

```bash
uv sync --all-extras --all-groups   # install all dependencies

uv run pytest                        # run tests
uv run ruff check .                  # lint (ruff, ALL rules enabled)
uv run ruff format .                 # format
uv run pyright                       # type-check (src/ and tests/ only)

uv run mkdocs serve                  # MkDocs local docs server

# webapp dev server
uvicorn tg_central_hub_bot.webapp.app:app --reload

# tutorial bot (scratch space)
uv run python scratch_space/tg_central_hub_bot_sample/tutorial_bot.py
```

Credentials live at `~/cred/tg-central-hub-bot/.env` (loaded by `load_env()` in `src/tg_central_hub_bot/params/load_env.py`).

## Key environment variables

| Variable                      | Required | Default        | Description                             |
| ----------------------------- | -------- | -------------- | --------------------------------------- |
| `BOT_TOKEN`                   | yes      | -              | Telegram bot token from BotFather       |
| `ENV_STAGE_TYPE`              | no       | `dev`          | `dev` or `prod`                         |
| `ENV_LOCATION_TYPE`           | no       | `local`        | `local` or `render`                     |
| `SESSION_SECRET_KEY`          | prod     | auto-gen       | 64-char hex secret for session signing  |
| `GOOGLE_CLIENT_ID`            | webapp   | -              | Google OAuth 2.0 client ID              |
| `GOOGLE_CLIENT_SECRET`        | webapp   | -              | Google OAuth 2.0 client secret          |
| `GOOGLE_REDIRECT_URI`         | no       | auto           | OAuth redirect URI                      |
| `CORS_ALLOWED_ORIGINS`        | no       | localhost      | Comma-separated list of allowed origins |
| `WEBAPP_HOST` / `WEBAPP_PORT` | no       | `0.0.0.0/8000` | Server bind settings                    |

## Architecture layers

| Layer       | Path                                                         | Role                                                                                                                 |
| ----------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| Params      | `src/tg_central_hub_bot/params/tg_central_hub_bot_params.py` | Singleton `TgCentralHubBotParams`; aggregates paths, sample, webapp, bot params                                      |
| Paths       | `src/tg_central_hub_bot/params/tg_central_hub_bot_paths.py`  | `TgCentralHubBotPaths`; env-aware filesystem references                                                              |
| Bot params  | `src/tg_central_hub_bot/params/bot_params.py`                | `BotParams` plain class; accepts `env_type: EnvType`, loads `BOT_TOKEN` from env, exposes `to_config() -> BotConfig` |
| Config      | `src/tg_central_hub_bot/config/`                             | Pydantic `BaseModelKwargs` models for typed settings (sample, webapp)                                                |
| Webapp      | `src/tg_central_hub_bot/webapp/`                             | FastAPI app factory, routers, services, schemas, middleware                                                          |
| Data models | `src/tg_central_hub_bot/data_models/basemodel_kwargs.py`     | `BaseModelKwargs` - Pydantic base with `to_kw()` kwargs flattening                                                   |
| Metaclasses | `src/tg_central_hub_bot/metaclasses/singleton.py`            | `Singleton` metaclass                                                                                                |
| Env type    | `src/tg_central_hub_bot/params/env_type.py`                  | `EnvType` dataclass wrapping `EnvStageType` and `EnvLocationType` enums                                              |
| Load env    | `src/tg_central_hub_bot/params/load_env.py`                  | `load_env()` loads `~/cred/tg-central-hub-bot/.env` via dotenv                                                       |

## Key patterns

**`TgCentralHubBotParams` singleton**  
Access project-wide config via `get_tg_central_hub_bot_params()`. It aggregates `TgCentralHubBotPaths`, `SampleParams`, `WebappParams`, and `BotParams`. Environment is controlled by `ENV_STAGE_TYPE` and `ENV_LOCATION_TYPE` env vars (read through `EnvType.from_env_var()`).

```python
from tg_central_hub_bot.params.tg_central_hub_bot_params import get_tg_central_hub_bot_params
from tg_central_hub_bot.params.tg_central_hub_bot_params import get_bot_params
from tg_central_hub_bot.params.tg_central_hub_bot_params import get_webapp_params

params = get_tg_central_hub_bot_params()
paths  = params.paths   # TgCentralHubBotPaths
bot    = params.bot     # BotParams  (token, parse_mode)
webapp = params.webapp  # WebappParams
# or access bot params directly
bot_params = get_bot_params()
webapp_params = get_webapp_params()
```

**`BotParams`**  
Owned by `TgCentralHubBotParams` (not a Singleton itself). Constructed with `BotParams(env_type=env_type)` which reads `BOT_TOKEN` from the environment. Use `get_bot_params()` as the main accessor. Raises `MissingBotTokenError` (not `ValueError`) if the token is absent. Token is stored as `SecretStr` internally and is fully masked in `__str__`. To obtain the raw token call `bot_params.to_config().token.get_secret_value()`. `to_config()` returns a `BotConfig(BaseModelKwargs)` instance from `src/tg_central_hub_bot/config/bot_config.py`.

```python
from tg_central_hub_bot.params.load_env import load_env
from tg_central_hub_bot.params.tg_central_hub_bot_params import get_bot_params

load_env()
bot_config = get_bot_params().to_config()  # BotConfig with SecretStr token
token = bot_config.token.get_secret_value()
app = ApplicationBuilder().token(token).build()
```

**`EnvType` dataclass**  
Wraps `EnvStageType` (`DEV`/`PROD`) and `EnvLocationType` (`LOCAL`/`RENDER`). Use `EnvType.from_env_var()` to build from env vars. `TgCentralHubBotParams.set_env_type()` accepts an explicit `EnvType` for tests.

**`BaseModelKwargs`**  
Extend `BaseModelKwargs` (not plain `BaseModel`) for any config that needs to be forwarded as `**kwargs` to a third-party constructor. `to_kw(exclude_none=True)` flattens a nested `kwargs` dict at the top level.

```python
class SampleConfig(BaseModelKwargs):
    some_int: int
    nested_model: NestedModel
    kwargs: dict = Field(default_factory=dict)

cfg = SampleConfig(some_int=1, nested_model=NestedModel(some_str="hi"), kwargs={"extra": True})
cfg.to_kw(exclude_none=True)  # {"some_int": 1, "nested_model": ..., "extra": True}
```

**Config / Params separation**

- `src/tg_central_hub_bot/config/` holds Pydantic `BaseModelKwargs` models that define the _shape_ of settings. Never read env vars inside config models.
- `src/tg_central_hub_bot/params/` holds plain classes that load _actual values_ (from env vars, `.env` file, etc.) and instantiate config models.
- Every `Params` class receives `env_type: EnvType` as its first constructor argument (following `TgCentralHubBotPaths` and `BotParams`). Do not call `EnvType.from_env_var()` inside a `Params` class; the caller passes it in.
- Raise a descriptive custom exception (e.g. `MissingBotTokenError`) rather than a bare `ValueError` or `RuntimeError`.
- Expose config objects through a `to_config()` method that returns the corresponding Pydantic model.

**FastAPI webapp factory**  
`create_app(config?)` in `src/tg_central_hub_bot/webapp/main.py` wires up middleware, routers, exception handlers, static files, and Jinja2 templates. Entry point for uvicorn: `tg_central_hub_bot.webapp.app:app`.

Webapp config objects (`CORSConfig`, `SessionConfig`, `RateLimitConfig`, `GoogleOAuthConfig`, `WebappConfig`) all extend `BaseModelKwargs` and live in `src/tg_central_hub_bot/config/webapp/`. In `dev` mode, self-hosted Swagger UI and ReDoc are mounted (no external CDN).

**Env-aware paths**  
`TgCentralHubBotPaths.load_config()` dispatches on `EnvLocationType` (`LOCAL` / `RENDER`) to set environment-specific paths. Common paths (`src_fol`, `root_fol`, `cache_fol`, `data_fol`, `static_fol`, `templates_fol`) are always set in `load_common_config_pre()`.

**`Singleton` metaclass**  
Use `metaclass=Singleton` for any class that must have exactly one instance per process (e.g., `TgCentralHubBotParams`). Reset in tests by clearing `Singleton._instances`.

## Telegram bot usage (PTB v22+)

The bot uses `python-telegram-bot` with the `ApplicationBuilder` pattern. See the tutorial sample at `scratch_space/tg_central_hub_bot_sample/tutorial_bot.py`.

```python
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from tg_central_hub_bot.params.load_env import load_env
from tg_central_hub_bot.params.tg_central_hub_bot_params import get_bot_params

load_env()
bot_params = get_bot_params()
token = bot_params.to_config().token.get_secret_value()
app = ApplicationBuilder().token(token).build()
app.add_handler(CommandHandler("start", start_handler))
app.run_polling()
```

## Style rules

- Never use em dashes (`--` or `---` or Unicode `—`). Use a hyphen `-` or rewrite the sentence.
- Use `loguru` (`from loguru import logger as lg`) for all logging.
- Raise descriptive custom exceptions (e.g., `UnknownEnvLocationError`, `UnknownEnvStageError`) rather than bare `ValueError`/`RuntimeError`.

## Testing & scratch space

- Tests live in `tests/` mirroring `src/tg_central_hub_bot/` structure.
- `scratch_space/` holds numbered exploratory notebooks and scripts. Not part of the package; ruff ignores `ERA001`/`F401`/`T20` there.

## Linting notes

- `ruff.toml` targets Python 3.13 with `select = ["ALL"]`. Key ignores: `COM812`, `D104`, `D203`, `D213`, `D413`, `FIX002`, `RET504`, `TD002`, `TD003`.
- Tests additionally allow `ARG001`, `INP001`, `PLR2004`, `S101`.
- Notebooks (`*.ipynb`) additionally allow `ERA001`, `F401`, `T20`.
- `meta/*` additionally allows `INP001`, `T20`.
- `max-args = 10` (pylint).

## End-of-task verification

After every code change, run the full verification suite before considering the task done:

```bash
uv run pytest && uv run ruff check . && uv run pyright
```
