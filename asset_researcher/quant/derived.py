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
from asset_researcher.quant.series import MetricSeries


@dataclass(frozen=True)
class DerivedValue:
    name: str
    period_label: str
    value: float | None
    unavailable_reason: str | None = None


def _at(series: MetricSeries, metric: str, index: int) -> float | None:
    periods = series.series.get(metric)
    if not periods or abs(index) > len(periods):
        return None
    return periods[index].value


def _safe_div(
    numerator: float | None,
    denominator: float | None,
    *,
    require_positive: bool = False,
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
    """
    if numerator is None or denominator is None or denominator == 0:
        return None
    if require_positive and denominator <= 0:
        return None
    if floor is not None and abs(denominator) < abs(floor):
        return None
    return numerator / denominator


def _safe_sub(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return a - b


def _safe_add(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return a + b


def compute_derived(series: MetricSeries, index: int = -1) -> dict[str, float | None]:
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
            g("operating_income"), g("interest_expense"), require_positive=True
        ),
        "working_capital": working_capital,
        # Invested capital within 1% of total assets of zero cannot carry a
        # return: the ratio explodes rather than informing.
        "roic": _safe_div(
            g("net_income"),
            invested_capital,
            require_positive=True,
            floor=(g("total_assets") or 0.0) * 0.01 or None,
        ),
        "gross_margin": _safe_div(g("gross_profit"), g("revenue")),
        "operating_margin": _safe_div(g("operating_income"), g("revenue")),
        "net_margin": _safe_div(g("net_income"), g("revenue")),
        # Financial-sector
        "rotce": _safe_div(g("net_income"), g("total_equity")),
        "efficiency_ratio": _safe_div(
            g("noninterest_expense"),
            _safe_add(g("net_interest_income"), g("noninterest_income")),
        ),
        "nim": _safe_div(g("net_interest_income"), g("total_assets")),
        "npl_ratio": _safe_div(g("nonperforming_loans"), g("total_assets")),
        # REIT
        "ffo": _safe_add(g("net_income"), g("depreciation_amortization")),
        # Energy
        "capex_intensity": _safe_div(g("capital_expenditures"), g("revenue")),
    }
