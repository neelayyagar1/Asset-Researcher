"""Citation verification: the layer that turns a claimed citation into a
checked one."""

from __future__ import annotations

from asset_researcher.grounding.verify import (
    CitationStatus,
    verify_citations,
)
from asset_researcher.llm.provider import Citation, CitedResponse, CitedSpan
from asset_researcher.sources.base import SourceDocument, Tier

DOC_TEXT = (
    "Apple designs and markets smartphones and personal computers. "
    "The Company's fiscal year ends on the last Saturday of September. "
    "Gross margin expanded during the period."
)


def _doc(text: str = DOC_TEXT) -> SourceDocument:
    return SourceDocument(
        text=text, tier=Tier.A_AUTHORITATIVE, label="AAPL 10-K Item 1",
        source_url="https://example.invalid", as_of="2025-10-31",
    )


def _span(text: str, *citations: Citation) -> CitedSpan:
    return CitedSpan(text=text, citations=list(citations))


def _cite(quote: str, start: int, end: int, index: int = 0) -> Citation:
    return Citation(
        cited_text=quote, document_index=index, document_title="AAPL 10-K Item 1",
        start_char_index=start, end_char_index=end,
    )


def test_citation_at_the_right_offsets_verifies():
    quote = "Apple designs and markets smartphones"
    start = DOC_TEXT.index(quote)
    r = verify_citations(
        CitedResponse([_span("Apple sells phones.", _cite(quote, start, start + len(quote)))]),
        [_doc()],
    )
    assert r.citation_validity == 1.0
    assert r.citation_checks[0].status is CitationStatus.VERIFIED


def test_real_quote_at_wrong_offsets_is_a_mismatch_not_a_fabrication():
    """Distinguishing these matters: a misaligned offset is a bug, a quote
    that appears nowhere is a fabricated citation."""
    quote = "Apple designs and markets smartphones"
    r = verify_citations(
        CitedResponse([_span("x", _cite(quote, 500, 540))]), [_doc()]
    )
    assert r.citation_checks[0].status is CitationStatus.OFFSET_MISMATCH
    assert not r.passed


def test_quote_that_appears_nowhere_is_flagged_as_not_found():
    r = verify_citations(
        CitedResponse([_span("x", _cite("Apple has abandoned the iPhone", 0, 30))]),
        [_doc()],
    )
    assert r.citation_checks[0].status is CitationStatus.TEXT_NOT_FOUND
    assert r.citation_validity == 0.0


def test_citation_pointing_at_a_document_that_was_not_sent():
    r = verify_citations(
        CitedResponse([_span("x", _cite("anything", 0, 5, index=7))]), [_doc()]
    )
    assert r.citation_checks[0].status is CitationStatus.UNKNOWN_DOCUMENT


def test_missing_offsets_are_unverifiable_rather_than_assumed_good():
    c = Citation(
        cited_text="Apple designs", document_index=0, document_title="d",
        start_char_index=None, end_char_index=None,
    )
    r = verify_citations(CitedResponse([_span("x", c)]), [_doc()])
    assert r.citation_checks[0].status is CitationStatus.NO_OFFSETS
    assert not r.passed


def test_whitespace_differences_do_not_fail_a_correct_citation():
    """Filings carry newlines from block-level HTML; the API may return the
    quote with them collapsed. Treating that as a mismatch would fail correct
    citations en masse."""
    text = "Gross margin\nexpanded during\nthe period."
    r = verify_citations(
        CitedResponse([_span("x", _cite("Gross margin expanded during the period.", 0, len(text)))]),
        [_doc(text)],
    )
    assert r.citation_checks[0].status is CitationStatus.VERIFIED


# --- numeric support ----------------------------------------------------


def test_a_figure_absent_from_the_cited_quote_is_flagged():
    quote = "Gross margin expanded during the period."
    start = DOC_TEXT.index(quote)
    r = verify_citations(
        CitedResponse([
            _span("Gross margin reached 46.7%.", _cite(quote, start, start + len(quote)))
        ]),
        [_doc()],
    )
    assert "46.7%" in r.unsupported_numbers
    assert not r.passed


def test_a_figure_present_in_the_cited_quote_is_accepted():
    text = "Gross margin reached 46.7% for the year."
    r = verify_citations(
        CitedResponse([_span("Margin was 46.7%.", _cite(text, 0, len(text)))]),
        [_doc(text)],
    )
    assert r.unsupported_numbers == []


def test_a_figure_matching_filed_xbrl_is_accepted():
    """The renderer legitimately splices filed values into prose."""
    r = verify_citations(
        CitedResponse([_span("Revenue was $416.2 billion.")]),
        [_doc()],
        known_figures={"416.2"},
    )
    assert r.unsupported_numbers == []


def test_sec_item_codes_are_not_treated_as_financial_figures():
    """Verified live on Apple: 'Item 2.02' and 'Item 5.02' were flagged as
    unsupported figures by an earlier rule that matched any decimal."""
    r = verify_citations(
        CitedResponse([_span("Earnings releases are furnished under Item 2.02 and Item 5.02.")]),
        [_doc()],
    )
    assert r.unsupported_numbers == []


def test_years_are_not_treated_as_figures():
    r = verify_citations(
        CitedResponse([_span("The fiscal year ended in 2025 and 2024.")]), [_doc()]
    )
    assert r.unsupported_numbers == []


# --- coverage -----------------------------------------------------------


def test_coverage_is_measured_by_characters_not_spans():
    """The API splits text at citation boundaries, so joiners like ';' become
    their own spans. Counting spans reported Apple at 50% cited when 76% of
    its prose was."""
    quote = "Apple designs and markets smartphones"
    start = DOC_TEXT.index(quote)
    long_cited = _span("A" * 400, _cite(quote, start, start + len(quote)))
    r = verify_citations(CitedResponse([long_cited, _span("; "), _span(", and")]), [_doc()])
    assert r.coverage == 1.0  # joiners are not uncited assertions


def test_a_substantive_uncited_claim_lowers_coverage():
    quote = "Apple designs and markets smartphones"
    start = DOC_TEXT.index(quote)
    r = verify_citations(
        CitedResponse([
            _span("A" * 100, _cite(quote, start, start + len(quote))),
            _span("The company will almost certainly grow faster than its peers next year."),
        ]),
        [_doc()],
    )
    assert 0.0 < r.coverage < 1.0


def test_markdown_headings_do_not_count_against_coverage():
    quote = "Apple designs and markets smartphones"
    start = DOC_TEXT.index(quote)
    r = verify_citations(
        CitedResponse([
            _span("## Risk Factors\n\n"),
            _span("A" * 100, _cite(quote, start, start + len(quote))),
        ]),
        [_doc()],
    )
    assert r.coverage == 1.0


def test_a_response_with_no_citations_at_all_does_not_pass():
    r = verify_citations(CitedResponse([_span("Entirely uncited prose about the company.")]), [_doc()])
    assert r.total_citations == 0
    assert not r.passed
