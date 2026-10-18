import pytest

from asset_researcher.sources.edgar.resolve import (
    TickerNotFoundError,
    cik_to_padded,
    resolve_ticker,
)


class _FakeClient:
    """Duck-typed stand-in for EdgarClient, no network, no cache dir."""

    def __init__(self, data: dict):
        self._data = data

    def get_json(self, url: str, cache_key: str, ttl_seconds) -> dict:
        return self._data


_SAMPLE = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA CORP"},
}


def test_resolve_ticker_finds_match():
    cik, name = resolve_ticker(_FakeClient(_SAMPLE), "AAPL")
    assert cik == 320193
    assert name == "Apple Inc."


def test_resolve_ticker_is_case_insensitive():
    cik, _ = resolve_ticker(_FakeClient(_SAMPLE), "aapl")
    assert cik == 320193


def test_resolve_ticker_strips_whitespace():
    cik, _ = resolve_ticker(_FakeClient(_SAMPLE), "  AAPL  ")
    assert cik == 320193


def test_resolve_unknown_ticker_raises_with_helpful_message():
    with pytest.raises(TickerNotFoundError, match="ZZZZZ"):
        resolve_ticker(_FakeClient(_SAMPLE), "ZZZZZ")


def test_cik_to_padded_formats_to_ten_digits():
    assert cik_to_padded(320193) == "CIK0000320193"
    assert cik_to_padded(1) == "CIK0000000001"
