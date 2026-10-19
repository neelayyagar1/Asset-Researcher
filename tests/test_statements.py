"""The financial summary: statement order, derived rows, absent rows."""

from __future__ import annotations

from asset_researcher.analysis.statements import (
    DERIVED,
    LINE,
    SECTION,
    SUBTOTAL,
    build_statement,
    periods_of,
)
from asset_researcher.quant.series import MetricPeriod, MetricSeries


def _series(sector: str = "standard", **metrics: dict[str, float]) -> MetricSeries:
    return MetricSeries(
        cik=320193,
        sector=sector,
        series={
            metric: [
                MetricPeriod(
                    end=f"{label[2:]}-09-30",
                    frame_label=label,
                    value=value,
                    accn="0000-00",
                )
                for label, value in sorted(periods.items())
            ]
            for metric, periods in metrics.items()
        },
    )


def _apple_like() -> MetricSeries:
    return _series(
        revenue={"FY2023": 383_285e6, "FY2024": 391_035e6, "FY2025": 416_161e6},
        cogs={"FY2023": 214_137e6, "FY2024": 210_352e6, "FY2025": 220_000e6},
        gross_profit={"FY2023": 169_148e6, "FY2024": 180_683e6, "FY2025": 196_161e6},
        operating_income={"FY2023": 114_301e6, "FY2024": 123_216e6, "FY2025": 132_000e6},
        net_income={"FY2023": 96_995e6, "FY2024": 93_736e6, "FY2025": 112_000e6},
        operating_cash_flow={"FY2023": 110_543e6, "FY2024": 118_254e6, "FY2025": 109_000e6},
        capital_expenditures={"FY2023": 10_959e6, "FY2024": 9_447e6, "FY2025": 10_200e6},
        total_equity={"FY2023": 62_146e6, "FY2024": 56_950e6, "FY2025": 60_000e6},
        total_assets={"FY2023": 352_583e6, "FY2024": 364_980e6, "FY2025": 370_000e6},
    )


def _labels(rows) -> list[str]:
    return [r.label for r in rows]


def test_revenue_precedes_every_other_income_statement_line():
    """The bug this module exists to fix: an alphabetical table put Capital
    Expenditure first and Revenue seventh."""
    labels = _labels(build_statement(_apple_like()))
    assert labels.index("Revenue") < labels.index("Gross profit")
    assert labels.index("Gross profit") < labels.index("Operating income")
    assert labels.index("Operating income") < labels.index("Net income")
    assert labels.index("Net income") < labels.index("Operating cash flow")
    assert labels.index("Operating cash flow") < labels.index("Total assets")


def test_sections_are_emitted_in_reading_order():
    sections = [r.label for r in build_statement(_apple_like()) if r.kind == SECTION]
    # The thinner fixture tags no per-share data, so that block drops out
    # with its rows, which is the no-empty-sections rule working.
    assert sections == [
        "Income statement",
        "Cash flow",
        "Returns and earnings quality",
        "Balance sheet",
    ]


def test_absent_metrics_do_not_produce_empty_rows():
    """A filer that never tags accounts receivable should not carry a row of
    NM across every period for it."""
    labels = _labels(build_statement(_apple_like()))
    assert "Accounts receivable" not in labels
    assert "Interest expense" not in labels


def test_a_section_whose_rows_all_dropped_is_dropped_with_them():
    only_income = _series(
        revenue={"FY2024": 100e6, "FY2025": 110e6},
        net_income={"FY2024": 10e6, "FY2025": 12e6},
    )
    sections = [r.label for r in build_statement(only_income) if r.kind == SECTION]
    assert sections == ["Income statement"]


def test_free_cash_flow_subtracts_capex_regardless_of_its_tagged_sign():
    """Capex is filed as a positive magnitude by some and a negative cash
    movement by others. Trusting the sign adds capex to cash flow for half
    of all filers, doubling the figure plausibly enough to pass unnoticed."""
    positive = _series(
        operating_cash_flow={"FY2025": 100e6},
        capital_expenditures={"FY2025": 30e6},
    )
    negative = _series(
        operating_cash_flow={"FY2025": 100e6},
        capital_expenditures={"FY2025": -30e6},
    )
    both = [
        next(r for r in build_statement(s) if r.label == "Free cash flow")
        for s in (positive, negative)
    ]
    assert both[0].values["FY2025"] == both[1].values["FY2025"] == "70"


def test_growth_is_blank_for_the_first_period_rather_than_zero_or_nm():
    """There is no prior period inside the window, so there is nothing to
    report. "NM" would assert that a growth rate exists and is not
    meaningful, which is a different and untrue claim."""
    rows = build_statement(_apple_like())
    growth = next(r for r in rows if r.label == "Revenue growth")
    assert growth.values["FY2023"] == ""
    assert growth.values["FY2024"] == "+2.0%"


def test_an_untagged_line_reads_as_not_disclosed_rather_than_not_meaningful():
    """Apple reports interest expense and stopped tagging it separately.
    Printing NM told a reader the figure was not meaningful, which is a
    statement about the company rather than about the filing."""
    partial = _series(
        revenue={"FY2024": 100e6, "FY2025": 110e6},
        net_income={"FY2024": 10e6, "FY2025": 12e6},
        operating_cash_flow={"FY2024": 20e6, "FY2025": 22e6},
    )
    rows = build_statement(partial)
    assert "Free cash flow" not in [r.label for r in rows]


def test_free_cash_flow_is_absent_when_capex_was_not_tagged():
    """Defaulting a missing capex year to zero printed operating cash flow
    under the label "Free cash flow", overstating it by the whole capital
    programme."""
    gap = _series(
        revenue={"FY2024": 100e6, "FY2025": 110e6},
        operating_cash_flow={"FY2024": 50e6, "FY2025": 60e6},
        capital_expenditures={"FY2025": 10e6},
    )
    row = next(r for r in build_statement(gap) if r.label == "Free cash flow")
    assert row.values["FY2024"] == "n.d."
    assert row.values["FY2025"] == "50"


def test_capital_expenditure_prints_as_an_outflow():
    """So the cash flow block foots: operating cash flow, less capex, equals
    free cash flow, read straight down the column."""
    cash = _series(
        revenue={"FY2024": 100e6, "FY2025": 110e6},
        operating_cash_flow={"FY2024": 50e6, "FY2025": 60e6},
        capital_expenditures={"FY2024": 8e6, "FY2025": 10e6},
    )
    rows = build_statement(cash)
    capex = next(r for r in rows if r.label == "Capital expenditure")
    assert capex.values["FY2025"] == "(10)"


def test_negative_values_are_parenthesised_not_signed():
    """A leading minus sign disappears in a column of right-aligned
    figures; parentheses are the published convention."""
    loss = _series(
        revenue={"FY2024": 100e6, "FY2025": 90e6},
        net_income={"FY2024": 5e6, "FY2025": -12_500_000},
    )
    rows = build_statement(loss)
    net = next(r for r in rows if r.label == "Net income")
    assert net.values["FY2025"] == "(13)"
    growth = next(r for r in rows if r.label == "Revenue growth")
    assert growth.values["FY2025"] == "(10.0%)"


def test_margins_are_computed_from_filed_lines_and_marked_derived():
    rows = build_statement(_apple_like())
    margin = next(r for r in rows if r.label == "Gross margin")
    assert margin.kind == DERIVED
    # 196,161 / 416,161
    assert margin.values["FY2025"] == "47.1%"
    assert next(r for r in rows if r.label == "Revenue").kind == LINE
    assert next(r for r in rows if r.label == "Gross profit").kind == SUBTOTAL


def test_a_bank_statement_omits_gross_profit_and_leads_with_its_own_lines():
    bank = _series(
        sector="financial",
        revenue={"FY2024": 160e9, "FY2025": 170e9},
        net_interest_income={"FY2024": 90e9, "FY2025": 92e9},
        total_deposits={"FY2024": 2_400e9, "FY2025": 2_500e9},
        net_income={"FY2024": 50e9, "FY2025": 54e9},
        total_equity={"FY2024": 340e9, "FY2025": 350e9},
    )
    rows = build_statement(bank, "financial")
    labels = _labels(rows)
    assert "Gross profit" not in labels
    assert "Net interest income" in labels
    assert "Total deposits" in labels
    roe = next(r for r in rows if r.label == "Return on equity")
    assert roe.values["FY2025"] == "15.4%"


def test_a_reit_statement_carries_leverage_rather_than_gross_margin():
    reit = _series(
        sector="reit",
        revenue={"FY2024": 4_000e6, "FY2025": 5_000e6},
        net_income={"FY2024": 800e6, "FY2025": 900e6},
        total_debt={"FY2024": 20_000e6, "FY2025": 26_000e6},
        total_assets={"FY2024": 50_000e6, "FY2025": 65_000e6},
        total_equity={"FY2024": 28_000e6, "FY2025": 34_000e6},
    )
    rows = build_statement(reit, "reit")
    labels = _labels(rows)
    assert "Gross margin" not in labels
    leverage = next(r for r in rows if r.label == "Debt to total assets")
    assert leverage.values["FY2025"] == "40.0%"


def test_the_window_holds_the_five_most_recent_periods():
    wide = _series(
        revenue={f"FY20{year}": year * 1e9 for year in range(18, 26)}
    )
    assert periods_of(wide) == ["FY2021", "FY2022", "FY2023", "FY2024", "FY2025"]


def test_no_series_yields_no_table_rather_than_an_empty_shell():
    assert build_statement(None) == []
    assert build_statement(MetricSeries(cik=1, sector="standard")) == []


def test_share_counts_are_scaled_as_counts_not_dollars():
    shares = _series(
        revenue={"FY2025": 100e9},
        shares_diluted={"FY2025": 15_200_000_000},
    )
    row = next(
        r for r in build_statement(shares) if r.label == "Diluted shares outstanding"
    )
    assert row.values["FY2025"] == "15,200"


# --- the lines a fundamentals screen leads with -------------------------


def _full() -> MetricSeries:
    return _series(
        revenue={"FY2024": 391_035e6, "FY2025": 416_161e6},
        gross_profit={"FY2024": 180_683e6, "FY2025": 195_201e6},
        operating_income={"FY2024": 123_216e6, "FY2025": 133_050e6},
        pretax_income={"FY2024": 123_485e6, "FY2025": 134_000e6},
        income_tax_expense={"FY2024": 29_749e6, "FY2025": 22_000e6},
        net_income={"FY2024": 93_736e6, "FY2025": 112_010e6},
        eps_diluted={"FY2024": 6.08, "FY2025": 7.47},
        shares_diluted={"FY2024": 15_408e6, "FY2025": 15_005e6},
        depreciation_amortization={"FY2024": 11_445e6, "FY2025": 11_698e6},
        operating_cash_flow={"FY2024": 118_254e6, "FY2025": 111_482e6},
        capital_expenditures={"FY2024": 9_447e6, "FY2025": 12_715e6},
        total_debt={"FY2024": 106_629e6, "FY2025": 98_657e6},
        cash_and_equivalents={"FY2024": 29_943e6, "FY2025": 35_935e6},
        short_term_investments={"FY2024": 35_228e6, "FY2025": 35_200e6},
        long_term_investments={"FY2024": 91_479e6, "FY2025": 91_500e6},
        total_equity={"FY2024": 56_950e6, "FY2025": 73_700e6},
        total_assets={"FY2024": 364_980e6, "FY2025": 359_241e6},
        accounts_receivable={"FY2024": 33_410e6, "FY2025": 39_777e6},
    )


def test_earnings_per_share_is_present_and_in_its_own_block():
    """The single most-read line on a fundamentals screen, and it was absent
    entirely while the share count sat under the balance sheet."""
    rows = build_statement(_full())
    labels = [r.label for r in rows]
    sections = [r.label for r in rows if r.kind == SECTION]

    assert "Per share" in sections
    eps = next(r for r in rows if r.label == "Diluted earnings per share")
    assert eps.values["FY2025"] == "$7.47"
    # The share count moved out of the balance sheet to sit beside it.
    assert labels.index("Diluted shares outstanding") == labels.index(
        "Diluted earnings per share"
    ) + 1
    assert labels.index("Diluted shares outstanding") < labels.index("Total debt")


def test_the_tax_line_and_the_rate_it_implies_are_both_shown():
    rows = build_statement(_full())
    rate = next(r for r in rows if r.label == "Effective tax rate")
    # 22,000 / 134,000
    assert rate.values["FY2025"] == "16.4%"
    assert rate.kind == DERIVED
    assert next(r for r in rows if r.label == "Pre-tax income").kind == SUBTOTAL


def test_net_debt_nets_the_securities_and_reads_as_net_cash():
    """The statement row uses the one shared definition, so it cannot
    disagree with the valuation bridge about what net debt means."""
    rows = build_statement(_full())
    net = next(r for r in rows if r.label == "Net debt")
    # 98,657 less 35,935 + 35,200 + 91,500: comfortably net cash.
    assert net.values["FY2025"].startswith("(")


def test_leverage_is_not_meaningful_in_a_year_ebitda_turned_negative():
    """Leverage against negative EBITDA reads as net cash, so the cell says
    NM rather than printing a negative multiple."""
    turned = _series(
        revenue={"FY2024": 100e6, "FY2025": 90e6},
        total_debt={"FY2024": 50e6, "FY2025": 50e6},
        operating_income={"FY2024": 20e6, "FY2025": -20e6},
    )
    row = next(r for r in build_statement(turned) if r.label == "Net debt / EBITDA")
    assert row.values["FY2024"] == "2.5x"
    assert row.values["FY2025"] == "NM"


def test_a_row_that_is_never_meaningful_is_dropped_rather_than_filled_with_nm():
    """A column of NM adds nothing a reader cannot see from the operating
    income line two rows above it."""
    loss = _series(
        revenue={"FY2024": 100e6, "FY2025": 90e6},
        total_debt={"FY2024": 50e6, "FY2025": 50e6},
        operating_income={"FY2024": -10e6, "FY2025": -20e6},
    )
    assert "Net debt / EBITDA" not in [r.label for r in build_statement(loss)]


def test_depreciation_sits_in_the_cash_flow_block_not_the_income_statement():
    """For a filer reporting it only in the cash flow reconciliation,
    printing it among operating lines implies it was disclosed as one."""
    rows = build_statement(_full())
    labels = [r.label for r in rows]
    cash_flow = labels.index("Operating cash flow")
    assert labels.index("Depreciation and amortisation") > cash_flow


def test_each_section_states_its_own_unit():
    """One "USD millions" in the corner of the table sat above rows of
    percentages, per-share amounts and share counts."""
    sections = {r.label: r.note for r in build_statement(_full()) if r.kind == SECTION}
    assert sections["Income statement"] == "USD millions"
    assert "shares in millions" in sections["Per share"]


def test_the_earliest_column_still_shows_a_growth_rate():
    """The lookback ran after the window was truncated, so the first column
    printed blank while the prior year sat in the series unused."""
    wide = _series(
        revenue={f"FY20{y}": float(y) * 1e9 for y in range(20, 26)}
    )
    rows = build_statement(wide, limit=5)
    growth = next(r for r in rows if r.label == "Revenue growth")
    assert periods_of(wide, 5)[0] == "FY2021"
    assert growth.values["FY2021"] != ""
    assert growth.values["FY2021"] == "+5.0%"  # 21/20


# --- returns and earnings quality ---------------------------------------


def test_the_quality_block_surfaces_what_the_code_already_computed():
    """Return on invested capital and the accrual ratio were both
    computable from filed lines and rendered nowhere. A capital-
    preservation reader asked for the first and a short-seller for the
    second; the code had both."""
    rows = {r.label: r for r in build_statement(_full())}

    roic = rows["Return on invested capital"]
    # NOPAT of 133,050 * (1 - 22,000/134,000) = 111,207, over invested
    # capital of 98,657 + 73,700 - 35,935 = 136,422.
    assert roic.values["FY2025"] == "81.5%"

    assert rows["Operating cash flow / net income"].values["FY2025"] == "99.5%"
    assert rows["Days sales outstanding"].values["FY2024"] == "31"


def test_the_accrual_ratio_carries_a_sign_because_the_direction_is_the_point():
    """Net income running ahead of operating cash flow is the signal; a
    column of unsigned percentages hides which way it went."""
    rows = {r.label: r for r in build_statement(_full())}
    accrual = rows["Accrual ratio"]
    # FY2024: net income below operating cash flow, so negative.
    assert accrual.values["FY2024"].startswith("(")


def test_return_on_invested_capital_is_absent_without_a_filed_tax_rate():
    """A return computed at a guessed tax rate is a number nobody can
    check."""
    untaxed = _series(
        revenue={"FY2024": 100e6, "FY2025": 110e6},
        operating_income={"FY2024": 30e6, "FY2025": 33e6},
        net_income={"FY2024": 20e6, "FY2025": 22e6},
        total_debt={"FY2024": 50e6, "FY2025": 50e6},
        total_equity={"FY2024": 40e6, "FY2025": 45e6},
        total_assets={"FY2024": 200e6, "FY2025": 210e6},
    )
    assert "Return on invested capital" not in [
        r.label for r in build_statement(untaxed)
    ]
