"""HTML building blocks for the report view.

Every block returns a string, takes no Streamlit dependency and escapes any
text that came from a model or a filing. That keeps the view testable: a test
can assert that a divergence is rendered with its materiality and that a
negative figure is parenthesised, without starting a server.

Two conventions run through all of it:

**Markup is emitted on one line.** Streamlit passes these strings through a
Markdown renderer before they reach the page, and that renderer treats a
blank line as a paragraph break and four leading spaces as a code block.
Indented, pretty-printed HTML arrives broken. `_one_line` collapses it.

**Nothing interpolated is trusted.** Company names, filing text and model
prose all go through `escape`. The one exception is `prose`, which receives
Markdown the app has already rendered, and which is documented as such.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from html import escape
from typing import Callable, Iterable, Sequence

from asset_researcher.ui import theme

_WS_BETWEEN_TAGS = re.compile(r">\s+<")
_RUNS = re.compile(r"\s{2,}")

# Tab, newline and carriage return survive; the rest of C0 does not.
_CONTROL = {c: None for c in range(32) if c not in (9, 10, 13)}
_CONTROL[127] = None


def _one_line(markup: str) -> str:
    """Collapse the whitespace a Markdown renderer would misread."""
    return _RUNS.sub(" ", _WS_BETWEEN_TAGS.sub("><", markup.strip()))


def escape_text(value: str) -> str:
    """Escape a composed sentence for the page.

    Composed sentences mix filed figures with model judgements, so they are
    escaped like anything else that passes through a model.

    C0 control characters are stripped as well as escaped, which
    `html.escape` alone does not do. The sibling `_text` has always done
    this; `escape_text` arrived later without it and reopened the hole for
    anything routed through the summary block, in the page and in the HTML
    export both.
    """
    return escape(str(value).translate(_CONTROL))


def plural(count: int, noun: str, plural_form: str | None = None) -> str:
    """"1 divergence", "2 divergences". Never "1 divergence(s)".

    The parenthesised plural is the single most recognisable sign that a
    sentence was assembled by a program rather than written, and it was
    appearing in the section notes and the staleness line, both of which a
    reader meets in the first screen.
    """
    word = noun if count == 1 else (plural_form or noun + "s")
    return f"{count:,} {word}"


def _text(value: object) -> str:
    """Escaped text, with an em-space placeholder for nothing at all.

    An empty table cell and a cell holding a missing value look identical,
    which is the one thing a financial table must never do. Absence is
    written as a word by the formatters upstream; this guards the rest.
    """
    if value is None:
        return "&mdash;"
    # C0 control characters survive html.escape, and a NUL makes the
    # document non-conforming: browsers substitute U+FFFD.
    rendered = str(value).translate(_CONTROL).strip()
    return escape(rendered) if rendered else "&nbsp;"


# --------------------------------------------------------------- masthead


def masthead(
    title: str, ticker: str, provenance: str, subline: Sequence[str]
) -> str:
    """Company name, ticker, and the provenance line beneath it.

    The eyebrow above the title is gone. A small tracked label announcing
    "EQUITY RESEARCH NOTE" above a heading that already says what it is adds
    a rank to the hierarchy and carries no information; the heading speaks
    for itself. The report date moves into the left rail, where the rest of
    the page keeps its quiet provenance.
    """
    parts = '<span class="sep">/</span>'.join(
        f"<span>{_text(p)}</span>" for p in subline if p
    )
    return _one_line(
        f'<div class="ar-masthead">'
        f'<div class="rail">{_text(provenance)}</div>'
        f"<div>"
        f'<h1 class="ar-title">{_text(title)}'
        # The space matters: the span is display:block so the eye sees two
        # lines, but textContent concatenates, and the heading was
        # announced as "Realty Income Corpo" and "Truist Financial
        # Corptfc". Streamlit also derives its anchor slug from that
        # string.
        f' <span class="ar-ticker">{_text(ticker)}</span></h1>'
        f'<div class="ar-subline">{parts}</div>'
        f"</div></div>"
    )


# ------------------------------------------------------------- stat strip


@dataclass(frozen=True)
class Stat:
    label: str
    value: str
    note: str = ""
    tone: str = ""  # "" | "pos" | "neg"
    # The one figure in a strip that this report authored, set a rank
    # larger than the ones it was handed.
    lead: bool = False


def stat_strip(stats: Iterable[Stat]) -> str:
    """The headline figures, as one hairline-divided row.

    A value of "NM" or "Unsolvable" is set smaller and recessive: it is a
    statement about the data rather than a figure, and giving it the same
    weight as a real number overstates it.
    """
    cells = []
    for stat in stats:
        tone = stat.tone
        if stat.value.strip() in {"NM", "Unsolvable", "n/a", "&mdash;"}:
            tone = "nm"
        # The note cell is always emitted, even when empty. `.ar-stat` is
        # `display: contents`, so each stat must occupy exactly three grid
        # cells; a missing note pulls the next stat's label up a row and
        # the whole strip staircases.
        cells.append(
            f'<div class="ar-stat{" lead" if stat.lead else ""}">'
            f'<div class="ar-stat-label">{_text(stat.label)}</div>'
            f'<div class="ar-stat-value {tone}">{_text(stat.value)}</div>'
            f'<div class="ar-stat-note">{_text(stat.note) if stat.note else "&nbsp;"}</div>'
            f"</div>"
        )
    return _one_line(f'<div class="ar-stats">{"".join(cells)}</div>')


# ---------------------------------------------------------------- framing


def slug(label: str) -> str:
    """A stable anchor id for a section, so the index can reach it."""
    return "s-" + re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def section(label: str, note: str = "") -> str:
    """A section label in the left rail, with a rule across the content
    column that fades toward the margin.

    The label sits in the rail rather than above the content because that
    is what gives the page a second axis. Everything in one centred column
    with even vertical rhythm is the shape of a template.
    """
    trailing = f'<div class="ar-sec-note">{_text(note)}</div>' if note else ""
    return _one_line(
        # A div, not a section. This is a heading band: the content it
        # names follows as a sibling block, so marking it `<section>`
        # published eighteen landmarks that each contained only their own
        # title, and a screen reader's landmark list offered eighteen
        # empty regions. The `<h2>` is what carries the structure, and it
        # stays.
        f'<div class="ar-sec" id="{slug(label)}">'
        f'<h2 class="ar-sec-label">{_text(label)}</h2>'
        f'<div class="ar-sec-body"><div class="ar-sec-rule"></div>'
        f"{trailing}</div></div>"
    )


def row(*parts: str) -> str:
    """Two or more pieces side by side, inside the content column.

    Laid out here rather than with Streamlit columns, because a Streamlit
    column is its own full-width block outside this grid: charts placed in
    one escaped the content column and stopped lining up with the tables
    above them. Doing it in our own markup is also what lets the screen and
    the exported file be the same object.
    """
    kept = [part for part in parts if part]
    if not kept:
        return ""
    if len(kept) == 1:
        return kept[0]
    return f'<div class="ar-row">{"".join(kept)}</div>'


def block(*parts: str) -> str:
    """Content aligned under the section rule, leaving the rail empty."""
    body = "".join(part for part in parts if part)
    return f'<div class="ar-block">{body}</div>' if body else ""


def chips(items: Sequence[tuple[str, str]]) -> str:
    """Provenance in a line beside the company name.

    Each chip links to the note at the foot carrying the full wording. The
    three states these replace (citations located, model divergence, filing
    age) are real and belong on the page; they do not belong in the most
    valuable space on it.
    """
    links = "".join(
        f'<a class="{tone}" href="#s-provenance">{_text(label)}</a>'
        for label, tone in items
    )
    return _one_line(f'<div class="ar-chips">{links}</div>') if links else ""


def nav(labels: Sequence[str]) -> str:
    """The section bar, stuck to the top of the viewport.

    The report is one continuous document rather than nine tabs, because a
    research note is read top to bottom and then jumped back through, and
    this is the jumping back. It sticks because the need to jump arises
    deep in the scroll, which is exactly where a list that only exists at
    the top of the page is useless.

    It was previously a column in a collapsible drawer, below four input
    widgets, which made the one control a reader uses constantly the
    hardest thing on the page to reach.
    """
    links = "".join(
        f'<a href="#{slug(label)}">{_text(label)}</a>' for label in labels
    )
    return _one_line(f'<nav class="ar-nav">{links}</nav>')


def caption(text: str) -> str:
    return _one_line(f'<p class="ar-caption">{_text(text)}</p>')


def footnote(text: str) -> str:
    return _one_line(f'<p class="ar-foot">{_text(text)}</p>')


def legend(*rendered: str) -> str:
    """A key for whichever tokens the tables above actually used.

    Printed, not only hovered. A tooltip serves a reader who already
    suspects there is something to find; a reader meeting "NM" for the
    first time needs it in the text. Only the tokens present are
    explained, so a page with no refusals carries no key.
    """
    blob = " ".join(rendered)
    parts = [
        f"<strong>{token}</strong> {_GLOSS[token].split(':', 1)[1].strip()}"
        for token in ("NM", "n.d.")
        if f">{token}</abbr>" in blob
    ]
    if not parts:
        return ""
    return _one_line(
        f'<p class="ar-foot ar-legend">{" ".join(parts)}</p>'
    )


_STATUS_CLASS = {"success": "ok", "warning": "warn", "error": "bad", "info": "info"}


# What each level is, in a word, for readers who do not get the hue. The
# level was carried by the colour of a 10px label and a 1px rule and by
# nothing else: not to a screen reader, not in greyscale print, not in
# forced-colours mode.
_STATUS_WORD = {
    "error": "Error: ",
    "warning": "Warning: ",
    "success": "",
    "info": "",
}
_STATUS_ROLE = {"error": ' role="alert"', "warning": ' role="status"'}


# A figure in parentheses is negative, by the accounting convention this
# document follows everywhere. Screen readers at their default punctuation
# level do not speak brackets, so "(1,823.1)" was announced as "one
# thousand eight hundred twenty three point one" - the sign, which on a
# loss-making filer is the whole content of the cell, reached nobody who
# was not looking at it. The glyph stays exactly as printed; a spoken form
# is carried beside it.
_PARENTHESISED = re.compile(r"^\((.+)\)$")


# What the terse tokens mean, spelled out. They appeared up to 43 times
# on a single page and were glossed nowhere: the Health table writes "not
# meaningful for this sector" in full prose, so the document knows how to
# say it, and simply never said it where the two-letter form is used.
# The title carries the hover; the hidden span carries the screen reader.
_GLOSS = {
    "NM": "Not meaningful: the figure is computable but its denominator "
          "makes the result misleading, usually a negative or near-zero "
          "base, or a measure that does not apply to this sector.",
    "n.d.": "No data: the company did not report this figure for this "
            "period.",
    "n/a": "Not applicable to this filer.",
}


def _glossed(token: str) -> str:
    """A token the reader should not have to guess at."""
    meaning = _GLOSS[token]
    short = meaning.split(":")[0]
    return (
        f'<abbr class="ar-token" title="{_text(meaning)}">{_text(token)}</abbr>'
        f'<span class="ar-sr">, {_text(short.lower())}</span>'
    )


def _figure(value) -> str:
    """A figure cell's content, with its conventions made legible."""
    rendered = str(value).strip()
    if rendered in _GLOSS:
        return _glossed(rendered)
    match = _PARENTHESISED.match(rendered)
    if not match:
        return _text(value)
    return (
        f'<span aria-hidden="true">{_text(rendered)}</span>'
        f'<span class="ar-sr">minus {_text(match.group(1))}</span>'
    )


def status(level: str, tag: str, message: str) -> str:
    """A ruled status line, in place of a filled alert panel."""
    cls = _STATUS_CLASS.get(level, "info")
    word = _STATUS_WORD.get(level, "")
    spoken = f'<span class="ar-sr">{word}</span>' if word else ""
    return _one_line(
        f'<div class="ar-status {cls}"{_STATUS_ROLE.get(level, "")}>'
        f'{spoken}<span class="tag">{_text(tag)}</span>'
        f"{_text(message)}</div>"
    )


def note(text: str) -> str:
    """A search that ran and returned nothing. Always a sentence."""
    return status("info", "No finding", text)


def declined(text: str) -> str:
    """Something this tool deliberately refused to produce.

    A judgement, not a gap. One grey "Not available" used to serve three
    different states - a search that found nothing, a deliberate refusal,
    and a step that should have produced output and did not - and reading
    three of them in a row is what made a sector page feel broken rather
    than disciplined.
    """
    return status("info", "Declined", text)


def unavailable(text: str) -> str:
    """A step that should have produced output and did not."""
    return status("warning", "Gap", text)


def prose(rendered_markdown: str) -> str:
    """Pre-rendered Markdown, wrapped for measure and citation styling.

    The input is trusted because the caller rendered it; everything in it
    originated from the citation renderer, not from free text.
    """
    return f'<div class="ar-prose">{rendered_markdown}</div>'


def paragraphs(text: str) -> str:
    """Model prose as paragraphs, escaped, blank-line separated."""
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text or "") if b.strip()]
    if not blocks:
        return _one_line('<div class="ar-prose"><p>Not stated.</p></div>')
    body = "".join(f"<p>{_text(b)}</p>" for b in blocks)
    return _one_line(f'<div class="ar-prose">{body}</div>')


# ----------------------------------------------------------------- tables


@dataclass(frozen=True)
class Col:
    key: str
    label: str
    num: bool = False  # right-aligned, mono, tabular figures
    wide: bool = False  # wrapping prose column
    emphasis: bool = False  # the identifying column
    link: bool = False  # the value is a URL, rendered as a short anchor


# "n.d." belongs here. It is the token the statement table actually
# emits for a period the filer did not tag, and leaving it out meant the
# cell rendered in full ink, indistinguishable from a figure that was
# filed. components.py's own rule, below, is that this is the one thing a
# financial table must never do.
_NM_VALUES = {"NM", "n.d.", "n/a", "Not disclosed.", "Not assessed.", ""}

# A value short enough to sit in a right-aligned figure column. Anything
# longer is prose that happens to occupy a value column, and forcing it to
# one nowrap line pushes every other column off the page. Observed on the
# financial health table, where a Beneish M-Score reports "insufficient data
# (missing two-year data for accounts_receivable, ...)" in the value slot.
_FIGURE_WIDTH = 14


def _is_figure(value: object) -> bool:
    return len(str(value).strip()) <= _FIGURE_WIDTH


def drop_empty_columns(
    columns: Sequence[Col], rows: Sequence[dict[str, str]]
) -> tuple[list[Col], list[str]]:
    """Columns that hold a figure somewhere, and the names of those that
    do not.

    A column whose every cell is a refusal says one thing, and says it
    once per row. On a bank, EBITDA, EBITDA margin and EV/EBITDA cannot
    be derived for any peer at all, so three of sixteen columns carried
    thirty-five refusals between them and no information. The fact is
    worth stating; the column is not worth printing. The caller names the
    dropped columns in the footnote, so nothing is hidden.
    """
    kept, dropped = [], []
    for column in columns:
        values = [str(r.get(column.key, "")).strip() for r in rows]
        real = [v for v in values if v and v not in _NM_VALUES]
        if real or not any(values):
            kept.append(column)
        else:
            dropped.append(column.label)
    return kept, dropped


def table(
    columns: Sequence[Col],
    rows: Sequence[dict[str, str]],
    classify: Callable[[int, dict[str, str]], str] | None = None,
    scrolls: bool = False,
) -> str:
    """A financial table: ruled header, no gridlines, figures right-aligned.

    `classify` names a row class, which is how the subject of a peer table is
    separated from its peers and how summary statistics are ruled off beneath
    them. `scrolls` lets a table wider than the content measure overflow and
    scroll rather than compress: a fifteen-column comparables table squeezed
    to fit wraps half the company names onto two lines.
    """
    if not rows:
        return ""

    head = "".join(
        f'<th scope="col" class="{"num" if c.num else ""}">{_text(c.label)}</th>'
        for c in columns
    )

    body = []
    for index, row in enumerate(rows):
        row_class = classify(index, row) if classify else ""
        cells = []
        for column in columns:
            value = row.get(column.key, "")
            classes = []
            if column.num and _is_figure(value):
                classes.append("num")
            elif column.num:
                classes.append("wide")
            if column.wide:
                classes.append("wide")
            if column.emphasis:
                classes.append("key")
            if str(value).strip() in _NM_VALUES:
                classes.append("nm")
            body_cell = (
                _anchor(str(value))
                if column.link
                else (_figure(value) if column.num else _text(value))
            )
            cells.append(
                f'<td class="{" ".join(classes)}">{body_cell}</td>'
            )
        # The spacer row is a rule drawn with table cells. To a screen
        # reader it was sixteen empty cells standing between the subject
        # and the first peer, each of which had to be stepped through.
        hidden = ' aria-hidden="true"' if row_class == "spacer" else ""
        body.append(
            f'<tr class="{row_class}"{hidden}>{"".join(cells)}</tr>'
        )

    variant = " ar-table-scroll" if scrolls else ""
    # A scrolling region has to be focusable or a keyboard cannot reach the
    # columns inside it. The comparables table is 1847px wide inside 687px,
    # so more than half its columns were unreachable without a mouse. Only
    # the scrolling variant gets this: making every table a tab stop would
    # add a dozen empty stops to the page.
    # Every wrapper is a scroll container below 900px, not only the
    # comparables one: the narrow-width rule sets overflow-x on all of
    # them. Ten of eleven were therefore unreachable by keyboard at phone
    # width and at 400% zoom, which is where the right-hand periods of a
    # statement live. The comparables table keeps `region`, being a
    # genuine landmark; the rest take `group`, so the export does not
    # grow ten landmarks.
    if scrolls:
        wrap = (
            '<div class="ar-table-wrap" tabindex="0" role="region"'
            ' aria-label="Comparable companies, scrollable">'
        )
    else:
        wrap = (
            '<div class="ar-table-wrap" tabindex="0" role="group"'
            ' aria-label="Table, scrollable when narrow">'
        )
    return _one_line(
        f'{wrap}<table class="ar-table{variant}">'
        f"<thead><tr>{head}</tr></thead>"
        f'<tbody>{"".join(body)}</tbody></table></div>'
    )


_SAFE_URL = re.compile(r"^https?://", re.IGNORECASE)


def _anchor(url: str) -> str:
    """A source link as a short anchor rather than a wrapped URL.

    A column of full EDGAR URLs is 90 characters of unreadable text that
    pushes every other column off the page. The scheme is checked because
    these URLs are assembled from filing metadata rather than typed here.
    """
    if not _SAFE_URL.match(url.strip()):
        return _text(url)
    return (
        f'<a href="{escape(url, quote=True)}" target="_blank" '
        f'rel="noopener noreferrer">Open</a>'
    )


def statement_table(rows, periods: Sequence[str]) -> str:
    """The financial summary, with its section headings and derived rows.

    Section headings span the table, subtotals are ruled above, and derived
    rows (growth rates, margins, free cash flow) are set in a lighter
    weight. The project guarantees that no figure is model-generated, not
    that none is computed, so the ones this module computes have to look
    different from the ones the company filed.
    """
    if not rows:
        return ""

    head = '<th scope="col" class="rowhead"></th>' + "".join(
        f'<th scope="col" class="num">{_text(p)}</th>' for p in periods
    )

    body = []
    for row in rows:
        if row.kind == "section":
            # The unit belongs with the section rather than in one corner
            # cell: a single "USD millions" sat above rows of percentages,
            # per-share amounts and share counts and described none of them.
            unit = (
                f'<span class="unit">{_text(row.note)}</span>' if row.note else ""
            )
            body.append(
                f'<tr class="statement-section">'
                f'<td colspan="{len(periods) + 1}">{_text(row.label)}{unit}'
                f"</td></tr>"
            )
            continue
        # A row header, not a cell. Reading across a statement row, a
        # screen reader announced the period and never the line item, so
        # a figure arrived with one of the two coordinates that give it
        # meaning. th.rowhead is already styled, so this costs nothing
        # visually.
        cells = [f'<th scope="row" class="rowhead">{_text(row.label)}</th>']
        for period in periods:
            value = row.values.get(period, "")
            nm = " nm" if str(value).strip() in _NM_VALUES else ""
            cells.append(f'<td class="num{nm}">{_figure(value)}</td>')
        body.append(f'<tr class="statement-{row.kind}">{"".join(cells)}</tr>')

    return _one_line(
        f'<div class="ar-table-wrap" tabindex="0" role="group" aria-label="Table, scrollable when narrow"><table class="ar-table ar-statement">'
        f"<thead><tr>{head}</tr></thead>"
        f'<tbody>{"".join(body)}</tbody></table></div>'
    )


def kv_table(pairs: Sequence[tuple[str, str, str]]) -> str:
    """Input / value / basis, the shape an assumptions table takes."""
    return table(
        [
            Col("input", "Input", emphasis=True),
            Col("value", "Value", num=True),
            Col("basis", "Basis", wide=True),
        ],
        [{"input": a, "value": b, "basis": c} for a, b, c in pairs],
    )


# --- the comparable-company table ---------------------------------------
#
# Row order carries meaning: subject, break, peers, then summary statistics
# ruled off beneath. `format_comp_table` already emits that order; this
# recovers the structure from it so the renderer can mark each kind of row.

def comps_classify(index: int, row: dict[str, str]) -> str:
    if not any(v.strip() for v in row.values()):
        return "spacer"
    company = row.get("Company", "")
    if company.startswith("Peer "):
        return "summary first" if company == "Peer mean" else "summary"
    return "subject" if index == 0 else ""


def sensitivity_table(
    grid: Sequence[dict[str, str]], reference_price: float | None
) -> str:
    """Discount rate against terminal growth, shaded by the traded price.

    The question a reader brings to this grid is not "what is the value"
    but "which assumptions would justify the price", so each cell is tinted
    by whether it clears the traded price. That turns a block of numbers
    into a boundary the eye finds immediately, and it is the convention on
    every published sensitivity table.
    """
    if not grid:
        return ""

    growth_columns = [k for k in grid[0].keys() if k != "WACC"]
    head = '<th scope="col" class="rowhead">WACC</th>' + "".join(
        f'<th scope="col" class="num">{_text(c)}</th>' for c in growth_columns
    )

    body = []
    for row in grid:
        # Worst case for a missing row header: a sensitivity cell means
        # nothing without both its discount rate and its terminal growth.
        cells = [
            f'<th scope="row" class="rowhead">'
            f'{_text(row.get("WACC", ""))}</th>'
        ]
        for column in growth_columns:
            raw = row.get(column, "")
            style = ""
            if reference_price:
                value = _parse_money(raw)
                if value is not None:
                    ratio = value / reference_price - 1
                    style = f' style="background:{_tint(ratio)}"'
            classes = "heat" + (" nm" if raw.strip() in _NM_VALUES else "")
            # The caption says a cell is shaded only where the modelled
            # value clears the traded price, and the shade was the only
            # carrier of that. Nothing reached a reader who cannot see
            # the tint.
            label = (
                f' aria-label="{_text(raw)}, clears the traded price"'
                if style
                else ""
            )
            cells.append(
                f'<td class="{classes}"{style}{label}>{_figure(raw)}</td>'
            )
        body.append(f'<tr>{"".join(cells)}</tr>')

    return _one_line(
        f'<div class="ar-table-wrap" tabindex="0" role="group" aria-label="Table, scrollable when narrow"><table class="ar-table">'
        f"<thead><tr>{head}</tr></thead>"
        f'<tbody>{"".join(body)}</tbody></table></div>'
    )


def _parse_money(text: str) -> float | None:
    cleaned = re.sub(r"[^\d.\-]", "", text or "")
    try:
        return float(cleaned) if cleaned not in {"", "-", "."} else None
    except ValueError:
        return None


def _tint(ratio: float) -> str:
    """Fill only the cells that clear the traded price.

    The question a reader brings to this grid is which assumptions would
    justify the price, so the fill answers that and nothing else. Shading
    both directions restated the sign of every cell: on a model diverging
    far from the market, nineteen of twenty cells came out tinted and the
    reader saw a wash rather than a boundary.

    When no cell clears the price the grid is clean, and that is the
    finding: no assumption in this range gets you there.
    """
    if ratio <= 0:
        return "transparent"
    strength = 0.05 + min(ratio / 0.40, 1.0) * 0.14
    return f"color-mix(in srgb, {theme.POSITIVE} {strength * 100:.0f}%, transparent)"


# --------------------------------------------------------------- findings


def finding(
    claim: str,
    data: str,
    assessment: str,
    agrees: bool,
    materiality: str,
) -> str:
    """One narrative-versus-figures comparison.

    Claim and figures are set side by side because the comparison *is* the
    finding. Stacked, the reader has to hold the first in memory while
    reading the second.
    """
    pill = (
        '<span class="ar-pill agree">Corroborated</span>'
        if agrees
        else '<span class="ar-pill diverge">Divergence</span>'
    )
    return _one_line(
        # The divergence carries a rule the corroboration does not: the
        # two were typographically identical and differed only in the
        # colour of a 10px pill, so a reader had to read the pill to sort
        # the section the whole report is built around.
        f'<div class="ar-finding{"" if agrees else " diverge"}">'
        f'<div class="ar-finding-head">{pill}'
        f'<span class="ar-pill mat">{_text(materiality)} materiality</span>'
        f"</div>"
        f'<div class="ar-finding-grid">'
        f'<div><div class="lbl">Management position</div>'
        f"<p>{_text(claim)}</p></div>"
        f'<div><div class="lbl">Reported figures</div>'
        f"<p>{_text(data)}</p></div></div>"
        f'<div class="ar-assess">{_text(assessment)}</div></div>'
    )


def split(
    left_label: str,
    left_text: str,
    right_label: str,
    right_text: str,
    left_tone: str = "",
    right_tone: str = "",
) -> str:
    """Two opposed positions in ruled columns: bull against bear, street
    against ours. The rule between them is the argument."""
    return _one_line(
        f'<div class="ar-split">'
        f'<div><div class="ar-col-label {left_tone}">{_text(left_label)}</div>'
        f"<p>{_text(left_text or 'Not stated.')}</p></div>"
        f'<div><div class="ar-col-label {right_tone}">{_text(right_label)}</div>'
        f"<p>{_text(right_text or 'Not stated.')}</p></div></div>"
    )


def bullets(items: Sequence[str]) -> str:
    if not items:
        return ""
    body = "".join(f"<li>{_text(i)}</li>" for i in items)
    return _one_line(f'<ul class="ar-prose">{body}</ul>')


# ------------------------------------------------------------- cover page


def home() -> str:
    """The first screen a stranger meets.

    It states the proposition and nothing else. The tool used to open on a
    form, which asks someone to supply an input before anything has told
    them what they get back for it.
    """
    return _one_line(
        '<div class="ar-home">'
        # Spaces before each break: without them textContent read
        # "Read the filings,then read whatmanagement saidabout them."
        "<h1>Read the filings, then read what management said "
        "about them.</h1>"
        '<p class="lede">A ticker in, a sourced research note out: the '
        "filed financial record, the narrative management wrapped around "
        "it, and the places where the two do not agree.</p>"
        "</div>"
    )


_EDGAR_NOISE = re.compile(r"\s*/\w+\s*$")
# Words that are acronyms rather than words, and would read wrongly in
# title case. Short all-alpha tokens are kept as-is anyway; these are the
# longer ones.
_KEEP_UPPER = {"REIT", "REITS", "ETF", "NYSE", "USA", "AG", "SPA"}
_SUFFIX = {
    "INC": "Inc.", "CORP": "Corp.", "CO": "Co.", "LLC": "LLC",
    "LTD": "Ltd.", "PLC": "plc", "LP": "LP", "NV": "N.V.", "SA": "S.A.",
    "GROUP": "Group", "HOLDINGS": "Holdings", "TR": "Trust",
}


def display_name(conformed: str) -> str:
    """An EDGAR conformed name, made fit to show a reader.

    EDGAR stores "COSTCO WHOLESALE CORP /NEW" and "REALTY INCOME CORP".
    Printed as filed, beside one filer that happens to be stored in title
    case, they read as a database field nobody looked at - and the "/NEW"
    is a filing-system artifact, not part of anyone's name. A reader who
    sees that in a company name concludes nothing was normalised on the
    way out, which is the opposite of this document's whole claim.
    """
    cleaned = _EDGAR_NOISE.sub("", conformed).strip()
    if not cleaned or not cleaned.isupper():
        return cleaned or conformed

    words = []
    for word in cleaned.split():
        bare = word.strip(".,")
        if bare in _SUFFIX:
            words.append(_SUFFIX[bare])
        elif bare in _KEEP_UPPER or (len(bare) <= 3 and bare.isalpha()):
            # An acronym stays an acronym: NNN, ADP, REIT, PNC.
            words.append(bare)
        else:
            words.append(word.title())
    return " ".join(words)


def door_costs(has_samples: bool) -> str:
    """What each way in costs, under the buttons that offer them.

    The home screen offered three doors that cost wildly different
    things and said so nowhere: a reviewer clicked the filled one and
    then watched a progress bar for a minute. The information existed,
    on the gate screen they had already dismissed.
    """
    if not has_samples:
        return _one_line(
            '<p class="ar-foot ar-doors">A report takes about a minute '
            "and spends one live API call.</p>"
        )
    return _one_line(
        '<p class="ar-foot ar-doors">'
        "<span>Samples are already built: instant, and free.</span>"
        "<span>A new report takes about a minute and spends one live "
        "API call.</span></p>"
    )


def samples_intro(count: int) -> str:
    """The sample gallery's own header.

    Says what these are and what they cost, because a reader who does not
    know whether a page is live output or a canned screenshot discounts
    it either way.
    """
    return _one_line(
        '<div class="ar-workspace ar-workspace-intro">'
        "<h1>Sample notes</h1>"
        f"<p>{escape_text(plural(count, 'note'))}, built from live SEC "
        "filings by the same pipeline the tool runs. Nothing here is a "
        "mock-up and nothing is re-generated when you open it, so reading "
        "one is instant and costs nothing.</p></div>"
    )


def about(body_html: str) -> str:
    """The written account, rendered inside the product.

    A reader who has to leave for a repository to find out what they are
    looking at usually does not come back.
    """
    return _one_line(
        '<div class="ar-workspace ar-about">'
        f'<div class="ar-prose">{body_html}</div></div>'
    )


def gate() -> str:
    """The passphrase screen.

    Says what the thing is before asking for anything, because a bare
    password box on an unexplained page reads as a phishing form. It also
    states why the gate exists: every report spends real money, and a
    reader who understands that is less likely to assume the tool is
    hiding something.
    """
    return _one_line(
        '<div class="ar-home ar-gate">'
        "<h1>Asset Researcher</h1>"
        '<p class="lede">Equity research built from the filings themselves. '
        "This demo is shared with named reviewers rather than published, "
        "because each report it builds is a real call against a metered "
        "API.</p>"
        '<p class="ar-foot">Enter the passphrase you were sent.</p>'
        "</div>"
    )


def home_foot() -> str:
    """Three claims, under the fold, as a ruled row rather than cards.

    What the product guarantees, stated where it can be read after the
    proposition has landed rather than competing with it.
    """
    claims = (
        (
            "Every figure is filed",
            "Financial data is read from the company's own XBRL submissions "
            "to the SEC. No figure is model-generated, and the ones computed "
            "from filed lines are marked as computed.",
        ),
        (
            "Every claim is located",
            "Narrative statements carry a citation resolved against the "
            "stored source text. Locating a quote is not establishing that "
            "it supports the claim, and the report says so.",
        ),
        (
            "The counter-case is mandatory",
            "Each report states the strongest evidence against its own "
            "thesis, what would falsify it, and what the sources could not "
            "see.",
        ),
    )
    blocks = "".join(
        f"<div><h2>{_text(title)}</h2><p>{_text(body)}</p></div>"
        for title, body in claims
    )
    return _one_line(f'<div class="ar-claims">{blocks}</div>')


def workspace_intro() -> str:
    """The empty workspace, which is a form and should say what it wants."""
    return _one_line(
        '<div class="ar-workspace ar-workspace-intro">'
        '<h1 class="ar-workspace-title">Build a note</h1>'
        '<p>Enter a ticker. The report takes about a minute and reads every '
        "filing it cites.</p></div>"
    )
