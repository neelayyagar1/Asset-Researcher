"""Call B, reconciliation, thesis, and the disconfirming case.

The second model call (ARCHITECTURE.md §6). Runs *without* citations, because it
needs schema-enforced structure and the API rejects both in one request. That
is an acceptable trade here: Call B reasons over material that is already
grounded, the descriptive note carries verified citations, and every figure
comes from filed XBRL, so its job is analysis over vetted inputs rather than
assertion about new ones.

Its output is still constrained: no figure may appear in the prose, and the
renderer inserts filed values. A number written here would be unverifiable.
"""

from __future__ import annotations


from pydantic import BaseModel, Field

from asset_researcher.analysis.bundle import SourceBundle
from asset_researcher.config.prompt_loader import load_prompt
from asset_researcher.analysis.mandate import MandateProfile
from asset_researcher.analysis.narrative import NarrativeResult
from asset_researcher.llm.provider import LLMProvider


class Reconciliation(BaseModel):
    """One narrative-versus-numbers comparison."""

    management_claim: str
    what_the_data_shows: str
    assessment: str  # why the gap matters, or why the data corroborates
    agrees: bool  # True when the figures support the claim
    materiality: str = "medium"  # low | medium | high


class Executive(BaseModel):
    """One named officer, as disclosed in the proxy or an 8-K."""

    name: str
    role: str
    tenure: str  # "since June 2019", or "not disclosed"
    background: str  # prior roles the filings actually state
    note: str = ""  # anything material: recent appointment, departure, transition


class ManagementAssessment(BaseModel):
    """Leadership, pay alignment and ownership.

    The reference pitch carries this as a dedicated section with named
    officers, tenure and prior roles, because who is running the business and
    what they are paid to do is part of the thesis rather than an appendix.
    None of it appears in a 10-K; it comes from the proxy statement.
    """

    executives: list[Executive] = Field(default_factory=list)
    compensation_structure: str = ""
    alignment_assessment: str = ""  # what pay actually rewards
    board_independence: str = ""
    insider_ownership: str = ""
    concerns: list[str] = Field(default_factory=list)


class VariantView(BaseModel):
    """Where the analysis departs from the prevailing market read.

    The reference pitch devotes a full slide to this, laid out as Street View
    against Our View. It is the part of a pitch that carries any actual
    argument: a note that agrees with consensus throughout has not said
    anything a price does not already reflect.
    """

    street_view: str
    our_view: str
    supporting_evidence: str
    confidence: str = "medium"  # low | medium | high


class Catalyst(BaseModel):
    description: str
    timeframe: str
    confirming_evidence: str  # what would show it is happening


class ReconciliationReport(BaseModel):
    financial_trajectory: str
    reconciliations: list[Reconciliation] = Field(default_factory=list)
    valuation_context: str = ""
    variant_views: list[VariantView] = Field(default_factory=list)
    management: ManagementAssessment = Field(default_factory=ManagementAssessment)
    what_would_have_to_be_true: str = ""
    catalysts: list[Catalyst] = Field(default_factory=list)
    bull_case: str = ""
    bear_case: str = ""
    # Mandatory by prompt and enforced below: a report that agrees with
    # management throughout and offers no counter-case is the failure mode
    # this section exists to prevent.
    disconfirming_evidence: str = ""
    questions_for_management: list[str] = Field(default_factory=list)
    data_limitations: str = ""

    @property
    def divergences(self) -> list[Reconciliation]:
        return [r for r in self.reconciliations if not r.agrees]

    @property
    def corroborations(self) -> list[Reconciliation]:
        return [r for r in self.reconciliations if r.agrees]


def _format_series(bundle: SourceBundle) -> str:
    """Filed figures, as a compact table for the model to reason over.

    Numbers appear here, in the *input*, precisely so the model does not
    have to invent any. It is instructed not to echo them into prose; the
    renderer inserts them into the finished report instead.
    """
    if not bundle.series or not bundle.series.series:
        return "No filed financial data available."

    lines = ["Filed figures (USD, from XBRL):"]
    for metric, periods in sorted(bundle.series.series.items()):
        if not periods:
            continue
        rendered = ", ".join(
            f"{p.frame_label}={p.value:,.0f}" for p in periods[-5:]
        )
        lines.append(f"  {metric}: {rendered}")

    if bundle.derived:
        lines.append("")
        lines.append("Derived (computed, not filed):")
        for name, value in sorted(bundle.derived.items()):
            if value is not None:
                lines.append(f"  {name}: {value:,.4g}")

    if bundle.health_scores:
        lines.append("")
        lines.append("Health scores:")
        for score in bundle.health_scores:
            lines.append(f"  {score.label}: {score.display()}")

    return "\n".join(lines)


def _format_comps(bundle: SourceBundle) -> str:
    table = bundle.comps
    if table is None or not table.rows:
        return "No peer comparison available."

    lines = [f"Peer comparison (peer set from {table.peer_source}):"]
    for row in table.rows:
        marker = "SUBJECT " if row.is_subject else "        "
        bits = []
        for name, attr in (
            ("P/E", "pe"),
            ("EV/EBITDA", "ev_to_ebitda"),
            ("P/S", "price_to_sales"),
            ("P/B", "price_to_book"),
        ):
            value = getattr(row, attr)
            bits.append(f"{name}={value:,.1f}" if value is not None else f"{name}=n/a")
        flag = "  [extreme, collapsed earnings]" if row.outlier_multiples else ""
        lines.append(f"  {marker}{row.ticker:6s} " + "  ".join(bits) + flag)

    median = table.median("pe")
    if median is not None:
        lines.append(f"  peer median P/E: {median:,.1f}")
    if table.coverage_note:
        lines.append(f"  caveat: {table.coverage_note}")
    return "\n".join(lines)


def _format_valuation(bundle: SourceBundle) -> str:
    """The cash flow model, its assumptions, and what the price implies.

    The implied expectations are given more weight than the target, because a
    single-stage model on a highly rated company lands far from the market and
    the reverse solve is the defensible half of the analysis.
    """
    if bundle.dcf is None or bundle.dcf_inputs is None:
        return "No valuation model available for this filer."

    lines = ["Discounted cash flow (deterministic, computed from filed data):"]
    for assumption in bundle.dcf_inputs.assumptions():
        lines.append(f"  {assumption.name}: {assumption.display()} ({assumption.basis})")
    lines.append(
        f"  Modelled value per share: ${bundle.dcf.value_per_share:,.2f}"
    )
    lines.append(
        f"  Share of value in the terminal assumption: "
        f"{bundle.dcf.terminal_share_of_value:.0%}"
    )

    if bundle.valuation_cases:
        lines.append("")
        lines.append("Cases (each a full model run at the stated assumptions):")
        for case in bundle.valuation_cases:
            lines.append(
                f"  {case.name}: ${case.value_per_share:,.2f} at "
                f"{case.growth * 100:.1f}% growth and "
                f"{case.discount_rate * 100:.1f}% discount rate "
                f"(probability {case.probability:.0%})"
            )

    if bundle.implied is not None:
        implied = bundle.implied
        lines.append("")
        lines.append("Implied expectations (solve the model backwards from today's price):")
        if implied.implied_growth is not None:
            lines.append(
                f"  The current price requires "
                f"{implied.implied_growth * 100:.1f}% annual free cash flow "
                f"growth over the forecast horizon."
            )
        else:
            lines.append(
                "  No growth rate within a plausible range explains the current "
                "price under these assumptions."
            )
        if implied.implied_discount_rate is not None:
            lines.append(
                f"  Equivalently, a discount rate of "
                f"{implied.implied_discount_rate * 100:.1f}%."
            )
        if implied.caveat:
            lines.append(f"  Caveat: {implied.caveat}")

    return "\n".join(lines)


def _format_gaps(bundle: SourceBundle) -> str:
    if not bundle.gaps:
        return "No known gaps in the source material."
    lines = ["Known gaps, do not paper over these:"]
    for gap in bundle.gaps:
        lines.append(f"  [{gap.severity}] {gap.source}: {gap.reason}")
    return "\n".join(lines)


def build_reconciliation_input(
    bundle: SourceBundle,
    narrative: NarrativeResult,
    mandate: MandateProfile,
) -> str:
    sections = [
        f"Company: {bundle.company_name} ({bundle.ticker})",
        f"Industry: {bundle.display_industry}",
        f"Report date: {bundle.as_of}",
    ]
    if bundle.staleness_note:
        sections.append(bundle.staleness_note)

    sections += [
        "",
        mandate.briefing(),
        "",
        "=== DESCRIPTIVE NOTE (every claim cited to source filings) ===",
        narrative.markdown,
        "",
        "=== FILED FINANCIAL DATA ===",
        _format_series(bundle),
        "",
        _format_comps(bundle),
        "",
        _format_valuation(bundle),
        "",
        _format_gaps(bundle),
        "",
        "Produce the sections described in your instructions. Remember: no "
        "figures in your prose, name the metric and its direction, and the "
        "renderer will insert the filed value.",
    ]
    return "\n".join(sections)


def generate_reconciliation(
    bundle: SourceBundle,
    narrative: NarrativeResult,
    mandate: MandateProfile,
    llm: LLMProvider,
    effort: str = "high",
    max_tokens: int = 16_000,
) -> ReconciliationReport:
    report = llm.complete_structured(
        system=load_prompt("reconciliation.md"),
        user=build_reconciliation_input(bundle, narrative, mandate),
        output_model=ReconciliationReport,
        effort=effort,
        max_tokens=max_tokens,
    )

    # The disconfirming section is the counterweight to every other part of
    # the design, a mandate-aware report that only ever agrees is precisely
    # the echo chamber this architecture exists to avoid. An empty one is a
    # defect, and is surfaced rather than quietly tolerated.
    if not report.disconfirming_evidence.strip():
        report.disconfirming_evidence = (
            # Plain prose, not Markdown. This string is rendered through a
            # component that escapes its input, so the asterisks reached the
            # page as asterisks and only looked right in the Markdown export.
            "Not produced. The model returned no disconfirming evidence for "
            "this report. Treat the analysis above as unchallenged and weigh "
            "it accordingly; this section is mandatory precisely because a "
            "case that survives no scrutiny has not been tested."
        )

    return report
