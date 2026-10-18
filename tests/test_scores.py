"""Health scores. The sector-gating tests here guard the failure mode the
design calls fatal: a confident Altman Z on a bank. Everything else in the
report can be imperfect; a plausible-looking wrong number cannot."""

from asset_researcher.quant.derived import compute_derived
from asset_researcher.quant.scores import ScoreStatus, compute_health_scores
from asset_researcher.quant.series import MetricPeriod, MetricSeries


def _industrial_series() -> MetricSeries:
    """Two years of Apple-shaped data, enough for the two-year scores."""
    s = MetricSeries(cik=320193, sector="standard")
    data = {
        "revenue": [391.0e9, 416.2e9],
        "gross_profit": [180.7e9, 195.2e9],
        "operating_income": [123.2e9, 133.1e9],
        "net_income": [93.7e9, 112.0e9],
        "total_assets": [365.0e9, 359.2e9],
        "total_liabilities": [308.0e9, 285.5e9],
        "total_equity": [57.0e9, 73.7e9],
        "current_assets": [153.0e9, 148.0e9],
        "current_liabilities": [176.4e9, 165.6e9],
        "retained_earnings": [-19.15e9, -14.26e9],
        "operating_cash_flow": [118.3e9, 111.5e9],
        "capital_expenditures": [9.4e9, 12.7e9],
        "depreciation_amortization": [11.4e9, 11.6e9],
        "accounts_receivable": [33.4e9, 39.3e9],
        "shares_diluted": [15.4e9, 14.9e9],
        "total_debt": [106.6e9, 101.7e9],
    }
    for metric, values in data.items():
        s.series[metric] = [
            MetricPeriod("2024-09-28", "FY2024", values[0], "x"),
            MetricPeriod("2025-09-27", "FY2025", values[1], "x"),
        ]
    return s


def test_financial_sector_refuses_all_three_scores():
    """The single most important test in the suite. Altman Z and Piotroski F
    assume a non-financial balance sheet; on a bank they produce confident
    garbage. They must decline, not compute."""
    s = _industrial_series()
    results = {r.name: r for r in compute_health_scores(s, "financial", 7.0e11)}

    for name in ("altman_z", "piotroski_f", "beneish_m"):
        assert results[name].status is ScoreStatus.NOT_MEANINGFUL
        assert results[name].value is None
        assert results[name].display() == "not meaningful for this sector"


def test_inapplicable_scores_are_reported_not_omitted():
    """A reader must be able to tell 'inapplicable' from 'forgotten'."""
    results = compute_health_scores(_industrial_series(), "financial", 7.0e11)
    assert len(results) == 3


def test_altman_z_computes_for_industrial():
    results = {r.name: r for r in compute_health_scores(_industrial_series(), "standard", 3.4e12)}
    z = results["altman_z"]
    assert z.status is ScoreStatus.OK
    assert z.value > 2.99
    assert z.band == "safe"  # Apple is not a distress candidate


def test_piotroski_f_computes_and_bands():
    results = {r.name: r for r in compute_health_scores(_industrial_series(), "standard", 3.4e12)}
    f = results["piotroski_f"]
    assert f.status is ScoreStatus.OK
    assert 0 <= f.value <= 9


def test_altman_z_without_market_cap_reports_insufficient_not_zero():
    """Market cap comes from a separate source (Finnhub). If it's missing the
    score must decline rather than silently substituting zero, which would
    drag Z down and imply distress."""
    results = {r.name: r for r in compute_health_scores(_industrial_series(), "standard", None)}
    z = results["altman_z"]
    assert z.status is ScoreStatus.INSUFFICIENT_DATA
    assert z.value is None
    assert "market_cap" in z.detail


def test_scores_decline_on_single_year_of_data():
    s = MetricSeries(cik=1, sector="standard")
    s.series["net_income"] = [MetricPeriod("2025-09-27", "FY2025", 112.0e9, "x")]
    s.series["total_assets"] = [MetricPeriod("2025-09-27", "FY2025", 359.2e9, "x")]
    s.series["operating_cash_flow"] = [MetricPeriod("2025-09-27", "FY2025", 111.5e9, "x")]
    results = {r.name: r for r in compute_health_scores(s, "standard", 3.4e12)}
    assert results["piotroski_f"].status is ScoreStatus.INSUFFICIENT_DATA


def test_derived_margins_match_hand_computation():
    d = compute_derived(_industrial_series())
    assert abs(d["gross_margin"] - (195.2 / 416.2)) < 1e-6
    assert abs(d["operating_margin"] - (133.1 / 416.2)) < 1e-6
    assert abs(d["net_margin"] - (112.0 / 416.2)) < 1e-6


def test_derived_returns_none_for_missing_inputs_not_zero():
    """A metric we cannot compute must be visibly absent. Returning 0.0 would
    render as a real value and be indistinguishable from a true zero."""
    s = MetricSeries(cik=1, sector="standard")
    s.series["revenue"] = [MetricPeriod("2025-09-27", "FY2025", 416.2e9, "x")]
    d = compute_derived(s)
    assert d["gross_margin"] is None
    assert d["ebitda"] is None
    assert d["roic"] is None


def test_derived_handles_zero_denominator_without_raising():
    s = MetricSeries(cik=1, sector="standard")
    s.series["revenue"] = [MetricPeriod("2025-09-27", "FY2025", 0.0, "x")]
    s.series["gross_profit"] = [MetricPeriod("2025-09-27", "FY2025", 100.0, "x")]
    assert compute_derived(s)["gross_margin"] is None
