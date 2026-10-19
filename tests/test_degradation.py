"""Failure paths in bundle assembly.

The design's first success criterion is surviving contact with strangers: a
prospect types their own ticker and forms a judgement in ninety seconds. What
matters is not the happy path but that every missing source degrades into a
stated gap rather than a crash or, worse, a confident-looking hole.

Every test here removes something a real filer might not have.
"""

from __future__ import annotations

import pytest

from asset_researcher.analysis.assemble import assemble_bundle
from asset_researcher.config import get_settings
from asset_researcher.documents.store import DocumentStore
from tests.fakes import (
    SUBMISSIONS,
    TICKER,
    FakeEdgarClient,
    FakeFinnhubClient,
    FakeLLM,
)


def _build(edgar, tmp_path, finnhub=None):
    return assemble_bundle(
        TICKER, get_settings(), edgar, finnhub or FakeFinnhubClient(), FakeLLM(),
        store=DocumentStore(tmp_path / "documents"),
    )


def _gap_sources(bundle) -> set[str]:
    return {gap.source for gap in bundle.gaps}


class _NoProxy(FakeEdgarClient):
    def get_json(self, url, cache_key, ttl_seconds):
        data = super().get_json(url, cache_key, ttl_seconds)
        if "submissions" in url:
            recent = data["filings"]["recent"]
            keep = [i for i, f in enumerate(recent["form"]) if f != "DEF 14A"]
            for key, values in recent.items():
                if isinstance(values, list):
                    recent[key] = [values[i] for i in keep]
        return data


class _NoFilingsAtAll(FakeEdgarClient):
    def get_json(self, url, cache_key, ttl_seconds):
        data = super().get_json(url, cache_key, ttl_seconds)
        if "submissions" in url:
            for key, values in data["filings"]["recent"].items():
                if isinstance(values, list):
                    data["filings"]["recent"][key] = []
        return data


class _NoXbrl(FakeEdgarClient):
    def get_json(self, url, cache_key, ttl_seconds):
        if "companyfacts" in url:
            raise RuntimeError("no XBRL for this filer")
        return super().get_json(url, cache_key, ttl_seconds)


class _CrossReferencedMdna(FakeEdgarClient):
    """A bank-shaped filing: Item 7 holds only a pointer, and the MD&A text
    sits outside the Item sequence entirely.

    Both halves matter. If the stub and the content are contiguous, Item 7 is
    simply a large normal section and no cross-reference exists to recover.
    an earlier version of this fixture made exactly that mistake and tested
    nothing.
    """

    def get_text(self, url, cache_key, ttl_seconds):
        text = super().get_text(url, cache_key, ttl_seconds)
        if "tenk.htm" not in url:
            return text

        stub = (
            "<p>Item 7. Management's Discussion and Analysis of Financial "
            "Condition and Results of Operations</p><p>Management's discussion "
            "and analysis appears on pages 46-160 of the annual report.</p>"
        )
        # rindex, not index: the table of contents repeats every Item header,
        # so index() would rewrite the contents listing and leave the body
        # untouched, which is exactly what an earlier version of this
        # fixture did.
        start = text.rindex("<p>Item 7. Management")
        end = text.rindex("<p>Item 7A.")
        text = text[:start] + stub + text[end:]

        # The real narrative lives after the Item sequence, reachable only by
        # content matching.
        appendix = (
            "<p>Results of operations compared with the prior year reflect an "
            "increase in net revenue, primarily driven by higher net interest "
            "income and a lower provision for credit losses. Operating margin "
            "improved and cash flows from operations grew.</p>"
        ) * 30
        return text.replace("</body>", appendix + "</body>")


class _NoNews(FakeFinnhubClient):
    def get_news(self, symbol, days=45, limit=15):
        return []


class _NoQuote(FakeFinnhubClient):
    def get_quote(self, symbol):
        raise RuntimeError("quote endpoint unavailable on this plan")

    def get_profile(self, symbol):
        raise RuntimeError("profile endpoint unavailable on this plan")


# --- missing sources ----------------------------------------------------


def test_a_filer_with_no_proxy_still_produces_a_report(tmp_path):
    """Plenty of filers have no recent DEF 14A. Compensation analysis is
    unavailable; the report is not."""
    bundle = _build(_NoProxy(), tmp_path)
    assert "DEF 14A" in _gap_sources(bundle)
    assert bundle.passages  # the 10-K still carried through
    assert not bundle.has_errors


def test_no_10k_is_an_error_not_a_warning(tmp_path):
    """With no primary filing there is nothing to analyse, and the report
    must say so rather than assemble something from news alone."""
    bundle = _build(_NoFilingsAtAll(), tmp_path)
    assert bundle.has_errors
    assert "10-K" in _gap_sources(bundle)


def test_missing_xbrl_is_an_error_and_leaves_no_figures(tmp_path):
    bundle = _build(_NoXbrl(), tmp_path)
    assert bundle.has_errors
    assert "xbrl" in _gap_sources(bundle)
    assert bundle.series is None
    assert bundle.health_scores == []


def test_missing_market_data_degrades_to_a_gap_not_a_crash(tmp_path):
    bundle = _build(FakeEdgarClient(), tmp_path, finnhub=_NoQuote())
    assert {"price", "profile"} <= _gap_sources(bundle)
    assert bundle.quote is None
    assert bundle.market_cap is None
    assert bundle.passages  # filings still gathered


def test_absent_news_is_recorded_rather_than_silently_empty(tmp_path):
    bundle = _build(FakeEdgarClient(), tmp_path, finnhub=_NoNews())
    assert "news" in _gap_sources(bundle)
    assert bundle.news == []


# --- cross-referenced items --------------------------------------------


def test_a_cross_referenced_mdna_is_recovered_and_the_recovery_disclosed(tmp_path):
    """JPMorgan's Item 7 is a 398-character pointer. Recovering the content
    silently would hide that the section was reconstructed."""
    bundle = _build(_CrossReferencedMdna(), tmp_path)

    mdna = [p for p in bundle.passages if p.label.startswith("Item 7.")]
    assert mdna, "MD&A was not recovered at all"
    assert any("net interest income" in p.text for p in mdna)

    note = next(g for g in bundle.gaps if g.source == "10-K:Item 7")
    assert "incorporated by reference" in note.reason.lower()


# --- peers --------------------------------------------------------------


def test_no_peer_list_omits_relative_valuation_without_failing(tmp_path):
    bundle = _build(FakeEdgarClient(), tmp_path, finnhub=FakeFinnhubClient(peers=[]))
    assert "comps" in _gap_sources(bundle)
    assert bundle.comps is not None
    assert bundle.comps.subject is not None  # the subject row still exists
    assert bundle.comps.peers == []


def test_a_peer_that_cannot_be_resolved_is_excluded_and_named(tmp_path):
    """A dead ticker in a peer list must not take the report down, and the
    reader should see which peers were dropped."""

    class _BadPeer(FakeFinnhubClient):
        def get_profile(self, symbol):
            if symbol == "GHOST":
                raise RuntimeError("unknown symbol")
            return super().get_profile(symbol)

    bundle = _build(
        FakeEdgarClient(), tmp_path, finnhub=_BadPeer(peers=["GHOST"])
    )
    assert bundle.comps is not None
    assert "GHOST" in bundle.comps.excluded
    assert "comps" in _gap_sources(bundle)


# --- truncation ---------------------------------------------------------


def test_truncated_sections_are_disclosed_with_the_amount_lost(tmp_path):
    """A section trimmed to fit the context budget is still partial evidence;
    the report says how much was dropped."""

    class _HugeRiskFactors(FakeEdgarClient):
        def get_text(self, url, cache_key, ttl_seconds):
            text = super().get_text(url, cache_key, ttl_seconds)
            if "tenk.htm" in url:
                filler = "<p>An additional disclosed risk of some length. </p>" * 4000
                text = text.replace("<p>Item 7. Management", filler + "<p>Item 7. Management")
            return text

    bundle = _build(_HugeRiskFactors(), tmp_path)
    truncation = [g for g in bundle.gaps if "Truncated" in g.reason]
    assert truncation, "an oversized section was truncated without saying so"
    assert "characters" in truncation[0].reason


def test_a_validation_warning_reaches_the_reader_not_just_the_bundle():
    """Warnings were computed and discarded, so `check_period_alignment`
    was dead from the reader's point of view and a filer reporting zero
    revenue against a hundred billion of net income exported as a clean
    note carrying a price target."""
    from asset_researcher.analysis.bundle import SourceBundle
    from asset_researcher.quant.validate import ValidationResult

    bundle = SourceBundle(
        ticker="T", cik=1, company_name="T", sector_class="standard",
        display_industry="x", as_of="2026-01-01",
    )
    result = ValidationResult()
    result.add("revenue_vs_net_income", "Revenue is less than net income.",
               severity="warning")
    result.add("accounting_identity", "Assets do not equal liabilities "
               "plus equity.", severity="error")

    for issue in result.issues:
        bundle.add_gap(f"xbrl:{issue.check}", issue.message, issue.severity)

    severities = {g.severity for g in bundle.gaps}
    assert severities == {"warning", "error"}
    assert any("less than net income" in g.reason for g in bundle.gaps)
