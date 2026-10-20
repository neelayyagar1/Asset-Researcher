"""The summary that sits under the headline figures.

The space directly below the stat strip is the most valuable on the page,
and it previously held three provenance notices: how many citations
resolved, how far the model sits from the market, and how old the primary
filing is. All three are true and none is analysis. They now sit with the
disclaimer at the foot of the note, reachable from a line of chips beside
the company name.

What replaces them is a summary composed here rather than written by the
model, which is what lets it carry figures at all. The model is forbidden
from putting a number in prose because a model-written number is
unverifiable; a sentence assembled by the renderer from filed values is
not, so this block can do something neither the tables nor the narrative
can: state the gap in a sentence.

Five lines, in the order an investment committee reads them:

1. **The gap.** What the price requires against what the record delivered.
   The only figure in the note that is neither a filed value nor a target.
2. **The variant view.** A note that agrees with consensus throughout has
   said nothing the price does not already reflect, so if there is no
   variant view the absence is the finding and is stated.
3. **Earnings quality.** The fastest available falsifier of the cash flow
   the whole valuation discounts.
4. **The material divergence.** Management's claim against the filed
   figures, compressed to the assessment.
5. **The nearest catalyst, and what the note could not read.**

Lines two to four reorder by mandate: a capital-preservation reader meets
earnings quality before the variant view, and a reader who can short meets
the divergence first.
"""

from __future__ import annotations

from math import isfinite

from asset_researcher.analysis.report import Report
from asset_researcher.ui import format as fmt
from asset_researcher.ui import components as ui


def _multiple(value: float | None) -> str | None:
    """A multiple, which may legitimately be below one.

    `,.0f` rendered 0.4x as "0 times free cash flow", the same class of
    defect as the "$0B" that `format.scaled_usd` was written to close.
    """
    if value is None or not isfinite(value):
        return None
    return f"{value:,.1f}" if abs(value) < 10 else f"{value:,.0f}"


def _gap_line(report: Report) -> str:
    """What the price requires, against what the filed record delivered."""
    context = report.bundle.cash_context
    implied = report.bundle.implied

    multiple = _multiple(context.multiple_of_fcf) if context else None
    growth = fmt.pct(implied.implied_growth) if implied else None
    cagr = fmt.pct(context.fcf_cagr) if context else None
    years = context.years_observed if context else 0

    if multiple and growth and cagr and years:
        return (
            f"At {multiple} times free cash flow the price requires "
            f"{growth} annual growth. The filed record compounded at "
            f"{cagr} over {ui.plural(years, 'year')}."
        )
    if multiple and cagr and years:
        return (
            f"The market capitalises free cash flow at {multiple} "
            f"times, against {cagr} compounded over "
            f"{ui.plural(years, 'year')} of filed history."
        )
    if multiple and growth:
        return (
            f"At {multiple} times free cash flow the price requires "
            f"{growth} annual growth, against a filed history too short to "
            f"compound."
        )
    return ""


def _variant_line(report: Report) -> str:
    views = report.reconciliation.variant_views
    if not views:
        return (
            "No variant view was identified against the prevailing read, so "
            "this analysis says nothing the price does not already reflect."
        )
    view = views[0]
    return (
        f"Where this departs from consensus, at {view.confidence} "
        f"confidence: {view.our_view}"
    )


def _quality_line(report: Report) -> str:
    """Cash conversion and accruals, which falsify the cash flow fastest."""
    series = report.bundle.series
    if series is None:
        return ""

    from asset_researcher.analysis.statements import build_statement

    rows = {
        row.label: row
        for row in build_statement(series, report.bundle.sector_class)
    }
    conversion = rows.get("Operating cash flow / net income")
    accrual = rows.get("Accrual ratio")
    if conversion is None:
        return ""

    return conversion_sentence(
        conversion.values, accrual.values if accrual is not None else {}
    )


def conversion_sentence(
    values: dict[str, str], accruals: dict[str, str]
) -> str:
    """The cash-conversion sentence, as a pure function of rendered rows.

    Separated from `_quality_line` so it can be tested without standing up
    a whole pipeline. It could not be before, which is why this module's
    most load-bearing sentence had no behavioural test at all and asserted
    a direction it had not measured.

    Both arguments map a period label to an already-rendered cell, in
    filing order, including the unmeasurable ones.
    """
    ordered = list(values)
    measured = [p for p in ordered if values[p] not in _UNMEASURED]
    if not measured:
        return ""

    # Name the period rather than implying the latest one. Filtering to
    # measurable periods and then reporting in the present tense stated a
    # four-year-old figure as current fact: a filer whose last four years
    # were losses reported its one profitable year as though it were the
    # position today, and called five filed years "one year only".
    newest, latest = measured[-1], values[measured[-1]]
    stale = newest != ordered[-1]
    asof = f" in {newest}" if stale else ""

    if len(measured) < 2:
        sentence = (
            f"Cash conversion was {latest} of net income{asof}, the only "
            f"period in which it could be measured"
        )
    else:
        first = values[measured[0]]
        low = min(measured, key=lambda p: _as_number(values[p]))
        delta = _as_number(latest) - _as_number(first)
        # No equality branch here meant a flat series read "up from" its
        # own value. A window is also not described by its endpoints: a
        # series running 130, 60, 40, 55, 130 is flat on the ends and hides
        # exactly the accrual build this line is billed as catching, so the
        # trough is named whenever it sits meaningfully below both.
        if abs(delta) < 0.05:
            movement = f"level with {first} at the start of the filed window"
        else:
            movement = (
                f"{'down' if delta < 0 else 'up'} from {first} across the "
                f"filed window"
            )
        sentence = f"Cash conversion is {latest} of net income{asof}, {movement}"
        trough = _as_number(values[low])
        if low not in (measured[0], measured[-1]) and trough < min(
            _as_number(first), _as_number(latest)
        ) - 10:
            sentence += (
                f", having fallen to {values[low]} in {low}"
            )

    accrual_now = accruals.get(newest, "")
    if accrual_now not in _UNMEASURED:
        sentence += f", with an accrual ratio of {accrual_now} in {newest}"
    return sentence + "."


_UNMEASURED = {"NM", "n.d.", ""}


def _as_number(rendered: str) -> float:
    cleaned = rendered.replace("(", "-").replace(")", "").replace("%", "")
    cleaned = cleaned.replace(",", "").replace("+", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _divergence_line(report: Report) -> str:
    rec = report.reconciliation
    total = len(rec.reconciliations)
    if not total:
        return "No management narrative was reconciled against the filings."

    divergences = rec.divergences
    if not divergences:
        return (
            f"Management's account is corroborated by the filed figures on "
            f"all {ui.plural(total, 'claim')} tested."
        )

    material = next(
        (d for d in divergences if d.materiality == "high"), divergences[0]
    )
    verb = "diverges" if len(divergences) == 1 else "diverge"
    return (
        f"{ui.plural(len(divergences), 'management claim')} of {total} "
        f"{verb} from the filed figures. The material one: "
        f"{material.assessment}"
    )


def _confidence_line(report: Report) -> str:
    """The nearest catalyst, and what the note could not read."""
    rec = report.reconciliation
    verification = report.narrative.verification
    gaps = len(report.bundle.gaps)

    parts: list[str] = []
    if rec.catalysts:
        catalyst = rec.catalysts[0]
        parts.append(f"{catalyst.timeframe}: {catalyst.description}")
    else:
        parts.append("No dated catalyst inside the mandate horizon.")

    located = verification.verified_citations
    total = verification.total_citations
    stamp = f"{located} of {ui.plural(total, 'citation')} located"
    if gaps:
        stamp += f", {ui.plural(gaps, 'gap')} in the source material"
    parts.append(stamp + ".")
    return " ".join(parts)


def summary_lines(report: Report) -> list[str]:
    """The summary, ordered for this reader's mandate."""
    gap = _gap_line(report)
    variant = _variant_line(report)
    quality = _quality_line(report)
    divergence = _divergence_line(report)
    confidence = _confidence_line(report)

    mandate = report.mandate
    body = [variant, quality, divergence]
    if mandate.is_short_capable:
        # The divergence between claim and filing is the trade.
        body = [divergence, variant, quality]
    elif {"quality", "compounder"} & set(mandate.style_tags):
        # For a capital-preservation reader the quality check is the
        # mandate, not a supporting detail.
        body = [quality, variant, divergence]

    return [line for line in [gap, *body, confidence] if line]


def summary_block(report: Report) -> str:
    """The summary as rendered markup."""
    lines = summary_lines(report)
    if not lines:
        return ""
    body = "".join(f"<p>{ui.escape_text(line)}</p>" for line in lines)
    return f'<div class="ar-summary">{body}</div>'
