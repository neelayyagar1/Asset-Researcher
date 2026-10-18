"""Item splitter. Every test here encodes a trap found against a real filing
during build, the table-of-contents collision is the one that would have
silently poisoned every report, because a TOC-derived citation still quotes
text that genuinely exists in the document, so even the verifier would pass.
"""

from asset_researcher.documents.extract import html_to_text
from asset_researcher.documents.sections import split_items

_BODY_FILLER = "This is substantive body text. " * 200  # ~6,200 chars


def _filing(toc_gap_chars: int = 2000) -> str:
    """Synthesizes a 10-K shaped like the real ones: a dense TOC listing
    every item, then the body with the same headers."""
    toc = "\n".join(
        [
            "Item 1. Business",
            "Item 1A. Risk Factors",
            "Item 1B. Unresolved Staff Comments",
            "Item 2. Properties",
            "Item 3. Legal Proceedings",
            "Item 5. Market for Common Equity",
            "Item 7. Management's Discussion and Analysis",
            "Item 7A. Quantitative and Qualitative Disclosures",
            "Item 8. Financial Statements",
            "Item 9A. Controls and Procedures",
        ]
    )
    body = "\n".join(
        [
            f"Item 1. Business\n{_BODY_FILLER}",
            f"Item 1A. Risk Factors\n{_BODY_FILLER}",
            f"Item 7. Management's Discussion and Analysis\n{_BODY_FILLER}",
            f"Item 7A. Quantitative and Qualitative Disclosures\n{_BODY_FILLER}",
        ]
    )
    return toc + ("\n" * 1) + ("x" * toc_gap_chars) + "\n" + body


def test_toc_is_not_mistaken_for_body():
    sections = split_items(_filing())
    assert sections["1"].char_count > 5000
    assert "substantive body text" in sections["1"].text


def test_toc_adjacent_to_body_still_separated():
    """JPMorgan's TOC ends 67 characters before its body begins. Any
    proximity-based rule merges them; span-based selection does not."""
    sections = split_items(_filing(toc_gap_chars=20))
    assert sections["1"].char_count > 5000
    assert "substantive body text" in sections["1"].text


def test_long_section_title_still_matches():
    """Regression: an earlier pattern capped titles at 60 chars anchored to
    end-of-line, so Item 7 ("Management's Discussion and Analysis of
    Financial Condition and Results of Operations", ~85 chars) silently
    never matched and the section vanished with no error."""
    long_title = (
        "Item 7. Management's Discussion and Analysis of Financial Condition "
        "and Results of Operations"
    )
    text = f"Item 1. Business\n{_BODY_FILLER}\n{long_title}\n{_BODY_FILLER}"
    sections = split_items(text)
    assert "7" in sections
    assert sections["7"].char_count > 5000


def test_out_of_order_item_is_rejected():
    """Realty Income's filing contains a 10-Q-style 'Item 1: Financial
    Statements' header inside the financial statements, positioned after
    Item 1A. It must not be mistaken for the Business section."""
    text = (
        f"Item 1. Business\n{_BODY_FILLER}\n"
        f"Item 1A. Risk Factors\n{_BODY_FILLER}\n"
        f"Item 1. Financial Statements\n{_BODY_FILLER}"
    )
    sections = split_items(text)
    assert "Business" in sections["1"].title


def test_cross_reference_section_is_flagged():
    """JPMorgan's Item 7 is a 398-char pointer: the MD&A is incorporated by
    reference. Building a report on that without flagging it would produce
    a confident but nearly empty analysis."""
    text = (
        f"Item 1. Business\n{_BODY_FILLER}\n"
        "Item 7. Management's Discussion and Analysis\n"
        "Management's discussion and analysis appears on pages 46-160.\n"
        f"Item 8. Financial Statements\n{_BODY_FILLER}"
    )
    sections = split_items(text)
    assert sections["7"].is_cross_reference
    assert not sections["1"].is_cross_reference


def test_empty_or_headerless_text_returns_empty():
    assert split_items("") == {}
    assert split_items("No item headers anywhere in this document.") == {}


def test_html_entities_are_decoded():
    """Filings are frequently double-escaped; literal '&#8217;' surviving
    into the text corrupts quoted spans in citations."""
    out = html_to_text("<p>Management&amp;#8217;s Discussion</p>")
    assert "&#8217;" not in out
    assert "’" in out or "'" in out


def test_html_to_text_is_deterministic():
    """Citation offsets are only meaningful against a byte-identical string,
    so extraction must produce the same output every time."""
    html = "<div><p>Alpha</p><table><tr><td>Beta</td></tr></table></div>"
    assert html_to_text(html) == html_to_text(html)


def test_malformed_html_degrades_rather_than_raising():
    out = html_to_text("<p>unclosed <div>tags <span>everywhere")
    assert "unclosed" in out
