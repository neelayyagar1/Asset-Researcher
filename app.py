"""The research interface.

A view layer only. Every function it calls is importable and testable without
Streamlit, which is what keeps the pipeline, the tests and this page on one
set of code paths. Nothing here computes a figure; it arranges figures other
modules produced.

Presentation follows published equity research rather than a web dashboard:
fixed column order, dollars in millions, negatives in parentheses, multiples
to one decimal with a trailing x, NM where a ratio is not meaningful, and the
subject separated from its peer set. An analyst reads dozens of these a week
and finds a number by its position, so the layout is a convention to be
matched rather than a design to be invented.

The markup and the charts live in asset_researcher/ui. Keeping them there
rather than inline is what lets the standalone HTML export come out of the
same renderers the page uses.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from asset_researcher.analysis.assemble import assemble_bundle
from asset_researcher.analysis.mandate import (
    default_profile,
    load_presets,
    parse_mandate,
)
from asset_researcher.analysis.narrative import generate_narrative
from asset_researcher.analysis.reconcile import generate_reconciliation
from asset_researcher.analysis.report import build_report, format_projection_table
from asset_researcher.analysis.statements import build_statement, periods_of
from asset_researcher.config import get_settings
from asset_researcher.hosting.spend import (
    ESTIMATED_REPORT_COST_USD,
    SpendLimitExceeded,
    SpendTracker,
)
from asset_researcher.llm.claude import ClaudeProvider
from asset_researcher.quant.comps import format_comp_table
from asset_researcher.quant.valuation import (
    probability_weighted_target,
    sensitivity_grid,
)
from asset_researcher.sources.edgar.client import EdgarClient
from asset_researcher.sources.finnhub import FinnhubClient
from asset_researcher.sources.web import UrlRejected, fetch_user_source
from asset_researcher.ui import charts, markdown, theme
from asset_researcher.ui import components as ui
from asset_researcher.ui.components import Col, Stat
from asset_researcher.ui.headline import headline_stats
from asset_researcher.ui.export import report_to_html, report_to_markdown

st.set_page_config(
    page_title="Asset Researcher",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(theme.stylesheet(), unsafe_allow_html=True)


def write(html: str) -> None:
    """Emit a rendered block.

    Nothing reaches this that the component producing it did not escape,
    which is why the components own escaping rather than the view.
    """
    if html:
        st.markdown(html, unsafe_allow_html=True)


# Charts are drawn at the pixel width they will occupy, so a type size in the
# SVG is the type size on screen. HALF is one of two columns inside the
# content measure; FULL is the measure itself.
HALF = 520
FULL = 1096


@st.cache_resource
def services():
    settings = get_settings()
    return (
        settings,
        EdgarClient(settings),
        FinnhubClient(settings),
        ClaudeProvider(settings),
        SpendTracker(
            # Anchored to the repository like every cache path. Relative to
            # the process working directory, launching from anywhere else
            # started the daily counter at zero with no error.
            path=settings.repo_root / "data" / "spend.json",
            daily_cap_usd=settings.hosting.spend_cap_daily_usd,
            session_cap_usd=settings.hosting.spend_cap_session_usd,
        ),
    )


settings, edgar, finnhub, llm, spend = services()
st.session_state.setdefault("session_spend", 0.0)
st.session_state.setdefault("report", None)


def pct(value: float | None, digits: int = 1) -> str:
    return f"{value * 100:,.{digits}f}%" if value is not None else "NM"


def signed_pct(value: float | None) -> str:
    """Growth and upside carry an explicit sign: the direction is the point."""
    if value is None:
        return "NM"
    return f"{'+' if value >= 0 else ''}{value * 100:,.1f}%"


def usd(value: float | None) -> str:
    return f"${value:,.2f}" if value is not None else "NM"


def billions(value: float | None) -> str:
    return f"${value / 1e9:,.0f}B" if value else "NM"


# ------------------------------------------------------------------ controls

with st.sidebar:
    write(
        '<div class="ar-eyebrow" style="border-top:2px solid var(--ink);'
        'padding-top:.7rem">Asset Researcher</div>'
        '<p style="font-size:.74rem;margin:.45rem 0 1.3rem">Equity research '
        'from primary filings.</p>'
    )

    ticker = st.text_input("Ticker", value="AAPL", max_chars=8).strip().upper()

    presets = load_presets()
    choice = st.selectbox(
        "Mandate template",
        ["Describe my own"] + [p.name for p in presets],
        index=1,
    )
    prefill = (
        ""
        if choice == "Describe my own"
        else next(p.description for p in presets if p.name == choice)
    )
    mandate_text = st.text_area(
        "Mandate", value=prefill, height=140, label_visibility="collapsed"
    )
    st.caption(
        "Sets emphasis and ordering only. It does not change the reported "
        "figures, the citations, or which divergences are disclosed."
    )

    urls_text = st.text_area("Additional sources", height=72, placeholder="https://")
    st.caption("Public URLs. Classified as secondary and attributed as opinion.")

    run = st.button("Generate report", type="primary", use_container_width=True)
    st.caption(f"Demo budget remaining today: ${spend.remaining_today():,.2f}")

    # Export is offered only once there is something to export, and both
    # formats come from the same renderers the page uses.
    existing = st.session_state.get("report")
    if existing is not None:
        st.divider()
        write('<div class="ar-field">Export</div>')
        st.download_button(
            "Standalone HTML",
            data=report_to_html(existing),
            file_name=f"{existing.ticker}-research-note.html",
            mime="text/html",
            use_container_width=True,
        )
        st.download_button(
            "Markdown",
            data=report_to_markdown(existing),
            file_name=f"{existing.ticker}-research-note.md",
            mime="text/markdown",
            use_container_width=True,
        )


def generate(ticker: str, mandate_text: str, urls: list[str]):
    try:
        spend.check_can_start(
            st.session_state["session_spend"], ESTIMATED_REPORT_COST_USD
        )
    except SpendLimitExceeded as exc:
        write(ui.status("error", "Budget", str(exc)))
        return None

    before = llm.usage.cost_usd
    user_sources = []

    # Call A costs roughly a dollar and runs before Call B, which is the one
    # that can fail on a truncated structured response. Recording the cost
    # only after both succeeded meant a repeatable late failure spent real
    # money against a counter that never moved, and neither cap ever bound.
    try:
        return _generate(ticker, mandate_text, urls, user_sources)
    finally:
        cost = llm.usage.cost_usd - before
        if cost:
            st.session_state["session_spend"] += cost
            spend.record(cost)


def _generate(ticker: str, mandate_text: str, urls: list[str], user_sources: list):
    with st.status(f"Building {ticker}", expanded=True) as status:
        for url in urls:
            try:
                user_sources.append(fetch_user_source(url))
                st.write(f"Source accepted: {url}")
            except UrlRejected as exc:
                st.write(f"Source rejected ({url}): {exc}")

        st.write("Retrieving filings, market data and the peer set")
        bundle = assemble_bundle(ticker, settings, edgar, finnhub, llm)
        st.write(
            f"{len(bundle.passages)} passages, "
            f"{bundle.total_passage_chars:,} characters"
        )

        st.write("Parsing mandate")
        mandate = (
            parse_mandate(mandate_text, llm)
            if mandate_text.strip()
            else default_profile()
        )

        st.write("Drafting descriptive sections and verifying citations")
        narrative = generate_narrative(
            bundle,
            llm,
            effort=settings.llm.effort.get("narrative", "medium"),
            user_sources=user_sources,
        )

        st.write("Reconciling the narrative against filed figures")
        reconciliation = generate_reconciliation(
            bundle,
            narrative,
            mandate,
            llm,
            effort=settings.llm.effort.get("reconciliation", "high"),
        )
        status.update(label=f"{ticker} complete", state="complete", expanded=False)

    return build_report(bundle, mandate, narrative, reconciliation)


if run:
    if not ticker:
        write(ui.status("error", "Input", "Enter a ticker."))
    else:
        urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
        try:
            st.session_state["report"] = generate(ticker, mandate_text, urls)
        except Exception as exc:
            st.session_state["report"] = None
            write(
                ui.status(
                    "error", "Failed", f"The report could not be generated: {exc}"
                )
            )


# -------------------------------------------------------------- cover page

report = st.session_state.get("report")
if report is None:
    write(
        ui.cover(
            "Equity research built from the filings themselves.",
            "A ticker in, a sourced research note out: the filed financial "
            "record, the narrative management wrapped around it, and the "
            "places where the two do not agree.",
            [
                (
                    "Every figure is filed",
                    "Financial data is read from the company's own XBRL "
                    "submissions to the SEC. No figure is model-generated, "
                    "and the ones computed from filed lines are marked as "
                    "computed.",
                ),
                (
                    "Every claim is cited",
                    "Narrative statements carry a citation resolved against "
                    "the exact stored text of the source document. A citation "
                    "that cannot be matched is shown as unverified rather "
                    "than quietly dropped.",
                ),
                (
                    "The counter-case is mandatory",
                    "Each report states the strongest evidence against its "
                    "own thesis, what would falsify it, and what the source "
                    "material could not see.",
                ),
            ],
        )
    )
    st.stop()


bundle = report.bundle
rec = report.reconciliation
price = bundle.quote.price if bundle.quote else None
cases = bundle.valuation_cases
target = probability_weighted_target(cases) if cases else None
upside = (target / price - 1) if (target and price) else None
implied = bundle.implied
context = bundle.cash_context

# ----------------------------------------------------------------- masthead

write(
    ui.masthead(
        bundle.company_name,
        bundle.ticker,
        "Equity research note",
        [
            bundle.display_industry,
            f"As of {bundle.as_of}",
            f"Prepared for {report.mandate.summary()}",
        ],
    )
)


write(ui.stat_strip(headline_stats(report)))

level, message = report.verification_banner
write(
    ui.status(
        level,
        {
            "success": "Citations verified",
            "warning": "Citations partial",
            "error": "Citations absent",
        }[level],
        message,
    )
)

# The modelled target is the weaker of the two valuation outputs wherever the
# cash flow model diverges sharply from the market, and the model says so
# itself. Leading with that caveat is more honest than printing a target the
# model has already disowned.
if implied is not None and implied.caveat:
    write(ui.status("warning", "Model divergence", implied.caveat))

if bundle.staleness_note:
    write(ui.status("info", "Source currency", bundle.staleness_note))


tabs = st.tabs(
    [
        "Summary",
        "Thesis",
        "Reconciliation",
        "Valuation",
        "Financials",
        "Peers",
        "Management",
        "Note",
        "Sources",
    ]
)

# ------------------------------------------------------------------ summary

with tabs[0]:
    write(
        ui.section(
            "Where this analysis departs from consensus",
            f"{len(rec.variant_views)} view(s)" if rec.variant_views else "",
        )
    )
    if rec.variant_views:
        for view in rec.variant_views:
            write(
                ui.split(
                    "Prevailing view",
                    view.street_view,
                    f"This analysis, {view.confidence} confidence",
                    view.our_view,
                    left_tone="street",
                    right_tone="ours",
                )
            )
            write(ui.footnote(f"Evidence: {view.supporting_evidence}"))
    else:
        write(
            ui.note(
                "No variant view was identified against the prevailing read. "
                "A note that agrees with consensus throughout has said "
                "nothing the price does not already reflect."
            )
        )

    if cases or bundle.series is not None:
        write(ui.section("Valuation in brief"))
        left, right = st.columns(2)
        with left:
            write(
                charts.figure(
                    charts.valuation_range(cases, price, width=HALF),
                    "Each case is a full model run at its own assumptions, "
                    "not a multiple applied to one forecast.",
                )
                or ui.note(
                    "No valuation range: the filings do not support a cash "
                    "flow model, or no quote was available to compare it to."
                )
            )
        with right:
            write(
                charts.figure(
                    charts.free_cash_flow_history(bundle.series, width=HALF)
                    if bundle.series is not None
                    else None,
                    context.summary() if context else "",
                )
                or ui.note(
                    "No free cash flow history: operating cash flow and "
                    "capital expenditure are not both filed for two or more "
                    "years."
                )
            )

    write(
        ui.section(
            "Principal divergences",
            f"{len(rec.divergences)} of {len(rec.reconciliations)} comparisons",
        )
    )
    if rec.divergences:
        write(
            ui.table(
                [
                    Col("materiality", "Materiality"),
                    Col("claim", "Management position", wide=True),
                    Col("data", "Reported figures", wide=True),
                ],
                [
                    {
                        "materiality": d.materiality.capitalize(),
                        "claim": d.management_claim,
                        "data": d.what_the_data_shows,
                    }
                    for d in rec.divergences[:4]
                ],
            )
        )
    else:
        write(
            ui.note(
                "The filed figures corroborate management's account "
                "throughout. Reconciliation carries each comparison."
            )
        )

    write(ui.section("What would have to be true"))
    write(ui.paragraphs(rec.what_would_have_to_be_true))

    if rec.catalysts:
        write(ui.section("Catalysts", "Over the mandate's horizon"))
        write(
            ui.table(
                [
                    Col("when", "Timeframe", emphasis=True),
                    Col("what", "Catalyst", wide=True),
                    Col("evidence", "Confirming evidence", wide=True),
                ],
                [
                    {
                        "when": c.timeframe,
                        "what": c.description,
                        "evidence": c.confirming_evidence,
                    }
                    for c in rec.catalysts
                ],
            )
        )

    if rec.questions_for_management:
        write(ui.section("Questions for management"))
        write(ui.bullets(rec.questions_for_management[:6]))

# ------------------------------------------------------------------- thesis

with tabs[1]:
    write(ui.section("Financial trajectory"))
    write(ui.paragraphs(rec.financial_trajectory))

    write(ui.section("Bull and bear"))
    write(
        ui.split(
            "Bull case",
            rec.bull_case,
            "Bear case",
            rec.bear_case,
            left_tone="bull",
            right_tone="bear",
        )
    )

    write(ui.section("Valuation context"))
    write(ui.paragraphs(rec.valuation_context))

    write(ui.section("Disconfirming evidence", "Produced on every report"))
    write(
        ui.caption(
            "The strongest case against the analysis above. A report that "
            "cannot state what would falsify it has not been tested."
        )
    )
    write(ui.status("warning", "Against this thesis", rec.disconfirming_evidence))

    if rec.data_limitations:
        write(ui.section("Data limitations"))
        write(ui.paragraphs(rec.data_limitations))

# ----------------------------------------------------------- reconciliation

with tabs[2]:
    write(
        ui.section(
            "Narrative against reported figures",
            f"{len(rec.divergences)} divergence(s), "
            f"{len(rec.corroborations)} corroborated",
        )
    )
    write(
        ui.caption(
            "Management's account set against the company's own filed data. "
            "Management narrative is a claim and filed data is a fact; where "
            "they disagree, that gap is the finding. Divergences first."
        )
    )
    if rec.reconciliations:
        for item in rec.divergences + rec.corroborations:
            write(
                ui.finding(
                    item.management_claim,
                    item.what_the_data_shows,
                    item.assessment,
                    item.agrees,
                    item.materiality,
                )
            )
    else:
        write(ui.note("No reconciliation was produced for this filer."))

# ---------------------------------------------------------------- valuation

with tabs[3]:
    if bundle.dcf is None or bundle.dcf_inputs is None:
        write(
            ui.note(
                "No discounted cash flow model was produced for this filer. "
                "Sources records why."
            )
        )
    else:
        if context and context.summary():
            write(ui.section("What the market is paying"))
            write(
                ui.stat_strip(
                    [
                        Stat(
                            "Market cap / free cash flow",
                            f"{context.multiple_of_fcf:,.0f}x"
                            if context.multiple_of_fcf
                            else "NM",
                        ),
                        Stat(
                            "Free cash flow yield",
                            pct(context.fcf_yield) if context.fcf_yield else "NM",
                        ),
                        Stat(
                            "Filed free cash flow CAGR",
                            pct(context.fcf_cagr),
                            f"Over {context.years_observed} years",
                        ),
                    ]
                )
            )
            write(ui.caption(context.summary()))

        write(ui.section("Implied expectations", "The primary output"))
        write(
            ui.caption(
                "Solved backwards from the traded price. This states what the "
                "current price requires an investor to believe rather than "
                "asserting a target, and it is the figure to interrogate when "
                "a single-stage model lands far from the market."
            )
        )
        write(
            ui.stat_strip(
                [
                    Stat(
                        "Implied annual FCF growth",
                        pct(implied.implied_growth)
                        if implied and implied.implied_growth is not None
                        else "Unsolvable",
                    ),
                    Stat(
                        "Implied discount rate",
                        pct(implied.implied_discount_rate)
                        if implied and implied.implied_discount_rate is not None
                        else "NM",
                    ),
                    Stat(
                        "Terminal share of value",
                        pct(bundle.dcf.terminal_share_of_value, 0),
                        "Above 75% the answer is the perpetuity assumption",
                    ),
                ]
            )
        )

        write(ui.section("Cases"))
        left, right = st.columns(2)
        with left:
            write(charts.figure(charts.valuation_range(cases, price, width=HALF)))
        with right:
            write(
                charts.figure(
                    charts.dcf_bridge(bundle.dcf, bundle.dcf_inputs, width=HALF),
                    "How much of the valuation is the forecast and how much "
                    "is the perpetuity assumption behind it.",
                )
            )

        write(
            ui.table(
                [
                    Col("case", "Case", emphasis=True),
                    Col("value", "Value per share", num=True),
                    Col("growth", "Revenue growth", num=True),
                    Col("wacc", "Discount rate", num=True),
                    Col("probability", "Probability", num=True),
                    Col("upside", "Upside", num=True),
                ],
                [
                    {
                        "case": c.name,
                        "value": usd(c.value_per_share),
                        "growth": pct(c.growth),
                        "wacc": pct(c.discount_rate),
                        "probability": pct(c.probability, 0),
                        "upside": signed_pct(c.upside_vs(price)) if price else "NM",
                    }
                    for c in cases
                ],
            )
        )

        write(ui.section("Sensitivity", "Value per share"))
        write(
            ui.caption(
                "Discount rate against terminal growth, all else unchanged. "
                "Cells are shaded by whether they clear the traded price, "
                "because the reader's question is which assumptions would "
                "justify it rather than what the midpoint is."
            )
        )
        write(
            ui.sensitivity_table(
                sensitivity_grid(
                    bundle.dcf_inputs,
                    [0.07, 0.08, 0.09, 0.10, 0.11],
                    [0.015, 0.020, 0.025, 0.030],
                ),
                price,
            )
        )

        write(ui.section("Projection", "Computed, not filed"))
        projection = format_projection_table(bundle)
        if projection:
            write(
                ui.table(
                    [
                        Col("Year", "Year", emphasis=True),
                        Col("Free cash flow", "Free cash flow", num=True),
                        Col("Discount factor", "Discount factor", num=True),
                        Col("Present value", "Present value", num=True),
                    ],
                    projection,
                    classify=lambda i, r: "total"
                    if r.get("Year") in {"Enterprise value", "Equity value"}
                    else "",
                )
            )

        write(ui.section("Assumptions"))
        write(
            ui.caption(
                "Every input with the basis a reviewer needs to challenge it. "
                "Inputs not derived from filings are labelled conventions and "
                "should be replaced with your own."
            )
        )
        write(
            ui.kv_table(
                [
                    (a.name, a.display(), a.basis)
                    for a in bundle.dcf_inputs.assumptions()
                ]
            )
        )

# --------------------------------------------------------------- financials

with tabs[4]:
    write(ui.section("Filed trends", "From XBRL, as submitted"))
    if bundle.series is None or not bundle.series.series:
        write(
            ui.note(
                "No filed financial data is available for this company, so "
                "no trend can be drawn."
            )
        )
    left, right = st.columns(2)
    with left:
        write(
            charts.figure(
                charts.metric_bars(
                    bundle.series,
                    "revenue",
                    "Revenue",
                    "As filed, by fiscal year",
                    width=HALF,
                )
                if bundle.series
                else None
            )
        )
    with right:
        write(
            charts.figure(
                charts.margin_lines(bundle.series, width=HALF)
                if bundle.series
                else None
            )
        )

    lower_left, lower_right = st.columns(2)
    with lower_left:
        write(
            charts.figure(
                charts.metric_bars(
                    bundle.series,
                    "operating_cash_flow",
                    "Operating cash flow",
                    "As filed",
                    width=HALF,
                )
                if bundle.series
                else None
            )
        )
    with lower_right:
        write(
            charts.figure(
                charts.free_cash_flow_history(bundle.series, width=HALF)
                if bundle.series
                else None
            )
        )

    write(ui.section("Financial summary", "Statement order"))
    statement = build_statement(bundle.series, bundle.sector_class)
    if statement:
        write(ui.statement_table(statement, periods_of(bundle.series)))
        write(
            ui.footnote(
                "Lines set in the lighter weight are computed from the filed "
                "lines above them (growth rates, margins, free cash flow). "
                "Every other figure is exactly as submitted to the SEC. Free "
                "cash flow is operating cash flow less capital expenditure."
            )
        )
    else:
        write(ui.note("No filed financial data is available for this company."))

    if bundle.health_scores:
        write(ui.section("Financial health"))
        write(
            ui.table(
                [
                    Col("measure", "Measure", emphasis=True),
                    Col("value", "Value", num=True),
                ],
                [
                    {"measure": s.label, "value": s.display()}
                    for s in bundle.health_scores
                ],
            )
        )
        write(
            ui.footnote(
                "Altman Z, Piotroski F and Beneish M are computed from filed "
                "statements using the published methodologies. They are "
                "reported as not meaningful for filers whose balance sheet "
                "structure those models do not fit, such as banks and REITs."
            )
        )

# -------------------------------------------------------------------- peers

with tabs[5]:
    table = bundle.comps
    if table is None or not table.rows:
        write(ui.note("No peer comparison is available for this filer."))
    else:
        write(
            ui.section("Comparable companies", f"Peer set from {table.peer_source}")
        )
        write(
            ui.caption(
                "Choosing a peer set is an analytical judgment, so this one is "
                "attributed rather than invented and every row states its "
                "basis for inclusion. Summary statistics are computed across "
                "peers only, excluding the subject and extreme multiples."
            )
        )
        write(
            ui.table(
                [
                    Col("Company", "Company", emphasis=True),
                    Col("Ticker", "Ticker"),
                    Col("FYE", "FYE"),
                    Col("Share price", "Share price", num=True),
                    Col("Equity value", "Equity value", num=True),
                    Col("Net debt", "Net debt", num=True),
                    Col("Enterprise value", "Enterprise value", num=True),
                    Col("Revenue", "Revenue", num=True),
                    Col("EBITDA", "EBITDA", num=True),
                    Col("EBITDA margin", "EBITDA margin", num=True),
                    Col("Net margin", "Net margin", num=True),
                    Col("EV/Revenue", "EV/Revenue", num=True),
                    Col("EV/EBITDA", "EV/EBITDA", num=True),
                    Col("P/E", "P/E", num=True),
                    Col("P/B", "P/B", num=True),
                    Col("Basis for inclusion", "Basis for inclusion", wide=True),
                ],
                format_comp_table(table),
                classify=ui.comps_classify,
                scrolls=True,
            )
        )
        write(
            ui.footnote(
                "Dollar figures in millions. EBITDA is operating income plus "
                "depreciation and amortisation, a convention rather than a "
                "reported line. " + (table.coverage_note or "")
            )
        )

        left, right = st.columns(2)
        with left:
            write(
                charts.figure(
                    charts.peer_bars(table, "pe", "Price to earnings", width=HALF)
                )
            )
        with right:
            write(
                charts.figure(
                    charts.peer_bars(table, "ev_to_ebitda", "EV / EBITDA", width=HALF)
                )
            )

# --------------------------------------------------------------- management

with tabs[6]:
    management = rec.management
    if not management.executives and not management.compensation_structure:
        write(
            ui.note(
                "No management analysis was produced. This section depends on "
                "a proxy statement; Sources records whether one was available."
            )
        )
    else:
        if management.executives:
            write(ui.section("Named officers", "As disclosed in the filings"))
            write(
                ui.table(
                    [
                        Col("name", "Name", emphasis=True),
                        Col("role", "Role"),
                        Col("tenure", "Tenure"),
                        Col("background", "Background", wide=True),
                        Col("note", "Note", wide=True),
                    ],
                    [
                        {
                            "name": e.name,
                            "role": e.role,
                            "tenure": e.tenure,
                            "background": e.background,
                            "note": e.note,
                        }
                        for e in management.executives
                    ],
                )
            )

        write(ui.section("Pay and alignment"))
        write(
            ui.split(
                "What the plan rewards",
                management.compensation_structure,
                "Whether it points where the business does",
                management.alignment_assessment,
            )
        )

        write(ui.section("Ownership and oversight"))
        write(
            ui.split(
                "Board independence",
                management.board_independence,
                "Insider ownership",
                management.insider_ownership,
            )
        )

        if management.concerns:
            write(ui.section("Governance concerns"))
            write(ui.bullets(management.concerns))

# ---------------------------------------------------------------------- note

with tabs[7]:
    write(ui.section("Descriptive note", "Every claim cited"))
    write(
        ui.caption(
            "Bracketed numbers link to the source document at the point of "
            "the claim. A marker labelled unverified could not be matched "
            "against the stored source text and should be treated as "
            "unsupported."
        )
    )
    write(ui.prose(markdown.to_html(report.narrative_markdown)))

# ------------------------------------------------------------------ sources

with tabs[8]:
    write(
        ui.section("Documents used", f"{bundle.total_passage_chars:,} characters")
    )
    write(
        ui.table(
            [
                Col("document", "Document", emphasis=True),
                Col("form", "Form"),
                Col("filed", "Filed"),
                Col("chars", "Characters", num=True),
                Col("link", "Source", link=True),
            ],
            [
                {
                    "document": p.label,
                    "form": p.form,
                    "filed": p.filing_date,
                    "chars": f"{p.char_count:,}",
                    "link": p.source_url,
                }
                for p in bundle.passages
            ],
        )
    )

    if report.mandate.assumptions:
        write(ui.section("Assumptions made about the mandate"))
        write(
            ui.caption(
                "Anything inferred rather than read from the mandate "
                "description, listed so it can be corrected."
            )
        )
        write(ui.bullets(report.mandate.assumptions))

    if bundle.gaps:
        write(ui.section("Gaps in the source material", str(len(bundle.gaps))))
        write(
            ui.caption(
                "Recorded rather than papered over, so the analysis can be "
                "weighed against what it could not see."
            )
        )
        write(
            ui.table(
                [
                    Col("severity", "Severity", emphasis=True),
                    Col("source", "Source"),
                    Col("detail", "Detail", wide=True),
                ],
                [
                    {
                        "severity": g.severity.capitalize(),
                        "source": g.source,
                        "detail": g.reason,
                    }
                    for g in bundle.gaps
                ],
            )
        )

    write(ui.section("Citations", f"{len(report.citations)} resolved"))
    write(
        ui.table(
            [
                Col("n", "No.", num=True),
                Col("quote", "Cited text", wide=True),
                Col("source", "Document"),
                Col("status", "Status"),
                Col("link", "Source", link=True),
            ],
            [
                {
                    "n": str(c.number),
                    "quote": c.quote[:220],
                    "source": c.source_label,
                    "status": "Verified" if c.verified else c.status,
                    "link": c.source_url,
                }
                for c in report.citations
            ],
        )
    )

write(
    '<p class="ar-foot" style="margin-top:2.6rem;border-top:1px solid '
    f'var(--rule);padding-top:.9rem">{settings.report.disclaimer}</p>'
)
