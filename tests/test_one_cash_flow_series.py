"""One free cash flow series per document.

Measured on the shipped ADP note. Its Financials table prints, for
"Free cash flow": FY2022 2,925; FY2023 4,001; FY2024 3,949; FY2025
4,771; FY2026 5,245 - in millions. The chart three sections above,
captioned "Operating cash flow less capital expenditure, by filed
year", prints FY2022 $3.1B; FY2023 $4.2B; FY2024 $4.2B; FY2025 $4.9B;
FY2026 $5.4B.

Every year disagrees, by four to six percent, under one label and one
stated definition. The headline "Filed free cash flow CAGR" is
computed from the second, so it is not reproducible from the table a
reader would check it against - and this is a product whose entire
claim is that the figures reconcile to the filing.

Both compute operating cash flow less the absolute capital
expenditure. They disagree on WHICH filed fact is that year's: the
statements key on the fiscal label and take the last point carrying
it, the history keyed on the period END DATE. A filer who reports a
52/53-week year, restates, or files the same year twice gives those
two rules different answers.

The statements table is the audit trail, so it wins; the history is
made to agree with it by construction rather than by coincidence.
"""

from __future__ import annotations

from asset_researcher.quant.series import MetricPeriod, MetricSeries
from asset_researcher.quant.valuation import free_cash_flow_history


def _series(operating, capex) -> MetricSeries:
    return MetricSeries(
        cik=1,
        sector="",
        series={
            "operating_cash_flow": [
                MetricPeriod(end=e, frame_label=l, value=v, accn="a")
                for e, l, v in operating
            ],
            "capital_expenditures": [
                MetricPeriod(end=e, frame_label=l, value=v, accn="a")
                for e, l, v in capex
            ],
        },
    )


def test_a_year_reported_twice_appears_once():
    """A restatement files the same fiscal year again. Keyed on the end
    date the two land in separate buckets, and the year is counted
    twice - which also moves the first and last points the CAGR is
    measured between."""
    series = _series(
        operating=[
            ("2025-06-30", "FY2025", 1000.0),
            ("2025-06-29", "FY2025", 1050.0),   # restated, a day apart
            ("2026-06-30", "FY2026", 1200.0),
        ],
        capex=[
            ("2025-06-30", "FY2025", 100.0),
            ("2025-06-29", "FY2025", 110.0),
            ("2026-06-30", "FY2026", 120.0),
        ],
    )
    labels = [label for _, label, _ in free_cash_flow_history(series)]
    assert labels == ["FY2025", "FY2026"], labels


def test_the_year_it_keeps_is_the_one_the_statements_print():
    """The statements build {frame_label: value} by iteration, so the
    LAST point carrying a label wins. The history has to make the same
    choice or the two tables disagree."""
    series = _series(
        operating=[
            ("2025-06-30", "FY2025", 1000.0),
            ("2025-06-29", "FY2025", 1050.0),
        ],
        capex=[
            ("2025-06-30", "FY2025", 100.0),
            ("2025-06-29", "FY2025", 110.0),
        ],
    )
    values = [value for _, _, value in free_cash_flow_history(series)]
    assert values == [1050.0 - 110.0]


def test_capex_filed_under_a_different_end_date_still_pairs():
    """The pairing was on the end date, so an operating figure dated
    one day from its own capex dropped the year entirely - and a
    52/53-week filer does exactly that."""
    series = _series(
        operating=[("2026-01-03", "FY2026", 900.0)],
        capex=[("2026-01-02", "FY2026", 100.0)],
    )
    assert [v for _, _, v in free_cash_flow_history(series)] == [800.0]


def test_a_year_with_no_capex_is_still_omitted():
    """Unchanged, and the reason stands: a year with untagged capex has
    unknown free cash flow, not zero capex."""
    series = _series(
        operating=[("2025-06-30", "FY2025", 1000.0),
                   ("2026-06-30", "FY2026", 1200.0)],
        capex=[("2026-06-30", "FY2026", 120.0)],
    )
    assert [l for _, l, _ in free_cash_flow_history(series)] == ["FY2026"]


def test_the_result_stays_in_filed_order():
    series = _series(
        operating=[("2024-06-30", "FY2024", 800.0),
                   ("2025-06-30", "FY2025", 1000.0),
                   ("2026-06-30", "FY2026", 1200.0)],
        capex=[("2024-06-30", "FY2024", 80.0),
               ("2025-06-30", "FY2025", 100.0),
               ("2026-06-30", "FY2026", 120.0)],
    )
    assert [l for _, l, _ in free_cash_flow_history(series)] == [
        "FY2024", "FY2025", "FY2026"
    ]
