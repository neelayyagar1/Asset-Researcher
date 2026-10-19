"""Assembles every source a report draws on into one object.

The bundle is the boundary between gathering and reasoning. Everything above
it is deterministic. HTTP, XBRL arithmetic, text extraction, and everything
below it is the model. Keeping that seam explicit means a report can be
regenerated from a stored bundle without re-fetching, and a disputed number
can be traced to the source that produced it without re-running anything.

Two properties matter more than completeness:

1. **Nothing is silently missing.** Every source that fails to load is
   recorded in `gaps` with a reason. A report built on a filing whose MD&A
   could not be found should say so; the alternative is a confident-looking
   thesis with a hole in it.
2. **Every text passage carries its document id and offsets**, so a citation
   the model returns can be resolved against the exact stored text it was
   given (documents/store.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from asset_researcher.quant.comps import CompsTable
from asset_researcher.quant.scores import ScoreResult
from asset_researcher.quant.series import MetricSeries
from asset_researcher.quant.valuation import (
    CashFlowContext,
    DcfInputs,
    DcfResult,
    ImpliedExpectations,
    ValuationCase,
)
from asset_researcher.quant.validate import ValidationResult
from asset_researcher.sources.finnhub import NewsItem, Quote


@dataclass(frozen=True)
class SourcePassage:
    """A span of text the model may cite.

    doc_id + (start, end) resolve against the stored document, so a citation
    is verifiable rather than merely plausible.
    """

    doc_id: str
    source_url: str
    form: str
    filing_date: str
    label: str  # human-readable, e.g. "Item 1A. Risk Factors"
    tier: str  # A authoritative | B primary | C secondary
    start: int
    end: int
    text: str

    @property
    def char_count(self) -> int:
        return len(self.text)


@dataclass(frozen=True)
class Gap:
    """A source that was expected but is absent, with why.

    Surfaced in the report rather than swallowed: an analyst reading a thesis
    needs to know the MD&A was a cross-reference that could not be recovered,
    or that the company has never filed a proxy.
    """

    source: str
    reason: str
    severity: str = "warning"  # "warning" | "error"


@dataclass
class SourceBundle:
    # --- identity -------------------------------------------------------
    ticker: str
    cik: int
    company_name: str
    sector_class: str  # statement model: standard | financial | reit | ...
    display_industry: str  # what a reader sees, e.g. "Technology (Electronic Computers)"
    as_of: str  # ISO date the bundle was assembled, every report shows this

    # --- quantitative (deterministic, never model-generated) -------------
    series: MetricSeries | None = None
    derived: dict[str, float | None] = field(default_factory=dict)
    health_scores: list[ScoreResult] = field(default_factory=list)
    validation: ValidationResult | None = None
    quote: Quote | None = None
    market_cap: float | None = None
    comps: CompsTable | None = None

    # Valuation is deterministic arithmetic over assumptions with a stated
    # basis, not a generated figure. None when the filings do not support a
    # cash flow model, which is the correct answer for some filers.
    dcf_inputs: DcfInputs | None = None
    dcf: DcfResult | None = None
    valuation_cases: list[ValuationCase] = field(default_factory=list)
    implied: ImpliedExpectations | None = None
    cash_context: CashFlowContext | None = None

    # --- qualitative (citable text) --------------------------------------
    passages: list[SourcePassage] = field(default_factory=list)
    news: list[NewsItem] = field(default_factory=list)

    # --- provenance -------------------------------------------------------
    filing_dates: dict[str, str] = field(default_factory=dict)  # form -> date
    gaps: list[Gap] = field(default_factory=list)

    def add_gap(self, source: str, reason: str, severity: str = "warning") -> None:
        self.gaps.append(Gap(source=source, reason=reason, severity=severity))

    def passages_for(self, *labels: str) -> list[SourcePassage]:
        wanted = set(labels)
        return [p for p in self.passages if p.label in wanted]

    @property
    def total_passage_chars(self) -> int:
        return sum(p.char_count for p in self.passages)

    @property
    def has_errors(self) -> bool:
        return any(g.severity == "error" for g in self.gaps)

    @property
    def staleness_note(self) -> str | None:
        """How old the primary filing is.

        A 10-K can be eleven months old. A report that reads as current while
        resting on stale disclosure is the fastest way to lose a reader's
        trust, so the age is stated rather than left to be inferred.
        """
        filed = self.filing_dates.get("10-K")
        if not filed:
            return None
        try:
            days = (date.fromisoformat(self.as_of) - date.fromisoformat(filed)).days
        except ValueError:
            return None
        if days < 0:
            return None
        months = days // 30
        if months < 1:
            unit = "day" if days == 1 else "days"
            return f"Primary filing (10-K) filed {filed}, {days} {unit} ago."
        unit = "month" if months == 1 else "months"
        return (
            f"Primary filing (10-K) filed {filed}, approximately {months} "
            f"{unit} ago. Developments since then appear only via 8-K "
            f"filings and news."
        )
