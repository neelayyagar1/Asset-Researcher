"""Inline-XBRL HTML -> plain text.

A 10-K is ~7x larger as HTML than as text (verified: Apple's is 1.5MB of HTML
for 220k chars of text) because most of the file is XBRL tagging markup. This
strips that down to what a reader would actually see.

**This function's output is the citation substrate.** Character offsets
returned by the model's citations are only meaningful against the exact
string produced here, so this must be deterministic and its output must be
persisted verbatim (documents/store.py). Changing the normalization rules
later silently invalidates every previously stored citation, treat edits
here as a breaking change.
"""

from __future__ import annotations

import html as html_module
import re

from lxml import html as lxml_html

_BLOCK_TAGS = {
    "p", "div", "br", "tr", "table", "h1", "h2", "h3", "h4", "h5", "h6",
    "li", "ul", "ol", "td", "th", "section", "article",
}


def html_to_text(raw_html: str) -> str:
    """Deterministic HTML -> text. Block-level elements become newlines so
    section headers stay on their own lines (which the Item splitter relies
    on); runs of whitespace collapse to single spaces within a line."""
    try:
        tree = lxml_html.fromstring(raw_html)
    except Exception:
        # Malformed markup: fall back to a regex strip rather than failing the
        # whole report. Rare, but a filing that won't parse should degrade,
        # not crash.
        stripped = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw_html)
        stripped = re.sub(r"(?s)<[^>]+>", "\n", stripped)
        return _normalize(stripped)

    for bad in tree.xpath("//script | //style"):
        bad.getparent().remove(bad)

    parts: list[str] = []

    def walk(node) -> None:
        tag = node.tag if isinstance(node.tag, str) else ""
        is_block = tag.lower() in _BLOCK_TAGS
        if is_block:
            parts.append("\n")
        if node.text:
            parts.append(node.text)
        for child in node:
            walk(child)
            if child.tail:
                parts.append(child.tail)
        if is_block:
            parts.append("\n")

    walk(tree)
    return _normalize("".join(parts))


def _normalize(text: str) -> str:
    # Filings are frequently double-escaped, so entities survive lxml's own
    # decoding and reach us as literal "&#8217;" / "&#160;" sequences. Left
    # in place they corrupt quoted text in citations (an apostrophe becomes
    # six characters) and pollute section titles.
    text = html_module.unescape(text)
    text = text.replace("\xa0", " ")  # non-breaking spaces are rife in filings
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
