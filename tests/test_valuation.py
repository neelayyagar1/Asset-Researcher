"""DCF, cases, sensitivity and implied expectations."""

from __future__ import annotations

import pytest

from asset_researcher.quant.series import MetricPeriod, MetricSeries
from asset_researcher.quant.valuation import (
    NM,
    DcfInputs,
    build_cases,
    derive_dcf_inputs,
    implied_expectations,
    probability_weighted_target,
    run_dcf,
    sensitivity_grid,
)


def _inputs(**kw) -> DcfInputs:
    base = dict(
        base_fcf=100e9, fcf_growth=0.05,
        discount_rate=0.09, terminal_growth=0.025, forecast_years=5,
        net_debt=50e9, shares_outstanding=15e9,
    )
    base.update(kw)
    return DcfInputs(**base)


def _series(**metrics) -> MetricSeries:
    """Metrics aligned so every one ends at the same, latest period.

    Each metric used to be labelled from FY2020 forwards over its own
    values, so a metric given one value landed in the OLDEST year while a
    metric given three ended in the newest. Nothing downstream resolves
    periods by position any more, so such a fixture described a filer
    that stopped reporting its balance sheet years before its income
    statement, and the latest period then had no debt in it.
    """
    series = MetricSeries(cik=1, sector="standard")
    span = max((len(v) for v in metrics.values()), default=0)
    for name, values in metrics.items():
        offset = span - len(values)
        series.series[name] = [
            MetricPeriod(
                f"202{i + offset}-12-31", f"FY202{i + offset}", v, "a"
            )
            for i, v in enumerate(values)
        ]
    return series


# --- DCF arithmetic -----------------------------------------------------


def test_discounting_matches_hand_calculation():
    """One year, no terminal ambiguity: FCF grows once, discounts once."""
    result = run_dcf(_inputs(forecast_years=1, fcf_growth=0.0,
                             terminal_growth=0.0, net_debt=0.0))
    year_one = 100e9 / 1.09
    terminal = (100e9 / 0.09) / 1.09
    assert result.pv_forecast == pytest.approx(year_one)
    assert result.enterprise_value == pytest.approx(year_one + terminal)


def test_net_debt_is_subtracted_to_reach_equity_value():
    with_debt = run_dcf(_inputs(net_debt=50e9))
    without = run_dcf(_inputs(net_debt=0.0))
    assert without.equity_value - with_debt.equity_value == pytest.approx(50e9)


def test_terminal_growth_at_or_above_discount_rate_is_refused():
    """Otherwise the terminal value is infinite and the model returns a
    number that looks real."""
    with pytest.raises(ValueError, match="must exceed terminal growth"):
        run_dcf(_inputs(discount_rate=0.05, terminal_growth=0.05))
    with pytest.raises(ValueError):
        run_dcf(_inputs(discount_rate=0.04, terminal_growth=0.06))


def test_terminal_share_is_reported_so_reliance_on_it_is_visible():
    """Measured at 74% on Apple. Above roughly three quarters the output is
    a claim about perpetuity growth, not about the forecast."""
    result = run_dcf(_inputs())
    assert 0.0 < result.terminal_share_of_value < 1.0
    assert result.pv_forecast + result.pv_terminal == pytest.approx(
        result.enterprise_value
    )


def test_higher_discount_rate_lowers_value():
    assert run_dcf(_inputs(discount_rate=0.12)).value_per_share < run_dcf(
        _inputs(discount_rate=0.07)
    ).value_per_share


# --- cases --------------------------------------------------------------


def test_cases_are_ordered_and_each_is_a_full_model_run():
    bear, base, bull = build_cases(_inputs())
    assert [c.name for c in (bear, base, bull)] == ["Bear", "Base", "Bull"]
    assert bear.value_per_share < base.value_per_share < bull.value_per_share
    # The spread comes from stated assumption deltas, not an undisclosed haircut.
    assert bear.growth < base.growth < bull.growth
    assert bear.discount_rate > base.discount_rate > bull.discount_rate


def test_case_probabilities_sum_to_one():
    assert sum(c.probability for c in build_cases(_inputs())) == pytest.approx(1.0)


def test_probability_weighted_target_sits_between_bear_and_bull():
    cases = build_cases(_inputs())
    target = probability_weighted_target(cases)
    assert cases[0].value_per_share < target < cases[2].value_per_share


def test_upside_is_relative_to_the_traded_price():
    case = build_cases(_inputs())[1]
    assert case.upside_vs(case.value_per_share) == pytest.approx(0.0)
    assert case.upside_vs(case.value_per_share / 2) == pytest.approx(1.0)
    assert case.upside_vs(0) is None


# --- sensitivity --------------------------------------------------------


def test_sensitivity_grid_marks_unresolvable_cells_rather_than_failing():
    """A cell where terminal growth meets or exceeds the discount rate has no
    finite answer. NM is the convention; a blank or a negative would read as
    a value."""
    grid = sensitivity_grid(_inputs(), [0.03, 0.09], [0.025, 0.04])
    flat = [value for row in grid for key, value in row.items() if key != "WACC"]
    assert NM in flat
    assert any(v.startswith("$") for v in flat)


def test_sensitivity_grid_values_fall_as_wacc_rises():
    grid = sensitivity_grid(_inputs(), [0.08, 0.10], [0.025])
    high, low = grid[0]["2.5%"], grid[1]["2.5%"]
    assert float(high.strip("$").replace(",", "")) > float(low.strip("$").replace(",", ""))


# --- deriving inputs from filings --------------------------------------


def test_inputs_come_from_filed_cash_flow_not_from_a_model():
    series = _series(
        operating_cash_flow=[110e9], capital_expenditures=[11e9],
        revenue=[300e9, 400e9], total_debt=[90e9], cash_and_equivalents=[30e9],
    )
    inputs = derive_dcf_inputs(series, shares_outstanding=15e9)
    assert inputs is not None
    assert inputs.base_fcf == pytest.approx(99e9)      # 110 less 11
    assert inputs.net_debt == pytest.approx(60e9)      # 90 less 30
    assert all(a.basis for a in inputs.assumptions())  # every input is justified


def test_exceptional_historical_growth_is_capped():
    """Extrapolating a 60% CAGR to perpetuity is the most common way a DCF
    flatters itself."""
    series = _series(
        operating_cash_flow=[110e9], capital_expenditures=[10e9],
        revenue=[100e9, 400e9],
    )
    inputs = derive_dcf_inputs(series, shares_outstanding=15e9)
    assert inputs.fcf_growth == pytest.approx(0.15)


def test_a_filer_without_cash_flow_data_yields_no_model():
    """Returning None is correct for a filer whose statements do not fit this
    shape. A fabricated DCF would be worse than none."""
    assert derive_dcf_inputs(_series(revenue=[100e9]), 15e9) is None


def test_negative_free_cash_flow_yields_no_model():
    series = _series(operating_cash_flow=[5e9], capital_expenditures=[40e9],
                     revenue=[100e9])
    assert derive_dcf_inputs(series, 15e9) is None


# --- implied expectations ----------------------------------------------


def test_implied_growth_reproduces_the_market_price():
    """The solved rate must actually return the price it was solved for.

    The price is chosen above the default-assumption value so it requires
    higher growth, which is the situation that actually arises: a richly
    valued company priced above what its own history supports.
    """
    inputs = _inputs()
    target_price = run_dcf(inputs).value_per_share * 1.5
    implied = implied_expectations(inputs, market_price=target_price)
    assert implied.implied_growth is not None
    assert implied.implied_growth > inputs.fcf_growth

    check = DcfInputs(**{**inputs.__dict__, "fcf_growth": implied.implied_growth})
    assert run_dcf(check).value_per_share == pytest.approx(target_price, rel=0.01)


def test_a_price_below_the_solver_floor_is_reported_as_unsolvable():
    """At the floor of -10% annual growth the model still exceeds some
    prices. No growth assumption explains them, and saying so beats
    extrapolating past the bracket."""
    implied = implied_expectations(_inputs(), market_price=1.0)
    assert implied.implied_growth is None


def test_an_unreachable_price_returns_none_rather_than_a_guess():
    """Verified on HPQ: the model exceeds the market at every growth rate in
    range, so no growth assumption explains the price."""
    implied = implied_expectations(_inputs(), market_price=0.01)
    assert implied.implied_growth is None


def test_a_large_divergence_from_market_is_flagged():
    """Measured at -67% on Apple. A gap that size indicts the assumptions,
    not the market, and the report must say so."""
    implied = implied_expectations(_inputs(), market_price=1000.0)
    assert implied.caveat is not None
    assert "defect in the assumptions" in implied.caveat


def test_no_caveat_when_the_model_lands_near_the_market():
    inputs = _inputs(forecast_years=5)
    fair = run_dcf(inputs).value_per_share
    implied = implied_expectations(inputs, market_price=fair)
    assert implied.model_vs_market == pytest.approx(0.0, abs=0.01)


# --- projection table ---------------------------------------------------


def test_projection_table_shows_the_forecast_the_model_runs_on():
    """A valuation that shows only its output asks the reader to take the
    arithmetic on trust."""
    from asset_researcher.analysis.bundle import SourceBundle
    from asset_researcher.analysis.report import format_projection_table

    bundle = SourceBundle(
        ticker="T", cik=1, company_name="T", sector_class="standard",
        display_industry="Tech", as_of="2026-08-25",
    )
    bundle.dcf_inputs = _inputs(forecast_years=3)
    bundle.dcf = run_dcf(bundle.dcf_inputs)

    rows = format_projection_table(bundle)
    years = [r["Year"] for r in rows]
    assert years[:3] == ["Y1", "Y2", "Y3"]
    assert years[-4:] == ["Terminal", "Enterprise value", "Less net debt",
                          "Equity value"]

    # Discount factors fall as the horizon lengthens.
    factors = [float(r["Discount factor"]) for r in rows[:3]]
    assert factors[0] > factors[1] > factors[2]


def test_net_debt_renders_as_an_accounting_negative():
    """(63.0B) is how a published statement writes it. "-$63.0B" reads as a
    typo beside "$1,611.0B"."""
    from asset_researcher.analysis.bundle import SourceBundle
    from asset_researcher.analysis.report import format_projection_table

    bundle = SourceBundle(
        ticker="T", cik=1, company_name="T", sector_class="standard",
        display_industry="Tech", as_of="2026-08-25",
    )
    bundle.dcf_inputs = _inputs(net_debt=50e9)
    bundle.dcf = run_dcf(bundle.dcf_inputs)

    row = next(r for r in format_projection_table(bundle) if r["Year"] == "Less net debt")
    assert row["Present value"].startswith("(")
    assert row["Present value"].endswith(")")


def test_projection_table_is_empty_without_a_model():
    from asset_researcher.analysis.bundle import SourceBundle
    from asset_researcher.analysis.report import format_projection_table

    bundle = SourceBundle(
        ticker="T", cik=1, company_name="T", sector_class="standard",
        display_industry="Tech", as_of="2026-08-25",
    )
    assert format_projection_table(bundle) == []


# --- cash flow context --------------------------------------------------


def test_cash_multiple_and_growth_are_reported_together():
    """Measured on Apple: 46x free cash flow on a 1.5% five-year CAGR. Each
    figure alone is unremarkable; together they explain why a model built on
    filed history lands far below the price."""
    from asset_researcher.quant.valuation import cash_flow_context

    series = _series(
        operating_cash_flow=[104e9, 122e9, 111e9, 118e9, 111e9],
        capital_expenditures=[11e9, 11e9, 11e9, 9e9, 12e9],
    )
    context = cash_flow_context(series, market_cap=4_575e9)

    assert context.multiple_of_fcf == pytest.approx(4_575e9 / 99e9, rel=0.02)
    assert context.fcf_yield == pytest.approx(1 / context.multiple_of_fcf)
    assert context.fcf_cagr is not None and abs(context.fcf_cagr) < 0.05
    assert "times" in context.summary()


def test_cash_context_degrades_without_a_market_cap():
    from asset_researcher.quant.valuation import cash_flow_context

    context = cash_flow_context(
        _series(operating_cash_flow=[100e9, 110e9],
                capital_expenditures=[10e9, 10e9]),
        market_cap=None,
    )
    assert context.multiple_of_fcf is None
    assert context.summary() is None


def test_base_fcf_is_normalised_over_the_recent_window():
    """One distorted year would otherwise set the base for every projected
    period."""
    from asset_researcher.quant.valuation import normalised_base_fcf

    series = _series(
        operating_cash_flow=[110e9, 120e9, 60e9],   # last year depressed
        capital_expenditures=[10e9, 10e9, 10e9],
    )
    normalised = normalised_base_fcf(series, window=3)
    assert normalised == pytest.approx((100e9 + 110e9 + 50e9) / 3)
    assert normalised > 50e9  # not dragged to the depressed year


def _cash_series(interest_end: str | None) -> MetricSeries:
    """Three years of cash flow, with interest expense tagged in one period
    the caller chooses."""
    series = MetricSeries(cik=1, sector="standard")
    ends = ["2023-09-30", "2024-09-30", "2025-09-30"]
    series.series["operating_cash_flow"] = [
        MetricPeriod(e, f"FY{e[:4]}", 100e9, "a") for e in ends
    ]
    series.series["capital_expenditures"] = [
        MetricPeriod(e, f"FY{e[:4]}", 10e9, "a") for e in ends
    ]
    if interest_end:
        series.series["interest_expense"] = [
            MetricPeriod(interest_end, f"FY{interest_end[:4]}", 4e9, "a")
        ]
    return series


def test_the_interest_add_back_must_come_from_the_cash_flow_window():
    """`_latest` returns the last period a metric has any value for. Apple
    stopped tagging interest expense after FY2023, so an FY2023 figure was
    added back to a base normalised over FY2023 to FY2025: a period
    mismatch inside the adjustment meant to make the arithmetic consistent."""
    from asset_researcher.quant.valuation import _unlever

    value, basis = _unlever(_cash_series("2019-09-30"), 90e9)
    assert value == 90e9
    assert "does not tag interest expense over the same period" in basis

    value, basis = _unlever(_cash_series("2025-09-30"), 90e9)
    assert value == pytest.approx(90e9 + 4e9 * 0.79)
    assert "after tax at 21%" in basis


def test_an_unlevered_base_is_not_double_charged_for_debt():
    """Operating cash flow is reported after interest, so discounting it at
    a weighted average cost of capital and then subtracting net debt charges
    the debt claim twice."""
    from asset_researcher.quant.valuation import _unlever

    levered, _ = _unlever(_cash_series(None), 90e9)
    unlevered, _ = _unlever(_cash_series("2025-09-30"), 90e9)
    assert unlevered > levered


def test_a_negative_assumption_is_parenthesised_like_every_other_figure():
    """A net-cash position printed "$-33.8B" in the assumptions table beside
    a statement row reading "(33,763)" for the same figure."""
    from asset_researcher.quant.valuation import Assumption

    assert Assumption("Net debt", -33.8e9, "$", "x").display() == "($33.8B)"
    assert Assumption("Net debt", 33.8e9, "$", "x").display() == "$33.8B"


def test_a_non_positive_share_count_refuses_rather_than_inventing_a_price():
    """Zero returned a $0.00 value per share and a -100% upside, both
    presented as findings. A negative count returned a trillion-dollar
    negative. The discount-rate guard refuses on the same grounds."""
    for shares in (0.0, -1.0):
        with pytest.raises(ValueError, match="positive"):
            run_dcf(_inputs(shares_outstanding=shares))
