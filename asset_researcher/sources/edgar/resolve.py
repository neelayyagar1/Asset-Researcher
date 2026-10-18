"""Ticker -> CIK resolution.

SEC publishes a flat ticker->CIK map at a fixed URL (verified during design.
no auth needed beyond the standard User-Agent). We cache it for a day; it's
updated by SEC roughly daily as new tickers list, but doesn't need to be fresh
to the minute for this use case.
"""

from __future__ import annotations

from asset_researcher.sources.edgar.client import EdgarClient, EdgarError

_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_TICKERS_CACHE_KEY = "company_tickers"
_TICKERS_TTL_SECONDS = 24 * 3600


class TickerNotFoundError(EdgarError):
    pass


def cik_to_padded(cik: int) -> str:
    """EDGAR's data.sec.gov endpoints want a 10-digit zero-padded CIK with
    a CIK prefix, e.g. CIK0000320193, this formatting bites people who copy
    the raw integer straight from company_tickers.json."""
    return f"CIK{cik:010d}"


def resolve_ticker(client: EdgarClient, ticker: str) -> tuple[int, str]:
    """Returns (cik, company_name) for a ticker, case-insensitive.

    Raises TickerNotFoundError with a message meant to be shown to the user
    directly, a stranger typing a bad ticker should see a clear explanation,
    not a stack trace (ARCHITECTURE.md §8, hosting robustness)."""
    data = client.get_json(_TICKERS_URL, _TICKERS_CACHE_KEY, _TICKERS_TTL_SECONDS)
    ticker_upper = ticker.strip().upper()
    for entry in data.values():
        if entry["ticker"].upper() == ticker_upper:
            return entry["cik_str"], entry["title"]
    raise TickerNotFoundError(
        f"'{ticker}' is not a ticker SEC EDGAR recognizes. Check the spelling, "
        f"or note that some foreign issuers and very new listings may not be "
        f"in this list yet."
    )
