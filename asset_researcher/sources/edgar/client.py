"""Low-level EDGAR HTTP client.

Everything specific to talking to SEC EDGAR lives here: the mandatory
User-Agent (a request without one gets a hard 403, verified during design,
not assumed), rate limiting, and disk caching. Higher-level modules
(resolve.py, filings.py, facts.py) never issue requests directly.
"""

from __future__ import annotations

import json
import threading
import time

import requests

from asset_researcher.config import Settings
from asset_researcher.sources._cache import DiskCache


class EdgarError(RuntimeError):
    """Raised on any EDGAR request failure, with enough context to debug.
    but never including the User-Agent value, which just carries a contact
    email and doesn't need to be echoed into logs."""


class _RateLimiter:
    """Simple sleep-based limiter shared across all EdgarClient instances in
    this process. SEC's documented ceiling is ~10 req/sec; settings.yaml
    defaults to 8 to leave headroom rather than ride the exact limit."""

    def __init__(self, per_second: float) -> None:
        self._min_interval = 1.0 / per_second
        self._lock = threading.Lock()
        self._last_call = 0.0

    def wait(self) -> None:
        with self._lock:
            elapsed = time.monotonic() - self._last_call
            remaining = self._min_interval - elapsed
            if remaining > 0:
                time.sleep(remaining)
            self._last_call = time.monotonic()


class EdgarClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._headers = {
            "User-Agent": settings.edgar_user_agent,
            "Accept-Encoding": "gzip, deflate",
        }
        self._limiter = _RateLimiter(settings.edgar.rate_limit_per_sec)
        self._cache = DiskCache(settings.resolved_cache_dir(settings.edgar.cache_dir))

    def _get(self, url: str) -> bytes:
        self._limiter.wait()
        try:
            resp = requests.get(url, headers=self._headers, timeout=30)
        except requests.RequestException as e:
            raise EdgarError(f"Request to {url} failed: {e}") from e
        if resp.status_code == 403:
            raise EdgarError(
                f"403 from {url}. EDGAR rejects requests without a compliant "
                f"User-Agent. Check EDGAR_USER_AGENT in .env."
            )
        if resp.status_code == 404:
            raise EdgarError(f"404 from {url}, not found on EDGAR.")
        if not resp.ok:
            raise EdgarError(f"{resp.status_code} from {url}: {resp.text[:300]}")
        return resp.content

    def get_json(self, url: str, cache_key: str, ttl_seconds: float | None) -> dict:
        cached = self._cache.get(cache_key, ttl_seconds)
        if cached is not None:
            return json.loads(cached)
        data = self._get(url)
        self._cache.put(cache_key, data)
        return json.loads(data)

    def get_text(self, url: str, cache_key: str, ttl_seconds: float | None) -> str:
        """ttl_seconds=None caches forever, appropriate for a specific filing
        document, which is immutable once accepted by EDGAR."""
        cached = self._cache.get(cache_key, ttl_seconds)
        if cached is not None:
            return cached.decode("utf-8", errors="replace")
        data = self._get(url)
        self._cache.put(cache_key, data)
        return data.decode("utf-8", errors="replace")
