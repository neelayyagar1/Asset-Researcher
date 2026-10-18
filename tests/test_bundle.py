"""SourceBundle: gap reporting, staleness, and passage provenance."""

from __future__ import annotations

from asset_researcher.analysis.bundle import SourceBundle, SourcePassage


def _bundle(**kw) -> SourceBundle:
    base = dict(
        ticker="AAPL", cik=320193, company_name="Apple Inc.",
        sector_class="standard", display_industry="Technology (Electronic Computers)",
        as_of="2026-08-07",
    )
    base.update(kw)
    return SourceBundle(**base)


def _passage(label: str, text: str = "some filing text") -> SourcePassage:
    return SourcePassage(
        doc_id="0000320193/acc/10-K",
        source_url="https://example.invalid/doc.htm",
        form="10-K", filing_date="2025-10-31", label=label, tier="A",
        start=0, end=len(text), text=text,
    )


def test_gaps_record_severity_so_a_missing_mdna_is_not_a_mere_warning():
    b = _bundle()
    b.add_gap("news", "No recent news available.")
    b.add_gap("10-K:Item 7", "Content could not be located.", severity="error")
    assert b.has_errors
    assert [g.severity for g in b.gaps] == ["warning", "error"]


def test_a_bundle_with_only_warnings_is_not_an_error():
    b = _bundle()
    b.add_gap("DEF 14A", "No proxy statement on file.")
    assert not b.has_errors


def test_staleness_note_states_filing_age_rather_than_leaving_it_inferred():
    """A 10-K can be eleven months old; a report that reads as current while
    resting on stale disclosure is how a reader's trust is lost."""
    b = _bundle(as_of="2026-08-07")
    b.filing_dates["10-K"] = "2025-10-31"
    note = b.staleness_note
    assert note and "9 month" in note
    assert "8-K" in note  # tells the reader where newer information came from


def test_staleness_note_uses_days_for_a_recent_filing():
    b = _bundle(as_of="2026-08-07")
    b.filing_dates["10-K"] = "2026-08-01"
    assert "6 days ago" in (b.staleness_note or "")


def test_no_staleness_note_without_a_primary_filing():
    assert _bundle().staleness_note is None


def test_passages_are_addressable_by_label():
    b = _bundle()
    b.passages = [
        _passage("Item 1. Business"),
        _passage("Item 1A. Risk Factors"),
        _passage("Proxy. Executive Compensation"),
    ]
    got = b.passages_for("Item 1A. Risk Factors", "Proxy. Executive Compensation")
    assert [p.label for p in got] == [
        "Item 1A. Risk Factors",
        "Proxy. Executive Compensation",
    ]
    assert b.passages_for("Nonexistent") == []


def test_passage_carries_what_is_needed_to_verify_a_citation():
    """doc_id plus offsets are what let a returned citation be checked
    against the exact stored text the model was given."""
    p = _passage("Item 1. Business", "Apple designs Macs.")
    assert p.doc_id and p.source_url
    assert p.end - p.start == p.char_count
    assert p.tier in {"A", "B", "C"}


def test_total_passage_chars_sums_the_context_actually_sent():
    b = _bundle()
    b.passages = [_passage("a", "x" * 100), _passage("b", "y" * 250)]
    assert b.total_passage_chars == 350
