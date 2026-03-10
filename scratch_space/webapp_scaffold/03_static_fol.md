# static folder location

static folder is here
/home/pmn/repos/tg-central-hub-bot/static

not inside src: that folder is for python only

use src/tg_central_hub_bot/params/tg_central_hub_bot_params.py and src/tg_central_hub_bot/params/tg_central_hub_bot_paths.py
to safely access the static folder location without hardcoding paths in the codebase (aside from the paths.py file itself, which is the single source of truth for static asset paths root folder)

update
- webapp code to use the paths from tg_central_hub_bot_paths.py instead of hardcoded paths to static assets
- CSP to allow loading from the static folder (swagger is locally served, so we can allow it in the CSP without opening up to external sources, update fastapi docs config to load local swagger)
- any other places in the codebase that reference static assets (e.g. templates) to use the paths from tg_central_hub_bot_paths.py (move templates as well to outside of src)
