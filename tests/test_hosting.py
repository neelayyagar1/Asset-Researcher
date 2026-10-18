"""Spend caps and report rendering for the hosted demo."""

from __future__ import annotations

import json
from datetime import date, timedelta

import pytest

from asset_researcher.analysis.narrative import NarrativeResult
from asset_researcher.analysis.report import render_with_citations
from asset_researcher.grounding.verify import verify_citations
from asset_researcher.hosting.spend import (
    ESTIMATED_REPORT_COST_USD,
    SpendLimitExceeded,
    SpendTracker,
    Usage,
)
from asset_researcher.llm.provider import Citation, CitedResponse, CitedSpan
from asset_researcher.sources.base import SourceDocument, Tier


def _tracker(tmp_path, daily=25.0, session=6.0) -> SpendTracker:
    return SpendTracker(
        path=tmp_path / "spend.json", daily_cap_usd=daily, session_cap_usd=session
    )


# --- spend --------------------------------------------------------------


def test_a_single_report_must_fit_inside_the_session_cap(tmp_path):
    """Regression: the estimate was once $3.50 against a $3.00 session cap,
    so every run was rejected before starting and the demo was dead."""
    from asset_researcher.config import get_settings

    settings = get_settings()
    assert ESTIMATED_REPORT_COST_USD < settings.hosting.spend_cap_session_usd
    _tracker(tmp_path).check_can_start(0.0, ESTIMATED_REPORT_COST_USD)  # no raise


def test_session_cap_stops_one_visitor_running_away(tmp_path):
    tracker = _tracker(tmp_path, session=6.0)
    tracker.check_can_start(0.0, 2.0)
    tracker.check_can_start(3.9, 2.0)
    with pytest.raises(SpendLimitExceeded, match="session"):
        tracker.check_can_start(5.0, 2.0)


def test_daily_cap_stops_the_account_being_drained_across_visitors(tmp_path):
    tracker = _tracker(tmp_path, daily=25.0)
    tracker.record(24.0)
    with pytest.raises(SpendLimitExceeded, match="daily budget"):
        tracker.check_can_start(0.0, 2.0)


def test_limits_point_the_user_somewhere_useful(tmp_path):
    """A blocked visitor should learn they can run it themselves rather than
    just hitting a wall."""
    tracker = _tracker(tmp_path, daily=1.0)
    with pytest.raises(SpendLimitExceeded, match="own API key"):
        tracker.check_can_start(0.0, 2.0)


def test_spend_persists_across_restarts(tmp_path):
    _tracker(tmp_path).record(4.0)
    assert _tracker(tmp_path).spent_today() == pytest.approx(4.0)


def test_yesterdays_spend_does_not_count_against_today(tmp_path):
    path = tmp_path / "spend.json"
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    path.write_text(json.dumps({"date": yesterday, "spent_usd": 25.0}))
    assert _tracker(tmp_path).spent_today() == 0.0
    assert _tracker(tmp_path).remaining_today() == pytest.approx(25.0)


def test_a_corrupt_counter_fails_closed_not_open(tmp_path):
    """Reading a damaged file as 'plenty of budget left' would be the worst
    possible interpretation."""
    (tmp_path / "spend.json").write_text("{not json")
    assert _tracker(tmp_path).remaining_today() == 0.0


def test_cost_is_computed_from_measured_tokens():
    usage = Usage(input_tokens=200_000, output_tokens=12_000)
    assert usage.cost_usd == pytest.approx(200_000 / 1e6 * 5 + 12_000 / 1e6 * 25)
    assert (Usage(input_tokens=1000) + Usage(output_tokens=500)).output_tokens == 500


# --- citation rendering -------------------------------------------------

_DOC_TEXT = "Apple designs and markets smartphones and personal computers."


def _narrative(spans: list[CitedSpan]) -> NarrativeResult:
    documents = [
        SourceDocument(
            text=_DOC_TEXT, tier=Tier.A_AUTHORITATIVE, label="AAPL 10-K Item 1",
            source_url="https://sec.gov/doc", as_of="2025-10-31",
        )
    ]
    response = CitedResponse(spans)
    return NarrativeResult(
        response=response,
        documents=documents,
        verification=verify_citations(response, documents),
    )


def test_verified_citations_render_as_plain_numbered_markers():
    quote = "Apple designs and markets smartphones"
    start = _DOC_TEXT.index(quote)
    narrative = _narrative(
        [
            CitedSpan(
                text="Apple sells phones.",
                citations=[
                    Citation(quote, 0, "AAPL 10-K Item 1", start, start + len(quote))
                ],
            )
        ]
    )
    markdown, citations = render_with_citations(narrative)
    # Inline hyperlink to the source, no separate footnote list to scroll to.
    assert "[[1](https://sec.gov/doc)]" in markdown
    assert "unverified" not in markdown
    assert citations[0].verified
    assert citations[0].source_url == "https://sec.gov/doc"


def test_a_failed_citation_is_marked_in_the_prose_not_dropped():
    """Showing the failure is the point, a reader must be able to see which
    claim could not be traced."""
    narrative = _narrative(
        [
            CitedSpan(
                text="Apple has exited hardware.",
                citations=[
                    Citation("Apple has exited hardware", 0, "AAPL 10-K Item 1", 0, 25)
                ],
            )
        ]
    )
    markdown, citations = render_with_citations(narrative)
    assert "unverified" in markdown
    assert not citations[0].verified
    assert citations[0].status == "text_not_found"


def test_uncited_prose_survives_rendering_without_a_marker():
    narrative = _narrative([CitedSpan(text="A general statement.", citations=[])])
    markdown, citations = render_with_citations(narrative)
    assert "A general statement." in markdown
    assert citations == []


def test_citation_numbering_is_sequential_across_spans():
    quote = "Apple designs"
    start = _DOC_TEXT.index(quote)
    cite = Citation(quote, 0, "AAPL 10-K Item 1", start, start + len(quote))
    narrative = _narrative(
        [
            CitedSpan(text="One.", citations=[cite]),
            CitedSpan(text=" Two.", citations=[cite]),
        ]
    )
    markdown, citations = render_with_citations(narrative)
    assert [c.number for c in citations] == [1, 2]
    assert "[1]" in markdown and "[2]" in markdown


# --- the EDGAR contact ---------------------------------------------------


def test_a_placeholder_edgar_contact_is_rejected_at_startup():
    """`.env.example` ships contact@example.com, and copying it verbatim is
    the obvious thing to do. That sends a fake contact to the SEC on every
    request, which earns an IP block part-way through a report rather than
    an error at startup where it can be understood."""
    from asset_researcher.config.loader import _require_edgar_user_agent

    with pytest.raises(RuntimeError, match="placeholder"):
        _require_edgar_user_agent("Asset-Researcher contact@example.com")


def test_an_edgar_contact_without_an_address_is_rejected():
    from asset_researcher.config.loader import _require_edgar_user_agent

    with pytest.raises(RuntimeError, match="contact email"):
        _require_edgar_user_agent("Asset-Researcher research tool")


def test_a_real_edgar_contact_is_accepted_unchanged():
    from asset_researcher.config.loader import _require_edgar_user_agent

    value = "Asset-Researcher research tool person@somefund.co"
    assert _require_edgar_user_agent(value) == value
