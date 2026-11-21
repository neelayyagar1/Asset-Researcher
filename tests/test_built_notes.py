"""The built sample notes, checked as documents.

These run only when `build/site` exists, because the notes are artifacts
rather than something the suite can regenerate: each costs a real API
call. When they are present they are checked properly - parsed, not
pattern-matched.

The previous audit of these notes used regular expressions and
`<th[^>]*>` matched `<thead>`, inflating every header count by one and
nearly reporting 1,249 ragged rows that did not exist. A parser knows
the difference between a tag and a prefix of one.
"""

from __future__ import annotations

import pathlib
from html.parser import HTMLParser

import pytest

SITE = pathlib.Path(__file__).resolve().parents[1] / "build" / "site"


def _notes() -> list[pathlib.Path]:
    if not SITE.is_dir():
        return []
    return [p for p in sorted(SITE.glob("*.html")) if p.stem != "index"]


pytestmark = pytest.mark.skipif(
    not _notes(), reason="no built notes in build/site"
)


class _Doc(HTMLParser):
    """Enough of a DOM to ask the questions that matter."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.hrefs: list[str] = []
        self.tables: list[list[int]] = []   # cells per row, per table
        self._row_counts: list[int] = []
        self._cells = 0
        self._stack: list[str] = []
        self.text_parts: list[str] = []
        self.unclosed: list[str] = []
        self.script_count = 0
        self._suppress = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a" and "href" in a:
            self.hrefs.append(a["href"])
        if tag == "table":
            self._row_counts = []
            self._stack.append("table")
        elif tag == "tr":
            self._cells = 0
        elif tag in ("td", "th"):
            # colspan counts as the columns it spans. A group heading
            # drawn as one full-width cell is not a ragged row, and
            # counting cells rather than columns reported every note's
            # statement table as broken.
            try:
                self._cells += max(1, int(a.get("colspan", 1)))
            except (TypeError, ValueError):
                self._cells += 1
        elif tag == "script":
            self.script_count += 1
            self._suppress = True
        elif tag == "style":
            self._suppress = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._suppress = False
        if tag == "tr":
            self._row_counts.append(self._cells)
        elif tag == "table":
            self.tables.append(self._row_counts)
            if self._stack and self._stack[-1] == "table":
                self._stack.pop()

    def handle_data(self, data):
        # Script and stylesheet bodies are not read by anyone. Collecting
        # them made the jump script's own source count as page text, and
        # a placeholder scan then reported "None" on every note.
        if not self._suppress:
            self.text_parts.append(data)

    @property
    def text(self) -> str:
        return " ".join(self.text_parts)


def _parse(path: pathlib.Path) -> _Doc:
    doc = _Doc()
    doc.feed(path.read_text(encoding="utf-8"))
    return doc


@pytest.mark.parametrize("note", _notes(), ids=lambda p: p.stem)
def test_every_table_is_rectangular(note):
    """A row with fewer cells than its header is a column silently
    dropped, which in a financial table means a figure read under the
    wrong heading."""
    doc = _parse(note)
    for index, rows in enumerate(doc.tables):
        body = [r for r in rows if r]
        if len(body) < 2:
            continue
        width = max(set(body), key=body.count)   # the common row width
        ragged = [r for r in body if r != width]
        assert not ragged, (
            f"{note.stem} table {index}: rows of {sorted(set(body))} cells "
            f"against a common width of {width}"
        )


@pytest.mark.parametrize("note", _notes(), ids=lambda p: p.stem)
def test_every_internal_link_resolves(note):
    """The section bar is the only way to move inside a 33,000px
    document."""
    doc = _parse(note)
    targets = [h[1:] for h in doc.hrefs if h.startswith("#") and len(h) > 1]
    missing = sorted({t for t in targets if t not in doc.ids})
    assert not missing, f"{note.stem}: links to absent ids {missing}"


@pytest.mark.parametrize("note", _notes(), ids=lambda p: p.stem)
def test_the_note_never_claims_a_citation_is_verified(note):
    """The product's whole discipline: a located quote is not a
    supported claim. This word appeared ninety times per note once."""
    doc = _parse(note)
    assert "Verified" not in doc.text, f"{note.stem} says Verified"


@pytest.mark.parametrize("note", _notes(), ids=lambda p: p.stem)
def test_no_unresolved_entities_or_placeholders_reach_the_reader(note):
    """Looks for a placeholder STANDING AS A VALUE, not for a word.

    Scanning the prose for "None" flagged every note on the sentence
    "None of this is softened by the filings", and for "nan" it would
    flag "financial". A leaked placeholder occupies a cell or a field on
    its own, so that is what is checked.
    """
    raw = note.read_text(encoding="utf-8")
    for bad in ("&amp;amp;", "&amp;nbsp;", ">None<", ">nan<", ">NaN<",
                ">{}<", ">TODO<", ">FIXME<", "Traceback (most recent"):
        assert bad not in raw, f"{note.stem} shows {bad!r} as a value"


@pytest.mark.parametrize("note", _notes(), ids=lambda p: p.stem)
def test_the_section_index_can_actually_jump(note):
    """Inside the app a note is an iframe whose baseURI is the parent
    page, so `#s-valuation` resolves against the wrong document. The
    script that resolves by id is what makes the bar work."""
    doc = _parse(note)
    assert doc.script_count >= 1, f"{note.stem} carries no jump script"


@pytest.mark.parametrize("note", _notes(), ids=lambda p: p.stem)
def test_the_section_names_are_the_vocabulary_the_project_settled_on(note):
    """Checks the SECTION NAMES, which is where vocabulary is a promise.

    Scanning the whole document flagged a footnote reading "Evidence:
    Implied expectations solved from current price", which is a sentence
    about the section rather than a heading, and the renamed heading
    sits directly above it. Headings and the index are what a reader
    navigates by.
    """
    import re

    raw = note.read_text(encoding="utf-8")
    headings = re.findall(r'<h2 class="ar-sec-label"[^>]*>(.*?)</h2>', raw, re.S)
    nav = re.findall(r'<nav class="ar-nav">(.*?)</nav>', raw, re.S)
    nav_labels = re.findall(r"<a [^>]*>(.*?)</a>", " ".join(nav), re.S)
    names = [re.sub(r"<[^>]+>", "", h).strip() for h in headings + nav_labels]
    assert names, f"{note.stem} has no section headings at all"

    retired = {"Counter-case", "Variant view", "Market pricing",
               "Implied expectations", "Reconciliation", "Health",
               "Summary", "Note", "Questions"}
    found = sorted(set(names) & retired)
    assert not found, (
        f"{note.stem} section names still use retired vocabulary: {found}"
    )


_IMPLEMENTATION_WORDS = (
    "the renderer", "renderer will", "this prompt", "the schema",
    "as instructed", "the model will", "placeholder", "TODO",
    "the pipeline", "JSON", "the template",
)


@pytest.mark.parametrize("note", _notes(), ids=lambda p: p.stem)
def test_no_implementation_vocabulary_reaches_the_reader(note):
    """A research note is not allowed to mention how it was built.

    ADP's note contained "all of which the renderer will populate",
    inside a cited sentence, in the Business description. The prompts
    explain the renderer to the model so it understands why it may not
    write a figure, and the model repeated the word back into the
    product. It is the one unambiguous crack in the fourth wall and it
    sits in the surface a reader is judging.
    """
    doc = _parse(note)
    text = doc.text.lower()
    found = [w for w in _IMPLEMENTATION_WORDS if w.lower() in text]
    assert not found, (
        f"{note.stem} shows implementation vocabulary to a reader: {found}"
    )
