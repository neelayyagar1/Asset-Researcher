"""The view layer, tested without starting a server.

Every renderer is a pure function from data to a string, which is the point
of keeping them out of app.py: the conventions this project claims to follow
(negatives in parentheses, the subject separated from its peers, absent
values shown as absent) are assertions rather than screenshots.
"""

from __future__ import annotations

from asset_researcher.quant.comps import CompRow, CompsTable, format_comp_table
from asset_researcher.quant.series import MetricPeriod, MetricSeries
from asset_researcher.quant.valuation import (
    DcfInputs,
    ValuationCase,
    run_dcf,
)
from asset_researcher.ui import charts, components, markdown, theme


# --------------------------------------------------------------- markdown


def test_model_prose_cannot_inject_markup():
    """Call A output reaches the page through this converter. A filing that
    quotes a tag, or a model that emits one, must arrive as text."""
    out = markdown.to_html("Revenue rose <script>alert(1)</script> sharply.")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_citation_links_survive_conversion():
    out = markdown.to_html("Margin contracted. [[1](https://sec.gov/a.htm)]")
    assert '<a href="https://sec.gov/a.htm"' in out
    assert 'rel="noopener noreferrer"' in out


def test_a_non_http_link_target_is_stripped_to_its_label():
    out = markdown.to_html("[click](javascript:alert(1))")
    assert "javascript:" not in out
    assert "click" in out


def test_headings_lists_and_bold_are_the_supported_subset():
    out = markdown.to_html(
        "## Business overview\n\n"
        "Apple designs **phones**.\n\n"
        "- One segment\n- Two segments\n"
    )
    assert "<h2>Business overview</h2>" in out
    assert "<strong>phones</strong>" in out
    assert out.count("<li>") == 2


def test_consecutive_lines_join_into_one_paragraph():
    out = markdown.to_html("First line\nsecond line\n\nNew paragraph")
    assert out.count("<p>") == 2
    assert "First line second line" in out


def test_empty_input_produces_nothing_rather_than_an_empty_element():
    assert markdown.to_html("") == ""
    assert markdown.to_html("   \n  ") == ""


# -------------------------------------------------------------- components


def test_rendered_html_carries_no_blank_lines_or_indentation():
    """Streamlit passes these strings through a Markdown renderer, which
    reads a blank line as a paragraph break and four leading spaces as a
    code block. Pretty-printed markup arrives broken."""
    out = components.stat_strip(
        [components.Stat("Traded price", "$313.45"), components.Stat("Upside", "NM")]
    )
    assert "\n" not in out
    assert "  " not in out


def test_a_not_meaningful_figure_is_set_apart_from_a_real_one():
    out = components.stat_strip([components.Stat("Implied upside", "NM")])
    assert 'class="ar-stat-value nm"' in out


def test_company_names_are_escaped():
    out = components.masthead("Smith & Co <b>", "SMT", "Equity research", ["x"])
    assert "<b>" not in out.replace('class="ar-ticker"', "")
    assert "Smith &amp; Co" in out


def test_an_empty_table_renders_nothing_rather_than_a_bare_header():
    assert components.table([components.Col("a", "A")], []) == ""


def test_numeric_columns_are_right_aligned_and_prose_columns_wrap():
    out = components.table(
        [
            components.Col("name", "Name", emphasis=True),
            components.Col("value", "Value", num=True),
            components.Col("why", "Basis", wide=True),
        ],
        [{"name": "Discount rate", "value": "8.5%", "why": "Convention"}],
    )
    assert '<th class="num">Value</th>' in out
    assert 'class="num"' in out
    assert 'class="wide"' in out
    assert 'class="key"' in out


def _comps() -> CompsTable:
    subject = CompRow(
        ticker="AAPL",
        company_name="Apple Inc",
        is_subject=True,
        market_cap=3_000e9,
        price=313.45,
        revenue=416e9,
        net_income=112e9,
        total_equity=60e9,
        total_debt=98e9,
        cash=30e9,
        ebitda=140e9,
        sic="3571",
    )
    peers = [
        CompRow(
            ticker=ticker,
            company_name=f"{ticker} Inc",
            is_subject=False,
            market_cap=cap,
            price=100.0,
            revenue=200e9,
            net_income=income,
            total_equity=50e9,
            total_debt=20e9,
            cash=10e9,
            ebitda=40e9,
            sic="3571",
        )
        for ticker, cap, income in (
            ("DELL", 100e9, 5e9),
            ("HPQ", 30e9, 3e9),
            ("MSFT", 3_100e9, 90e9),
        )
    ]
    return CompsTable(
        subject_ticker="AAPL", peer_source="Finnhub peer list", rows=[subject, *peers]
    )


def test_the_subject_row_is_marked_and_never_sorted_into_the_peer_set():
    rows = format_comp_table(_comps())
    classes = [components.comps_classify(i, r) for i, r in enumerate(rows)]
    assert classes[0] == "subject"
    assert "spacer" in classes
    assert classes.count("summary first") == 1
    assert classes[-1] == "summary"


def test_summary_rows_are_ruled_off_beneath_the_peers():
    rows = format_comp_table(_comps())
    first_summary = next(
        i for i, r in enumerate(rows) if r.get("Company") == "Peer mean"
    )
    assert components.comps_classify(first_summary, rows[first_summary]) == (
        "summary first"
    )


def test_the_sensitivity_grid_is_shaded_against_the_traded_price():
    """The reader's question is which assumptions would justify the price,
    so the fill marks the boundary rather than the magnitude."""
    grid = [
        {"WACC": "8.0%", "2.0%": "$400.00", "2.5%": "$200.00"},
        {"WACC": "9.0%", "2.0%": "$100.00", "2.5%": "NM"},
    ]
    out = components.sensitivity_table(grid, reference_price=300.0)
    assert theme.POSITIVE in out  # the $400 cell clears the price
    assert theme.NEGATIVE in out  # the $100 cell does not
    assert "NM" in out


def test_a_sensitivity_grid_without_a_price_is_rendered_unshaded():
    grid = [{"WACC": "8.0%", "2.0%": "$400.00"}]
    out = components.sensitivity_table(grid, reference_price=None)
    assert "background" not in out


def test_a_divergence_states_both_sides_and_its_materiality():
    out = components.finding(
        claim="Management cites supply-chain improvement.",
        data="Gross margin did not expand.",
        assessment="The claim is not visible in the filed figures.",
        agrees=False,
        materiality="high",
    )
    assert "ar-pill diverge" in out
    assert "high materiality" in out
    assert "Gross margin did not expand." in out


def test_a_corroboration_is_labelled_as_one():
    out = components.finding("c", "d", "a", agrees=True, materiality="low")
    assert "ar-pill agree" in out
    assert "diverge" not in out


def test_status_levels_map_to_distinct_rules():
    assert "ar-status ok" in components.status("success", "Verified", "m")
    assert "ar-status warn" in components.status("warning", "Partial", "m")
    assert "ar-status bad" in components.status("error", "None", "m")


# ------------------------------------------------------------------ charts


def _series() -> MetricSeries:
    def points(values: dict[str, float]) -> list[MetricPeriod]:
        return [
            MetricPeriod(end=f"{k[2:]}-09-30", frame_label=k, value=v, accn="x")
            for k, v in sorted(values.items())
        ]

    return MetricSeries(
        cik=320193,
        sector="standard",
        series={
            "revenue": points(
                {"FY2023": 383e9, "FY2024": 391e9, "FY2025": 416e9}
            ),
            "gross_profit": points(
                {"FY2023": 169e9, "FY2024": 180e9, "FY2025": 196e9}
            ),
            "operating_income": points(
                {"FY2023": 114e9, "FY2024": 123e9, "FY2025": 132e9}
            ),
            "operating_cash_flow": points(
                {"FY2023": 110e9, "FY2024": 118e9, "FY2025": 109e9}
            ),
            "capital_expenditures": points(
                {"FY2023": 10e9, "FY2024": 9e9, "FY2025": 10e9}
            ),
        },
    )


def test_charts_are_wellformed_scalable_svg():
    out = charts.metric_bars(_series(), "revenue", "Revenue")
    assert out.startswith("<svg viewBox=")
    assert "</svg>" in out
    # A viewBox and no fixed width is what lets the chart scale with its
    # column instead of being pasted at one size.
    assert 'width="' not in out.split(">")[0]


def test_a_chart_needs_at_least_two_periods():
    thin = MetricSeries(
        cik=1,
        sector="standard",
        series={
            "revenue": [
                MetricPeriod(end="2025-09-30", frame_label="FY2025", value=1e9, accn="x")
            ]
        },
    )
    assert charts.metric_bars(thin, "revenue", "Revenue") is None
    assert charts.margin_lines(thin) is None


def test_a_missing_metric_yields_no_chart_rather_than_an_empty_frame():
    assert charts.metric_bars(_series(), "proved_reserves", "Reserves") is None


def test_chart_text_is_escaped():
    series = _series()
    series.series["revenue"][0] = MetricPeriod(
        end="2023-09-30", frame_label="<b>FY23", value=383e9, accn="x"
    )
    out = charts.metric_bars(series, "revenue", "Revenue & Growth")
    assert "<b>" not in out
    assert "&amp;" in out


def test_margin_chart_labels_each_series_at_its_last_point():
    out = charts.margin_lines(_series())
    assert "Gross margin" in out
    assert "Operating margin" in out
    # Two lines, each with one end label, on one shared percentage axis.
    assert out.count("<path") == 2


def test_peer_chart_colours_only_the_subject():
    out = charts.peer_bars(_comps(), "pe", "Price to earnings")
    assert out is not None
    assert out.count(theme.ACCENT) >= 1
    assert out.count(theme.NEUTRAL) >= 2


def test_peer_chart_needs_three_usable_multiples():
    thin = CompsTable(
        subject_ticker="AAPL",
        peer_source="x",
        rows=[CompRow(ticker="AAPL", company_name="Apple", is_subject=True)],
    )
    assert charts.peer_bars(thin, "pe", "P/E") is None


def test_valuation_range_marks_the_traded_price_separately_from_the_cases():
    cases = [
        ValuationCase("Bear", 80.0, 0.01, 0.105, 0.25),
        ValuationCase("Base", 119.0, 0.03, 0.085, 0.50),
        ValuationCase("Bull", 170.0, 0.07, 0.075, 0.25),
    ]
    out = charts.valuation_range(cases, market_price=313.45)
    assert "Traded $313.45" in out
    assert theme.ACCENT_2 in out
    assert out.count("<circle") == 3


def test_valuation_range_without_a_price_is_not_drawn():
    cases = [ValuationCase("Base", 119.0, 0.03, 0.085, 1.0)]
    assert charts.valuation_range(cases, market_price=None) is None


def _dcf_inputs() -> DcfInputs:
    return DcfInputs(
        base_fcf=100e9,
        fcf_growth=0.03,
        discount_rate=0.085,
        terminal_growth=0.025,
        forecast_years=10,
        net_debt=60e9,
        shares_outstanding=15e9,
        basis={},
    )


def test_the_valuation_bridge_runs_from_forecast_to_equity_value():
    inputs = _dcf_inputs()
    out = charts.dcf_bridge(run_dcf(inputs), inputs)
    for label in ("PV", "forecast", "terminal", "Enterprise", "Equity"):
        assert label in out


def test_free_cash_flow_chart_marks_the_window_the_model_takes_as_its_base():
    """The rule used to be the mean of every filed year while the model
    normalises over three. They coincide on Apple and diverge on anyone with
    a longer record, and the label said neither."""
    out = charts.free_cash_flow_history(_series())
    assert out is not None
    assert "3-year mean" in out
    assert "stroke-dasharray" in out


def test_the_axis_does_not_add_a_whole_step_above_the_data():
    """`(int(max/step)+1)*step` ran Apple's revenue axis to $600B against a
    $416B maximum: 44% of the plot spent on nothing, which flattens the
    trend the chart exists to show."""
    assert charts._axis_top(416e9, 100e9) == 500e9
    assert charts._axis_top(500e9, 100e9) == 500e9  # already on a gridline
    assert charts._axis_top(0.0, 100e9) == 100e9


def test_figure_wrapper_omits_itself_when_there_is_no_chart():
    assert charts.figure(None, "caption") == ""
    assert "figcaption" in charts.figure("<svg></svg>", "A caption")


def test_a_wide_table_is_marked_to_scroll_rather_than_compress():
    """Regression: `scrolls` was accepted and silently ignored, so the
    comparables table squeezed fifteen columns into the content measure and
    wrapped half the company names onto two lines."""
    columns = [components.Col("a", "A"), components.Col("b", "B", num=True)]
    rows = [{"a": "Hewlett Packard Enterprise", "b": "1.0x"}]
    assert "ar-table-scroll" in components.table(columns, rows, scrolls=True)
    assert "ar-table-scroll" not in components.table(columns, rows)


def test_a_long_value_in_a_figure_column_wraps_instead_of_widening_the_table():
    """Regression: the Beneish M-Score reports "insufficient data (missing
    two-year data for ...)" in a value column, and one nowrap line of it
    pushed the value header off the page."""
    columns = [components.Col("m", "Measure"), components.Col("v", "Value", num=True)]
    short = components.table(columns, [{"m": "Altman Z", "v": "5.12 (safe)"}])
    long = components.table(
        columns, [{"m": "Beneish M", "v": "insufficient data (missing two-year data)"}]
    )
    assert '<td class="num">5.12 (safe)</td>' in short
    assert 'class="wide"' in long


# --------------------------------------------------------------- headline


def _report_with(caveat: str | None):
    """A stand-in carrying only the fields the headline builder reads."""
    from dataclasses import dataclass, field

    from asset_researcher.quant.valuation import CashFlowContext

    @dataclass
    class Quote:
        price: float

    @dataclass
    class Implied:
        caveat: str | None
        implied_growth: float = 0.168
        implied_discount_rate: float = 0.047

    @dataclass
    class Bundle:
        quote: Quote
        market_cap: float
        valuation_cases: list
        implied: Implied
        cash_context: CashFlowContext

    @dataclass
    class Report:
        bundle: Bundle

    return Report(
        bundle=Bundle(
            quote=Quote(343.46),
            market_cap=5_013e9,
            valuation_cases=[
                ValuationCase("Bear", 69.0, 0.01, 0.105, 0.25),
                ValuationCase("Base", 133.0, 0.033, 0.085, 0.50),
                ValuationCase("Bull", 210.0, 0.073, 0.075, 0.25),
            ],
            implied=Implied(caveat=caveat),
            cash_context=CashFlowContext(
                latest_fcf=98.8e9,
                average_fcf=102.3e9,
                fcf_cagr=0.015,
                years_observed=4,
                market_cap=5_013e9,
            ),
        )
    )


def test_the_headline_leads_with_the_target_when_the_model_holds():
    from asset_researcher.ui.headline import headline_stats

    labels = [s.label for s in headline_stats(_report_with(None))]
    assert labels[1] == "Probability-weighted target"
    assert labels[2] == "Implied upside"


def test_a_disowned_target_is_demoted_rather_than_led_with():
    """Setting a modelled target at the largest type size on the page with a
    caveat beneath it disowning that same number is not a presentation a
    reader can act on."""
    from asset_researcher.ui.headline import headline_stats

    stats = headline_stats(_report_with("The model differs from the market by -63%."))
    labels = [s.label for s in stats]

    assert labels[0] == "Traded price"
    assert labels[1] == "Market cap / free cash flow"
    assert labels[2] == "Price implies FCF growth"
    # Still present, still last, and labelled for what it is.
    assert labels[-1] == "Modelled value, illustrative"
    assert "divergence note" in stats[-1].note


def test_the_page_and_the_export_build_one_headline():
    """They built it separately, which is how the page came to demote a
    disowned target while the file a reader forwards still led with it."""
    import inspect

    from asset_researcher.ui import export

    assert "headline_stats(report)" in inspect.getsource(export.report_to_html)
