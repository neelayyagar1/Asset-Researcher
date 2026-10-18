"""Select the highest-signal regions of a document by content density.

Used where a filing's structure cannot be parsed reliably:

- **Proxy statements** have no mandated section structure, repeat page headers
  on every page, and mention key phrases in the contents, the body, and a
  glossary alike.
- **Cross-referenced 10-K Items.** JPMorgan's Item 7 reads "appears on pages
  46-160", the MD&A is in the same document but outside the Item sequence,
  so the splitter cannot reach it.

Both are "find the relevant part" problems rather than "parse the structure"
problems. Scoring overlapping windows on the vocabulary and figures that
appear in substantive disclosure, and penalising the page numbers that
characterise a contents listing, is robust to formatting differences between
filers, needs no per-filer tuning, and degrades gracefully: a slightly wrong
boundary costs a little budget, whereas a wrong section is a wrong report.

Precise boundaries are not the goal. The output is context for a model that
can locate the relevant lines itself; the goal is to not spend the budget on
a table of contents.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_TERM_CAP = 3  # per term, per window, stops one repeated term dominating

# Substantive disclosure carries figures; a contents listing carries page
# numbers.
_MONEY = re.compile(r"\$\s?[\d,]{3,}")
_PERCENT = re.compile(r"\d+(?:\.\d+)?\s?%")
_PAGE_NUMBER_LINE = re.compile(r"^\s*\d{1,3}\s*$", re.MULTILINE)

# Inline-XBRL filings leak machine markup into extracted text, hidden fact
# blocks render as runs of "us-gaap:CreditRiskContractMember 2025-12-31 ...".
# Verified on JPMorgan's 10-K, where an early version of the Item 7A fallback
# selected a 1.3M-character region of exactly this, because taxonomy names
# contain the same vocabulary the signal terms look for. It reads as content
# to a scorer and as noise to a model.
_XBRL_MARKUP = re.compile(r"\b(?:us-gaap|ifrs-full|srt|dei|xbrli):")


# How far a boundary may move to land on a paragraph break. Beyond this the
# window is left alone rather than distorted to find one.
_SNAP_TOLERANCE_CHARS = 600


@dataclass(frozen=True)
class DenseRegion:
    start: int
    end: int
    score: float
    topic: str

    @property
    def char_count(self) -> int:
        return self.end - self.start

    def text_starts_cleanly(self, text: str) -> bool:
        """True when this region opens on a non-whitespace character, i.e.
        it will render as a passage rather than as leading blank space."""
        return bool(text[self.start : self.start + 1].strip())


def _snap_to_paragraph(text: str, start: int, end: int) -> tuple[int, int]:
    """Move a window's edges onto paragraph breaks where one is close by.

    Windows are chosen on a fixed stride, so they routinely open and close
    mid-sentence. That is harmless as model context but not as a *citation
    target*: the click-through-to-source view would show a passage beginning
    partway through a clause, which reads like a bug even when the underlying
    quote is correct.

    Snapping is best-effort. If no break falls within the tolerance the
    original offset stands, a slightly ragged edge is better than a window
    dragged far from the content that scored.
    """
    search_from = max(0, start - _SNAP_TOLERANCE_CHARS)
    para_start = text.rfind("\n\n", search_from, start)
    if para_start != -1:
        start = para_start + 2

    para_end = text.find("\n\n", end, end + _SNAP_TOLERANCE_CHARS)
    if para_end != -1:
        end = para_end

    return start, end


def score_window(chunk: str, signal_terms: dict[str, tuple[str, ...]]) -> tuple[float, str]:
    """Returns (score, dominant topic) for one window of text."""
    lowered = chunk.lower()

    per_topic: dict[str, int] = {}
    for topic, terms in signal_terms.items():
        per_topic[topic] = sum(
            min(lowered.count(term), _TERM_CAP)
            for term in terms
            if term in lowered
        )

    signal = sum(per_topic.values())
    if signal == 0:
        return 0.0, next(iter(signal_terms))

    figures = len(_MONEY.findall(chunk)) + len(_PERCENT.findall(chunk))
    page_numbers = len(_PAGE_NUMBER_LINE.findall(chunk))
    markup = len(_XBRL_MARKUP.findall(chunk))

    # Markup is disqualifying rather than merely penalised: a window thick
    # with taxonomy names contains no prose worth citing, however well its
    # vocabulary happens to score.
    if markup > 20:
        return 0.0, next(iter(signal_terms))

    score = signal + min(figures, 40) * 0.5 - page_numbers * 1.5 - markup * 2.0
    dominant = max(per_topic.items(), key=lambda kv: kv[1])[0]
    return score, dominant


def select_dense_regions(
    text: str,
    signal_terms: dict[str, tuple[str, ...]],
    char_budget: int,
    window_chars: int = 5_000,
    step_chars: int = 1_000,
) -> list[DenseRegion]:
    """Highest-scoring non-overlapping windows, merged and in document order."""
    if not text or len(text) < window_chars:
        return []

    windows: list[DenseRegion] = []
    for start in range(0, len(text) - window_chars + 1, step_chars):
        end = start + window_chars
        score, topic = score_window(text[start:end], signal_terms)
        if score > 0:
            windows.append(DenseRegion(start=start, end=end, score=score, topic=topic))

    if not windows:
        return []

    selected: list[DenseRegion] = []
    consumed = 0
    for window in sorted(windows, key=lambda w: w.score, reverse=True):
        if consumed >= char_budget:
            break
        if any(window.start < s.end and window.end > s.start for s in selected):
            continue
        selected.append(window)
        consumed += window.char_count

    selected.sort(key=lambda w: w.start)

    # Merge adjacent picks so the model sees continuous prose rather than
    # arbitrary slices of the same discussion.
    merged: list[DenseRegion] = []
    for window in selected:
        if merged and window.start <= merged[-1].end:
            previous = merged[-1]
            merged[-1] = DenseRegion(
                start=previous.start,
                end=max(previous.end, window.end),
                score=max(previous.score, window.score),
                topic=previous.topic if previous.score >= window.score else window.topic,
            )
        else:
            merged.append(window)

    # Snap last, so boundaries are tidied once per final region rather than
    # per candidate window, snapping before the merge would let adjacent
    # windows drift apart and stop being detected as adjacent.
    snapped: list[DenseRegion] = []
    for window in merged:
        start, end = _snap_to_paragraph(text, window.start, window.end)
        snapped.append(
            DenseRegion(start=start, end=end, score=window.score, topic=window.topic)
        )
    return snapped
