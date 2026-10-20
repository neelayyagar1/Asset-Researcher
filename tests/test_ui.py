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
    # scope="col" is not decoration: a screen reader reads a figure back
    # with its column name only where the header says what it governs.
    assert '<th scope="col" class="num">Value</th>' in out
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


def test_only_the_cells_that_clear_the_traded_price_are_shaded():
    """The reader's question is which assumptions would justify the price.
    Shading both directions restated the sign of every cell: on a model
    diverging far from the market, nineteen of twenty came out tinted and
    the grid read as a wash rather than a boundary."""
    grid = [
        {"WACC": "8.0%", "2.0%": "$400.00", "2.5%": "$200.00"},
        {"WACC": "9.0%", "2.0%": "$100.00", "2.5%": "NM"},
    ]
    out = components.sensitivity_table(grid, reference_price=300.0)
    assert out.count("color-mix") == 1  # only the $400 cell
    assert theme.POSITIVE in out
    assert theme.NEGATIVE not in out
    assert "NM" in out


def test_a_grid_where_nothing_clears_the_price_is_left_clean():
    """And that is the finding: no assumption in this range gets you
    there."""
    grid = [{"WACC": "9.0%", "2.0%": "$100.00", "2.5%": "$120.00"}]
    out = components.sensitivity_table(grid, reference_price=300.0)
    assert "color-mix" not in out


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
    # Sienna is the market everywhere in this report: the traded price here,
    # the prevailing view in a split.
    assert theme.ACCENT_2 in out
    # Ticks, not filled dots on a track. A dot on a track is a slider, and
    # nothing on this scale is draggable.
    assert "<circle" not in out
    assert out.count(f'stroke="{theme.ACCENT}"') == 3


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


def test_the_bridge_names_net_cash_rather_than_calling_it_net_debt():
    """The bridge step is minus net debt, so a net-cash filer adds here. It
    was labelled "Net debt $33.8B" on a company holding net cash, which
    reads as debt being added to enterprise value."""
    from asset_researcher.quant.valuation import run_dcf

    cash_rich = DcfInputs(
        base_fcf=100e9, fcf_growth=0.03, discount_rate=0.085,
        terminal_growth=0.025, forecast_years=10, net_debt=-33.8e9,
        shares_outstanding=15e9, basis={},
    )
    # Multi-word bar labels are drawn as two stacked lines, so the words
    # are asserted rather than the joined string.
    out = charts.dcf_bridge(run_dcf(cash_rich), cash_rich)
    assert "net cash" in out and "Plus" in out
    assert "net debt" not in out

    levered = DcfInputs(**{**cash_rich.__dict__, "net_debt": 60e9})
    out = charts.dcf_bridge(run_dcf(levered), levered)
    assert "net debt" in out and "Less" in out
    assert "net cash" not in out


def test_counts_read_as_written_english_not_as_a_template():
    """"1 divergence(s)" is the single most recognisable sign a sentence was
    assembled by a program, and it was appearing in section notes and the
    staleness line, both of which a reader meets in the first screen."""
    assert components.plural(1, "divergence") == "1 divergence"
    assert components.plural(2, "divergence") == "2 divergences"
    assert components.plural(0, "view") == "0 views"
    assert components.plural(1, "company", "companies") == "1 company"
    assert components.plural(3, "company", "companies") == "3 companies"
    assert components.plural(1500, "character") == "1,500 characters"


def test_the_valuation_range_draws_a_spread_rather_than_normalising_it_away():
    """The axis was the data range plus 16% at each end, so a three-fold
    spread and a five-percent spread drew identically: the one chart whose
    stated purpose is that the spread is the analysis was the one chart
    that could not show a spread."""
    import re

    def marks(cases):
        out = charts.valuation_range(cases, market_price=300.0)
        return [
            float(m) for m in re.findall(
                rf'<line x1="([\d.]+)"[^>]*stroke="{theme.ACCENT}"', out
            )
        ]

    wide = marks([
        ValuationCase("Bear", 100.0, 0.01, 0.105, 0.25),
        ValuationCase("Base", 200.0, 0.03, 0.085, 0.50),
        ValuationCase("Bull", 300.0, 0.07, 0.075, 0.25),
    ])
    tight = marks([
        ValuationCase("Bear", 195.0, 0.01, 0.105, 0.25),
        ValuationCase("Base", 200.0, 0.03, 0.085, 0.50),
        ValuationCase("Bull", 205.0, 0.07, 0.075, 0.25),
    ])
    assert max(wide) - min(wide) > (max(tight) - min(tight)) * 5


def test_the_valuation_range_carries_a_measurable_axis():
    cases = [ValuationCase("Base", 200.0, 0.03, 0.085, 1.0)]
    out = charts.valuation_range(cases, market_price=300.0)
    assert "$0" in out  # anchored at zero rather than fitted to the data
    assert out.count(f'stroke="{theme.RULE}"') >= 3  # gridlines


def test_the_bridge_draws_its_smallest_step():
    """A net-cash step is small against enterprise value and drew as a
    0.8px hairline, leaving its label floating above a bar nobody could
    see."""
    import re

    from asset_researcher.quant.valuation import run_dcf

    inputs = DcfInputs(
        base_fcf=100e9, fcf_growth=0.03, discount_rate=0.085,
        terminal_growth=0.025, forecast_years=10, net_debt=-2e9,
        shares_outstanding=15e9, basis={},
    )
    out = charts.dcf_bridge(run_dcf(inputs), inputs)
    heights = [float(h) for h in re.findall(r'<rect[^>]*height="([\d.]+)"', out)]
    assert min(heights) >= 2.0
    # And the bars are connected, so they read as a waterfall.
    assert "stroke-dasharray" in out


def test_a_negative_bar_does_not_waste_a_whole_band_below_the_axis():
    """`(int(bottom/step) - 1) * step` subtracted a whole extra step below
    the minimum, pushing the zero line up the plot."""
    assert charts._axis_top(300e9, 100e9) == 300e9


# ------------------------------------------------------------ formatting


def test_zero_is_a_figure_and_absence_is_not():
    """`if value else "NM"` reported a company with no market
    capitalisation as unmeasurable, which is the one thing a financial
    table must never do."""
    from asset_researcher.ui import format as fmt

    assert fmt.scaled_usd(0.0) == "$0"
    assert fmt.scaled_usd(None) == "NM"


def test_a_small_cap_does_not_round_to_zero_billion():
    """A $499m company exported as "Market capitalisation: $0B"."""
    from asset_researcher.ui import format as fmt

    assert fmt.scaled_usd(4.99e8) == "$499M"
    assert fmt.scaled_usd(1e6) == "$1M"
    assert fmt.scaled_usd(5.013e12) == "$5,013.0B"


def test_negative_zero_does_not_collect_two_signs():
    from asset_researcher.ui import format as fmt

    assert fmt.signed_pct(-0.0) == "0.0%"
    assert fmt.signed_pct(0.0) == "0.0%"
    assert fmt.signed_pct(0.05) == "+5.0%"
    assert fmt.signed_pct(-0.05) == "(5.0%)" or fmt.signed_pct(-0.05) == "-5.0%"


def test_a_non_finite_figure_never_reaches_the_page():
    """Python's own JSON parser accepts a bare NaN literal, so a malformed
    upstream payload can carry one all the way to a renderer."""
    from asset_researcher.ui import format as fmt

    for bad in (float("nan"), float("inf"), float("-inf")):
        assert fmt.usd(bad) == "NM"
        assert fmt.pct(bad) == "NM"
        assert fmt.scaled_usd(bad) == "NM"
        assert fmt.signed_pct(bad) == "NM"


def test_an_absent_value_never_renders_as_an_empty_cell():
    """An empty cell and a cell holding a missing value must not look
    identical. Mutating this to return "" left the whole suite green."""
    out = components.table(
        [components.Col("a", "A"), components.Col("b", "B")],
        [{"a": None, "b": ""}],
    )
    assert "&mdash;" in out
    assert "&nbsp;" in out


def test_markup_is_collapsed_so_a_markdown_renderer_cannot_break_it():
    """Streamlit passes these through a Markdown renderer, which reads a
    blank line as a paragraph break and four leading spaces as a code
    block. The previous test used two short stats containing no whitespace
    to collapse, so it passed with the collapsing removed."""
    out = components.finding(
        claim="A claim\n\n    with an indented second paragraph",
        data="Figures\n\nin two blocks",
        assessment="An assessment",
        agrees=False,
        materiality="high",
    )
    assert "\n" not in out
    assert "    " not in out


def test_the_note_is_wrapped_so_it_gets_the_reading_measure():
    """Returning the markdown unwrapped dropped the measure, the type size
    and the citation styling, and no test noticed."""
    out = components.prose("<p>Body.</p>")
    assert out.startswith('<div class="ar-prose">')
    assert out.endswith("</div>")


def test_a_source_url_is_attribute_escaped():
    """These are assembled from filing metadata rather than typed here, and
    removing the escaping left the suite green."""
    out = components.table(
        [components.Col("link", "Source", link=True)],
        [{"link": 'https://sec.gov/a.htm?x="><script>alert(1)</script>'}],
    )
    assert "<script>" not in out
    assert "&quot;" in out


def test_a_control_label_inherits_the_control_colour():
    """Streamlit wraps a button's label in its own <p>, and the document's
    global paragraph colour then won against the button's: the primary
    action rendered #403c33 on #17150f, about 1.8:1, which is invisible.

    The regression is in the stylesheet rather than in rendered markup, so
    the rule itself is what gets asserted."""
    css = theme.stylesheet()
    assert ".stButton > button *" in css
    assert "color: inherit;" in css
