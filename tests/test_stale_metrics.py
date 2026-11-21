"""A metric series can be fully populated and still be years out of date.

Measured on real filers with a working API key: Lumen's capital
expenditure resolves to a concept the company stopped tagging after
FY2013, and ADP's total debt to one abandoned after FY2011. Both series
carry six annual points, so nothing downstream objected. The valuation
pairs operating cash flow with capital expenditure on matching period
end dates, which means Lumen's discounted cash flow was built on
pre-2014 free cash flow for a company whose business has since been
rebuilt - and that is where the sample note's -91% headline target came
from. ADP's net-debt bridge used $37m against real debt near $3bn.

The existing completeness check only guarded revenue and net income, so
both of these passed clean.
"""

from __future__ import annotations

from asset_researcher.quant.series import MetricPeriod, MetricSeries
from asset_researcher.quant.validate import validate


def _series(**metrics: list[tuple[str, float]]) -> MetricSeries:
    s = MetricSeries(cik=1, sector="standard")
    for name, points in metrics.items():
        s.series[name] = [
            MetricPeriod(end=end, frame_label=f"FY{end[:4]}", value=val, accn="x")
            for end, val in points
        ]
    return s


def _current() -> MetricSeries:
    return _series(
        revenue=[("2023-12-31", 100e9), ("2024-12-31", 110e9), ("2025-12-31", 120e9)],
        net_income=[("2023-12-31", 9e9), ("2024-12-31", 10e9), ("2025-12-31", 11e9)],
        operating_cash_flow=[
            ("2023-12-31", 20e9), ("2024-12-31", 21e9), ("2025-12-31", 22e9)
        ],
        capital_expenditures=[
            ("2023-12-31", 5e9), ("2024-12-31", 5.2e9), ("2025-12-31", 5.4e9)
        ],
        total_debt=[("2023-12-31", 30e9), ("2024-12-31", 31e9), ("2025-12-31", 32e9)],
        total_equity=[("2023-12-31", 40e9), ("2024-12-31", 44e9), ("2025-12-31", 48e9)],
        total_assets=[("2023-12-31", 70e9), ("2024-12-31", 75e9), ("2025-12-31", 80e9)],
        total_liabilities=[
            ("2023-12-31", 30e9), ("2024-12-31", 31e9), ("2025-12-31", 32e9)
        ],
    )


def test_a_current_series_is_not_flagged():
    assert validate(_current()).ok


def test_capital_expenditure_that_stopped_twelve_years_ago_is_an_error():
    """Lumen's shape: cash flow current, capex ending 2013."""
    s = _current()
    s.series["capital_expenditures"] = [
        MetricPeriod("2011-12-31", "FY2011", 3.0e9, "x"),
        MetricPeriod("2012-12-31", "FY2012", 3.1e9, "x"),
        MetricPeriod("2013-12-31", "FY2013", 3.0e9, "x"),
    ]
    result = validate(s)
    assert not result.ok
    text = " ".join(str(getattr(i, "message", i)) for i in result.issues)
    assert "capital_expenditures" in text
    assert "FY2013" in text or "2013" in text


def test_total_debt_that_stopped_fourteen_years_ago_is_an_error():
    """ADP's shape: a debt tag abandoned after FY2011."""
    s = _current()
    s.series["total_debt"] = [
        MetricPeriod("2009-06-30", "FY2009", 40e6, "x"),
        MetricPeriod("2010-06-30", "FY2010", 38e6, "x"),
        MetricPeriod("2011-06-30", "FY2011", 37e6, "x"),
    ]
    result = validate(s)
    assert not result.ok
    text = " ".join(str(getattr(i, "message", i)) for i in result.issues)
    assert "total_debt" in text


def test_a_metric_one_period_behind_is_not_flagged():
    """A filer can legitimately file a line late. The check is for a
    series that stopped years ago, not for one period of lag."""
    s = _current()
    s.series["total_debt"] = s.series["total_debt"][:-1]
    assert validate(s).ok


# ------------------------------------------------- the model must refuse

def test_the_discounted_cash_flow_refuses_a_stale_capex_series():
    """The point of the whole exercise.

    Validation reporting the defect is not enough: the model still
    produced a target, and a target is what a reader remembers. Refusing
    reuses the path a REIT and a bank already take, so the note prints
    NM and says it declined.
    """
    from asset_researcher.quant.valuation import derive_dcf_inputs

    s = _current()
    assert derive_dcf_inputs(s, shares_outstanding=1e9) is not None, (
        "a current series must still produce a model, or this test proves "
        "nothing about staleness"
    )

    s.series["capital_expenditures"] = [
        MetricPeriod("2011-12-31", "FY2011", 3.0e9, "x"),
        MetricPeriod("2012-12-31", "FY2012", 3.1e9, "x"),
        MetricPeriod("2013-12-31", "FY2013", 3.0e9, "x"),
    ]
    assert derive_dcf_inputs(s, shares_outstanding=1e9) is None, (
        "a capex series that stopped in FY2013 must not produce a "
        "discounted cash flow for a filer reporting through FY2025"
    )


def test_an_instant_a_day_off_the_period_end_is_not_counted_as_a_period():
    """Balance-sheet facts are instants and income facts are durations,
    and for some filers they land a day apart within the same fiscal
    year. Indexing raw end dates made every such pair an extra slot, so
    a line exactly one year late - which this check tolerates - counted
    as two behind, was reported as abandoned, and had its valuation
    refused. Lag is counted in fiscal periods for that reason.
    """
    s = _current()
    for metric in ("total_assets", "total_liabilities", "total_equity"):
        s.series[metric] = [
            MetricPeriod(end.replace("-31", "-30"), label, value, "x")
            for end, label, value in (
                (p.end, p.frame_label, p.value) for p in s.series[metric]
            )
        ]
    # One fiscal year late, which is ordinary and must be tolerated.
    s.series["total_debt"] = s.series["total_debt"][:-1]

    result = validate(s)
    assert result.ok, (
        "a one-year-late line was reported as abandoned because other "
        f"metrics' instants fell a day earlier: "
        f"{[i.message for i in result.issues]}"
    )


def test_a_stale_debt_tag_refuses_the_equity_bridge():
    """ADP's shape, which the first version of this guard missed.

    The model discounts cash flow to an enterprise value and bridges to
    equity across net debt. Operating cash flow and capital expenditure
    were guarded; total debt was not - so ADP, whose debt concept stops
    at FY2011 at $37m against FY2026 cash of $4.23bn, produced a bridge
    that added about $4.4bn of net cash the company does not have, and
    the note led with a per-share target built on it.

    The figure a reader acts on is the per-share target, and it is the
    bridge that produces it, so a stale bridge refuses the model.
    """
    from asset_researcher.quant.valuation import derive_dcf_inputs

    s = _current()
    assert derive_dcf_inputs(s, shares_outstanding=1e9) is not None

    s.series["total_debt"] = [
        MetricPeriod("2010-12-31", "FY2010", 38e6, "x"),
        MetricPeriod("2011-12-31", "FY2011", 37e6, "x"),
    ]
    assert derive_dcf_inputs(s, shares_outstanding=1e9) is None, (
        "a debt series that stopped in FY2011 must not produce an equity "
        "value for a filer reporting through FY2025"
    )
