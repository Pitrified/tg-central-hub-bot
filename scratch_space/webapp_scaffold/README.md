# Simple WebApp Scaffold

## Overview

This feature creates a production-ready FastAPI web application scaffold with Google OAuth authentication, following the project's established config/params patterns. The webapp will be deployable to Render with comprehensive security practices.

### Option A: Monolithic Webapp Module (Recommended)

- **What:** Create a self-contained `webapp/` directory under `src/tg_central_hub_bot/` containing all FastAPI components (routers, schemas, services, core, api).
- **Config Integration:** Add `WebappParams` to `TgCentralHubBotParams` singleton; config models in `src/tg_central_hub_bot/config/webapp/`.
- **Pros:** Clear separation, follows existing project patterns, easy to import and extend.
- **Cons:** Larger initial scope.

### Option B: Minimal Webapp Entry Point

- **What:** Single `webapp.py` file with minimal FastAPI setup; settings inline.
- **Pros:** Faster to implement, lower complexity.
- **Cons:** Does not scale; inconsistent with project config/params architecture.

### Option C: Separate Package

- **What:** Create `src/tg_central_hub_bot_webapp/` as a sibling package.
- **Pros:** Full isolation.
- **Cons:** Complicates imports, environment setup, and deployment; over-engineered for this use case.

**Selected Approach: Option A** — Monolithic Webapp Module integrated with the existing config/params pattern.

---

## Plan

### Phase 1: Configuration Layer

1. [ ] Create `src/tg_central_hub_bot/config/webapp/` directory
2. [ ] Create `src/tg_central_hub_bot/config/webapp/__init__.py`
3. [ ] Create `src/tg_central_hub_bot/config/webapp/webapp_config.py` with Pydantic models:
   - `CORSConfig(BaseModelKwargs)`: `allow_origins: list[str]`, `allow_methods: list[str]`, `allow_headers: list[str]`, `allow_credentials: bool`
   - `SessionConfig(BaseModelKwargs)`: `secret_key: str`, `session_cookie_name: str`, `max_age: int`, `same_site: Literal["lax", "strict", "none"]`, `https_only: bool`
   - `RateLimitConfig(BaseModelKwargs)`: `requests_per_minute: int`, `burst_size: int`
   - `GoogleOAuthConfig(BaseModelKwargs)`: `client_id: str`, `redirect_uri: str`, `scopes: list[str]`
   - `WebappConfig(BaseModelKwargs)`: `host: str`, `port: int`, `debug: bool`, `cors: CORSConfig`, `session: SessionConfig`, `rate_limit: RateLimitConfig`, `google_oauth: GoogleOAuthConfig`

4. [ ] Create `src/tg_central_hub_bot/params/webapp/` directory
5. [ ] Create `src/tg_central_hub_bot/params/webapp/__init__.py`
6. [ ] Create `src/tg_central_hub_bot/params/webapp/webapp_params.py`:
   - `WebappParams` class with environment-aware loading
   - Load values from environment variables with fallbacks
   - Support `ENV_STAGE_TYPE` (dev/prod) and `ENV_LOCATION_TYPE` (local/render) for config overrides
   - Method `to_config() -> WebappConfig`

7. [ ] Update `src/tg_central_hub_bot/params/tg_central_hub_bot_params.py`:
   - Add `self.webapp = WebappParams()` in `load_config()`
   - Add `get_webapp_params() -> WebappParams` helper function

### Phase 2: Webapp Core Infrastructure

8. [ ] Create `src/tg_central_hub_bot/webapp/` directory
9. [ ] Create `src/tg_central_hub_bot/webapp/__init__.py`
10. [ ] Create `src/tg_central_hub_bot/webapp/core/` directory with:
    - `__init__.py`
    - `security.py`: Security utilities
      - Password hashing utilities (for future local auth extension)
      - Token generation/validation helpers
      - CSRF token management
      - Input sanitization functions
    - `dependencies.py`: FastAPI dependency injection
      - `get_current_user` dependency
      - `get_db_session` dependency (placeholder for future DB integration)
      - `get_settings` dependency (returns `WebappConfig`)
      - `rate_limiter` dependency
    - `exceptions.py`: Custom HTTP exceptions
      - `NotAuthenticatedException`
      - `NotAuthorizedException`
      - `RateLimitExceededException`
      - `ValidationException`
    - `middleware.py`: Custom middleware
      - Request ID middleware (add unique ID to each request)
      - Security headers middleware (X-Content-Type-Options, X-Frame-Options, etc.)
      - Request logging middleware

### Phase 3: Authentication System

11. [ ] Create `src/tg_central_hub_bot/webapp/services/` directory with:
    - `__init__.py`
    - `auth_service.py`: Authentication service
      - `GoogleAuthService` class
        - Method: `get_google_auth_url() -> str`
        - Method: `verify_google_token(token: str) -> GoogleUserInfo`
        - Method: `create_session(user_info: GoogleUserInfo) -> SessionData`
        - Method: `validate_session(session_id: str) -> SessionData | None`
        - Method: `revoke_session(session_id: str) -> None`
      - Session storage abstraction (in-memory for MVP, extensible to Redis)
    - `user_service.py`: User management (placeholder)
      - `UserService` class
        - Method: `get_or_create_user(google_user_info: GoogleUserInfo) -> User`
        - Method: `get_user_by_id(user_id: str) -> User | None`

12. [ ] Create `src/tg_central_hub_bot/webapp/schemas/` directory with:
    - `__init__.py`
    - `auth_schemas.py`: Pydantic schemas for auth
      - `GoogleUserInfo(BaseModel)`: `email: str`, `name: str`, `picture: str | None`, `sub: str`
      - `SessionData(BaseModel)`: `session_id: str`, `user_id: str`, `email: str`, `created_at: datetime`, `expires_at: datetime`
      - `LoginResponse(BaseModel)`: `access_token: str`, `token_type: str`, `expires_in: int`
      - `UserResponse(BaseModel)`: `id: str`, `email: str`, `name: str`, `picture: str | None`
    - `common_schemas.py`: Shared schemas
      - `HealthResponse(BaseModel)`: `status: str`, `version: str`, `timestamp: datetime`
      - `ErrorResponse(BaseModel)`: `detail: str`, `error_code: str | None`, `request_id: str | None`

### Phase 4: API Routers

13. [ ] Create `src/tg_central_hub_bot/webapp/routers/` directory with:
    - `__init__.py`
    - `auth_router.py`: Authentication endpoints
      - `GET /auth/google/login`: Redirect to Google OAuth consent screen
      - `GET /auth/google/callback`: Handle OAuth callback, create session, set cookie
      - `POST /auth/logout`: Invalidate session, clear cookie
      - `GET /auth/me`: Get current authenticated user info
    - `health_router.py`: Health check endpoints
      - `GET /health`: Basic health check
      - `GET /health/ready`: Readiness probe (check dependencies)
      - `GET /health/live`: Liveness probe

14. [ ] Create `src/tg_central_hub_bot/webapp/api/` directory with:
    - `__init__.py`
    - `v1/` subdirectory for versioned API
      - `__init__.py`
      - `api_router.py`: Main API router aggregating all v1 routes
    - Protected route example demonstrating auth requirement

### Phase 5: Application Entry Point

15. [ ] Create `src/tg_central_hub_bot/webapp/main.py`: FastAPI application factory
    - `create_app() -> FastAPI` function
    - Configure CORS middleware using `WebappConfig`
    - Configure session middleware (using `starlette-session` or `itsdangerous`)
    - Register exception handlers
    - Include all routers with appropriate prefixes
    - Add OpenAPI metadata (title, description, version, contact)
    - Lifespan context manager for startup/shutdown events

16. [ ] Create `src/tg_central_hub_bot/webapp/app.py`: Application instance
    - Instantiate `app = create_app()`
    - Entry point for uvicorn: `uvicorn tg_central_hub_bot.webapp.app:app`

### Phase 6: Render Deployment Configuration

17. [ ] Create `render.yaml` in project root:
    - Service type: `web`
    - Environment: `python`
    - Build command: `pip install .` or `uv pip install .`
    - Start command: `uvicorn tg_central_hub_bot.webapp.app:app --host 0.0.0.0 --port $PORT`
    - Environment variables section with placeholders for secrets
    - Health check path: `/health`

18. [ ] Update `pyproject.toml`:
    - Add webapp dependencies to `[project.dependencies]`:
      - `fastapi>=0.109.0`
      - `uvicorn[standard]>=0.27.0`
      - `python-multipart>=0.0.6` (for form data)
      - `itsdangerous>=2.1.0` (for session signing)
      - `httpx>=0.26.0` (for Google OAuth HTTP calls)
      - `slowapi>=0.1.9` (for rate limiting)
    - Add optional webapp extras: `[project.optional-dependencies] webapp = [...]`

### Phase 7: Environment Variables & Documentation

19. [ ] Update environment variable loading in `src/tg_central_hub_bot/__init__.py`:
    - Ensure webapp-related env vars are loaded from credential path

20. [ ] Document required environment variables:
    - `GOOGLE_CLIENT_ID`: Google OAuth 2.0 client ID
    - `GOOGLE_CLIENT_SECRET`: Google OAuth 2.0 client secret (if using server-side flow)
    - `SESSION_SECRET_KEY`: Secret key for session signing (generate with `secrets.token_hex(32)`)
    - `WEBAPP_HOST`: Host to bind (default: `0.0.0.0`)
    - `WEBAPP_PORT`: Port to bind (default: `8000`)
    - `ENV_STAGE_TYPE`: `dev` or `prod`
    - `ENV_LOCATION_TYPE`: `local` or `render`
      Also create a `.env.example` file with placeholders for these variables and clear instructions.

21. [ ] Create `docs/guides/webapp_setup.md`:
    - Google Cloud Console setup instructions (create OAuth credentials)
    - Local development setup
    - Environment variable configuration
    - Running locally with uvicorn
    - Deploying to Render

### Phase 8: Security Implementation Details

22. [ ] Implement security headers in middleware:
    - `X-Content-Type-Options: nosniff`
    - `X-Frame-Options: DENY`
    - `X-XSS-Protection: 1; mode=block`
    - `Strict-Transport-Security: max-age=31536000; includeSubDomains` (prod only)
    - `Content-Security-Policy`: restrictive policy
    - `Referrer-Policy: strict-origin-when-cross-origin`

23. [ ] Input validation strategy:
    - Use Pydantic models for all request bodies
    - Use `Query`, `Path`, `Body` with validation constraints
    - HTML entity encoding for any user-provided content rendered in responses
    - SQL parameterization (when DB is added)

24. [ ] CSRF protection:
    - Use `SameSite=Lax` or `SameSite=Strict` for session cookies
    - For non-GET state-changing operations, validate `Origin`/`Referer` headers
    - Consider double-submit cookie pattern for API endpoints

25. [ ] Rate limiting configuration:
    - Global rate limit: 100 requests/minute per IP
    - Auth endpoints: 10 requests/minute per IP (stricter)
    - Use `slowapi` with Redis backend in production (in-memory for dev)

### Phase 9: Testing Infrastructure

26. [ ] Create `tests/webapp/` directory structure:
    - `__init__.py`
    - `conftest.py`: Shared fixtures
      - `test_client` fixture using `TestClient`
      - `mock_google_oauth` fixture
      - `authenticated_client` fixture (with valid session)
    - `test_health.py`: Health endpoint tests
    - `test_auth.py`: Authentication flow tests
    - `test_security.py`: Security header and CSRF tests
    - `test_rate_limit.py`: Rate limiting tests

27. [ ] Create `tests/config/webapp/` directory:
    - `test_webapp_config.py`: Config model validation tests
    - `test_webapp_params.py`: Params loading tests with env var mocking

---

## File Structure Summary

```
src/tg_central_hub_bot/
├── config/
│   └── webapp/
│       ├── __init__.py
│       └── webapp_config.py          # Pydantic config models
├── params/
│   ├── tg_central_hub_bot_params.py        # Updated: add webapp attribute
│   └── webapp/
│       ├── __init__.py
│       └── webapp_params.py          # Environment-aware params
└── webapp/
    ├── __init__.py
    ├── main.py                       # create_app() factory
    ├── app.py                        # Application instance
    ├── core/
    │   ├── __init__.py
    │   ├── security.py
    │   ├── dependencies.py
    │   ├── exceptions.py
    │   └── middleware.py
    ├── services/
    │   ├── __init__.py
    │   ├── auth_service.py
    │   └── user_service.py
    ├── schemas/
    │   ├── __init__.py
    │   ├── auth_schemas.py
    │   └── common_schemas.py
    ├── routers/
    │   ├── __init__.py
    │   ├── auth_router.py
    │   └── health_router.py
    └── api/
        ├── __init__.py
        └── v1/
            ├── __init__.py
            └── api_router.py

tests/
├── config/
│   └── webapp/
│       ├── test_webapp_config.py
│       └── test_webapp_params.py
└── webapp/
    ├── __init__.py
    ├── conftest.py
    ├── test_health.py
    ├── test_auth.py
    ├── test_security.py
    └── test_rate_limit.py

docs/
└── guides/
    └── webapp_setup.md               # Setup and deployment guide

render.yaml                           # Render deployment blueprint
```

---

## Dependencies to Add

| Package             | Version     | Purpose                     |
| ------------------- | ----------- | --------------------------- |
| `fastapi`           | `>=0.109.0` | Web framework               |
| `uvicorn[standard]` | `>=0.27.0`  | ASGI server                 |
| `python-multipart`  | `>=0.0.6`   | Form data parsing           |
| `itsdangerous`      | `>=2.1.0`   | Secure session signing      |
| `httpx`             | `>=0.26.0`  | Async HTTP client for OAuth |
| `slowapi`           | `>=0.1.9`   | Rate limiting               |

---

## Environment Variables Reference

| Variable               | Required | Default                     | Description                            |
| ---------------------- | -------- | --------------------------- | -------------------------------------- |
| `GOOGLE_CLIENT_ID`     | Yes      | —                           | Google OAuth 2.0 client ID             |
| `SESSION_SECRET_KEY`   | Yes      | —                           | 64-char hex string for session signing |
| `WEBAPP_HOST`          | No       | `0.0.0.0`                   | Server bind host                       |
| `WEBAPP_PORT`          | No       | `8000`                      | Server bind port                       |
| `WEBAPP_DEBUG`         | No       | `false`                     | Enable debug mode                      |
| `ENV_STAGE_TYPE`       | No       | `dev`                       | `dev` or `prod`                        |
| `ENV_LOCATION_TYPE`    | No       | `local`                     | `local` or `render`                    |
| `CORS_ALLOWED_ORIGINS` | No       | `["http://localhost:3000"]` | Comma-separated origins                |

---

## Security Checklist

- [ ] All user input validated via Pydantic models
- [ ] Session cookies: `HttpOnly`, `Secure` (prod), `SameSite=Lax`
- [ ] Security headers applied via middleware
- [ ] Rate limiting on all endpoints
- [ ] Stricter rate limiting on auth endpoints
- [ ] CORS properly configured (no wildcards in prod)
- [ ] Secrets loaded from environment, never hardcoded
- [ ] Google OAuth state parameter to prevent CSRF
- [ ] Session expiration enforced
- [ ] Logging sanitizes sensitive data (no passwords/tokens in logs)

---

## Render Deployment Notes

- Use `render.yaml` for Infrastructure as Code
- Set environment variables in Render dashboard (secrets)
- Configure custom domain with automatic HTTPS
- Health check endpoint: `GET /health`
- Auto-deploy on push to `main` branch
- Start command: `uvicorn tg_central_hub_bot.webapp.app:app --host 0.0.0.0 --port $PORT`
