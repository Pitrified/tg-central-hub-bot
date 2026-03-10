# CSP hardening analysis (production-grade)

## Current CSP status

Current policy (from latest middleware):

```text
default-src 'self';
script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js;
style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css;
img-src 'self' data: https://fastapi.tiangolo.com/img/favicon.png;
font-src 'self';
connect-src 'self' https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css.map;
frame-ancestors 'none';
base-uri 'self';
form-action 'self';
object-src 'none';
worker-src 'self';
manifest-src 'self'
```

## Is this safe for production?

### Short answer

**Moderately safe, but not high-assurance.**

### What is good

- `default-src 'self'` baseline is strong.
- `frame-ancestors 'none'` prevents clickjacking.
- `base-uri 'self'` and `form-action 'self'` reduce common injection abuse paths.
- `object-src 'none'`, `worker-src 'self'`, and `manifest-src 'self'` are good hardening additions.
- Third-party domains are explicitly scoped (not wildcarded).

### Main production concerns

1. **`'unsafe-inline'` in `script-src`**
   - Biggest risk. Inline script execution is allowed globally.
   - Any HTML/script injection bug becomes much easier to exploit.

2. **`'unsafe-inline'` in `style-src`**
   - Lower risk than scripts, but still expands injection surface.
   - Can assist UI redressing/phishing style attacks.

3. **CSP applied uniformly to all routes**
   - Swagger/ReDoc needs are leaking into API/runtime pages.
   - Production app pages should be stricter than docs pages.

4. **Overly specific URL-source usage may be brittle**
   - Current policy pins full CDN asset URLs (including path/version).
   - This is tight, but can break docs on upstream asset/version changes.

5. **`connect-src` points to a source-map URL**
   - `connect-src` controls XHR/fetch/WebSocket targets, not stylesheet loading.
   - `...swagger-ui.css.map` is usually unnecessary in production.

6. **`font-src 'self'` may be too strict for CDN-served docs assets**
   - If docs CSS references CDN fonts, they will be blocked.
   - Validate browser network panel before keeping this strict value.

---

## Recommended hardening options

## Option A (recommended practical baseline)

**Keep docs enabled in prod, but split CSP by route.**

- Strict CSP for app/API routes.
- Slightly relaxed CSP only for `/docs` and `/redoc`.

### App/API CSP (strict)

```text
default-src 'self';
script-src 'self';
style-src 'self';
img-src 'self' data:;
font-src 'self';
connect-src 'self';
object-src 'none';
frame-ancestors 'none';
base-uri 'self';
form-action 'self';
worker-src 'self';
upgrade-insecure-requests
```

### Docs CSP (controlled exceptions)

```text
default-src 'self';
script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
img-src 'self' data: https://fastapi.tiangolo.com;
font-src 'self' https://cdn.jsdelivr.net;
connect-src 'self';
object-src 'none';
frame-ancestors 'none';
base-uri 'self';
form-action 'self'
```

Why this is better:

- Risk from `'unsafe-inline'` is isolated to docs pages.
- Runtime app pages get much stronger guarantees.

---

## Option B (stronger)

**Self-host Swagger/ReDoc assets and remove CDN entirely.**

- Bundle JS/CSS locally (or pin by hash-integrity and cache internally).
- Use:
  - `script-src 'self'`
  - `style-src 'self'` (or minimal nonce/hash exceptions)

Benefits:

- Eliminates third-party supply chain dependency at runtime.
- Smaller outbound trust surface.

Tradeoff:

- More maintenance when FastAPI/Swagger assets update.

---

## Option C (highest assurance)

**Disable interactive docs in production.**

- Serve OpenAPI JSON only (or internal-only docs behind VPN/auth).
- Use strict CSP globally with no inline allowances.

Best for:

- Compliance-heavy or internet-exposed high-risk systems.

---

## Additional production hardening (independent of option)

1. Add:
   - `object-src 'none'`
   - `worker-src 'self'`
   - `manifest-src 'self'`
2. Consider `report-uri` / `report-to` for CSP violation telemetry.
3. Add `Content-Security-Policy-Report-Only` during rollout before enforcement changes.
4. Keep HSTS enabled in prod (`max-age>=31536000`; include subdomains only if all subdomains are HTTPS-ready).
5. Periodically test policy with browser devtools + automated security scans.

---

## Final verdict

Current CSP is **acceptable for early production**, but **not optimal** due to global `'unsafe-inline'` usage for scripts/styles.

If this service is externally exposed, the best near-term move is:

- **Option A now** (route-specific CSP), then
- **Option B later** (self-host docs assets), or
- **Option C** for highly sensitive environments.

DECISION: option b+c, no need to allow external assets for docs in production. We can self-host the docs assets and remove the `'unsafe-inline'` allowances, which will significantly reduce the attack surface while still providing interactive documentation for internal use.
