# UI Base – Login/Logout, Dashboard & Docs Links

## Overview

The webapp scaffold currently serves only JSON API endpoints. There is no HTML front-end: no login page, no dashboard, and no way for an end-user to interact with the app via a browser beyond Swagger UI (dev only). This feature adds a minimal, server-rendered UI layer.

### Constraints & Security Posture

- The existing CSP is strict: `script-src 'self' 'unsafe-inline' …` only for the CDN-hosted Swagger assets. Any UI approach **must not weaken** this policy.
- Session cookies are already `HttpOnly`, `Secure` (prod), `SameSite=Lax`. The UI must rely on these cookies — no client-side token storage.
- CSRF protection via `SameSite` cookie + OAuth state parameter is in place. State-changing UI forms (logout) must use `POST` with the session cookie — never `GET`.
- All user-provided content displayed in HTML must be escaped (existing `sanitize_html` in `security.py`).
- No client-side JavaScript frameworks that would require loosening CSP. Minimal/zero custom JS.

### Existing Architecture (Relevant)

| Component    | Location                         | Notes                                                          |
| ------------ | -------------------------------- | -------------------------------------------------------------- |
| App factory  | `webapp/main.py`                 | `create_app()` with lifespan                                   |
| Middleware   | `webapp/core/middleware.py`      | CSP, security headers, request ID, logging                     |
| Auth router  | `webapp/routers/auth_router.py`  | Google OAuth login/callback/logout/me/status                   |
| Dependencies | `webapp/core/dependencies.py`    | `get_current_session`, `get_current_user`, `get_optional_user` |
| Schemas      | `webapp/schemas/auth_schemas.py` | `SessionData`, `UserResponse`                                  |
| Config       | `config/webapp/webapp_config.py` | `WebappConfig` with debug flag                                 |
| CSP          | `middleware.py`                  | Uniform policy, `'unsafe-inline'` for Swagger CDN              |

---

### Option A: Jinja2 Server-Side Templates (Recommended)

Use FastAPI's built-in Jinja2 template support (`Jinja2Templates` + `StaticFiles`). All HTML rendered server-side; zero or near-zero client-side JavaScript.

**Pros:**

- No CSP weakening needed — all HTML is server-rendered, no inline scripts required for the UI itself.
- `Jinja2` is a mature, auto-escaping template engine (XSS protection by default).
- FastAPI has first-class support (`starlette.templating.Jinja2Templates`).
- Lightweight: no build step, no bundler, no Node.js toolchain.
- Static CSS (plain or classless framework like Pico CSS / Simple.css) can be self-hosted → no CDN dependency for the UI.
- Responsive design achievable with pure CSS (media queries or a small classless framework).
- Accessibility (ARIA landmarks, semantic HTML, keyboard nav) fully controlled in templates.
- Flash messages / error feedback handled via query params or session-stored flash data.

**Cons:**

- More files to maintain (templates, static assets, a new page router).
- No rich client-side interactivity (acceptable for login/dashboard).
- Template rendering adds minor per-request overhead vs pure JSON.

**Security Impact:** Neutral-to-positive. Jinja2 auto-escaping prevents XSS. No new CSP exceptions needed for the app pages. CSP can be tightened for non-docs routes (Option A from CSP analysis) simultaneously.

---

### Option B: HTMX + Jinja2 Templates

Server-rendered Jinja2 templates enhanced with HTMX for dynamic partial updates (e.g., checking auth status, toast notifications) without full page reloads.

**Pros:**

- All benefits of Option A, plus smooth UX transitions (partial DOM swaps).
- HTMX is a single `<script>` tag (~14 KB gzipped), self-hostable.
- No build step, no custom JS to write for common interactions.
- Still server-side rendering — no CSP `'unsafe-eval'` needed.

**Cons:**

- Adds HTMX as a dependency (JS library, even if self-hosted).
- Requires `script-src 'self'` which we already have, but adds a JS execution surface.
- HTMX attributes (`hx-get`, `hx-post`, etc.) may be unfamiliar to contributors.
- Over-engineering for a login + dashboard page.
- HTMX triggers HTTP requests implicitly — needs careful CSRF consideration on `hx-post`/`hx-delete` endpoints.

**Security Impact:** Slightly negative. HTMX injects and executes HTML fragments from server responses. An attacker who achieves response injection could leverage HTMX to execute further requests. Must ensure HTMX response endpoints are equally protected.

---

### Option C: SPA (React/Vue/Svelte) with Separate Build

Build a client-side Single-Page Application served as static files, communicating with the existing JSON API.

**Pros:**

- Rich, responsive UI with full client-side interactivity.
- Separation of concerns (front-end team vs back-end team).

**Cons:**

- **CSP must be significantly loosened**: `'unsafe-eval'` for many frameworks, or complex nonce/hash setup.
- Requires a Node.js build toolchain (npm/yarn/pnpm), adding operational complexity.
- Increases attack surface: client-side token/session handling, XSS in client-rendered content.
- Over-engineered for login + dashboard + docs links.
- Contradicts the project's Python-only, lightweight philosophy.
- CORS configuration becomes more complex if served from a different origin.

**Security Impact:** Negative. SPAs inherently require looser CSP and move security-sensitive logic (routing, auth state) to the client. Not recommended for this use case.

---

### Decision

**Option B (HTMX + Jinja2 Templates)** selected.

**Rationale:** This is a template project intended to showcase good patterns for future apps that will grow. HTMX demonstrates the hypermedia-driven pattern — a modern, well-regarded approach to building interactive web apps in FastAPI without an SPA toolchain. It pairs naturally with server-side rendering and keeps everything in Python.

---

## CSS Framework Selection: Bulma

| Framework       | Size (min+gzip)       | JS Required    | Classes      | Dark Mode              | License |
| --------------- | --------------------- | -------------- | ------------ | ---------------------- | ------- |
| **Bulma 1.0.x** | ~28 KB                | ❌ No          | ✅ Rich      | ✅ Built-in (CSS vars) | MIT     |
| Bootstrap 5     | ~23 KB CSS + 16 KB JS | ⚠️ Optional JS | ✅ Rich      | ✅                     | MIT     |
| Tailwind        | ~30+ KB (purged)      | ❌             | Utility-only | Via config             | MIT     |
| Pico CSS        | ~10 KB                | ❌             | ❌ Classless | ✅                     | MIT     |

**Bulma** is the choice:

- **CSS-only** — zero JavaScript, so it adds no execution surface and needs no additional CSP exceptions beyond `style-src`.
- **Class-based** — rich component vocabulary (`navbar`, `card`, `message`, `notification`, `hero`, `columns`, `button`, `tag`, etc.) that templates good UI patterns.
- **Modern** — Flexbox + CSS Grid + CSS Variables, built-in dark mode via `prefers-color-scheme`.
- **Well-maintained** — 50k+ GitHub stars, active releases (1.0.4, Apr 2025).
- **No bloat** — single CSS file, no JS runtime, no build step.
- **Self-hostable** — download `bulma.min.css` into the static directory → no CDN dependency for app pages.

### CSP Impact

Self-hosting Bulma means app/UI pages need **no CDN allowances** at all:

```text
# App/UI pages (strict — no CDN, no unsafe-inline for styles)
style-src 'self';
script-src 'self';   # for self-hosted htmx.min.js only
```

The existing `'unsafe-inline'` and jsdelivr CDN exceptions remain **only** for `/docs`/`/redoc` (Swagger UI). This achieves the CSP route-splitting recommended in `01_csp_hardening.md` Option A.

### HTMX Security Hardening

HTMX will be configured with these security settings via `<meta>` tag in the base template:

```html
<meta
  name="htmx-config"
  content='{
  "selfRequestsOnly": true,
  "allowScriptTags": false,
  "allowEval": false,
  "historyCacheSize": 0
}'
/>
```

- `selfRequestsOnly: true` — (default) prevents HTMX from making requests to external domains.
- `allowScriptTags: false` — HTMX will not execute `<script>` tags found in swapped content.
- `allowEval: false` — disables all `eval()`-based features (trigger filters, `js:` prefixed `hx-vals`/`hx-headers`).
- `historyCacheSize: 0` — prevents sensitive page content from being stored in `localStorage`.

Additionally, all user-provided content rendered in templates will use Jinja2 auto-escaping (default) and the existing `sanitize_html()` utility. The `hx-disable` attribute will be placed around any raw/user content blocks.

---

## Plan

### Phase 1: Dependencies & Static Assets

1. [ ] Add `jinja2>=3.1.0` to `[project.optional-dependencies] webapp` in `pyproject.toml`
2. [ ] Run `uv sync --all-extras --all-groups`
3. [ ] Create static assets directory structure:
   ```
   src/tg_central_hub_bot/webapp/
   ├── static/
   │   ├── css/
   │   │   ├── bulma.min.css        # Self-hosted Bulma 1.0.x (~195 KB uncompressed)
   │   │   └── app.css              # Custom overrides & HTMX indicator styles
   │   ├── js/
   │   │   └── htmx.min.js          # Self-hosted HTMX 2.0.x (~17 KB gzipped)
   │   └── img/
   │       └── logo.svg             # Placeholder app logo (or favicon)
   └── templates/
       ├── base.html                # Master layout
       ├── pages/
       │   ├── landing.html         # Public landing / login page
       │   ├── dashboard.html       # Authenticated dashboard
       │   └── error.html           # Generic error page (404, 500, etc.)
       └── partials/
           ├── navbar.html          # Top navigation bar (shared)
           ├── flash.html           # Flash message / notification component
           ├── footer.html          # Page footer
           └── user_card.html       # User info card (HTMX-swappable partial)
   ```
4. [ ] Download `bulma.min.css` (v1.0.4) from GitHub releases into `static/css/`
5. [ ] Download `htmx.min.js` (v2.0.8) from jsdelivr/npm into `static/js/`
6. [ ] Create `static/css/app.css` with:
   - HTMX indicator styles (`.htmx-indicator { opacity: 0; } .htmx-request .htmx-indicator { opacity: 1; }`)
   - Loading state transitions
   - Skip-nav link styles
   - Any Bulma CSS variable overrides for branding

### Phase 2: Template Engine Setup

7. [ ] Register `StaticFiles` mount in `create_app()` (`main.py`):

   ```python
   from starlette.staticfiles import StaticFiles
   app.mount("/static", StaticFiles(directory="path/to/static"), name="static")
   ```

   - Use `pathlib.Path(__file__).parent / "static"` for the directory path
   - Mount **before** including routers (so `/static/...` is resolved first)

8. [ ] Create `Jinja2Templates` instance (in a new `webapp/core/templating.py` or in the page router):

   ```python
   from starlette.templating import Jinja2Templates
   templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))
   ```

   - Ensure `autoescape=True` (Jinja2 default when extension is `.html`)
   - Add template globals: `app_name`, `app_version`, `debug` (from config)

9. [ ] Create `templates/base.html` — master layout:
   - `<!DOCTYPE html>` + `<html lang="en">`
   - `<head>`:
     - `<meta charset="utf-8">`
     - `<meta name="viewport" content="width=device-width, initial-scale=1">`
     - `<meta name="htmx-config" content='{ "selfRequestsOnly": true, "allowScriptTags": false, "allowEval": false, "historyCacheSize": 0 }'>`
     - `<link rel="stylesheet" href="/static/css/bulma.min.css">`
     - `<link rel="stylesheet" href="/static/css/app.css">`
     - `<title>{% block title %}{{ app_name }}{% endblock %}</title>`
   - `<body>`:
     - Skip-nav link: `<a href="#main-content" class="skip-link">Skip to main content</a>`
     - `{% include "partials/navbar.html" %}`
     - `{% include "partials/flash.html" %}`
     - `<main id="main-content" role="main">{% block content %}{% endblock %}</main>`
     - `{% include "partials/footer.html" %}`
     - `<script src="/static/js/htmx.min.js"></script>` (at end of body)
   - Blocks: `title`, `head_extra`, `content`, `scripts_extra`

### Phase 3: Page Router & Routes

10. [ ] Create `src/tg_central_hub_bot/webapp/routers/pages_router.py`:
    - `router = APIRouter(tags=["pages"])`
    - Depends on `get_optional_user` (not `get_current_user`) for unauthenticated pages

11. [ ] Implement page routes:

    **`GET /`** — Landing page
    - If authenticated → redirect to `/dashboard` (302)
    - If not authenticated → render `pages/landing.html` with login button
    - Query param `?error=...` → display error flash message (OAuth errors)

    **`GET /dashboard`** — Dashboard (requires auth)
    - Depends on `get_current_user` (raises 401 → redirect to `/` if not authenticated)
    - Render `pages/dashboard.html` with:
      - User info card (name, email, picture)
      - Links: API docs (`/docs` if debug), API v1 root (`/api/v1/`)
      - Logout button (HTMX `hx-post="/auth/logout"` or standard form POST)
    - Showcase HTMX pattern: user card loaded via `hx-get="/pages/partials/user-card"` with `hx-trigger="load"` to demonstrate partial loading

    **`GET /pages/partials/user-card`** — HTMX partial endpoint
    - Returns only the `partials/user_card.html` fragment (no base layout)
    - Demonstrates the HTMX partial-swap pattern for future developers
    - Protected: requires `get_current_user`

    **`GET /error/{status_code}`** — Error page (optional)
    - Renders `pages/error.html` with status code and message
    - Used by exception handlers that detect HTML-accepting requests

12. [ ] Register `pages_router` in `main.py`:
    ```python
    app.include_router(pages_router)
    ```

### Phase 4: Template Implementation

13. [ ] `partials/navbar.html`:
    - Bulma `navbar` component with:
      - Brand/logo on the left
      - If authenticated: user name/avatar + "Dashboard" link + "Logout" button
      - If not authenticated: "Login with Google" button
      - Responsive burger menu (`navbar-burger`) — Bulma's only interactive element; implement toggle with a minimal inline `onclick` on the burger (or an HTMX approach)
    - Burger menu toggle approach: use a tiny `<script>` block in base.html OR use CSS-only approach with `:target` or checkbox hack to avoid any inline JS entirely
    - ARIA: `role="navigation"`, `aria-label="main navigation"`, `aria-expanded` on burger

14. [ ] `partials/flash.html`:
    - Conditionally rendered Bulma `notification` component
    - Supports `success`, `error`, `warning`, `info` types
    - Dismissible via Bulma's `delete` button (CSS-only or HTMX `hx-on:click="this.parentElement.remove()"`)
    - Flash data passed via template context (from query params or a flash middleware)
    - Accessible: `role="alert"` and `aria-live="polite"`

15. [ ] `partials/footer.html`:
    - Bulma `footer` component
    - App name, version, links

16. [ ] `partials/user_card.html`:
    - Bulma `card` component with user avatar (img), name, email
    - Demonstrates a self-contained HTMX-swappable partial

17. [ ] `pages/landing.html`:
    - Extends `base.html`
    - Bulma `hero` section with app name, tagline
    - "Login with Google" button → links to `/auth/google/login`
    - Flash area for OAuth error display (e.g., `?error=auth_failed`)

18. [ ] `pages/dashboard.html`:
    - Extends `base.html`
    - Bulma `columns` layout:
      - Left column: user card (loaded via HTMX partial or inline)
      - Right column: quick links (API docs, health status)
    - "Logout" form: `<form method="post" action="/auth/logout">` with CSRF considerations
    - HTMX demo: health status widget using `hx-get="/health" hx-trigger="load" hx-target="#health-status"` — shows a live health indicator swapped into a `<span>`

19. [ ] `pages/error.html`:
    - Extends `base.html`
    - Bulma `hero is-danger` or `is-warning` with error code + message
    - Link back to home

### Phase 6: Auth Flow Integration

22. [ ] Modify `auth_router.py` callback to redirect to `/dashboard` on success:
    - Change `redirect_url = "/"` → `redirect_url = "/dashboard"`

23. [ ] Modify `auth_router.py` logout to redirect to `/` (landing):
    - After revoking session + clearing cookie, return `RedirectResponse(url="/", status_code=302)` for browser requests
    - Detect browser vs API: check `Accept` header or `HX-Request` header
    - For HTMX requests (`HX-Request: true`): return `HX-Redirect: /` header so HTMX does a client-side redirect

24. [ ] Handle authentication failures gracefully in the UI:
    - OAuth errors redirect to `/?error=<error_code>`
    - `NotAuthenticatedException` handler: if request accepts HTML, redirect to `/` instead of returning JSON 401
    - Detect HTML requests: check `Accept: text/html` header OR absence of `HX-Request` header

25. [ ] Flash message mechanism:
    - Simple approach: pass error messages via query parameters (`?error=auth_failed&message=...`)
    - Landing page template reads `error` query param and maps to user-friendly message
    - Map known error codes: `auth_failed` → "Authentication failed. Please try again.", `invalid_state` → "Session expired. Please try again."

### Phase 7: CSRF Protection for Forms

26. [ ] For the logout form (the main state-changing UI action):
    - Existing protection: `SameSite=Lax` cookies prevent cross-site POST (browser won't send cookie on cross-origin POST)
    - Additional layer: validate `Origin` or `Referer` header matches the app domain on POST endpoints
    - HTMX automatically sends `HX-Request: true` header — can be validated server-side
    - Consider adding CSRF token via `TokenManager` (already in `security.py`):
      - Generate token in template context, embed as hidden `<input>` in forms
      - Validate on POST endpoints
      - Or use HTMX `hx-headers` to send the token with every request

27. [ ] HTMX CSRF integration (if using token approach):

    ```html
    <body hx-headers='{"X-CSRF-Token": "{{ csrf_token }}"}'></body>
    ```

    - This sends the CSRF token with every HTMX request automatically
    - Validate the token in a middleware or dependency

### Phase 8: Accessibility

28. [ ] Semantic HTML in all templates:
    - `<header>` for navbar, `<main>` for content, `<footer>` for footer
    - `<nav>` with `aria-label` for navigation regions
    - `<section>` with headings for content areas
    - `<form>` with `<label>` elements properly associated via `for` attribute

29. [ ] Skip navigation link:
    - First focusable element in `<body>`: `<a href="#main-content" class="skip-link">Skip to main content</a>`
    - Visible only on `:focus` (CSS: `position: absolute; left: -9999px;` → `left: 0` on focus)

30. [ ] Keyboard navigation:
    - All interactive elements (buttons, links, form controls) are natively focusable
    - Visible focus indicators (Bulma provides these; verify contrast in `app.css`)
    - Tab order follows visual order (no `tabindex` hacks)
    - Burger menu toggle accessible via keyboard

31. [ ] ARIA enhancements:
    - `role="alert"` + `aria-live="polite"` on flash messages
    - `aria-expanded="true|false"` on burger menu toggle
    - `aria-current="page"` on active nav link
    - `aria-label` on icon-only buttons

32. [ ] HTMX accessibility:
    - Use `aria-busy="true"` on swap targets during requests (HTMX does not do this automatically)
    - Consider `htmx:afterSwap` event to move focus to swapped content for screen readers
    - Ensure swapped partials maintain valid HTML structure

### Phase 9: Responsive Design

33. [ ] Viewport meta tag (in `base.html`):

    ```html
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    ```

34. [ ] Bulma's built-in responsive features:
    - `columns` class with responsive modifiers (`is-mobile`, `is-desktop`)
    - `is-hidden-mobile`, `is-hidden-tablet` helpers for responsive visibility
    - `navbar-burger` for mobile navigation collapse

35. [ ] Touch targets:
    - Minimum 44×44px for all interactive elements (Bulma buttons meet this by default)
    - Adequate spacing between tap targets in mobile view

36. [ ] `app.css` responsive overrides:
    - Ensure card layout stacks vertically on mobile
    - Dashboard columns collapse to single column below tablet breakpoint
    - Flash messages are full-width on mobile

### Phase 10: Tests

37. [ ] Create `tests/webapp/test_pages.py`:
    - **Landing page tests:**
      - `GET /` returns 200 with HTML content type
      - `GET /` contains "Login with Google" link
      - `GET /?error=auth_failed` displays error flash message
      - `GET /` when authenticated → redirects to `/dashboard`
    - **Dashboard tests:**
      - `GET /dashboard` when authenticated → 200 with user info
      - `GET /dashboard` when not authenticated → redirects to `/`
      - Dashboard contains logout form/button
      - Dashboard contains user name/email
    - **Partial tests:**
      - `GET /pages/partials/user-card` when authenticated → returns partial HTML (no `<html>` tag)
      - `GET /pages/partials/user-card` when not authenticated → 401
    - **Error page tests:**
      - Error page renders with status code and message

38. [ ] Update `tests/webapp/test_security.py`:
    - **CSP route-splitting tests:**
      - `GET /` → CSP does NOT contain `'unsafe-inline'`
      - `GET /` → CSP does NOT contain `cdn.jsdelivr.net`
      - `GET /` → CSP contains `script-src 'self'` (no inline)
      - `GET /docs` (if debug) → CSP contains `'unsafe-inline'` and CDN domains
      - `GET /api/v1/` → CSP is strict (no inline, no CDN)
    - **HTMX-specific tests:**
      - Verify `htmx.min.js` is served from `/static/js/htmx.min.js`
      - Verify `bulma.min.css` is served from `/static/css/bulma.min.css`

39. [ ] Update `tests/webapp/test_auth.py`:
    - Test that successful OAuth callback redirects to `/dashboard` (not `/`)
    - Test that logout from browser redirects to `/`
    - Test that HTMX logout returns `HX-Redirect` header

### Phase 11: Documentation

40. [ ] Update `docs/guides/webapp_setup.md`:
    - Add section on UI layer: templates, static assets, Bulma, HTMX
    - Document the HTMX security configuration
    - Document the CSP route-splitting approach
    - Add instructions for customizing Bulma (CSS variable overrides in `app.css`)
    - Add instructions for adding new pages (create template, add route, extend base)
    - Document the flash message pattern

41. [ ] Update the main webapp scaffold `README.md` with a note about the UI layer

---

## File Structure Summary (New/Modified)

```
src/tg_central_hub_bot/webapp/
├── static/                          # NEW: self-hosted assets
│   ├── css/
│   │   ├── bulma.min.css            # Bulma 1.0.x (self-hosted)
│   │   └── app.css                  # Custom styles, HTMX indicators
│   ├── js/
│   │   └── htmx.min.js             # HTMX 2.0.x (self-hosted)
│   └── img/
│       └── logo.svg                 # Placeholder logo
├── templates/                       # NEW: Jinja2 templates
│   ├── base.html                    # Master layout
│   ├── pages/
│   │   ├── landing.html             # Public landing/login
│   │   ├── dashboard.html           # Authenticated dashboard
│   │   └── error.html               # Error display
│   └── partials/
│       ├── navbar.html              # Navigation bar
│       ├── flash.html               # Flash messages
│       ├── footer.html              # Page footer
│       └── user_card.html           # HTMX-swappable user info
├── core/
│   ├── middleware.py                 # MODIFIED: CSP route-splitting
│   └── templating.py                # NEW: Jinja2Templates setup
├── routers/
│   ├── auth_router.py               # MODIFIED: redirect targets
│   └── pages_router.py              # NEW: HTML page routes
└── main.py                          # MODIFIED: mount static, register pages router

tests/webapp/
├── test_pages.py                    # NEW: page rendering & auth redirect tests
├── test_security.py                 # MODIFIED: CSP route-split assertions
└── test_auth.py                     # MODIFIED: redirect target assertions
```

## Dependencies Summary

| Package         | Add To                                   | Purpose         |
| --------------- | ---------------------------------------- | --------------- |
| `jinja2>=3.1.0` | `[project.optional-dependencies] webapp` | Template engine |

Self-hosted assets (not pip packages):

- `bulma.min.css` v1.0.4 — CSS framework
- `htmx.min.js` v2.0.8 — Hypermedia library

## Security Checklist for This Feature

- [ ] Bulma CSS self-hosted (no CDN for app pages)
- [ ] HTMX JS self-hosted (no CDN for app pages)
- [ ] CSP route-split: strict for app, relaxed only for Swagger docs
- [ ] No `'unsafe-inline'` in app page CSP
- [ ] HTMX config: `selfRequestsOnly`, `allowScriptTags=false`, `allowEval=false`
- [ ] HTMX `historyCacheSize=0` (no sensitive data in localStorage)
- [ ] Jinja2 auto-escaping enabled (default for `.html`)
- [ ] `hx-disable` on any user-content blocks
- [ ] CSRF: `SameSite=Lax` + `Origin`/`Referer` validation on POST
- [ ] Flash messages use escaped content only (no raw HTML)
- [ ] All query param values sanitized before template rendering
- [ ] Logout is POST-only (never GET)
- [ ] Static files served with correct MIME types and caching headers
