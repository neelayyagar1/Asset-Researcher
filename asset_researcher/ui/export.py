"""The report as a file someone can keep.

A research note that exists only inside a running web application is not a
deliverable. The work product of this tool is a document a PM forwards to an
analyst, attaches to an investment committee pack, or opens six weeks later
to check what the thesis actually said. So the report leaves in two forms.

**Standalone HTML** is the primary one: one file, no network dependency for
anything structural, the charts inline as SVG and the stylesheet inline in
the head. It opens in any browser and prints to PDF with the layout intact.
The one external reference is the webfont, which degrades to Georgia and a
system grotesque when offline.

**Markdown** is the secondary one, for pasting into a memo, a wiki or an
email without carrying styling along.

Both come out of the same renderers the page uses, which is the reason the
components live in this package rather than inline in app.py: an export built
from a second set of formatters drifts from the screen within a week, and the
first time it matters is when somebody circulates the drifted version.
"""

from __future__ import annotations

from html import escape

from asset_researcher.analysis.report import Report, format_projection_table
from asset_researcher.config import get_settings
from asset_researcher.analysis.statements import build_statement, periods_of
from asset_researcher.quant.comps import format_comp_table
from asset_researcher.quant.valuation import (
    probability_weighted_target,
    sensitivity_grid,
)
from asset_researcher.ui import charts, markdown, theme
from asset_researcher.ui import components as ui
from asset_researcher.ui.headline import headline_stats
from asset_researcher.ui.components import Col, Stat

# Wider than the two-column screen layout, because the export is read as one
# continuous document rather than a set of tabs.
_CHART = 620


def _pct(value: float | None, digits: int = 1) -> str:
    return f"{value * 100:,.{digits}f}%" if value is not None else "NM"


def _signed_pct(value: float | None) -> str:
    if value is None:
        return "NM"
    return f"{'+' if value >= 0 else ''}{value * 100:,.1f}%"


def _usd(value: float | None) -> str:
    return f"${value:,.2f}" if value is not None else "NM"


def _billions(value: float | None) -> str:
    return f"${value / 1e9:,.0f}B" if value else "NM"


# --------------------------------------------------------------------- HTML


def report_to_html(report: Report, notice: str = "") -> str:
    """One self-contained document, in reading order.

    Tabs are a navigation device for a screen. A circulated note is linear,
    so the sections appear in the order an analyst reads them: what the
    conclusion is, what the argument is, then the evidence it rests on.
    """
    bundle = report.bundle
    rec = report.reconciliation
    price = bundle.quote.price if bundle.quote else None
    cases = bundle.valuation_cases
    target = probability_weighted_target(cases) if cases else None
    upside = (target / price - 1) if (target and price) else None

    body: list[str] = []
    if notice:
        body.append(ui.status("error", "Not a research note", notice))

    body += [
        ui.masthead(
            bundle.company_name,
            bundle.ticker,
            "Equity research note",
            [
                bundle.display_industry,
                f"As of {bundle.as_of}",
                f"Prepared for {report.mandate.summary()}",
            ],
        ),
        ui.stat_strip(headline_stats(report)),
    ]

    level, message = report.verification_banner
    body.append(
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
    if bundle.implied is not None and bundle.implied.caveat:
        body.append(ui.status("warning", "Model divergence", bundle.implied.caveat))
    if bundle.staleness_note:
        body.append(ui.status("info", "Source currency", bundle.staleness_note))

    body.extend(_variant_section(rec))
    body.extend(_valuation_section(bundle, cases, price))
    body.extend(_thesis_section(rec))
    body.extend(_reconciliation_section(rec))
    body.extend(_financials_section(bundle))
    body.extend(_peers_section(bundle))
    body.extend(_management_section(rec))
    body.extend(_note_section(report))
    body.extend(_sources_section(report))

    body.append(
        '<p class="ar-foot" style="margin-top:2.6rem;border-top:1px solid '
        f'var(--rule);padding-top:.9rem">{escape(_disclaimer(report))}</p>'
    )

    title = f"{bundle.company_name} ({bundle.ticker}) research note"
    return (
        "<!doctype html>"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{escape(title)}</title>"
        f"{theme.stylesheet()}"
        "<style>"
        "body{margin:0;background:var(--paper);color:var(--ink);"
        "font-family:var(--sans);font-size:14.5px;line-height:1.62;"
        "-webkit-font-smoothing:antialiased}"
        ".ar-page{max-width:1180px;margin:0 auto;padding:2.4rem 2rem 4rem}"
        "@media print{body{background:#fff}.ar-page{padding:0;max-width:none}"
        ".ar-finding,.ar-split{break-inside:avoid}"
        "table.ar-table{break-inside:auto}"
        ".ar-sec{break-after:avoid}}"
        "</style></head>"
        f'<body><div class="ar-page">{"".join(body)}</div></body></html>'
    )


def _disclaimer(report: Report) -> str:
    """Carried on the exported file as well as the page.

    Read from configuration rather than written here. Two texts for one
    legal notice is how a disclaimer ends up saying different things on the
    screen and in the file somebody actually circulates.

    A note read six weeks later, detached from the application that produced
    it, is exactly where the reader most needs to be told what it is.
    """
    base = " ".join(get_settings().report.disclaimer.split())
    return f"{base} Report date {report.bundle.as_of}."


def _variant_section(rec) -> list[str]:
    out = [ui.section("Where this analysis departs from consensus")]
    if not rec.variant_views:
        out.append(
            ui.note(
                "No variant view was identified against the prevailing read."
            )
        )
        return out
    for view in rec.variant_views:
        out.append(
            ui.split(
                "Prevailing view",
                view.street_view,
                f"This analysis, {view.confidence} confidence",
                view.our_view,
                left_tone="street",
                right_tone="ours",
            )
        )
        out.append(ui.footnote(f"Evidence: {view.supporting_evidence}"))
    return out


def _valuation_section(bundle, cases, price) -> list[str]:
    out: list[str] = []
    context = bundle.cash_context
    implied = bundle.implied

    if context and context.summary():
        out.append(ui.section("What the market is paying"))
        out.append(
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
                        _pct(context.fcf_yield) if context.fcf_yield else "NM",
                    ),
                    Stat("Filed free cash flow CAGR", _pct(context.fcf_cagr)),
                ]
            )
        )
        out.append(ui.caption(context.summary()))

    if bundle.dcf is None or bundle.dcf_inputs is None:
        out.append(ui.section("Valuation"))
        out.append(
            ui.note("No discounted cash flow model was produced for this filer.")
        )
        return out

    out.append(ui.section("Implied expectations", "The primary output"))
    out.append(
        ui.stat_strip(
            [
                Stat(
                    "Implied annual FCF growth",
                    _pct(implied.implied_growth)
                    if implied and implied.implied_growth is not None
                    else "Unsolvable",
                ),
                Stat(
                    "Implied discount rate",
                    _pct(implied.implied_discount_rate)
                    if implied and implied.implied_discount_rate is not None
                    else "NM",
                ),
                Stat(
                    "Terminal share of value",
                    _pct(bundle.dcf.terminal_share_of_value, 0),
                ),
            ]
        )
    )

    out.append(ui.section("Cases"))
    out.append(charts.figure(charts.valuation_range(cases, price, width=_CHART)))
    out.append(
        charts.figure(
            charts.dcf_bridge(bundle.dcf, bundle.dcf_inputs, width=_CHART),
            "How much of the valuation is the forecast and how much is the "
            "perpetuity assumption behind it.",
        )
    )
    out.append(
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
                    "value": _usd(c.value_per_share),
                    "growth": _pct(c.growth),
                    "wacc": _pct(c.discount_rate),
                    "probability": _pct(c.probability, 0),
                    "upside": _signed_pct(c.upside_vs(price)) if price else "NM",
                }
                for c in cases
            ],
        )
    )

    projection = format_projection_table(bundle)
    if projection:
        out.append(ui.section("Projection", "Computed, not filed"))
        out.append(
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

    out.append(ui.section("Sensitivity", "Value per share"))
    out.append(
        ui.caption(
            "Discount rate against terminal growth, all else unchanged. "
            "Cells are shaded by whether they clear the traded price."
        )
    )
    out.append(
        ui.sensitivity_table(
            sensitivity_grid(
                bundle.dcf_inputs,
                [0.07, 0.08, 0.09, 0.10, 0.11],
                [0.015, 0.020, 0.025, 0.030],
            ),
            price,
        )
    )

    out.append(ui.section("Assumptions"))
    out.append(
        ui.caption(
            "Every input the model reads, with the basis a reviewer needs to "
            "challenge it. Inputs that are conventions rather than filings "
            "say so."
        )
    )
    out.append(
        ui.kv_table(
            [(a.name, a.display(), a.basis) for a in bundle.dcf_inputs.assumptions()]
        )
    )
    return out


def _thesis_section(rec) -> list[str]:
    out = [
        ui.section("Financial trajectory"),
        ui.paragraphs(rec.financial_trajectory),
        ui.section("Bull and bear"),
        ui.split(
            "Bull case",
            rec.bull_case,
            "Bear case",
            rec.bear_case,
            left_tone="bull",
            right_tone="bear",
        ),
        ui.section("What would have to be true"),
        ui.paragraphs(rec.what_would_have_to_be_true),
        ui.section("Valuation context"),
        ui.paragraphs(rec.valuation_context),
        ui.section("Disconfirming evidence", "Produced on every report"),
        ui.status("warning", "Against this thesis", rec.disconfirming_evidence),
    ]
    if rec.data_limitations:
        out.append(ui.section("Data limitations"))
        out.append(ui.paragraphs(rec.data_limitations))
    if rec.catalysts:
        out.append(ui.section("Catalysts"))
        out.append(
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
        out.append(ui.section("Questions for management"))
        out.append(ui.bullets(rec.questions_for_management))
    return out


def _reconciliation_section(rec) -> list[str]:
    out = [
        ui.section(
            "Narrative against reported figures",
            f"{len(rec.divergences)} divergence(s), "
            f"{len(rec.corroborations)} corroborated",
        )
    ]
    if not rec.reconciliations:
        out.append(ui.note("No reconciliation was produced for this filer."))
        return out
    for item in rec.divergences + rec.corroborations:
        out.append(
            ui.finding(
                item.management_claim,
                item.what_the_data_shows,
                item.assessment,
                item.agrees,
                item.materiality,
            )
        )
    return out


def _financials_section(bundle) -> list[str]:
    out = [ui.section("Filed trends", "From XBRL, as submitted")]
    if bundle.series is not None:
        out.append(
            charts.figure(
                charts.metric_bars(
                    bundle.series,
                    "revenue",
                    "Revenue",
                    "As filed, by fiscal year",
                    width=_CHART,
                )
            )
        )
        out.append(charts.figure(charts.margin_lines(bundle.series, width=_CHART)))
        out.append(
            charts.figure(charts.free_cash_flow_history(bundle.series, width=_CHART))
        )

    statement = build_statement(bundle.series, bundle.sector_class)
    if statement:
        out.append(ui.section("Financial summary", "Statement order"))
        out.append(ui.statement_table(statement, periods_of(bundle.series)))
        out.append(
            ui.footnote(
                "Lines set in the lighter weight are computed from the filed "
                "lines above them. Every other figure is exactly as submitted "
                "to the SEC."
            )
        )

    if bundle.health_scores:
        out.append(ui.section("Financial health"))
        out.append(
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
    return out


def _peers_section(bundle) -> list[str]:
    table = bundle.comps
    if table is None or not table.rows:
        return [
            ui.section("Comparable companies"),
            ui.note("No peer comparison is available for this filer."),
        ]
    out = [
        ui.section("Comparable companies", f"Peer set from {table.peer_source}"),
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
        ),
        ui.footnote(
            "Dollar figures in millions. EBITDA is operating income plus "
            "depreciation and amortisation, a convention rather than a "
            "reported line. " + (table.coverage_note or "")
        ),
    ]
    out.append(charts.figure(charts.peer_bars(table, "pe", "Price to earnings", _CHART)))
    out.append(
        charts.figure(charts.peer_bars(table, "ev_to_ebitda", "EV / EBITDA", _CHART))
    )
    return out


def _management_section(rec) -> list[str]:
    management = rec.management
    if not management.executives and not management.compensation_structure:
        return []
    out = [ui.section("Management and governance")]
    if management.executives:
        out.append(
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
    out.append(
        ui.split(
            "What the plan rewards",
            management.compensation_structure,
            "Whether it points where the business does",
            management.alignment_assessment,
        )
    )
    out.append(
        ui.split(
            "Board independence",
            management.board_independence,
            "Insider ownership",
            management.insider_ownership,
        )
    )
    if management.concerns:
        out.append(ui.section("Governance concerns"))
        out.append(ui.bullets(management.concerns))
    return out


def _note_section(report: Report) -> list[str]:
    return [
        ui.section("Descriptive note", "Every claim cited"),
        ui.prose(markdown.to_html(report.narrative_markdown)),
    ]


def _sources_section(report: Report) -> list[str]:
    bundle = report.bundle
    out = [
        ui.section("Documents used", f"{bundle.total_passage_chars:,} characters"),
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
    ]
    if report.mandate.assumptions:
        out.append(ui.section("Assumptions made about the mandate"))
        out.append(ui.bullets(report.mandate.assumptions))

    if bundle.gaps:
        out.append(ui.section("Gaps in the source material"))
        out.append(
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
    if report.citations:
        out.append(ui.section("Citations", f"{len(report.citations)} resolved"))
        out.append(
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
                        "quote": c.quote,
                        "source": c.source_label,
                        "status": "Verified" if c.verified else c.status,
                        "link": c.source_url,
                    }
                    for c in report.citations
                ],
            )
        )
    return out


def _md(text: object) -> str:
    """Model and filing text, made safe for a Markdown document.

    `report_to_html` escapes everything through the component layer. The
    Markdown writer interpolated the same strings raw, so a company name or
    a model sentence containing a tag travelled verbatim into a .md file,
    and most Markdown renderers (wikis, issue trackers, chat clients) pass
    inline HTML straight through to the page.

    A pipe is escaped for a different reason: one in a company name silently
    breaks every row of the table it lands in.
    """
    if text is None:
        return ""
    out = str(text).strip()
    out = out.replace("<", "&lt;").replace(">", "&gt;")
    return out.replace("|", "\\|")


def _md_block(text: object) -> str:
    """The same, for prose that may legitimately span lines."""
    if text is None:
        return ""
    return str(text).strip().replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------- Markdown


def report_to_markdown(report: Report, notice: str = "") -> str:
    """Plain text, for pasting into a memo without carrying styling along."""
    bundle = report.bundle
    rec = report.reconciliation
    price = bundle.quote.price if bundle.quote else None
    cases = bundle.valuation_cases
    target = probability_weighted_target(cases) if cases else None
    upside = (target / price - 1) if (target and price) else None

    lines = []
    if notice:
        lines += [f"> **NOT A RESEARCH NOTE.** {_md_block(notice)}", ""]
    lines += [
        f"# {_md(bundle.company_name)} ({_md(bundle.ticker)})",
        "",
        f"{_md(bundle.display_industry)}. As of {_md(bundle.as_of)}. "
        f"Prepared for {_md(report.mandate.summary())}.",
        "",
        "## Headline",
        "",
        f"- Traded price: {_usd(price)}",
        f"- Market capitalisation: {_billions(bundle.market_cap)}",
        f"- Probability-weighted target: {_usd(target)}",
        f"- Implied upside: {_signed_pct(upside)}",
    ]
    if bundle.implied:
        lines.append(
            f"- Price implies annual FCF growth: "
            f"{_pct(bundle.implied.implied_growth)}"
        )
        lines.append(
            f"- Price implies a discount rate of "
            f"{_pct(bundle.implied.implied_discount_rate)}"
        )
    if bundle.cash_context and bundle.cash_context.multiple_of_fcf:
        lines.append(
            f"- Market capitalises free cash flow at "
            f"{bundle.cash_context.multiple_of_fcf:,.0f}x, against a filed "
            f"CAGR of {_pct(bundle.cash_context.fcf_cagr)}"
        )

    _, message = report.verification_banner
    lines += ["", "## Verification", "", _md_block(message)]
    if bundle.implied and bundle.implied.caveat:
        lines += ["", _md_block(bundle.implied.caveat)]

    if rec.variant_views:
        lines += ["", "## Where this analysis departs from consensus", ""]
        for view in rec.variant_views:
            lines += [
                f"**Prevailing view.** {_md_block(view.street_view)}",
                "",
                f"**This analysis ({_md(view.confidence)} confidence).** {_md_block(view.our_view)}",
                "",
                f"*Evidence.* {_md_block(view.supporting_evidence)}",
                "",
            ]

    lines += ["", "## Financial trajectory", "", _md_block(rec.financial_trajectory)]
    lines += ["", "## Narrative against reported figures", ""]
    for item in rec.divergences + rec.corroborations:
        label = "Corroborated" if item.agrees else "Divergence"
        lines += [
            f"### {label}, {_md(item.materiality)} materiality",
            "",
            f"**Management position.** {_md_block(item.management_claim)}",
            "",
            f"**Reported figures.** {_md_block(item.what_the_data_shows)}",
            "",
            f"**Assessment.** {_md_block(item.assessment)}",
            "",
        ]

    lines += ["", "## Bull case", "", _md_block(rec.bull_case) or "Not stated."]
    lines += ["", "## Bear case", "", _md_block(rec.bear_case) or "Not stated."]
    lines += [
        "",
        "## What would have to be true",
        "",
        _md_block(rec.what_would_have_to_be_true) or "Not stated.",
    ]
    lines += ["", "## Valuation context", "",
              _md_block(rec.valuation_context) or "Not stated."]
    lines += ["", "## Disconfirming evidence", "",
              _md_block(rec.disconfirming_evidence)]

    if cases:
        lines += ["", "## Cases", "", "| Case | Value per share | Upside |", "| --- | ---: | ---: |"]
        for case in cases:
            lines.append(
                f"| {_md(case.name)} | {_usd(case.value_per_share)} | "
                f"{_signed_pct(case.upside_vs(price)) if price else 'NM'} |"
            )

    statement = build_statement(bundle.series, bundle.sector_class)
    if statement:
        periods = periods_of(bundle.series)
        lines += [
            "",
            "## Financial summary",
            "",
            "USD millions, as filed. Growth rates, margins and free cash "
            "flow are computed from the filed lines.",
            "",
            "| | " + " | ".join(_md(p) for p in periods) + " |",
            "| --- |" + " ---: |" * len(periods),
        ]
        for row in statement:
            if row.kind == "section":
                heading = f"{row.label} ({row.note})" if row.note else row.label
                lines.append(f"| **{_md(heading)}** |" + " |" * len(periods))
                continue
            cells = " | ".join(_md(row.values.get(p, "")) for p in periods)
            # On screen a derived row is distinguished by weight and colour,
            # neither of which survives a paste into a memo or a spreadsheet,
            # so plain text says it in words.
            label = _md(row.label)
            if row.kind == "derived":
                label += " (derived)"
            lines.append(f"| {label} | {cells} |")

    if bundle.dcf_inputs is not None:
        lines += [
            "",
            "## Assumptions",
            "",
            "| Input | Value | Basis |",
            "| --- | ---: | --- |",
        ]
        for a in bundle.dcf_inputs.assumptions():
            lines.append(f"| {_md(a.name)} | {_md(a.display())} | {_md(a.basis)} |")

    projection = format_projection_table(bundle)
    if projection:
        lines += [
            "",
            "## Projection",
            "",
            "Computed from the assumptions above, not taken from a filing.",
            "",
            "| Year | Free cash flow | Discount factor | Present value |",
            "| --- | ---: | ---: | ---: |",
        ]
        for row in projection:
            lines.append(
                f"| {_md(row['Year'])} | {_md(row['Free cash flow'])} | "
                f"{_md(row['Discount factor'])} | {_md(row['Present value'])} |"
            )

    if bundle.comps is not None and bundle.comps.rows:
        # Markdown is what gets pasted into a memo, and a memo without the
        # comparables has lost the relative-valuation half of the argument.
        columns = [
            "Company", "Ticker", "FYE", "Share price", "Equity value",
            "Enterprise value", "Revenue", "EBITDA", "EBITDA margin",
            "EV/EBITDA", "P/E",
        ]
        lines += [
            "",
            "## Comparable companies",
            "",
            f"Peer set from {_md(bundle.comps.peer_source)}. Dollar figures "
            f"in millions. EBITDA is operating income plus depreciation and "
            f"amortisation, a convention rather than a reported line.",
            "",
            "| " + " | ".join(columns) + " |",
            "| --- |" + " ---: |" * (len(columns) - 1),
        ]
        for row in format_comp_table(bundle.comps):
            if not any(v.strip() for v in row.values()):
                continue
            cells = " | ".join(_md(row.get(c, "")) for c in columns)
            lines.append(f"| {cells} |")
        if bundle.comps.coverage_note:
            lines += ["", _md_block(bundle.comps.coverage_note)]

    if rec.catalysts:
        lines += ["", "## Catalysts", ""]
        for catalyst in rec.catalysts:
            lines.append(
                f"- **{_md(catalyst.timeframe)}.** {_md_block(catalyst.description)} "
                f"Confirming evidence: {_md_block(catalyst.confirming_evidence)}"
            )

    if rec.questions_for_management:
        lines += ["", "## Questions for management", ""]
        lines += [f"- {_md_block(q)}" for q in rec.questions_for_management]

    lines += ["", "## Descriptive note", "", _md_block(report.narrative_markdown)]

    lines += ["", "## Sources", ""]
    for passage in bundle.passages:
        lines.append(
            f"- {_md(passage.label)} ({_md(passage.form)}, filed "
            f"{_md(passage.filing_date)}): {_md(passage.source_url)}"
        )
    if bundle.gaps:
        lines += ["", "### Gaps in the source material", ""]
        for gap in bundle.gaps:
            lines.append(f"- [{_md(gap.severity)}] {_md(gap.source)}: {_md_block(gap.reason)}")

    lines += ["", "---", "", _disclaimer(report)]
    return "\n".join(lines)
