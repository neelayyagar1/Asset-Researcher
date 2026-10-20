"""Metrics indexed by position combined different fiscal years.

`_at` took each metric's own list and indexed it at -1 or -2. Where a
filer's balance-sheet series runs longer than its income-statement series
(a transition-period stub, a comparative tagged a year late, a change of
fiscal year end), position -1 meant a different year for different
metrics, and every ratio built from the two spanned them.

The measured effect was not marginal: Altman Z printed 3.06 and was
reported as "safe" where the period-aligned score is 2.17, inside
Altman's own grey zone. Working capital changed sign. A live
fiscal-year-end change produced a return on equity of 194%.

A score built from two different years is worse than no score, so a
metric with no fact for the aligned period now returns None and the
ratios depending on it decline to compute.
"""

from __future__ import annotations

from asset_researcher.quant.derived import _at, aligned_labels, compute_derived
from asset_researcher.quant.series import MetricPeriod, MetricSeries


def _period(label: str, value: float) -> MetricPeriod:
    return MetricPeriod(
        end=f"{label[2:]}-12-31", frame_label=label, value=value, accn="a-1"
    )


def _ragged() -> MetricSeries:
    """A balance sheet running one year longer than the income statement,
    which is the shape that triggered this."""
    return MetricSeries(
        cik=1,
        sector="standard",
        series={
            "total_assets": [
                _period("FY2022", 100.0),
                _period("FY2023", 110.0),
                _period("FY2024", 120.0),
            ],
            "net_income": [_period("FY2022", 8.0), _period("FY2023", 9.0)],
            "revenue": [_period("FY2022", 50.0), _period("FY2023", 60.0)],
        },
    )


def test_the_alignment_window_covers_every_period_in_the_series():
    assert aligned_labels(_ragged()) == ["FY2022", "FY2023", "FY2024"]


def test_a_metric_absent_from_the_latest_period_is_not_borrowed_from_an_earlier_one():
    """The defect in one line: net income had no FY2024 fact, and position
    -1 handed back FY2023's, to be divided by FY2024 assets."""
    series = _ragged()
    assert _at(series, "total_assets", -1) == 120.0
    assert _at(series, "net_income", -1) is None


def test_the_previous_period_is_also_resolved_by_label_not_by_position():
    series = _ragged()
    assert _at(series, "total_assets", -2) == 110.0
    assert _at(series, "net_income", -2) == 9.0


def test_a_ratio_spanning_two_years_declines_rather_than_combining_them():
    values = compute_derived(_ragged())
    assert values["net_margin"] is None


def test_alignment_leaves_a_complete_series_untouched():
    """The fix must not cost anything where every metric covers every
    period, which is the ordinary case."""
    series = MetricSeries(
        cik=1,
        sector="standard",
        series={
            "net_income": [_period("FY2023", 9.0), _period("FY2024", 12.0)],
            "revenue": [_period("FY2023", 60.0), _period("FY2024", 100.0)],
        },
    )
    assert _at(series, "net_income", -1) == 12.0
    assert compute_derived(series)["net_margin"] == 0.12


def test_an_index_beyond_the_window_resolves_to_nothing():
    assert _at(_ragged(), "total_assets", -9) is None


# ------------------------------------------------- restatement footing

def test_a_period_mixing_restated_and_original_lines_fails_to_foot():
    """Facts are deduped per concept, keeping the most recently filed value
    per period. A filer restating revenue alone therefore gets restated
    revenue beside original cost of revenue and original gross profit, and
    the three no longer foot. This raised nothing at all before."""
    from asset_researcher.quant.validate import validate

    series = MetricSeries(
        cik=1,
        sector="standard",
        series={
            "revenue": [
                MetricPeriod(
                    end="2023-12-31", frame_label="FY2023", value=300.0,
                    accn="0000-23-restated",
                )
            ],
            "cogs": [
                MetricPeriod(
                    end="2023-12-31", frame_label="FY2023", value=181.5,
                    accn="0000-23-original",
                )
            ],
            "gross_profit": [
                MetricPeriod(
                    end="2023-12-31", frame_label="FY2023", value=148.5,
                    accn="0000-23-original",
                )
            ],
        },
    )
    checks = {i.check for i in validate(series).issues}
    assert "income_statement_footing" in checks


def test_a_period_that_foots_raises_nothing():
    from asset_researcher.quant.validate import validate

    def line(metric: str, value: float) -> tuple[str, list[MetricPeriod]]:
        return metric, [
            MetricPeriod(
                end="2023-12-31", frame_label="FY2023", value=value,
                accn="0000-23-original",
            )
        ]

    series = MetricSeries(
        cik=1,
        sector="standard",
        series=dict(
            [
                line("revenue", 300.0),
                line("cogs", 181.5),
                line("gross_profit", 118.5),
            ]
        ),
    )
    checks = {i.check for i in validate(series).issues}
    assert "income_statement_footing" not in checks
