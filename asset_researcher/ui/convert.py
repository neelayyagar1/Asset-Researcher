"""The rendered note, in the formats a reader actually circulates.

The note is authored once, as HTML, and that document is the source of
truth here: nothing in this module recomputes a figure, re-reads a
filing or re-renders a chart. It reads the note that was built and
re-expresses it. That is deliberate - a converter that computed its own
numbers would be the one place in this product where a figure appeared
that the document behind it does not contain.

PDF is NOT here, and that is a decision rather than an omission. The
note already carries a complete print stylesheet, so the browser's own
print engine produces a page-faithful PDF with the real typography,
the real rules and live hyperlinks back to EDGAR. Every server-side
engine available without system libraries would re-lay-out the document
worse and lose the links. The button for it lives in the view layer,
where the browser is.
"""

from __future__ import annotations

import io
import re

import lxml.html

__all__ = ("outline", "to_docx", "to_pptx")

# Blocks that carry a section's prose. Lists are flattened to their
# items; a table is kept as rows because a research note's tables are
# the audit trail and dropping them would leave the claims unsupported.
_PROSE = ("p", "li")
_WS = re.compile(r"\s+")


def _clean(text: str) -> str:
    return _WS.sub(" ", (text or "")).strip()


def outline(html: str):
    """The note as (heading, blocks), read out of the rendered document.

    Blocks are ``("text", str)`` or ``("table", [[cell, ...], ...])``.
    Content before the first ``h2`` belongs to no section and is
    returned under an empty heading, which is where the masthead lands.
    """
    root = lxml.html.document_fromstring(html)
    # The note's own navigation is a list of links to its sections. It
    # is chrome, not content, and reproduced in a document it becomes a
    # page of dead section names.
    for junk in root.xpath('//nav | //script | //style | //*[@aria-hidden="true"]'):
        junk.getparent().remove(junk)

    out, heading, blocks = [], "", []
    for el in root.iter():
        tag = str(el.tag).lower()
        if tag in ("h2", "h1"):
            if heading or blocks:
                out.append((heading, blocks))
            heading, blocks = _clean(el.text_content()), []
        elif tag == "h3":
            text = _clean(el.text_content())
            if text:
                blocks.append(("text", text))
        elif tag == "table":
            # Ancestry, not an identity set. The first version kept a
            # set of `id(el)` to avoid emitting a nested table twice -
            # but lxml builds a fresh proxy object for an element on
            # every access, so those ids are neither stable nor unique
            # and the set silently swallowed seven of this note's
            # twelve tables. The question being asked was always "is
            # this table inside another one", so it is asked directly.
            if el.xpath("ancestor::table"):
                continue
            rows = []
            for tr in el.xpath(".//tr"):
                cells = [_clean(c.text_content())
                         for c in tr.xpath("./th | ./td")]
                if any(cells):
                    rows.append(cells)
            if rows:
                blocks.append(("table", rows))
        elif tag in _PROSE:
            # A paragraph inside a table cell is already carried by the
            # table, and one inside another paragraph is not a thing.
            if el.xpath("ancestor::table | ancestor::nav"):
                continue
            text = _clean(el.text_content())
            if text:
                blocks.append(("text", text))
    if heading or blocks:
        out.append((heading, blocks))
    return out


def to_docx(html: str, title: str) -> bytes:
    """The note as an editable Word document.

    For the reader who marks it up or pastes a section into a memo,
    which is the thing a PDF cannot do and the reason this exists
    alongside one.
    """
    from docx import Document
    from docx.shared import Pt

    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10)

    doc.add_heading(title, level=0)
    for heading, blocks in outline(html):
        if heading:
            doc.add_heading(heading, level=1)
        for kind, body in blocks:
            if kind == "text":
                doc.add_paragraph(body)
            else:
                width = max(len(r) for r in body)
                table = doc.add_table(rows=0, cols=width)
                table.style = "Table Grid"
                for row in body:
                    cells = table.add_row().cells
                    for i, value in enumerate(row[:width]):
                        cells[i].text = value
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# How much of a section reaches a slide. A research note runs tens of
# thousands of pixels; a deck that reproduced it would be unreadable in
# a room, which is the only place a deck is used. The slide carries the
# section's opening argument and points at the document for the rest.
_SLIDE_CHARS = 420
_SLIDE_BULLETS = 4


def to_pptx(html: str, title: str) -> bytes:
    """The note as a deck, because pitches are given in a room.

    An honest warning lives in the deck itself: this is a summary of
    the note, not a replacement for it. A slide cannot carry a
    reconciliation table and a reader who treats it as the evidence has
    been misled by the format rather than by the figures.
    """
    from pptx import Presentation
    from pptx.util import Inches, Pt

    deck = Presentation()
    deck.slide_width = Inches(13.333)
    deck.slide_height = Inches(7.5)

    cover = deck.slides.add_slide(deck.slide_layouts[0])
    cover.shapes.title.text = title
    cover.placeholders[1].text = (
        "Built from the company's own filings to the SEC. "
        "Summary of the full research note - every figure and its "
        "citation is in the note itself."
    )

    body_layout = deck.slide_layouts[1]
    for heading, blocks in outline(html):
        points = []
        for kind, body in blocks:
            if kind != "text":
                continue
            points.append(body[:_SLIDE_CHARS].rstrip())
            if len(points) >= _SLIDE_BULLETS:
                break
        if not heading or not points:
            continue
        slide = deck.slides.add_slide(body_layout)
        slide.shapes.title.text = heading
        frame = slide.placeholders[1].text_frame
        frame.word_wrap = True
        for i, point in enumerate(points):
            para = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
            para.text = point
            para.font.size = Pt(14)

    buf = io.BytesIO()
    deck.save(buf)
    return buf.getvalue()
