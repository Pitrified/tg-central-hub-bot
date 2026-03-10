# Plan: Bot Params, Config & Sample Script Update

## Goal

Wire the existing `TgCentralHubBotParams` / `TgCentralHubBotPaths` Singleton pattern
into a new `BotParams` layer that holds the Telegram token and runtime config,
and update the tutorial sample script to load its token from that system
instead of a hardcoded string.

All handler logic in the sample script is left untouched for now.

---

## 1. Files to Create

### `src/tg_central_hub_bot/params/bot_params.py`

A new `BotParams` dataclass (not a Singleton — it is owned by `TgCentralHubBotParams`)
that holds every Telegram-specific runtime value read from environment variables.

```python
"""Telegram bot runtime parameters."""

import os
from dataclasses import dataclass

from tg_central_hub_bot.params.env_type import EnvStageType


@dataclass
class BotParams:
    """Telegram bot runtime parameters."""

    token: str
    parse_mode: str = "HTML"

    @classmethod
    def from_env(cls) -> "BotParams":
        """Load bot params from environment variables.

        Raises:
            ValueError: If BOT_TOKEN is not set.
        """
        token = os.getenv("BOT_TOKEN")
        if not token:
            msg = "BOT_TOKEN environment variable is not set"
            raise ValueError(msg)
        return cls(token=token)

    def __str__(self) -> str:
        """Return the string representation (token is masked)."""
        masked = f"{self.token[:6]}...{self.token[-4:]}"
        return f"BotParams: token={masked}, parse_mode={self.parse_mode}"

    def __repr__(self) -> str:
        """Return the string representation of the object."""
        return str(self)
```

---

### `src/tg_central_hub_bot/params/bot_params.py` — env var reference

| Variable    | Required | Default | Description          |
| ----------- | -------- | ------- | -------------------- |
| `BOT_TOKEN` | yes      | —       | Token from BotFather |

---

## 2. Files to Modify

### `src/tg_central_hub_bot/params/tg_central_hub_bot_params.py`

Add `BotParams` as a field loaded in `load_config()`, and expose a getter.

**Changes:**

```python
# add import
from tg_central_hub_bot.params.bot_params import BotParams

# in load_config():
self.bot = BotParams.from_env()

# add __str__ line:
s += f"\n{self.bot}"

# add getter at module level:
def get_bot_params() -> BotParams:
    """Get the bot params."""
    return get_tg_central_hub_bot_params().bot
```

---

### `src/tg_central_hub_bot/params/load_env.py`

No changes needed. Already loads from `~/cred/tg-central-hub-bot/.env`.
`BOT_TOKEN` should be placed in that file locally:

```
# ~/cred/tg-central-hub-bot/.env
BOT_TOKEN=1234567890:ABCdef...
```

On Render, set `BOT_TOKEN` as an environment variable in the dashboard.

---

### `scratch_space/tg_central_hub_bot_sample/tutorial_bot.py` _(new file)_

A copy of the
[tutorial script](https://gitlab.com/Athamaxy/telegram-bot-tutorial/-/blob/main/TutorialBot.py)
with only the `main()` function updated to load the token via `TgCentralHubBotParams`.
All handler logic is preserved verbatim.
See Section 3 below.

---

## 3. Updated Sample Script

The sample script lives in `scratch_space/` — it is a prototype, not production
code. The only change from the original tutorial is in `main()`:

- `load_env()` is called first to populate env vars from `~/cred/`
- use the getter `get_bot_params()` to load the token instead of a hardcoded string
- `bot_params.token` replaces the hardcoded `"<YOUR_BOT_TOKEN_HERE>"`
- `loguru` replaces the stdlib `logging` call
- The PTB `Updater`/`dispatcher` API is updated to v20 style (using `ApplicationBuilder` and async handlers) but the handler logic is unchanged.

See `scratch_space/tg_central_hub_bot_sample/tutorial_bot.py`.

---

## 4. Files to Create for Tests

### `tests/params/test_bot_params.py`

```python
"""Tests for BotParams."""

import os
import pytest
from tg_central_hub_bot.params.bot_params import BotParams


def test_bot_params_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """BotParams loads token from environment."""
    monkeypatch.setenv("BOT_TOKEN", "test-token-123")
    params = BotParams.from_env()
    assert params.token == "test-token-123"


def test_bot_params_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """BotParams raises ValueError if BOT_TOKEN is missing."""
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    with pytest.raises(ValueError, match="BOT_TOKEN"):
        BotParams.from_env()


def test_bot_params_str_masks_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Token is masked in string representation."""
    monkeypatch.setenv("BOT_TOKEN", "123456:ABCDEFxyz")
    params = BotParams.from_env()
    s = str(params)
    assert "123456" in s
    assert "ABCDEFxyz" not in s  # full token not exposed
```

---

## 5. Credential File Setup (one-time, local)

```bash
mkdir -p ~/cred/tg-central-hub-bot
echo "BOT_TOKEN=<your_token_here>" > ~/cred/tg-central-hub-bot/.env
chmod 600 ~/cred/tg-central-hub-bot/.env
```

This file is never in the repo. It is loaded by `load_env()` at startup.

---

## 6. Summary of Touches

| File                                          | Action                               |
| --------------------------------------------- | ------------------------------------ |
| `src/.../params/bot_params.py`                | **Create**                           |
| `src/.../params/tg_central_hub_bot_params.py` | **Modify** — add `self.bot`, getter  |
| `scratch_space/.../tutorial_bot.py`           | **Create** — updated sample          |
| `tests/params/test_bot_params.py`             | **Create**                           |
| `~/cred/tg-central-hub-bot/.env`              | **Create locally** (never committed) |

No changes to paths, env_type, singleton, or any handler logic.
