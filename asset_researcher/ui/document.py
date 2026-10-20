"""The report as an ordered list of sections.

Both surfaces render this. The running application and the exported file
used to build their own section lists, which is how the screen came to show
one set of labels and the file another, and how the sensitivity grid existed
on screen for weeks while the file a reader actually forwards did not carry
one.

A section is a label, an optional note, and a body of already-escaped HTML.
Nothing here imports Streamlit, so the whole document is a pure function of
a Report and can be rendered to a file, asserted on in a test, or written to
a page.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from asset_researcher.analysis.report import Report, format_projection_table
from asset_researcher.analysis.statements import build_statement, periods_of
from asset_researcher.quant.comps import format_comp_table
from asset_researcher.quant.valuation import sensitivity_grid
from asset_researcher.ui import charts, markdown
from asset_researcher.ui import components as ui
from asset_researcher.ui.components import Col, Stat
from asset_researcher.ui.summary import summary_block

# Charts are drawn at the pixel width they will occupy, so a type size in an
# SVG is the type size beside it. HALF is one of two columns inside the
# content column; FULL is the content column itself.
HALF = 500
FULL = 1030


@dataclass
class Section:
    label: str
    note: str = ""
    parts: list[str] = field(default_factory=list)

    @property
    def html(self) -> str:
        return ui.section(self.label, self.note) + "".join(self.parts)


def pct(value: float | None, digits: int = 1) -> str:
    return f"{value * 100:,.{digits}f}%" if value is not None else "NM"


def signed_pct(value: float | None) -> str:
    """Growth and upside carry an explicit sign: the direction is the point."""
    if value is None:
        return "NM"
    return f"{'+' if value >= 0 else ''}{value * 100:,.1f}%"


def usd(value: float | None) -> str:
    return f"${value:,.2f}" if value is not None else "NM"


def _gap_reason(bundle, source: str) -> str:
    """The recorded reason for a refusal, so it can be stated where it
    bites rather than only in the log at the foot of the note."""
    for gap in bundle.gaps:
        if gap.source == source:
            return gap.reason
    return ""


def _currency_note(report) -> str:
    """What currency the filed figures are in, said plainly.

    Silence here would be its own claim, so the USD case is stated too.
    """
    series = report.bundle.series
    foreign = getattr(series, "foreign_currencies", None) if series else None
    if foreign:
        found = ", ".join(sorted(foreign))
        return (
            f"This filer tags monetary facts in {found}. Those figures were "
            f"refused rather than read as dollars, so the financial data "
            f"here is incomplete and the multiples and valuation should not "
            f"be relied on."
        )
    if series is None:
        return ""
    return (
        "All filed figures are in US dollars, as submitted. Market data is "
        "quoted in US dollars."
    )


def provenance_items(report: Report) -> list[tuple[str, str]]:
    """The three provenance states, compressed to chips."""
    verification = report.narrative.verification
    level, _ = report.verification_banner
    tone = {"success": "ok", "warning": "warn", "error": "bad"}[level]

    items = [
        (
            f"{verification.verified_citations}/"
            f"{verification.total_citations} cited",
            tone,
        )
    ]
    implied = report.bundle.implied
    if implied is not None and implied.caveat and implied.model_vs_market:
        items.append((f"Model {implied.model_vs_market:+.0%}", "warn"))
    if report.bundle.filing_dates.get("10-K"):
        items.append((f"Filed {report.bundle.filing_dates['10-K']}", ""))
    return items


def sections(report: Report) -> list[Section]:
    """Every section of the note, in reading order."""
    out: list[Section] = []

    def emit(label: str, note: str = "") -> None:
        out.append(Section(label, note))

    def add(html: str) -> None:
        if html:
            out[-1].parts.append(html)

    bundle = report.bundle
    rec = report.reconciliation
    price = bundle.quote.price if bundle.quote else None
    cases = bundle.valuation_cases
    implied = bundle.implied
    context = bundle.cash_context
    table = bundle.comps
    management = rec.management

    emit("Summary", "What the price requires, and where this departs")
    add(ui.block(summary_block(report)))

    # -------------------------------------------------------- variant view

    emit(
        "Variant view",
        "Where this analysis departs from consensus"
        + (f", {ui.plural(len(rec.variant_views), 'view')}"
       if rec.variant_views else ""),
    )
    if rec.variant_views:
        for view in rec.variant_views:
            add(
                ui.block(
                    ui.split(
                        "Prevailing view",
                        view.street_view,
                        f"This analysis, {view.confidence} confidence",
                        view.our_view,
                        left_tone="street",
                        right_tone="ours",
                    ),
                    ui.footnote(f"Evidence: {view.supporting_evidence}"),
                )
            )
    else:
        add(
            ui.block(
                ui.note(
                    "No variant view was identified against the prevailing read. "
                    "A note that agrees with consensus throughout has said "
                    "nothing the price does not already reflect."
                )
            )
        )

    # ------------------------------------------------------- market pricing

    if context and context.summary():
        emit("Market pricing", "What the market is paying for this cash flow")
        add(
            ui.block(
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
                ),
                ui.caption(context.summary()),
                charts.figure(
                    charts.free_cash_flow_history(bundle.series, width=FULL)
                    if bundle.series is not None
                    else None
                ),
            )
        )

    # ------------------------------------------------------------ valuation

    if bundle.dcf is None or bundle.dcf_inputs is None:
        emit("Valuation")
        add(
            ui.block(
                # The reason is already written, well, in the gap log.
                # Pointing at another section for it is the tool
                # declining to answer and then declining to say why, and
                # that is what makes a deliberate refusal read as a
                # failure.
                ui.declined(
                    _gap_reason(bundle, "valuation")
                    or "No discounted cash flow model was produced for "
                       "this filer."
                )
            )
        )
    else:
        emit("Implied expectations", "The primary output")
        add(
            ui.block(
                ui.caption(
                    "Solved backwards from the traded price. This states what "
                    "the current price requires an investor to believe rather "
                    "than asserting a target, and it is the figure to "
                    "interrogate when a single-stage model lands far from the "
                    "market."
                ),
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
                ),
            )
        )

        emit("Valuation", "Modelled from the assumptions below, not filed")
        add(
            ui.block(
                ui.row(
                    charts.figure(charts.valuation_range(cases, price, width=HALF)),
                    charts.figure(
                        charts.dcf_bridge(bundle.dcf, bundle.dcf_inputs, width=HALF),
                        "How much of the valuation is the forecast and how much "
                        "is the perpetuity assumption behind it.",
                    ),
                ),
                ui.table(
                    [
                        Col("case", "Case", emphasis=True),
                        Col("value", "Value per share", num=True),
                        Col("growth", "FCF growth", num=True),
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
                ),
                ui.caption(
                    "Discount rate against terminal growth, all else "
                    "unchanged. A cell is shaded only where the modelled "
                    "value clears the traded price, because that is the "
                    "question: which assumptions would justify what the "
                    "market is asking. An unshaded grid means none in this "
                    "range do."
                ),
                ui.sensitivity_table(
                    sensitivity_grid(
                        bundle.dcf_inputs,
                        [0.07, 0.08, 0.09, 0.10, 0.11],
                        [0.015, 0.020, 0.025, 0.030],
                    ),
                    price,
                ),
            )
        )

        projection = format_projection_table(bundle)
        add(
            ui.block(
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
                if projection
                else "",
                ui.caption(
                    "Every input the model reads, with the basis a reviewer "
                    "needs to challenge it. Inputs that are conventions rather "
                    "than filings say so."
                ),
                ui.kv_table(
                    [
                        (a.name, a.display(), a.basis)
                        for a in bundle.dcf_inputs.assumptions()
                    ]
                ),
            )
        )

    # ------------------------------------------------------------ the thesis

    emit(
        "Trajectory", "What the filed record shows")
    add(ui.block(ui.paragraphs(rec.financial_trajectory)))

    emit(
        "Bull and bear")
    add(
        ui.block(
            ui.split(
                "Bull case",
                rec.bull_case,
                "Bear case",
                rec.bear_case,
                left_tone="bull",
                right_tone="bear",
            )
        )
    )

    emit(
        "What must be true", "Conditions under which the price is justified")
    add(ui.block(ui.paragraphs(rec.what_would_have_to_be_true)))

    emit(
        "Counter-case", "Disconfirming evidence, produced on every report")
    add(
        ui.block(
            ui.caption(
                "The strongest case against the analysis above. A report that "
                "cannot state what would falsify it has not been tested."
            ),
            ui.status("warning", "Against this thesis", rec.disconfirming_evidence),
        )
    )

    if rec.data_limitations:
        emit("Limitations")
        add(ui.block(ui.paragraphs(rec.data_limitations)))

    # -------------------------------------------------------- reconciliation

    emit(
        "Reconciliation",
        f"Narrative against reported figures: "
        f"{ui.plural(len(rec.divergences), 'divergence')}, "
        f"{len(rec.corroborations)} corroborated",
    )
    add(
        ui.block(
            ui.caption(
                "Management's account set against the company's own filed data. "
                "Management narrative is a claim and filed data is a fact; where "
                "they disagree, that gap is the finding. Divergences first."
            ),
            "".join(
                ui.finding(
                    item.management_claim,
                    item.what_the_data_shows,
                    item.assessment,
                    item.agrees,
                    item.materiality,
                )
                for item in rec.divergences + rec.corroborations
            )
            or ui.note("No reconciliation was produced for this filer."),
        )
    )

    if rec.catalysts:
        emit("Catalysts", "Over the mandate's horizon")
        add(
            ui.block(
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
        )

    if rec.questions_for_management:
        emit("Questions", "What the disclosure does not answer")
        add(ui.block(ui.bullets(rec.questions_for_management)))

    # ----------------------------------------------------------- financials

    emit(
        "Financials", "Statement order, from XBRL as submitted")
    statement = build_statement(bundle.series, bundle.sector_class)
    add(
        ui.block(
            ui.row(
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
                ),
                charts.figure(
                    charts.margin_lines(bundle.series, width=HALF)
                    if bundle.series
                    else None
                ),
            ),
            _statement_html := (
                ui.statement_table(statement, periods_of(bundle.series))
                if statement
                else ui.note(
                    "No filed financial data is available for this company."
                )
            ),
            ui.footnote(
                "Lines set in the lighter weight are computed from the filed "
                "lines above them (growth rates, margins, free cash flow, net "
                "debt). Every other figure is exactly as submitted to the SEC. "
                "Two lines here net cash against debt and they do it "
                "differently, deliberately. Net debt nets cash, short-term "
                "investments and, where the sector permits it, long-term "
                "investments, because a reader pricing the equity is buying "
                "the whole portfolio. Return on invested capital nets cash "
                "and equivalents only: netting a large securities portfolio "
                "out of invested capital shrinks the denominator until the "
                "ratio stops describing the operating business, which on one "
                "large-cap filer produced returns above 800%."
            )
            if statement
            else "",
            ui.legend(_statement_html),
        )
    )

    if bundle.health_scores:
        emit("Health", "Published screens, where the balance sheet fits them")
        add(
            ui.block(
                ui.table(
                    [
                        Col("measure", "Measure", emphasis=True),
                        Col("value", "Value", num=True),
                    ],
                    [
                        {"measure": s.label, "value": s.display()}
                        for s in bundle.health_scores
                    ],
                ),
                ui.footnote(
                    "Altman Z, Piotroski F and Beneish M are computed from filed "
                    "statements using the published methodologies. They are "
                    "reported as not meaningful for filers whose balance sheet "
                    "structure those models do not fit, such as banks and REITs."
                ),
            )
        )

    # ---------------------------------------------------------------- peers

    table = bundle.comps
    emit(
        "Peers",
        f"Comparable companies, peer set from {table.peer_source}"
        if table and table.rows
        else "Comparable companies",
    )
    if table is None or not table.rows:
        add(ui.block(ui.note("No peer comparison is available for this filer.")))
    else:
        comp_rows = format_comp_table(table)
        comp_columns, comp_dropped = ui.drop_empty_columns(
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
            comp_rows,
        )
        dropped_note = (
            f" {ui.plural(len(comp_dropped), 'column')} "
            f"({', '.join(comp_dropped)}) "
            f"{'is' if len(comp_dropped) == 1 else 'are'} not derivable for "
            f"any company in this peer set and {'has' if len(comp_dropped) == 1 else 'have'} "
            f"been omitted rather than printed as a column of refusals."
            if comp_dropped
            else ""
        )
        add(
            ui.block(
                ui.caption(
                    "Choosing a peer set is an analytical judgment, so this one "
                    "is attributed rather than invented and every row states its "
                    "basis for inclusion and the fiscal year it reports on. "
                    "Summary statistics are computed across peers only, "
                    "excluding the subject and extreme multiples."
                ),
                _comps_html := ui.table(
                    comp_columns,
                    comp_rows,
                    classify=ui.comps_classify,
                    scrolls=True,
                ),
                ui.footnote(
                    "Dollar figures in millions. EBITDA is operating income plus "
                    "depreciation and amortisation, a convention rather than a "
                    "reported line. " + (table.coverage_note or "")
                    + dropped_note
                ),
                ui.legend(_comps_html),
                ui.row(
                    charts.figure(
                        charts.peer_bars(table, "pe", "Price to earnings", width=HALF)
                    ),
                    charts.figure(
                        charts.peer_bars(table, "ev_to_ebitda", "EV / EBITDA", width=HALF)
                    ),
                ),
            )
        )

    # ----------------------------------------------------------- management

    management = rec.management
    emit(
        "Management", "Officers, pay and ownership, from the proxy")
    if not management.executives and not management.compensation_structure:
        add(
            ui.block(
                ui.note(
                    "A proxy statement was read but no management analysis "
                    "came back from it. Treat that as a gap in this report "
                    "rather than as an absence of disclosure."
                    if any(p.form == "DEF 14A" for p in bundle.passages)
                    else "No proxy statement was available for this filer, "
                    "so there is nothing to assess on pay, board "
                    "independence or ownership. Sources records why."
                )
            )
        )
    else:
        add(
            ui.block(
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
                if management.executives
                else "",
                ui.split(
                    "What the plan rewards",
                    management.compensation_structure,
                    "Whether it points where the business does",
                    management.alignment_assessment,
                ),
                ui.split(
                    "Board independence",
                    management.board_independence,
                    "Insider ownership",
                    management.insider_ownership,
                ),
                ui.bullets(management.concerns) if management.concerns else "",
            )
        )

    # ---------------------------------------------------------------- note

    emit(
        "Note", "The descriptive sections, every claim cited")
    add(
        ui.block(
            ui.caption(
                "Bracketed numbers link to the source document at the point of "
                "the claim. A marker labelled unverified could not be matched "
                "against the stored source text and should be treated as "
                "unsupported."
            ),
            ui.prose(markdown.to_html(report.narrative_markdown)),
        )
    )

    # -------------------------------------------------------------- sources

    emit(
        "Sources", f"Documents, gaps and citations. "
            f"{bundle.total_passage_chars:,} characters read")
    add(
        ui.block(
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
            ),
            ui.caption(
                "Anything inferred rather than read from the mandate "
                "description, listed so it can be corrected."
            )
            if report.mandate.assumptions
            else "",
            ui.bullets(report.mandate.assumptions)
            if report.mandate.assumptions
            else "",
            ui.caption(
                "Gaps recorded rather than papered over, so the analysis can be "
                "weighed against what it could not see."
            )
            if bundle.gaps
            else "",
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
            if bundle.gaps
            else "",
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
            ),
        )
    )


    # The provenance the summary displaced, in full, at the foot where a
    # reader goes to check rather than to decide.
    emit("Provenance", "What was read, what was checked, what was missing")
    level, message = report.verification_banner
    add(
        ui.block(
            ui.status(
                level,
                {
                    "success": "Citations located",
                    "warning": "Citations partial",
                    "error": "Citations absent",
                }[level],
                message,
            ),
            ui.status("warning", "Model divergence", report.bundle.implied.caveat)
            if report.bundle.implied is not None and report.bundle.implied.caveat
            else "",
            # This chip was labelled "Source currency" and rendered the
            # filing-age sentence: the one line in the note that promised
            # to address currency printed something else entirely. Both
            # facts are worth showing, under their own names.
            ui.status("info", "Source currency", _currency_note(report))
            if _currency_note(report)
            else "",
            ui.status("info", "Filing age", report.bundle.staleness_note)
            if report.bundle.staleness_note
            else "",
        )
    )

    return out
