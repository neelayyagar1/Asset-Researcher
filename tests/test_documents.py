"""Document layer: store integrity, density selection, proxy and MD&A recovery."""

from __future__ import annotations

import pytest

from asset_researcher.documents.density import score_window, select_dense_regions
from asset_researcher.documents.proxy import extract_proxy_sections
from asset_researcher.documents.sections import (
    recover_cross_referenced_section,
    split_items,
)
from asset_researcher.documents.store import (
    DocumentIntegrityError,
    DocumentStore,
    StoredDocument,
    compute_sha256,
    make_doc_id,
)


def _doc(text: str = "Hello filing world.") -> StoredDocument:
    return StoredDocument(
        doc_id=make_doc_id(320193, "0000320193-25-000079", "10-K"),
        cik=320193,
        form="10-K",
        filing_date="2025-10-31",
        accession_number="0000320193-25-000079",
        source_url="https://example.invalid/doc.htm",
        title="Apple 10-K",
        text=text,
        sha256=compute_sha256(text),
    )


# --- store -------------------------------------------------------------


def test_stored_text_round_trips_byte_identical(tmp_path):
    """Citation offsets are only meaningful against the exact stored string."""
    store = DocumentStore(tmp_path)
    original = "Item 7. Management’s Discussion, margins improved 3.2%.\n\nNext."
    store.put(_doc(original))
    loaded = store.load(make_doc_id(320193, "0000320193-25-000079", "10-K"))
    assert loaded is not None
    assert loaded.text == original


def test_tampered_text_raises_rather_than_serving_shifted_offsets(tmp_path):
    """Silently serving altered text would resolve every citation to the
    wrong passage while still looking valid, fail loudly instead."""
    store = DocumentStore(tmp_path)
    doc = store.put(_doc("original text here"))
    text_path, _ = store._paths(doc.doc_id)
    text_path.write_text("tampered text here", encoding="utf-8")

    with pytest.raises(DocumentIntegrityError):
        store.load(doc.doc_id)


def test_slice_clamps_instead_of_raising(tmp_path):
    doc = _doc("abcdef")
    assert doc.slice(2, 4) == "cd"
    assert doc.slice(4, 999) == "ef"  # clamped, not an exception
    assert doc.slice(-1, 3) == ""
    assert doc.slice(3, 3) == ""


def test_doc_id_is_filesystem_safe_for_forms_containing_spaces():
    assert " " not in make_doc_id(1, "0001-2", "DEF 14A")
    assert make_doc_id(1, "0001-2", "10-K/A").count("/") == 2  # cik/accn/form only


# --- density -----------------------------------------------------------

_TERMS = {"comp": ("total compensation", "stock awards", "salary")}


def test_page_number_lines_score_below_prose():
    """A contents listing and a real section can share vocabulary; page
    numbers are what distinguish them."""
    toc = "Salary\n63\nStock awards\n64\nTotal compensation\n65\n" * 3
    prose = (
        "Total compensation for the named executive officers reflects salary "
        "of $1,000,000 and stock awards valued at $22,157,075 for the year. "
    ) * 3
    assert score_window(prose, _TERMS)[0] > score_window(toc, _TERMS)[0]


def test_xbrl_markup_window_is_rejected_outright():
    """Verified on JPMorgan: taxonomy names carry the same vocabulary as
    prose and once won a 1.3M-character region of pure markup."""
    markup = "0000019617 us-gaap:CreditRiskContractMember 2025-12-31 salary " * 40
    score, _ = score_window(markup, _TERMS)
    assert score == 0.0


def test_select_dense_regions_respects_budget_and_returns_document_order():
    text = ("filler " * 800) + ("total compensation salary stock awards " * 300)
    regions = select_dense_regions(text, _TERMS, char_budget=10_000)
    assert regions
    assert sum(r.char_count for r in regions) <= 15_000
    assert regions == sorted(regions, key=lambda r: r.start)


# --- proxy -------------------------------------------------------------


def test_proxy_extraction_prefers_disclosure_over_contents_listing():
    toc = "I. Summary compensation table\n63\nII. Grants of plan-based awards\n64\n" * 20
    body = (
        "Summary Compensation Table. Salary of $1,500,000, stock awards of "
        "$22,157,075, and all other compensation of $22,182 for fiscal 2025. "
        "The compensation committee approved a target award reflecting "
        "performance share vesting and a clawback provision. "
    ) * 40
    text = toc + body
    sections = extract_proxy_sections(text, char_budget=10_000)
    assert sections
    assert all(s.start >= len(toc) - 5_000 for s in sections)


def test_proxy_returns_nothing_for_a_document_with_no_signal():
    assert extract_proxy_sections("lorem ipsum " * 2000) == []


# --- cross-reference recovery -----------------------------------------


def test_cross_reference_is_detected_not_treated_as_content():
    text = (
        "Item 7. Management’s Discussion and Analysis.\n\n"
        "Management’s discussion and analysis appears on pages 46-160.\n\n"
        "Item 8. Financial Statements.\n\n" + ("detail " * 500)
    )
    section = split_items(text)["7"]
    assert section.is_cross_reference


def test_recovery_returns_separate_passages_within_budget():
    """An earlier version returned first-region-start to last-region-end,
    which spanned 1,085,000 characters of JPMorgan's 10-K."""
    filler = "unrelated boilerplate text " * 2000
    mdna = (
        "Results of operations for the period compared with the prior year "
        "reflect an increase in net revenue of $1,200,000, primarily driven by "
        "higher net interest income and a lower provision for credit losses. "
    ) * 60
    text = filler + mdna + filler
    sections = recover_cross_referenced_section(text, "7", char_budget=20_000)
    assert sections
    assert sum(s.char_count for s in sections) <= 25_000
    assert all(s.item == "7" for s in sections)
    assert "recovered by content" in sections[0].title


def test_recovery_is_a_noop_for_items_without_fallback_vocabulary():
    assert recover_cross_referenced_section("some text " * 1000, "1") == []


def test_windows_snap_to_paragraph_breaks_when_one_is_near():
    """Fixed-stride windows open mid-sentence, which reads as a bug in the
    click-through-to-source view even when the quote itself is correct."""
    # Lead-in carries no signal terms, so scoring regions start well after
    # offset 0, otherwise "starts at 0" satisfies the assertion trivially
    # and the test cannot fail.
    # Must exceed the window (5,000) so early windows contain no signal at
    # all and cannot be selected.
    lead = ("Boilerplate preamble sentence with no scoring vocabulary. " * 12 + "\n\n") * 20

    # Paragraphs (~760 chars) are shorter than the 1,000-char stride, so an
    # unsnapped window start lands mid-paragraph with a break close behind it.
    paragraph = (
        "Total compensation for the named executives reflects salary and "
        "stock awards granted during the fiscal year, together with amounts "
        "reported under all other compensation. " * 4
    ) + "\n\n"
    text = lead + paragraph * 60

    regions = select_dense_regions(text, _TERMS, char_budget=20_000)
    assert regions
    assert any(r.start > 0 for r in regions), "fixture failed to produce a non-zero start"

    for r in regions:
        assert r.start == 0 or text[r.start - 2 : r.start] == "\n\n", (
            f"region at {r.start} does not begin at a paragraph break: "
            f"{text[r.start : r.start + 40]!r}"
        )
        assert r.text_starts_cleanly(text), "region opens on whitespace"


def test_boundaries_are_left_alone_when_no_break_is_within_tolerance():
    """Snapping is best-effort: a ragged edge beats dragging a window far
    from the content that actually scored."""
    text = "salary stock awards total compensation " * 2000  # no "\n\n" at all
    regions = select_dense_regions(text, _TERMS, char_budget=10_000)
    assert regions
    for r in regions:
        assert r.end > r.start
        assert r.char_count > 0


def test_8k_cover_page_is_skipped_so_the_disclosure_is_not_lost():
    """Verified live on Apple's April 2026 8-K: the first 2,973 characters
    are inline-XBRL cover metadata, and the disclosure, a CEO succession
    announcement, begins at 'Item 5.02'. Sending the first N characters
    delivered pure metadata and silently dropped the most material fact
    available for that company."""
    from asset_researcher.documents.sections import extract_8k_content

    cover = "true\n\ntrue\n\nNASDAQ\n\n0000320193\n\n2026-04-17\n\n" * 40
    body = (
        "Item 5.02\n\nDeparture of Directors or Certain Officers.\n\n"
        "On April 20, 2026, Apple Inc. announced that Tim Cook will "
        "transition from his role as Chief Executive Officer."
    )
    content = extract_8k_content(cover + body)
    assert content.lstrip().startswith("Item 5.02")
    assert "Tim Cook" in content
    assert "NASDAQ" not in content


def test_8k_without_an_item_heading_is_returned_whole():
    """A filing we cannot parse is better sent whole than dropped."""
    from asset_researcher.documents.sections import extract_8k_content

    text = "Some unparseable 8-K body with no item heading at all."
    assert extract_8k_content(text) == text
