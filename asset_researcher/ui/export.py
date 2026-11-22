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
from asset_researcher.ui import format as fmt
from asset_researcher.ui import document
from asset_researcher.ui.headline import headline_stats
from asset_researcher.ui.components import Col, Stat
from asset_researcher.ui.summary import summary_lines

# Wider than the two-column screen layout, because the export is read as one
# continuous document rather than a set of tabs.
_CHART = 620


# --------------------------------------------------------------------- HTML


# The section bar has to scroll the document itself rather than rely on
# the browser resolving "#s-valuation" against it.
#
# This file is shown two ways. Opened on its own, a fragment link works
# as fragment links do. Rendered inside the app, it is the srcdoc of an
# iframe whose baseURI is the PARENT page - measured as
# "http://host/?k=...&view=samples" - so "#s-valuation" resolves against
# that page instead, and clicking a section name navigated the frame to
# the app's own URL rather than scrolling. Every section link in every
# sample was dead for that reason.
#
# Resolving the target by id and scrolling to it is correct in both
# cases and depends on no base URL at all. The href stays, so the links
# still work with script disabled and still say where they go.
# The handler as every note built before this carries it, kept here so
# `frame.repair` can replace it in the six that are already sealed.
OLD_CLICK = """  document.addEventListener('click', function (event) {
    var link = event.target.closest('nav.ar-nav a[href^="#"]');
    if (!link) return;
    var target = document.getElementById(link.getAttribute('href').slice(1));
    if (!target) return;
    event.preventDefault();
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    // Moves keyboard focus with the view, so the next Tab continues from
    // the section the reader just jumped to rather than from the bar.
    target.setAttribute('tabindex', '-1');
    target.focus({ preventScroll: true });
  });"""

# EVERY fragment link in the note, not only the ones in the section bar.
#
# Scoping the handler to `nav.ar-nav` left the rest of the document's
# own links resolving the broken way, and one of them is in the
# masthead: the "Filed 2026-08-05" chip points at `#s-provenance`.
# Clicking it navigated the FRAME to the application's own URL, so the
# whole site - top bar, section index, the lot - rendered a second time
# inside the box where the note is supposed to be. The cause is the same
# base-URL inheritance described above; only the selector decided which
# links it still reached.
#
# The flash is the other half of landing somewhere. A jump that moves
# 30,000px in one frame gives a reader no sense of where they arrived or
# which direction they came from, and `:target` cannot mark it because
# the default navigation is prevented. So the destination says so
# itself, for two seconds, and then stops.
NEW_CLICK = """  function arFlash(target) {
    target.classList.remove('ar-hit');
    void target.offsetWidth;
    target.classList.add('ar-hit');
    window.setTimeout(function () {
      target.classList.remove('ar-hit');
    }, 2400);
  }
  document.addEventListener('click', function (event) {
    var link = event.target.closest('a[href^="#"]');
    if (!link) return;
    var target = document.getElementById(link.getAttribute('href').slice(1));
    if (!target) return;
    event.preventDefault();
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    arFlash(target);
    // Moves keyboard focus with the view, so the next Tab continues from
    // the section the reader just jumped to rather than from the bar.
    target.setAttribute('tabindex', '-1');
    target.focus({ preventScroll: true });
  });"""

_JUMP_SCRIPT = """<script>
(function () {
__CLICK__

  // A note runs to about 36,000px and was shown in a 2,000px frame:
  // one eighteenth of the document at a time, through a scrollbar
  // nested inside the page's own, with the note's section index
  // trapped in the frame. The frame is same-origin, so the document
  // can size it to its own content and the page then scrolls once.
  //
  // Guarded twice. A downloaded note has no frameElement, and reaching
  // for one across origins throws - a note that raises on load shows a
  // reader nothing at all.
  function arTableStops() {
  /* A wrapper is a tab stop only where it actually scrolls.
     Announcing "scrollable when narrow" on a wrapper that cannot
     scroll describes a capability it does not have, and ten of
     eleven were in that state above 900px. */
  var wraps = document.querySelectorAll('.ar-table-wrap');
  for (var i = 0; i < wraps.length; i++) {
    var w = wraps[i];
    if (w.getAttribute('role') === 'region') continue;
    if (w.scrollWidth > w.clientWidth + 1) {
      w.setAttribute('tabindex', '0');
      w.setAttribute('role', 'group');
      w.setAttribute('aria-label', 'Table, scrollable');
    } else {
      w.removeAttribute('tabindex');
      w.removeAttribute('role');
      w.removeAttribute('aria-label');
    }
  }
}
function fitFrame() {
    try {
      var frame = window.frameElement;
      if (!frame) return;
      var height = document.documentElement.scrollHeight;
      if (!height) return;
      frame.style.height = height + 'px';
      var wrap = frame.parentElement;
      if (wrap) wrap.style.height = height + 'px';
    } catch (e) {
      // Cross-origin, or a host that does not allow it. The frame keeps
      // whatever height it was given and scrolls, which is the old
      // behaviour rather than a broken one.
    }
  }
  // Braced, and both functions on every entry point.
  //
  // This line read `if (...) fitFrame();arTableStops();` with no
  // braces, which makes the `else` below belong to no `if` - a
  // SyntaxError that cost the entire script, not the one statement.
  // Neither function was ever defined in any note that shipped. The
  // frame therefore stayed at the 2,000px the host gave it with a
  // 38,959px document scrolling inside it, so every section link in
  // the index scrolled the PAGE to a position far past its end and
  // landed, clamped, at the same spot every time; and the table
  // wrappers kept whatever tab-stop state the server guessed.
  //
  // Nothing in the suite could see it. Every test asserts on the
  // string this module RETURNS, and that string always declared both
  // functions exactly once, spelled correctly. A string is not a
  // program, and nothing here was ever parsed.
  function arFit() { fitFrame(); arTableStops(); }
  if (document.readyState === 'complete') { arFit(); }
  else { window.addEventListener('load', arFit); }
  window.addEventListener('resize', arFit);
})();
</script>""".replace("__CLICK__", NEW_CLICK)


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
            bundle.as_of,
            [
                bundle.display_industry,
                f"Prepared for {report.mandate.summary()}",
            ],
        ),
        ui.chips(document.provenance_items(report)),
        ui.stat_strip(headline_stats(report)),
    ]

    blocks = document.sections(report)
    body.append(ui.nav([section.label for section in blocks]))
    body.extend(section.html for section in blocks)

    body.append(
        '<p class="ar-foot" style="margin-top:2.6rem;border-top:1px solid '
        f'var(--rule);padding-top:.9rem">{escape(_disclaimer(report))}</p>'
    )

    # Through `_clean` as well as `escape`: the document title is the one
    # string that bypasses the component layer, and a NUL here makes the
    # whole document non-conforming.
    title = _clean(f"{bundle.company_name} ({bundle.ticker}) research note")
    return (
        "<!doctype html>"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{escape(title)}</title>"
        f"{theme.document_stylesheet()}"
        "<style>"
        "body{margin:0;background:var(--paper);color:var(--ink);"
        "font-family:var(--sans);font-size:14.5px;line-height:1.62;"
        "-webkit-font-smoothing:antialiased}"
        ".ar-page{max-width:1180px;margin:0 auto;padding:2.4rem 2rem 4rem}"
        "@media print{body{background:#fff}.ar-page{padding:0;max-width:none}"
        ".ar-finding,.ar-split{break-inside:avoid}"
        "table.ar-table{break-inside:auto}"
        ".ar-sec{break-after:avoid}"
        # A horizontally scrolling table prints only the visible slice. The
        # comparables table lost ten of sixteen columns, every multiple
        # among them, with no cue that anything was missing.
        ".ar-table-wrap,.ar-table-wrap:has(>.ar-table-scroll)"
        "{overflow:visible!important}"
        "table.ar-table.ar-table-scroll{width:100%;table-layout:fixed;"
        "font-size:7.5pt}"
        "table.ar-table.ar-table-scroll td,"
        "table.ar-table.ar-table-scroll th{white-space:normal;"
        "word-break:break-word;padding:3px 4px}"
        "table.ar-table thead th{position:static}"
        ".ar-nav{display:none}}"
        "</style></head>"
        # A `main` landmark and a bypass link. The exported file had
        # neither, and it carries twenty section anchors ahead of its
        # content, so a screen-reader user had no way past the index.
        f'<body><a class="ar-skip" href="#ar-content">Skip to report</a>'
        f'<main id="ar-content" class="ar-page">{"".join(body)}</main>'
        f"{_JUMP_SCRIPT}"
        f"</body></html>"
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


_CONTROL = {c: None for c in range(32) if c not in (9, 10, 13)}
_CONTROL[127] = None

# Markdown gives these meaning at the start of a line, and model prose has
# no business opening a heading, a list or a quote inside a research note.
_STRUCTURAL = ("#", ">", "-", "+", "*", "=", "|")


def _clean(text: str) -> str:
    """Strip C0 control characters.

    `html.escape` does not touch them, so a NUL in a company name made the
    HTML non-conforming and the Markdown file binary to git and to every
    wiki that would receive it.
    """
    return text.translate(_CONTROL).strip()


def _defuse_leading(text: str) -> str:
    if text[:1] in _STRUCTURAL:
        return "\\" + text
    return text


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
    out = _clean(str(text))
    out = out.replace("<", "&lt;").replace(">", "&gt;")
    # Newlines collapse. A model sentence carrying "\n\n## Conclusion: SELL"
    # opened a real heading inside the note, and an unterminated bold run
    # across a line break corrupted every row after it.
    out = " ".join(out.split())
    out = out.replace("|", "\\|")
    return _defuse_leading(out)


def _md_block(text: object) -> str:
    """The same, for prose that may legitimately span lines."""
    if text is None:
        return ""
    out = _clean(str(text)).replace("<", "&lt;").replace(">", "&gt;")
    # Paragraph breaks survive here, because this is prose; structural
    # characters at the start of any line do not.
    paragraphs = [
        _defuse_leading(" ".join(block.split()))
        for block in out.split("\n\n")
        if block.strip()
    ]
    return "\n\n".join(paragraphs)


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
        f"- Traded price: {fmt.usd(price)}",
        f"- Market capitalisation: {fmt.scaled_usd(bundle.market_cap)}",
        f"- Probability-weighted target: {fmt.usd(target)}",
        f"- Implied upside: {fmt.signed_pct(upside)}",
    ]
    if bundle.implied:
        lines.append(
            f"- Price implies annual FCF growth: "
            f"{fmt.pct(bundle.implied.implied_growth)}"
        )
        lines.append(
            f"- Price implies a discount rate of "
            f"{fmt.pct(bundle.implied.implied_discount_rate)}"
        )
    if bundle.cash_context and bundle.cash_context.multiple_of_fcf:
        lines.append(
            f"- Market capitalises free cash flow at "
            f"{bundle.cash_context.multiple_of_fcf:,.0f}x, against a filed "
            f"CAGR of {fmt.pct(bundle.cash_context.fcf_cagr)}"
        )

    # The summary is the block a reader of the plain-text version most
    # needs, and it was the one the Markdown path did not carry.
    lines += ["", "## Investment summary", ""]
    lines += [_md_block(line) for line in summary_lines(report)]

    _, message = report.verification_banner
    lines += ["", "## Provenance", "", _md_block(message)]
    if bundle.implied and bundle.implied.caveat:
        lines += ["", _md_block(bundle.implied.caveat)]

    if rec.variant_views:
        lines += ["", "## Variant perception", ""]
        for view in rec.variant_views:
            lines += [
                f"**Prevailing view.** {_md_block(view.street_view)}",
                "",
                f"**This analysis ({_md(view.confidence)} confidence).** {_md_block(view.our_view)}",
                "",
                f"*Evidence.* {_md_block(view.supporting_evidence)}",
                "",
            ]

    lines += ["", "## Trajectory", "", _md_block(rec.financial_trajectory)]
    lines += ["", "## Management vs. filed figures", ""]
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
        "## What must be true",
        "",
        _md_block(rec.what_would_have_to_be_true) or "Not stated.",
    ]
    lines += ["", "## Current valuation", "",
              _md_block(rec.valuation_context) or "Not stated."]
    lines += ["", "## Bear case", "",
              _md_block(rec.disconfirming_evidence)]

    if cases:
        lines += ["", "## Cases", "", "| Case | Value per share | Upside |", "| --- | ---: | ---: |"]
        for case in cases:
            lines.append(
                f"| {_md(case.name)} | {fmt.usd(case.value_per_share)} | "
                f"{fmt.signed_pct(case.upside_vs(price)) if price else 'NM'} |"
            )

    statement = build_statement(bundle.series, bundle.sector_class)
    if statement:
        periods = periods_of(bundle.series)
        lines += [
            "",
            "## Financials",
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
            "## Peers",
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

    lines += ["", "## Business description", "", _md_block(report.narrative_markdown)]

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
