"""One free cash flow series, one implementation.

The ADP note's Financials row reads FY2026 5,245 while the chart
three sections above, captioned "Operating cash flow less capital
expenditure, by filed year", reads $5.4B. Recovered from the note's
own ratios - Free cash flow / net income 118.8% and Operating cash
flow / net income 123.3% share a denominator - FY2026 operating cash
flow is $5,444m. The chart was plotting OPERATING cash flow, with
capital expenditure never subtracted, under a caption promising it
had been.

`charts.free_cash_flow_history` was a third implementation of a
calculation that already existed twice, and it defaulted a missing
year to `capex.get(label, 0.0)`. That is precisely the defect the
valuation module's docstring records fixing: "A year in which capital
expenditure is not tagged is omitted rather than treated as a year of
zero capex. Defaulting it to zero turned free cash flow into
operating cash flow for that year and said nothing."

The same mistake, in a different file, surviving the fix because the
fix was applied to one copy.

An earlier commit tonight corrected the keying in the valuation copy
and claimed the two tables would now agree by construction. That was
half right: it fixed a real latent fault - restatements and 53-week
years - and did not touch this, because I had assumed one
implementation where there were two.
"""

from __future__ import annotations

from asset_researcher.quant.series import MetricPeriod, MetricSeries
from asset_researcher.quant.valuation import free_cash_flow_history
from asset_researcher.ui import charts


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


def test_the_chart_plots_the_same_numbers_the_tables_print():
    series = _series(
        operating=[("2024-06-30", "FY2024", 4000.0),
                   ("2025-06-30", "FY2025", 4500.0),
                   ("2026-06-30", "FY2026", 5444.0)],
        capex=[("2024-06-30", "FY2024", 400.0),
               ("2025-06-30", "FY2025", 450.0),
               ("2026-06-30", "FY2026", 199.0)],
    )
    expected = [round(v) for _, _, v in free_cash_flow_history(series)]
    plotted = [round(v) for _, _, v in charts.fcf_points(series)]
    assert plotted == expected, (
        f"the chart plots {plotted} where the tables print {expected}"
    )


def test_a_year_without_capex_is_dropped_not_zeroed():
    """`capex.get(label, 0.0)` prints operating cash flow under a
    label that says capital expenditure has been taken off."""
    series = _series(
        operating=[("2025-06-30", "FY2025", 4500.0),
                   ("2026-06-30", "FY2026", 5444.0)],
        capex=[("2026-06-30", "FY2026", 199.0)],
    )
    points = charts.fcf_points(series)
    assert [l for _, l, _ in points] == ["FY2026"]
    assert round(points[0][2]) == 5245


def test_capex_filed_with_either_sign_is_subtracted():
    for sign in (1, -1):
        series = _series(
            operating=[("2025-06-30", "FY2025", 1000.0),
                       ("2026-06-30", "FY2026", 1200.0)],
            capex=[("2025-06-30", "FY2025", 100.0 * sign),
                   ("2026-06-30", "FY2026", 200.0 * sign)],
        )
        assert [round(v) for _, _, v in charts.fcf_points(series)] == [900, 1000]


def test_the_spoken_description_matches_the_bars():
    """The description read `p.value` off the operating-cash-flow
    series while the bars were drawn from the capex-subtracted
    figures. The visible chart was right; its caption and its spoken
    description were operating cash flow under a label saying capital
    expenditure had been taken off - and the caption is what anyone
    reading the file sees."""
    import re

    # Real magnitudes: ADP's FY2026 operating cash flow is $5,444m
    # and its free cash flow $5,245m.
    series = _series(
        operating=[("2025-06-30", "FY2025", 4_500e6),
                   ("2026-06-30", "FY2026", 5_444e6)],
        capex=[("2025-06-30", "FY2025", 450e6),
               ("2026-06-30", "FY2026", 199e6)],
    )
    svg = charts.free_cash_flow_history(series)
    described = re.findall(r"FY20\d\d \$[\d.,]+[BMK]?", svg)
    assert described, f"no described points found in {svg[:300]}"
    assert not any("5.4B" in d for d in described), (
        f"the description still carries operating cash flow: {described}"
    )
    assert any("5.2B" in d for d in described), described
