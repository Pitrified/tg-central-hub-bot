"""URL utility functions for reverse-proxy-aware request handling."""

from fastapi import Request


def get_public_base_url(request: Request, override: str | None = None) -> str:
    """Determine the public base URL of the application.

    Works correctly behind reverse proxies such as Cloudflare Tunnel that
    forward ``X-Forwarded-Proto`` and ``X-Forwarded-Host`` headers.

    Resolution order:
    1. ``override`` - explicit value (e.g. ``PUBLIC_BASE_URL`` env var).
    2. ``X-Forwarded-Proto`` + ``X-Forwarded-Host`` headers (set by the proxy).
    3. Scheme and netloc from the raw request URL (local / direct access).

    Args:
        request: Incoming FastAPI request.
        override: Optional explicit base URL (e.g. ``https://yourdomain.com``).
            If provided, all header inspection is skipped.

    Returns:
        Base URL string without trailing slash, e.g. ``https://yourdomain.com``.
    """
    if override:
        return override.rstrip("/")

    forwarded_proto = request.headers.get("x-forwarded-proto")
    forwarded_host = request.headers.get("x-forwarded-host")

    if forwarded_proto and forwarded_host:
        return f"{forwarded_proto}://{forwarded_host}"

    return f"{request.url.scheme}://{request.url.netloc}"
