"""Finnhub client. Two things matter most here and both are tested offline:
the millions->absolute unit conversion (an error would silently make market
cap 1e6x wrong, feeding a wrong Altman Z), and token redaction (Finnhub
authenticates by URL query parameter, so the credential can leak through any
path that records a URL)."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from asset_researcher.config import get_settings
from asset_researcher.sources._cache import DiskCache
from asset_researcher.sources.finnhub import FinnhubClient, FinnhubError


@pytest.fixture
def client(tmp_path: Path) -> FinnhubClient:
    """Cache is redirected to a temp dir per test. Without this, entries
    written by earlier live calls satisfy the request before the mock is
    ever consulted, the test then asserts against real cached data and
    silently stops testing what it claims to."""
    c = FinnhubClient(get_settings())
    c._token = "SECRET-TOKEN-VALUE"  # noqa: S105 - deliberate test sentinel
    c._cache = DiskCache(tmp_path)
    return c


def _response(status=200, json_data=None, text="", ok=True):
    r = Mock()
    r.status_code = status
    r.ok = ok
    r.text = text
    r.content = b"{}"
    if json_data is None:
        r.json.side_effect = ValueError("Expecting value: line 1 column 1 (char 0)")
    else:
        r.json.return_value = json_data
    return r


def test_market_cap_converted_from_millions_to_absolute(client):
    """Finnhub reports marketCapitalization in MILLIONS. Apple at ~$4.5T
    arrives as 4559367.68, if this conversion is dropped, Altman Z's
    market-cap term is off by a factor of a million."""
    with patch(
        "asset_researcher.sources.finnhub.requests.get",
        return_value=_response(
            json_data={
                "ticker": "AAPL",
                "name": "Apple Inc",
                "marketCapitalization": 4559367.676,
                "shareOutstanding": 14694.0,
                "finnhubIndustry": "Technology",
            }
        ),
    ):
        p = client.get_profile("AAPL")
    assert p.market_cap == pytest.approx(4.559367676e12)
    assert p.shares_outstanding == pytest.approx(1.4694e10)


def test_unknown_symbol_returns_none_not_zero_price(client):
    """Finnhub returns c=0 for an unknown symbol rather than a 404. Treating
    that as a real $0 price would corrupt every downstream multiple."""
    with patch(
        "asset_researcher.sources.finnhub.requests.get",
        return_value=_response(json_data={"c": 0, "t": None}),
    ):
        assert client.get_quote("ZZZZZZ") is None


def test_non_json_response_raises_redacted_finnhub_error(client):
    """A raw JSONDecodeError would bypass redaction entirely, caught during
    build when a bogus endpoint returned a non-JSON 200."""
    with patch(
        "asset_researcher.sources.finnhub.requests.get", return_value=_response(json_data=None)
    ):
        with pytest.raises(FinnhubError) as exc:
            client._get("/bogus", {}, "k", 1)
    assert "SECRET-TOKEN-VALUE" not in str(exc.value)


def test_http_error_body_is_redacted(client):
    """If the API echoes the request URL back in an error body, the token
    inside it must not reach the exception message."""
    with patch(
        "asset_researcher.sources.finnhub.requests.get",
        return_value=_response(
            status=400,
            ok=False,
            text="bad request for url ...?token=SECRET-TOKEN-VALUE",
            json_data={},
        ),
    ):
        with pytest.raises(FinnhubError) as exc:
            client._get("/quote", {}, "k", 1)
    assert "SECRET-TOKEN-VALUE" not in str(exc.value)
    assert "***REDACTED***" in str(exc.value)


def test_network_exception_is_redacted(client):
    import requests as req

    with patch(
        "asset_researcher.sources.finnhub.requests.get",
        side_effect=req.RequestException("failed connecting to ...?token=SECRET-TOKEN-VALUE"),
    ):
        with pytest.raises(FinnhubError) as exc:
            client._get("/quote", {}, "k", 1)
    assert "SECRET-TOKEN-VALUE" not in str(exc.value)


def test_bad_key_gives_clean_auth_message(client):
    with patch(
        "asset_researcher.sources.finnhub.requests.get",
        return_value=_response(status=401, ok=False, text="invalid", json_data={}),
    ):
        with pytest.raises(FinnhubError, match="rejected the API key"):
            client._get("/quote", {}, "k", 1)


def test_peers_excludes_self(client):
    with patch(
        "asset_researcher.sources.finnhub.requests.get",
        return_value=_response(json_data=["AAPL", "DELL", "HPQ"]),
    ):
        assert client.get_peers("AAPL") == ["DELL", "HPQ"]
