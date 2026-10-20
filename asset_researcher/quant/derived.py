"""Derived metrics, deterministic arithmetic over the canonical series.

Nothing here calls a model. Every value is computed from XBRL figures the
company filed, which is what lets the report state them as fact rather than
as a claim needing a citation (ARCHITECTURE.md §6, Layer 1).

Missing inputs yield None rather than a guess or a zero: a metric we cannot
compute must be visibly absent, never silently wrong.
"""

from __future__ import annotations

from dataclasses import dataclass

from asset_researcher.quant.capital import net_debt_from_values
from asset_researcher.quant.metrics_config import derived_for_sector
from asset_researcher.quant.series import MetricSeries


@dataclass(frozen=True)
class DerivedValue:
    name: str
    period_label: str
    value: float | None
    unavailable_reason: str | None = None


def aligned_labels(series: MetricSeries) -> list[str]:
    """Every fiscal label present anywhere in the series, oldest first.

    The alignment key. Labels are "FY" plus a four-digit year, so sorting
    them is chronological.
    """
    labels: set[str] = set()
    for points in series.series.values():
        labels.update(p.frame_label for p in points)
    return sorted(labels)


def _at(series: MetricSeries, metric: str, index: int = -1) -> float | None:
    """One metric's value for the period at `index` of the aligned window.

    Indexing each metric's own list independently is what this replaces,
    and it silently combined periods. Any filer whose balance-sheet series
    runs longer than its income-statement series - a transition-period
    stub, a comparative tagged late - had position -1 mean different
    years for different metrics. Measured on such a filer: Altman Z
    printed 3.06, reported as "safe", where the period-aligned score is
    2.17, inside Altman's own grey zone. Working capital flipped sign,
    ROIC moved 1.5 points, and in a live fiscal-year-end change the same
    defect produced a return on equity of 194%.

    Returning None where this metric has no fact for that period is the
    point: a score built from two different years is worse than one that
    declines to compute.
    """
    labels = aligned_labels(series)
    if not labels or abs(index) > len(labels):
        return None
    target = labels[index]
    for period in series.series.get(metric) or ():
        if period.frame_label == target:
            return period.value
    return None


def _safe_div(
    numerator: float | None,
    denominator: float | None,
    *,
    require_positive: bool = False,
    require_positive_numerator: bool = False,
    floor: float | None = None,
) -> float | None:
    """A ratio, or None where the denominator makes it meaningless.

    Guarding only against an exact zero is not enough. A mature company that
    has bought its equity down against a large cash balance has invested
    capital near zero, and the arithmetic then returns a true but useless
    number: invested capital of $0.1B against $10B of earnings reported a
    return on invested capital of 10,000%. These values are handed to the
    model as filed context, where a 10,000% return becomes narrative.

    `require_positive` refuses a negative denominator, which is what makes a
    ratio read backwards: net debt over negative EBITDA returned -6.25x,
    which scans as net cash. `floor` refuses a denominator too small relative
    to the business to carry a ratio at all.

    `require_positive_numerator` is the other half of that, and was
    missing. Interest coverage guarded only its denominator, so operating
    income of -$4.9B over interest of $0.7B printed -7.0x for a company
    with negative EBITDA, which is exactly the "coverage on a loss reads as
    cover" failure the comment at the call site claimed to have prevented.
    A loss does not cover interest a little bit; it does not cover it.
    """
    if numerator is None or denominator is None or denominator == 0:
        return None
    if require_positive and denominator <= 0:
        return None
    if require_positive_numerator and numerator <= 0:
        return None
    if floor is not None and abs(denominator) < abs(floor):
        return None
    return numerator / denominator


def _nopat(g) -> float | None:
    """Operating income after the filer's own effective tax rate.

    Returns None rather than falling back to an assumed rate: a return on
    invested capital computed at a guessed tax rate is a number nobody can
    check, and the point of this layer is that every figure traces to a
    filing.
    """
    operating = g("operating_income")
    pretax, tax = g("pretax_income"), g("income_tax_expense")
    if operating is None or pretax is None or tax is None or pretax <= 0:
        return None
    rate = tax / pretax
    if not 0.0 <= rate < 1.0:
        # A credit, or a rate above 100%, means the year carried something
        # the ratio cannot absorb.
        return None
    return operating * (1 - rate)


def _safe_sub(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return a - b


def _safe_add(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return a + b


def compute_derived(
    series: MetricSeries, index: int = -1, *, sector: str | None = None
) -> dict[str, float | None]:
    """Computes every derived metric that has the inputs available, for the
    period at `index` (default: most recent). Returns None for any metric
    whose inputs are missing."""
    g = lambda m: _at(series, m, index)  # noqa: E731 - local shorthand, reads better here

    ebitda = _safe_add(g("operating_income"), g("depreciation_amortization"))
    fcf = _safe_sub(g("operating_cash_flow"), g("capital_expenditures"))
    # The shared definition: debt less cash *and* the marketable securities
    # the sector permits netting. See quant/capital.py.
    net_debt = net_debt_from_values(
        total_debt=g("total_debt"),
        cash=g("cash_and_equivalents"),
        short_term_investments=g("short_term_investments"),
        long_term_investments=g("long_term_investments"),
        sector_class=series.sector,
    ).value if g("total_debt") is not None else None
    working_capital = _safe_sub(g("current_assets"), g("current_liabilities"))

    invested_capital = None
    if g("total_debt") is not None and g("total_equity") is not None:
        invested_capital = _safe_sub(
            _safe_add(g("total_debt"), g("total_equity")), g("cash_and_equivalents")
        )

    return {
        "ebitda": ebitda,
        "fcf": fcf,
        "fcf_conversion": _safe_div(fcf, g("net_income"), require_positive=True),
        "net_debt": net_debt,
        # Leverage against negative EBITDA reads as net cash. Coverage on a
        # loss reads as cover. Both are reported as unavailable instead.
        "net_debt_to_ebitda": _safe_div(net_debt, ebitda, require_positive=True),
        "interest_coverage": _safe_div(
            g("operating_income"),
            g("interest_expense"),
            require_positive=True,
            require_positive_numerator=True,
        ),
        "working_capital": working_capital,
        # Invested capital within 1% of total assets of zero cannot carry a
        # return: the ratio explodes rather than informing.
        # NOPAT over invested capital, not net income. Net income is after
        # interest and after non-operating items, so dividing it by capital
        # that includes debt measures the capital structure as much as the
        # business. The effective tax rate comes from the filer's own
        # pre-tax income and tax expense; where either is untagged, the
        # return is reported as unavailable rather than silently falling
        # back to net income.
        "roic": _safe_div(
            _nopat(g),
            invested_capital,
            require_positive=True,
            floor=(g("total_assets") or 0.0) * 0.01 or None,
        ),
        "gross_margin": _safe_div(g("gross_profit"), g("revenue")),
        "operating_margin": _safe_div(g("operating_income"), g("revenue")),
        "net_margin": _safe_div(g("net_income"), g("revenue")),
        # Financial-sector.
        #
        # Return on equity, named for what it computes. It was labelled
        # return on tangible common equity, and no tangible adjustment
        # exists anywhere in this codebase: goodwill is not a canonical
        # metric, so there is nothing to deduct. For a bank carrying
        # material goodwill the label overstated the denominator and
        # understated the metric, which is the wrong direction to be wrong
        # about a bank.
        "roe": _safe_div(g("net_income"), g("total_equity"), require_positive=True),
        "efficiency_ratio": _safe_div(
            g("noninterest_expense"),
            _safe_add(g("net_interest_income"), g("noninterest_income")),
        ),
        # Net interest income over total assets. The textbook denominator is
        # average earning assets, which needs a loan and securities balance
        # this taxonomy does not carry, so total assets stands in and the
        # result reads slightly low. Labelled as an approximation wherever
        # it is displayed.
        "nim_on_assets": _safe_div(
            g("net_interest_income"), g("total_assets"), require_positive=True
        ),
        "npl_ratio": _safe_div(g("nonperforming_loans"), g("total_assets")),
        # REIT. Net income plus depreciation, without the gain-on-sale
        # deduction the NAREIT definition carries: gains on property sales
        # are not a canonical metric here, so for a REIT that sold property
        # during the year this runs high. Named and documented for what it
        # computes rather than for the standard it approximates.
        "ffo_before_disposals": _safe_add(
            g("net_income"), g("depreciation_amortization")
        ),
        # Energy
        # Capital expenditure is tagged with either sign depending on the
        # filer, and the raw sign reached this ratio: a filer tagging capex
        # negative reported negative capital intensity, which reads as
        # disposing of plant. Intensity is a magnitude.
        "capex_intensity": _safe_div(
            abs(g("capital_expenditures"))
            if g("capital_expenditures") is not None
            else None,
            g("revenue"),
            require_positive=True,
        ),
    }

    # Gate by sector. `metrics_config.derived_for_sector` has always
    # existed and was never called, so every consumer of this dictionary
    # received metrics the taxonomy declares meaningless for the filer:
    # `reconcile._format_series` hands the whole thing to the model under
    # "Derived (computed, not filed)", which meant the model reasoned over
    # a REIT's capital intensity and free-cash-flow conversion, and over a
    # bank's net debt of $20bn standing against $1.3tn of deposits. The
    # health scores and the statement table were already gated; this layer
    # was the leak.
    #
    # `sector=None` leaves the dictionary ungated, for callers that want
    # every computable value and will gate it themselves.
    if sector is None:
        return values
    permitted = {d.name for d in derived_for_sector(sector)}
    return {k: v for k, v in values.items() if k in permitted}
