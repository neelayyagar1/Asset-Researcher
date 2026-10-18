"""Splits 10-K text into its canonical Items (1, 1A, 7, 7A, ...).

**The table-of-contents trap.** Every Item header appears at least twice in a
10-K: once in the table of contents and once at the actual section. Verified
on Apple's FY2025 10-K, 23 items listed between chars 20,651 and 21,961
(the TOC, ~1,300 chars total), then the same 23 again between 24,277 and
234,982 (the body, ~210,000 chars).

Naively taking the first match parses the table of contents as content: every
"section" is one line long, the report is built on nothing, and, worst of
all, it looks like it worked. Citations would point at TOC lines that
genuinely contain the quoted words, so even the verifier would pass.

The discriminator used here is density: a TOC packs many distinct items into
a small span, whereas real sections are spread across the document. That is
structural rather than cosmetic, so it survives the formatting differences
between filers (unlike, say, matching on bold tags or leading whitespace).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from asset_researcher.documents.density import select_dense_regions

# Item headers sit on their own line after extract.py's block-level newlines.
# The title capture is deliberately unbounded: an earlier version capped it at
# 60 chars anchored to end-of-line, which silently failed to match Item 7 in
# both Apple's and JPMorgan's 10-Ks because "Management's Discussion and
# Analysis of Financial Condition and Results of Operations" runs ~85 chars.
# The section simply vanished from the output with no error.
_ITEM_PATTERN = re.compile(
    r"^[ \t]*Item[ \t]+(\d{1,2}[A-C]?)[ \t]*[.:\-—]?[ \t]*(.*)$",
    re.IGNORECASE | re.MULTILINE,
)

# Canonical 10-K item order, used to reject out-of-sequence matches. Realty
# Income's filing contains an "Item 1: Financial Statements" header (10-Q
# style, inside the financial statements) that appears *after* Item 1A and
# would otherwise be mistaken for the Business section.
_CANONICAL_ORDER = [
    "1", "1A", "1B", "1C", "2", "3", "4", "5", "6", "7", "7A", "8",
    "9", "9A", "9B", "9C", "10", "11", "12", "13", "14", "15", "16",
]
_ORDER_INDEX = {item: i for i, item in enumerate(_CANONICAL_ORDER)}


# Below this length a "section" is almost certainly a pointer rather than
# content. Verified on JPMorgan's FY2025 10-K, whose Item 7 is 398 chars
# reading "...appears on pages 46-160", the MD&A is incorporated by
# reference into the annual report rather than written inline.
_CROSS_REFERENCE_MAX_CHARS = 1500

_REFERENCE_MARKERS = ("appears on page", "incorporated by reference", "refer to")


@dataclass(frozen=True)
class Section:
    item: str  # normalized, e.g. "1", "1A", "7A"
    title: str
    start: int  # offset into the source text
    end: int
    text: str

    @property
    def char_count(self) -> int:
        return len(self.text)

    @property
    def is_cross_reference(self) -> bool:
        """True when this section points elsewhere instead of containing
        content. Callers should surface this rather than silently building a
        report on a 400-character MD&A, a thin section that looks populated
        is exactly the kind of quiet degradation this project avoids."""
        if self.char_count > _CROSS_REFERENCE_MAX_CHARS:
            return False
        lowered = self.text.lower()
        return any(marker in lowered for marker in _REFERENCE_MARKERS)


@dataclass(frozen=True)
class _Match:
    item: str
    title: str
    start: int
    line_end: int


def _find_matches(text: str) -> list[_Match]:
    out = []
    for m in _ITEM_PATTERN.finditer(text):
        item = m.group(1).upper()
        title = m.group(2).strip(" .:\u2014-")
        out.append(_Match(item=item, title=title, start=m.start(), line_end=m.end()))
    return out


def _greedy_sequence_from(matches: list[_Match], start_idx: int) -> list[_Match]:
    """Builds a canonically-ordered run of items starting at start_idx.

    Filings contain stray "Item N" headers outside the main sequence.
    cross-references, exhibit indexes, and 10-Q-style headers embedded in
    the financial statements. Requiring monotonic progression through
    _CANONICAL_ORDER discards them without enumerating every case.
    """
    selected = [matches[start_idx]]
    last_rank = _ORDER_INDEX.get(matches[start_idx].item, -1)
    for match in matches[start_idx + 1 :]:
        rank = _ORDER_INDEX.get(match.item)
        if rank is None or rank <= last_rank:
            continue
        selected.append(match)
        last_rank = rank
    return selected


def _select_body_sequence(matches: list[_Match]) -> list[_Match]:
    """Picks the item sequence that covers the most text.

    Separating a table of contents from the body by *proximity* fails on
    real filings: JPMorgan's TOC ends just 67 characters before its body
    begins, so any gap threshold either merges them or splits Apple's body
    incorrectly. Span is the reliable discriminator instead, a TOC lists
    ~23 items inside ~1,500 characters, while the body's same 23 items span
    hundreds of thousands. Evaluating every candidate start and keeping the
    widest-spanning sequence needs no tuned threshold at all.
    """
    if not matches:
        return []
    best: list[_Match] = []
    best_span = -1
    for i in range(len(matches)):
        if _ORDER_INDEX.get(matches[i].item) is None:
            continue
        candidate = _greedy_sequence_from(matches, i)
        span = candidate[-1].start - candidate[0].start
        if span > best_span:
            best, best_span = candidate, span
    return best


_EIGHT_K_ITEM = re.compile(r"^\s*Item\s+\d+\.\d+", re.IGNORECASE | re.MULTILINE)


def extract_8k_content(text: str) -> str:
    """Strip an 8-K's cover page and return the disclosure itself.

    An 8-K opens with an inline-XBRL cover block that extracts as runs of
    "true / NASDAQ / 0000320193 / 2026-04-17", machine metadata with no
    prose in it. Verified on Apple's April 2026 filing: the first 2,973
    characters are that boilerplate, and the disclosure begins at "Item 5.02
    … Tim Cook will transition from his role as Chief Executive Officer to
    Executive Chair".

    Taking the first N characters therefore sent the model pure metadata and
    silently dropped a CEO succession announcement, the single most material
    fact available for that company. Nothing errored; the report was simply
    written without it, and Call B reported an "officer or director change
    whose subject is unknown".

    Returns the text from the first real Item heading. Falls back to the whole
    document when no heading is found, since a filing we cannot parse is
    better sent whole than dropped.
    """
    match = _EIGHT_K_ITEM.search(text)
    if match is None:
        return text
    return text[match.start() :]


def recover_cross_referenced_section(
    text: str, item: str, char_budget: int = 60_000
) -> list[Section]:
    """Locate an Item's content when its header only points elsewhere.

    Verified on JPMorgan's FY2025 10-K: Item 7 is 398 characters reading
    "...appears on pages 46-160". The MD&A is present in the same document.
    around offset 403,000 of 1.45M, but sits outside the Item sequence, so
    the splitter cannot reach it. Without this, every bank's report would be
    built with no MD&A narrative at all: not an error, just a thesis missing
    the section management actually wrote.

    Falls back to content density (documents/density.py) since there is no
    structural marker left to follow. Returns the scoring passages in
    document order, or an empty list when nothing scores, which the caller
    should surface rather than silently continue.

    Each region is returned separately rather than merged into one span. An
    earlier version returned first-region-start to last-region-end, which on
    JPMorgan spanned 1,085,000 characters, the whole document, budget
    ignored, most of it irrelevant.
    """
    signal_terms = _FALLBACK_SIGNALS.get(item)
    if signal_terms is None:
        return []

    regions = select_dense_regions(text, signal_terms, char_budget=char_budget)
    title = f"{_FALLBACK_TITLES.get(item, 'Recovered section')} (recovered by content)"
    return [
        Section(
            item=item,
            title=title,
            start=r.start,
            end=r.end,
            text=text[r.start : r.end],
        )
        for r in regions
    ]


# Vocabulary characteristic of the narrative each Item contains, used only
# when the Item itself is a cross-reference.
_FALLBACK_SIGNALS: dict[str, dict[str, tuple[str, ...]]] = {
    "7": {
        "mdna": (
            "results of operations", "compared with", "compared to",
            "primarily driven by", "primarily due to", "increase in",
            "decrease in", "net revenue", "operating margin", "gross margin",
            "net interest income", "provision for credit losses",
            "efficiency ratio", "liquidity and capital", "cash flows from",
            "critical accounting", "non-interest expense", "year-over-year",
        )
    },
    "7A": {
        "market_risk": (
            "interest rate risk", "value-at-risk", "market risk",
            "foreign exchange risk", "sensitivity analysis", "hypothetical",
            "basis point", "trading portfolio", "hedging",
        )
    },
}

_FALLBACK_TITLES = {
    "7": "Management's Discussion and Analysis",
    "7A": "Quantitative and Qualitative Disclosures About Market Risk",
}


def split_items(text: str) -> dict[str, Section]:
    """Returns item -> Section for the body of the filing. Sections are
    delimited by the next body item header, so each carries its full text."""
    matches = _find_matches(text)
    if not matches:
        return {}

    body = _select_body_sequence(matches)
    if not body:
        return {}

    sections: dict[str, Section] = {}
    for idx, match in enumerate(body):
        end = body[idx + 1].start if idx + 1 < len(body) else len(text)
        sections[match.item] = Section(
            item=match.item,
            title=match.title,
            start=match.start,
            end=end,
            text=text[match.start : end],
        )
    return sections
