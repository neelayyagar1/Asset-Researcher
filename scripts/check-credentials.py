"""Check all three credentials before a demo, without spending real money.

A report costs about a dollar and takes a minute, so discovering a dead key
part-way through one is the expensive way to find out. This makes the
cheapest possible call against each provider and reports pass or fail.

    python scripts/check-credentials.py

Never prints a key. A prefix and a length are enough to tell two keys apart
when one of them is stale, and anything more ends up in a terminal
scrollback that gets pasted somewhere.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import dotenv_values  # noqa: E402

OK, BAD = "  PASS", "  FAIL"


def _shape(value: str | None) -> str:
    """Enough to tell two keys apart, and no more.

    This printed the first fourteen characters. For an Anthropic key that
    is mostly a fixed prefix, but a Finnhub key is about twenty characters
    of undifferentiated entropy, so fourteen of them went to stdout and
    into terminal scrollback, which contradicts this module's own promise
    never to print a key. The last four identify a key to someone who
    already holds it and are no use to anyone who does not.
    """
    if not value:
        return "not set"
    return f"ending {value[-4:]} ({len(value)} chars)"


def check_anthropic(key: str | None) -> bool:
    print(f"\nAnthropic   {_shape(key)}")
    if not key:
        print(f"{BAD}  ANTHROPIC_API_KEY is missing from .env")
        return False
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=key)
        client.messages.create(
            model="claude-opus-5",
            max_tokens=1,
            messages=[{"role": "user", "content": "."}],
        )
    except Exception as exc:
        name = type(exc).__name__
        if "Authentication" in name:
            print(f"{BAD}  The key was rejected. It has been revoked or "
                  f"rotated, or it belongs to a different organisation.")
        elif "Credit" in name or "credit" in str(exc):
            print(f"{BAD}  The key is valid but the organisation has no "
                  f"credit balance.")
        else:
            print(f"{BAD}  {name}: {str(exc)[:120]}")
        return False
    print(f"{OK}  Key accepted and the organisation has credit.")
    return True


def check_finnhub(key: str | None) -> bool:
    print(f"\nFinnhub     {_shape(key)}")
    if not key:
        print(f"{BAD}  FINNHUB_API_KEY is missing from .env")
        return False
    import requests

    try:
        response = requests.get(
            "https://finnhub.io/api/v1/quote",
            params={"symbol": "AAPL", "token": key},
            timeout=10,
        )
    except requests.RequestException as exc:
        print(f"{BAD}  Could not reach Finnhub: {type(exc).__name__}")
        return False
    if response.status_code == 401:
        print(f"{BAD}  The key was rejected.")
        return False
    if response.status_code == 429:
        print(f"{BAD}  Rate limited. The key works; wait a minute.")
        return False
    if response.status_code != 200 or not response.json().get("c"):
        print(f"{BAD}  HTTP {response.status_code}, no quote returned.")
        return False
    print(f"{OK}  Quote returned (AAPL ${response.json()['c']:,.2f}).")
    return True


def check_edgar(user_agent: str | None) -> bool:
    print(f"\nSEC EDGAR   {user_agent or 'not set'}")
    if not user_agent:
        print(f"{BAD}  EDGAR_USER_AGENT is missing from .env")
        return False
    try:
        from asset_researcher.config.loader import _require_edgar_user_agent

        _require_edgar_user_agent(user_agent)
    except RuntimeError as exc:
        print(f"{BAD}  {exc}")
        return False

    import requests

    try:
        response = requests.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers={"User-Agent": user_agent},
            timeout=15,
        )
    except requests.RequestException as exc:
        print(f"{BAD}  Could not reach EDGAR: {type(exc).__name__}")
        return False
    if response.status_code == 403:
        print(f"{BAD}  EDGAR refused the request. The contact is rejected "
              f"or this address is blocked.")
        return False
    if response.status_code != 200:
        print(f"{BAD}  HTTP {response.status_code}.")
        return False
    print(f"{OK}  Accepted ({len(response.json()):,} tickers indexed).")
    return True


def main() -> int:
    env = dotenv_values(ROOT / ".env")
    if not env:
        print("No .env found. Copy .env.example to .env and fill it in.")
        return 1

    results = [
        check_anthropic(env.get("ANTHROPIC_API_KEY")),
        check_finnhub(env.get("FINNHUB_API_KEY")),
        check_edgar(env.get("EDGAR_USER_AGENT")),
    ]

    print()
    if all(results):
        print("All three credentials work. A live report will run.")
        return 0
    print(f"{sum(results)} of 3 working. Fix the above before a live run.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
