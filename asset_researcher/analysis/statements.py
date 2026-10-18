"""The financial summary, in statement order.

This replaced an alphabetical dump of whatever canonical metrics resolved,
which put Capital Expenditures above Cash and Revenue below Operating Income.
No financial statement is ordered alphabetically, and an analyst reading one
finds a line by its position: revenue at the top, then cost, gross profit,
operating income, net income, then cash flow, then the balance sheet. A table
that orders them any other way costs the reader time on every single lookup
even when every figure in it is correct.

Three kinds of row appear, and the distinction is load-bearing:

- **Filed** lines come straight from XBRL and are exactly what the company
  reported.
- **Subtotals** are filed lines the statement itself presents as sums.
- **Derived** lines (growth rates, margins, free cash flow) are arithmetic
  this module performs on filed lines.

Derived rows are marked in the output so the renderer can set them apart.
The guarantee the project rests on is that no figure is model-generated, not
that no figure is computed, and the difference has to be visible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from asset_researcher.quant.series import MetricSeries

# Row kinds, in the order of visual weight the renderer gives them.
SECTION = "section"
LINE = "line"
SUBTOTAL = "subtotal"
DERIVED = "derived"


@dataclass(frozen=True)
class StatementRow:
    label: str
    kind: str
    values: dict[str, str] = field(default_factory=dict)


# --- row specifications --------------------------------------------------
#
# Each entry is (kind, label, spec). The spec says how to get the value:
#   ("filed", metric)                read the canonical metric
#   ("ratio", numerator, denominator) a percentage of the denominator
#   ("growth", metric)               year on year change
#   ("fcf",)                         operating cash flow less capex

_STANDARD: list[tuple[str, str, tuple]] = [
    (SECTION, "Income statement", ()),
    (LINE, "Revenue", ("filed", "revenue")),
    (DERIVED, "Revenue growth", ("growth", "revenue")),
    (LINE, "Cost of goods sold", ("filed", "cogs")),
    (SUBTOTAL, "Gross profit", ("filed", "gross_profit")),
    (DERIVED, "Gross margin", ("ratio", "gross_profit", "revenue")),
    (SUBTOTAL, "Operating income", ("filed", "operating_income")),
    (DERIVED, "Operating margin", ("ratio", "operating_income", "revenue")),
    (LINE, "Depreciation and amortisation", ("filed", "depreciation_amortization")),
    (LINE, "Interest expense", ("filed", "interest_expense")),
    (SUBTOTAL, "Net income", ("filed", "net_income")),
    (DERIVED, "Net margin", ("ratio", "net_income", "revenue")),
    (SECTION, "Cash flow", ()),
    (LINE, "Operating cash flow", ("filed", "operating_cash_flow")),
    (LINE, "Capital expenditure", ("outflow", "capital_expenditures")),
    (DERIVED, "Free cash flow", ("fcf",)),
    (DERIVED, "Free cash flow margin", ("fcf_ratio",)),
    (SECTION, "Balance sheet", ()),
    (LINE, "Cash and equivalents", ("filed", "cash_and_equivalents")),
    (LINE, "Accounts receivable", ("filed", "accounts_receivable")),
    (LINE, "Current assets", ("filed", "current_assets")),
    (LINE, "Current liabilities", ("filed", "current_liabilities")),
    (LINE, "Total debt", ("filed", "total_debt")),
    (LINE, "Total assets", ("filed", "total_assets")),
    (LINE, "Total liabilities", ("filed", "total_liabilities")),
    (SUBTOTAL, "Total equity", ("filed", "total_equity")),
    (LINE, "Diluted shares outstanding", ("shares", "shares_diluted")),
]

# A bank's income statement has no gross profit and no cost of goods, and
# leading with revenue misstates how the business is read. Net interest
# income is the top line that matters.
_FINANCIAL: list[tuple[str, str, tuple]] = [
    (SECTION, "Income statement", ()),
    (LINE, "Revenue", ("filed", "revenue")),
    (DERIVED, "Revenue growth", ("growth", "revenue")),
    (LINE, "Net interest income", ("filed", "net_interest_income")),
    (LINE, "Noninterest income", ("filed", "noninterest_income")),
    (LINE, "Noninterest expense", ("filed", "noninterest_expense")),
    (LINE, "Provision for loan losses", ("filed", "provision_for_loan_losses")),
    (SUBTOTAL, "Net income", ("filed", "net_income")),
    (DERIVED, "Net margin", ("ratio", "net_income", "revenue")),
    (SECTION, "Balance sheet", ()),
    (LINE, "Total deposits", ("filed", "total_deposits")),
    (LINE, "Nonperforming loans", ("filed", "nonperforming_loans")),
    (LINE, "Tier 1 capital", ("filed", "tier1_capital")),
    (LINE, "Cash and equivalents", ("filed", "cash_and_equivalents")),
    (LINE, "Total debt", ("filed", "total_debt")),
    (LINE, "Total assets", ("filed", "total_assets")),
    (SUBTOTAL, "Total equity", ("filed", "total_equity")),
    (DERIVED, "Return on equity", ("ratio", "net_income", "total_equity")),
    (LINE, "Diluted shares outstanding", ("shares", "shares_diluted")),
]

_REIT: list[tuple[str, str, tuple]] = [
    (SECTION, "Income statement", ()),
    (LINE, "Revenue", ("filed", "revenue")),
    (DERIVED, "Revenue growth", ("growth", "revenue")),
    (LINE, "Depreciation and amortisation", ("filed", "depreciation_amortization")),
    (LINE, "Interest expense", ("filed", "interest_expense")),
    (SUBTOTAL, "Net income", ("filed", "net_income")),
    (SECTION, "Cash flow", ()),
    (LINE, "Operating cash flow", ("filed", "operating_cash_flow")),
    (LINE, "Capital expenditure", ("outflow", "capital_expenditures")),
    (SECTION, "Balance sheet", ()),
    (LINE, "Real estate investments, at cost", ("filed", "real_estate_investments")),
    (LINE, "Cash and equivalents", ("filed", "cash_and_equivalents")),
    (LINE, "Total debt", ("filed", "total_debt")),
    (LINE, "Total assets", ("filed", "total_assets")),
    (SUBTOTAL, "Total equity", ("filed", "total_equity")),
    (DERIVED, "Debt to total assets", ("ratio", "total_debt", "total_assets")),
    (LINE, "Diluted shares outstanding", ("shares", "shares_diluted")),
]

_ORDERS = {
    "standard": _STANDARD,
    "energy": _STANDARD,
    "biotech": _STANDARD,
    "financial": _FINANCIAL,
    "reit": _REIT,
}


def statement_order(sector_class: str) -> list[tuple[str, str, tuple]]:
    return _ORDERS.get(sector_class, _STANDARD)


# --- formatting ----------------------------------------------------------
#
# Dollars in millions with no decimal, which is how a statement of this scale
# is published: at Apple's revenue a decimal place is six significant figures
# of false precision. Negatives in parentheses, the published convention,
# because a leading minus sign is lost in a column of numbers.

# Three distinct tokens, because they mean three different things and one
# token for all of them makes a claim about the company that is not true.
# The report told a reader "Interest expense NM" for Apple, which reports it;
# the line was simply not tagged in those years. NM means the ratio has no
# meaning. ND means the company did not disclose it, or did not tag it.
NM = "NM"  # a ratio whose denominator is negative, zero or vanishing
ND = "n.d."  # not disclosed, or not tagged in this period
BLANK = ""  # no prior period against which to compute a change


def _round(value: float, places: int) -> Decimal:
    """Half away from zero, the convention in published statements.

    Python rounds half to even, so a filed $12,500,000 renders as 12 while
    $13,500,000 renders as 14. Both are defensible as arithmetic and neither
    matches the filing a reader is checking the table against.
    """
    quantum = Decimal(1).scaleb(-places)
    return Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP)


def _millions(value: float | None) -> str:
    if value is None:
        return ND
    scaled = _round(value / 1e6, 0)
    if scaled < 0:
        return f"({abs(scaled):,.0f})"
    return f"{scaled:,.0f}"


def _count_millions(value: float | None) -> str:
    """Share counts, which are already in units rather than dollars."""
    if value is None:
        return ND
    return f"{_round(value / 1e6, 0):,.0f}"


def _percent(value: float | None) -> str:
    if value is None:
        return NM
    scaled = _round(value * 100, 1)
    if scaled < 0:
        return f"({abs(scaled):,.1f}%)"
    return f"{scaled:,.1f}%"


def _signed_percent(value: float | None) -> str:
    """Growth rates carry an explicit sign: the direction is the point."""
    if value is None:
        return NM
    scaled = _round(value * 100, 1)
    if scaled < 0:
        return f"({abs(scaled):,.1f}%)"
    return f"+{scaled:,.1f}%"


def periods_of(series: MetricSeries, limit: int = 5) -> list[str]:
    """The most recent fiscal periods present anywhere in the series.

    Sorted by label, which is safe because labels are FY plus a four-digit
    year, and truncated to the most recent five: a wider table does not fit
    a page and the sixth year is rarely what a reader is checking.
    """
    labels: set[str] = set()
    for points in series.series.values():
        labels.update(p.frame_label for p in points)
    return sorted(labels)[-limit:]


def build_statement(
    series: MetricSeries | None, sector_class: str = "standard", limit: int = 5
) -> list[StatementRow]:
    """The financial summary as ordered rows, one column per period.

    A row whose every value is missing is dropped: a filer that does not tag
    accounts receivable should not carry an empty row for it. A section
    heading whose rows all dropped is dropped with them.
    """
    if series is None or not series.series:
        return []

    periods = periods_of(series, limit)
    if not periods:
        return []

    lookup = {
        metric: {p.frame_label: p.value for p in points}
        for metric, points in series.series.items()
    }

    def filed(metric: str, period: str) -> float | None:
        return lookup.get(metric, {}).get(period)

    rows: list[StatementRow] = []
    for kind, label, spec in statement_order(sector_class):
        if kind == SECTION:
            rows.append(StatementRow(label=label, kind=SECTION))
            continue

        values: dict[str, str] = {}
        present = False

        for index, period in enumerate(periods):
            rendered, has_value = _evaluate(
                spec, period, periods, index, filed
            )
            values[period] = rendered
            present = present or has_value

        if present:
            rows.append(StatementRow(label=label, kind=kind, values=values))

    return _drop_empty_sections(rows)


def _evaluate(
    spec: tuple, period: str, periods: list[str], index: int, filed
) -> tuple[str, bool]:
    """One cell: its rendered text, and whether it holds a real value."""
    how = spec[0]

    if how == "filed":
        value = filed(spec[1], period)
        return _millions(value), value is not None

    if how == "outflow":
        # Capital expenditure is a use of cash. Printed unsigned directly
        # above a free cash flow line computed by subtracting it, the block
        # does not foot and the reader has to work out which way it goes.
        value = filed(spec[1], period)
        if value is None:
            return ND, False
        return _millions(-abs(value)), True

    if how == "shares":
        value = filed(spec[1], period)
        return _count_millions(value), value is not None

    if how == "ratio":
        numerator, denominator = filed(spec[1], period), filed(spec[2], period)
        if numerator is None or denominator is None:
            return ND, False
        if denominator <= 0:
            return NM, False
        return _percent(numerator / denominator), True

    if how == "growth":
        if index == 0:
            # No prior period inside the window. Left blank rather than
            # marked: there is nothing to report, and "NM" would assert that
            # a growth rate exists and is not meaningful.
            return BLANK, False
        current = filed(spec[1], period)
        prior = filed(spec[1], periods[index - 1])
        if current is None or prior is None:
            return ND, False
        if prior <= 0:
            return NM, False
        return _signed_percent(current / prior - 1), True

    if how == "fcf":
        value = _free_cash_flow(filed, period)
        return _millions(value), value is not None

    if how == "fcf_ratio":
        value = _free_cash_flow(filed, period)
        revenue = filed("revenue", period)
        if value is None or revenue is None:
            return ND, False
        if revenue <= 0:
            return NM, False
        return _percent(value / revenue), True

    return ND, False


def _free_cash_flow(filed, period: str) -> float | None:
    """Operating cash flow less capital expenditure.

    Capex is tagged as a positive magnitude by some filers and a negative
    cash movement by others, so its absolute value is subtracted. Taking the
    tagged sign at face value adds capex to cash flow for roughly half of
    all filers, which doubles the number and looks entirely plausible.
    """
    operating = filed("operating_cash_flow", period)
    capex = filed("capital_expenditures", period)
    if operating is None or capex is None:
        # A year with no tagged capex is a year whose free cash flow is
        # unknown, not a year of zero capex. Defaulting it printed operating
        # cash flow under the label "Free cash flow", which overstated it by
        # the whole capital programme.
        return None
    return operating - abs(capex)


def _drop_empty_sections(rows: list[StatementRow]) -> list[StatementRow]:
    kept: list[StatementRow] = []
    for index, row in enumerate(rows):
        if row.kind != SECTION:
            kept.append(row)
            continue
        following = rows[index + 1 :]
        has_content = any(
            r.kind != SECTION for r in _until_next_section(following)
        )
        if has_content:
            kept.append(row)
    return kept


def _until_next_section(rows: list[StatementRow]) -> list[StatementRow]:
    out = []
    for row in rows:
        if row.kind == SECTION:
            break
        out.append(row)
    return out
