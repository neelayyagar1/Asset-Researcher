"""Finnhub client, price, market cap, price history, news, and peers.

The only non-EDGAR data dependency (ARCHITECTURE.md §8). Market cap is not
cosmetic: Altman Z needs it, and without it that score correctly declines
rather than substituting zero.

SECURITY: Finnhub authenticates via a `token` URL query parameter, not a
header. That means the credential can leak through any path that records a
URL, exception messages, tracebacks, logs, or a cache key derived from the
URL. Every such path in this module routes through _redact(). Cache keys are
built from the symbol and endpoint name, never from the request URL.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from datetime import date, timedelta

import requests

from asset_researcher.config import Settings, require_secret
from asset_researcher.sources._cache import DiskCache

_QUOTE_TTL_SECONDS = 15 * 60
_PROFILE_TTL_SECONDS = 24 * 3600
_NEWS_TTL_SECONDS = 6 * 3600
_PEERS_TTL_SECONDS = 7 * 24 * 3600


class FinnhubError(RuntimeError):
    """Never carries a raw URL, see _redact()."""


@dataclass(frozen=True)
class Quote:
    symbol: str
    price: float
    as_of: str


@dataclass(frozen=True)
class CompanyProfile:
    symbol: str
    name: str
    market_cap: float | None  # absolute USD, converted from Finnhub's millions
    shares_outstanding: float | None
    industry: str | None
    exchange: str | None


@dataclass(frozen=True)
class NewsItem:
    headline: str
    summary: str
    url: str
    source: str
    published: str  # ISO date


class _RateLimiter:
    def __init__(self, per_second: float) -> None:
        self._min_interval = 1.0 / per_second
        self._lock = threading.Lock()
        self._last = 0.0

    def wait(self) -> None:
        with self._lock:
            remaining = self._min_interval - (time.monotonic() - self._last)
            if remaining > 0:
                time.sleep(remaining)
            self._last = time.monotonic()


class FinnhubClient:
    def __init__(self, settings: Settings) -> None:
        self._token = require_secret(settings.finnhub_api_key, "FINNHUB_API_KEY")
        self._base = settings.finnhub.base_url
        self._limiter = _RateLimiter(settings.finnhub.rate_limit_per_sec)
        self._cache = DiskCache(
            settings.resolved_cache_dir(settings.finnhub.cache_dir)
        )

    def _redact(self, text: str) -> str:
        """Strips the API token from any string before it can reach an
        exception message, log, or console. The token appears in request URLs
        because Finnhub authenticates by query parameter."""
        return text.replace(self._token, "***REDACTED***")

    def _get(self, path: str, params: dict, cache_key: str, ttl: float):
        cached = self._cache.get(cache_key, ttl)
        if cached is not None:
            return json.loads(cached)

        self._limiter.wait()
        try:
            resp = requests.get(
                f"{self._base}{path}",
                params={**params, "token": self._token},
                timeout=20,
            )
        except requests.RequestException as e:
            raise FinnhubError(f"Finnhub {path} request failed: {self._redact(str(e))}") from None

        if resp.status_code == 401:
            raise FinnhubError("Finnhub rejected the API key (401). Check FINNHUB_API_KEY.")
        if resp.status_code == 429:
            raise FinnhubError("Finnhub rate limit hit (429). Free tier allows 60 calls/min.")
        if not resp.ok:
            raise FinnhubError(
                f"Finnhub {path} returned {resp.status_code}: "
                f"{self._redact(resp.text[:200])}"
            )

        # A 200 with a non-JSON body must not escape as a raw JSONDecodeError:
        # that exception is raised by the json library, bypassing _redact(),
        # and requests can include the request URL, which carries the token.
        # in some error paths. Convert it into a redacted FinnhubError.
        try:
            parsed = resp.json()
        except ValueError as e:
            raise FinnhubError(
                f"Finnhub {path} returned a non-JSON response "
                f"({resp.status_code}): {self._redact(str(e))}"
            ) from None

        self._cache.put(cache_key, resp.content)
        return parsed

    def get_quote(self, symbol: str) -> Quote | None:
        data = self._get("/quote", {"symbol": symbol}, f"quote-{symbol}", _QUOTE_TTL_SECONDS)
        price = data.get("c")
        if not price:  # Finnhub returns c=0 for unknown symbols rather than 404
            return None
        ts = data.get("t")
        as_of = date.fromtimestamp(ts).isoformat() if ts else date.today().isoformat()
        return Quote(symbol=symbol, price=float(price), as_of=as_of)

    def get_profile(self, symbol: str) -> CompanyProfile | None:
        data = self._get(
            "/stock/profile2", {"symbol": symbol}, f"profile-{symbol}", _PROFILE_TTL_SECONDS
        )
        if not data or not data.get("ticker"):
            return None
        # Finnhub reports marketCapitalization in MILLIONS. Multiplying to
        # absolute USD here means every downstream consumer (Altman Z, comps
        # table) works in one consistent unit and can't be off by 1e6.
        raw_cap = data.get("marketCapitalization")
        market_cap = float(raw_cap) * 1e6 if raw_cap else None
        raw_shares = data.get("shareOutstanding")
        shares = float(raw_shares) * 1e6 if raw_shares else None
        return CompanyProfile(
            symbol=symbol,
            name=data.get("name", ""),
            market_cap=market_cap,
            shares_outstanding=shares,
            industry=data.get("finnhubIndustry"),
            exchange=data.get("exchange"),
        )

    def get_peers(self, symbol: str) -> list[str]:
        """Finnhub's curated peer list. Verified available on the free tier.
        Excludes the symbol itself. Peer *quality* is generic (SIC-adjacent),
        so a hand-curated override may be preferable for a given name."""
        data = self._get(
            "/stock/peers", {"symbol": symbol}, f"peers-{symbol}", _PEERS_TTL_SECONDS
        )
        if not isinstance(data, list):
            return []
        return [p for p in data if p and p.upper() != symbol.upper()]

    def get_news(self, symbol: str, days: int = 45, limit: int = 15) -> list[NewsItem]:
        to_date = date.today()
        from_date = to_date - timedelta(days=days)
        data = self._get(
            "/company-news",
            {"symbol": symbol, "from": from_date.isoformat(), "to": to_date.isoformat()},
            f"news-{symbol}-{from_date.isoformat()}",
            _NEWS_TTL_SECONDS,
        )
        if not isinstance(data, list):
            return []
        items = []
        for entry in data[:limit]:
            ts = entry.get("datetime")
            items.append(
                NewsItem(
                    headline=entry.get("headline", ""),
                    summary=entry.get("summary", ""),
                    url=entry.get("url", ""),
                    source=entry.get("source", ""),
                    published=date.fromtimestamp(ts).isoformat() if ts else "",
                )
            )
        return items
