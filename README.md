# Tg central hub bot

## Installation

### Setup `uv`

To install the package:

Setup [`uv`](https://docs.astral.sh/uv/getting-started/installation/).

### Install the package

Run the following command:

```bash
uv sync --all-extras --all-groups
```

## Setup

### Environment Variables

To setup the package, create a `.env` file in `~/cred/tg_central_hub_bot/.env` with the following content:

```bash
TG_CENTRAL_HUB_BOT_SAMPLE_ENV_VAR=sample
```

And for VSCode to recognize the environment file, add the following line to the
workspace [settings file](.vscode/settings.json):

```json
"python.envFile": "/home/pmn/cred/tg_central_hub_bot/.env"
```

Note that the path to the `.env` file should be absolute.

### Pre-commit

To install the pre-commit hooks, run the following command:

```bash
pre-commit install
```

Run against all the files:

```bash
pre-commit run --all-files
```

### Linting

Use pyright for type checking:

```bash
uv run pyright
```

Use ruff for linting:

```bash
uv run ruff check --fix
uv run ruff format
```

### Testing

To run the tests, use the following command:

```bash
uv run pytest
```

or use the VSCode interface.

## IDEAs

- [x] too
- [ ] many
