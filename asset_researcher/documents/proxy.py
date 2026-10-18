"""DEF 14A (proxy statement) -> the passages relevant to leadership analysis.

A proxy is the only place several things a PM cares about are disclosed:
executive pay and what it is tied to, board composition and independence,
insider ownership, and the say-on-pay vote. None of it is in the 10-K.

**Why this is density-based rather than structural.** The obvious approach.
locate headings, split into sections, like sections.py does for 10-K Items.
fails on real proxies, verified against Apple's and JPMorgan's 2026 filings:

- Proxies have no mandated section structure, so there is no canonical
  ordering to validate a sequence against.
- JPMorgan repeats a running page header ("Corporate governance | Director
  nominees") on nearly every page: 100+ heading-shaped matches that are
  navigation furniture, not sections.
- The phrase "Summary compensation table" appears in the table of contents,
  twice inside the pay-versus-performance discussion, and once in a glossary
  of abbreviations. The real table is headed "Executive compensation tables
  I. Summary compensation table".
- Compensation tables are full of short lines ("Name", "Year", "Salary")
  that are indistinguishable from headings by shape.

So this does not try to recover section boundaries. It scores overlapping
windows on how densely they carry *content* signals, the vocabulary and
figures that appear in real disclosure rather than in navigation, and
returns the best-scoring windows within a budget. Precise boundaries do not
matter: the output is context for a model that can locate the relevant lines
itself. What matters is not spending the budget on a table of contents.

Offsets are into the proxy's stored text, so citations resolve normally.
"""

from __future__ import annotations

from dataclasses import dataclass

from asset_researcher.documents.density import select_dense_regions

_WINDOW_CHARS = 5_000
_STEP_CHARS = 1_000

# Signal terms are drawn from the body of disclosure, not from headings, so a
# repeated page header scores no better than the prose around it.
_SIGNAL_TERMS: dict[str, tuple[str, ...]] = {
    "compensation": (
        "salary", "bonus", "stock awards", "option awards", "non-equity",
        "incentive plan", "all other compensation", "total compensation",
        "restricted stock unit", "performance share", "vesting", "clawback",
        "severance", "change in control", "pay ratio", "say-on-pay",
        "peer group", "target award", "realized pay", "deferred compensation",
    ),
    "board": (
        "director since", "independent director", "audit committee",
        "compensation committee", "nominating", "principal occupation",
        "other public company", "board meetings", "lead independent",
        "director nominee", "committee membership", "board oversight",
        "director qualification", "board refreshment", "tenure",
    ),
    "ownership": (
        "beneficially owned", "beneficial ownership", "percent of class",
        "shares of common stock", "stock ownership guideline",
        "5% holder", "institutional holder",
    ),
}

_TITLES = {
    "compensation": "Executive Compensation",
    "board": "Board and Governance",
    "ownership": "Beneficial Ownership",
}


@dataclass(frozen=True)
class ProxySection:
    topic: str  # dominant signal group: compensation | board | ownership
    title: str
    start: int  # offset into the proxy's stored text, citations resolve here
    end: int
    text: str

    @property
    def char_count(self) -> int:
        return len(self.text)


def extract_proxy_sections(
    text: str, char_budget: int = 48_000
) -> list[ProxySection]:
    """Highest-signal passages from a proxy statement.

    char_budget approximates the configured token budget (~4 chars/token).
    """
    regions = select_dense_regions(
        text,
        _SIGNAL_TERMS,
        char_budget=char_budget,
        window_chars=_WINDOW_CHARS,
        step_chars=_STEP_CHARS,
    )
    return [
        ProxySection(
            topic=r.topic,
            title=_TITLES[r.topic],
            start=r.start,
            end=r.end,
            text=text[r.start : r.end],
        )
        for r in regions
    ]
