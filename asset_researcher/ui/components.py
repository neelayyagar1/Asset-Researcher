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


def _one_line(markup: str) -> str:
    """Collapse the whitespace a Markdown renderer would misread."""
    return _RUNS.sub(" ", _WS_BETWEEN_TAGS.sub("><", markup.strip()))


def _text(value: object) -> str:
    """Escaped text, with an em-space placeholder for nothing at all.

    An empty table cell and a cell holding a missing value look identical,
    which is the one thing a financial table must never do. Absence is
    written as a word by the formatters upstream; this guards the rest.
    """
    if value is None:
        return "&mdash;"
    rendered = str(value).strip()
    return escape(rendered) if rendered else "&nbsp;"


# --------------------------------------------------------------- masthead


def masthead(
    title: str, ticker: str, eyebrow: str, subline: Sequence[str]
) -> str:
    """Company name, ticker and the provenance line beneath it."""
    parts = '<span class="sep">/</span>'.join(
        f"<span>{_text(p)}</span>" for p in subline if p
    )
    return _one_line(
        f'<div class="ar-masthead">'
        f'<div class="ar-eyebrow">{_text(eyebrow)}</div>'
        f'<div class="ar-title">{_text(title)}'
        f'<span class="ar-ticker">{_text(ticker)}</span></div>'
        f'<div class="ar-subline">{parts}</div>'
        f"</div>"
    )


# ------------------------------------------------------------- stat strip


@dataclass(frozen=True)
class Stat:
    label: str
    value: str
    note: str = ""
    tone: str = ""  # "" | "pos" | "neg"


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
        note = (
            f'<div class="ar-stat-note">{_text(stat.note)}</div>'
            if stat.note
            else ""
        )
        cells.append(
            f'<div class="ar-stat">'
            f'<div class="ar-stat-label">{_text(stat.label)}</div>'
            f'<div class="ar-stat-value {tone}">{_text(stat.value)}</div>'
            f"{note}</div>"
        )
    return _one_line(f'<div class="ar-stats">{"".join(cells)}</div>')


# ---------------------------------------------------------------- framing


def section(label: str, note: str = "") -> str:
    """A section label with a rule running to the right margin."""
    trailing = f'<div class="ar-sec-note">{_text(note)}</div>' if note else ""
    return _one_line(
        f'<div class="ar-sec">'
        f'<div class="ar-sec-label">{_text(label)}</div>'
        f'<div class="ar-sec-rule"></div>{trailing}</div>'
    )


def caption(text: str) -> str:
    return _one_line(f'<p class="ar-caption">{_text(text)}</p>')


def footnote(text: str) -> str:
    return _one_line(f'<p class="ar-foot">{_text(text)}</p>')


_STATUS_CLASS = {"success": "ok", "warning": "warn", "error": "bad", "info": "info"}


def status(level: str, tag: str, message: str) -> str:
    """A ruled status line, in place of a filled alert panel."""
    cls = _STATUS_CLASS.get(level, "info")
    return _one_line(
        f'<div class="ar-status {cls}">'
        f'<span class="tag">{_text(tag)}</span>{_text(message)}</div>'
    )


def note(text: str) -> str:
    """Where a section has nothing to show, and why. Always a sentence."""
    return status("info", "Not available", text)


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


_NM_VALUES = {"NM", "n/a", "Not disclosed.", "Not assessed.", ""}

# A value short enough to sit in a right-aligned figure column. Anything
# longer is prose that happens to occupy a value column, and forcing it to
# one nowrap line pushes every other column off the page. Observed on the
# financial health table, where a Beneish M-Score reports "insufficient data
# (missing two-year data for accounts_receivable, ...)" in the value slot.
_FIGURE_WIDTH = 14


def _is_figure(value: object) -> bool:
    return len(str(value).strip()) <= _FIGURE_WIDTH


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
        f'<th class="{"num" if c.num else ""}">{_text(c.label)}</th>'
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
                _anchor(str(value)) if column.link else _text(value)
            )
            cells.append(
                f'<td class="{" ".join(classes)}">{body_cell}</td>'
            )
        body.append(f'<tr class="{row_class}">{"".join(cells)}</tr>')

    variant = " ar-table-scroll" if scrolls else ""
    return _one_line(
        f'<div class="ar-table-wrap"><table class="ar-table{variant}">'
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

    head = '<th class="rowhead">USD millions</th>' + "".join(
        f'<th class="num">{_text(p)}</th>' for p in periods
    )

    body = []
    for row in rows:
        if row.kind == "section":
            body.append(
                f'<tr class="statement-section">'
                f'<td colspan="{len(periods) + 1}">{_text(row.label)}</td></tr>'
            )
            continue
        cells = [f'<td class="rowhead">{_text(row.label)}</td>']
        for period in periods:
            value = row.values.get(period, "")
            nm = " nm" if str(value).strip() in _NM_VALUES else ""
            cells.append(f'<td class="num{nm}">{_text(value)}</td>')
        body.append(f'<tr class="statement-{row.kind}">{"".join(cells)}</tr>')

    return _one_line(
        f'<div class="ar-table-wrap"><table class="ar-table ar-statement">'
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
    head = '<th class="rowhead">WACC</th>' + "".join(
        f'<th class="num">{_text(c)}</th>' for c in growth_columns
    )

    body = []
    for row in grid:
        cells = [f'<td class="rowhead">{_text(row.get("WACC", ""))}</td>']
        for column in growth_columns:
            raw = row.get(column, "")
            style = ""
            if reference_price:
                value = _parse_money(raw)
                if value is not None:
                    ratio = value / reference_price - 1
                    style = f' style="background:{_tint(ratio)}"'
            classes = "heat" + (" nm" if raw.strip() in _NM_VALUES else "")
            cells.append(f'<td class="{classes}"{style}>{_text(raw)}</td>')
        body.append(f'<tr>{"".join(cells)}</tr>')

    return _one_line(
        f'<div class="ar-table-wrap"><table class="ar-table">'
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
    """A fill whose strength tracks distance from the traded price.

    Capped at 30% divergence so one extreme corner does not saturate the
    whole grid, and kept pale: the number has to stay the most legible thing
    in the cell.
    """
    strength = min(abs(ratio) / 0.30, 1.0) * 0.17
    base = theme.POSITIVE if ratio >= 0 else theme.NEGATIVE
    return f"color-mix(in srgb, {base} {strength * 100:.0f}%, transparent)"


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
        f'<div class="ar-finding"><div class="ar-finding-head">{pill}'
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


def cover(headline: str, lede: str, pillars: Sequence[tuple[str, str]]) -> str:
    """The pre-report state.

    An empty application is the first thing anyone sees, and "enter a ticker"
    in a grey box says nothing about what the tool guarantees. This states
    the three claims the engine is built to make good on.
    """
    blocks = "".join(
        f'<div><div class="n">{index:02d}</div>'
        f'<div class="h">{_text(title)}</div><p>{_text(body)}</p></div>'
        for index, (title, body) in enumerate(pillars, start=1)
    )
    return _one_line(
        f'<div class="ar-cover"><h1>{_text(headline)}</h1>'
        f'<p class="lede">{_text(lede)}</p></div>'
        f'<div class="ar-guarantee">{blocks}</div>'
    )
