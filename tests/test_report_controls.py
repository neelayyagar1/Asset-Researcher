"""The two controls above a report, and the one above the index.

The report screen used to carry seven controls in two rows: Home and
"Generate a new report" on the first, and HTML, PDF, Word, PowerPoint
and Markdown on the second, narrower and left-aligned under them. Seven
controls, none of which is what a reader came to the screen to do.

It is two now, on one line, equal width: the way out, and the one
control named for what all five exports are.
"""

from __future__ import annotations

import pathlib
import re

from asset_researcher.ui import components as ui

APP = (pathlib.Path(__file__).resolve().parents[1] / "app.py").read_text(
    encoding="utf-8"
)


def test_the_exports_are_behind_one_control():
    """Five `download_button`s on the page, or five inside a popover,
    is the difference between a row of formats and a menu of them."""
    body = APP[APP.index("def _download_row("):]
    body = body[: body.index("\ndef ", 1)]
    assert 'st.popover("Download"' in body, (
        "the exports are not behind a single Download control"
    )
    opened = body.index('st.popover("Download"')
    for fmt in ("HTML", "PDF", "Word", "PowerPoint", "Markdown"):
        assert body.index(f'"{fmt}"') > opened, (
            f"{fmt} is offered before the menu that is meant to hold it"
        )


def test_neither_report_screen_offers_a_new_run():
    """Both screens, pinned together, because they were fixed together
    and the next person will restore one and forget the other."""
    # Exactly one caller is left, and it is the empty state below.
    assert APP.count("ui.NEW_LABEL") == 1, (
        "a report screen still offers to generate another report: "
        f"{APP.count('ui.NEW_LABEL')} callers"
    )
    here = APP.index("ui.NEW_LABEL")
    assert "samples_build_empty" in APP[here : here + 300]
    # The empty state keeps it, and should: there is no report on that
    # screen to be distracted from, and nothing else to do there.
    assert "samples_build_empty" in APP


def test_back_and_download_share_one_row():
    """They sat on two rows of different widths - two small buttons
    left-aligned above four stretched ones - so the screen read as
    two unrelated groups rather than one pair."""
    for anchor in ('if acts[0].button("Back"', 'if actions[0].button("Home"'):
        here = APP.index(anchor)
        row = APP[here - 400:here]
        cols = re.findall(r"st\.columns\(\[([0-9., ]+)\]\)", row)
        assert cols, f"no column row found above {anchor}"
        widths = [float(x) for x in cols[-1].split(",")]
        assert widths[0] == widths[1], (
            f"the pair above {anchor} is not two equal columns: {widths}"
        )
        after = APP[here : here + 600]
        assert "_download_row(" in after, (
            f"Download is not on the same row as {anchor}"
        )
        assert "use_container_width=True" in APP[here : here + 120], (
            f"{anchor} does not fill its column, so the pair is uneven"
        )


# ------------------------------------------------------------- the top bar

def test_the_bar_names_the_product_and_the_screen_and_nothing_else():
    """"SEC EDGAR - XBRL" sat in the far right of every screen.

    Provenance belongs to a document, not to a window. Standing in the
    chrome it made the same claim above the gate, the empty form and
    the error state, none of which has read a filing - and it was the
    only thing in a bar with no controls that a reader could mistake
    for one. The note states its own sources, beside every figure.
    """
    for screen in ("reports", "samples", "tool", "report"):
        bar = ui.topbar(screen)
        assert "EDGAR" not in bar, f"{screen} still carries the mark"
        assert "XBRL" not in bar
        assert "Asset Researcher" in bar


def test_the_mark_is_gone_from_the_stylesheet_too():
    """A rule for an element nothing emits is how it comes back."""
    from asset_researcher.ui import theme

    css = re.sub(r"/\*.*?\*/", "", theme._APP_CSS, flags=re.S)
    assert ".ar-topbar .meta" not in css, (
        "the bar's provenance slot still has rules waiting for it"
    )


# -------------------------------------------------------- the index legend

ROWS = [
    {"ticker": "ADP", "company": "Automatic Data Processing", "slug": "adp",
     "cited": "105/105"},
    {"ticker": "O", "company": "Realty Income", "slug": "o",
     "cited": "98/98"},
]


def test_the_legend_defines_every_term_the_header_cannot():
    """Three of the eight headers are terms rather than words, and a
    reader meeting the table is being asked to take all three on
    trust. Printed, not hovered - the note's own legend works the
    same way, and for the same reason."""
    out = ui.index_legend(ROWS)
    for term in ("FCF yield", "FCF CAGR", "Cited"):
        assert f"<b>{term}</b>" in out, term
    assert "market capitalisation" in out
    assert "out of figures stated" in out


def test_the_coverage_total_is_counted_rather_than_written():
    """It is the one claim this product exists to make, stated as a
    number on the screen where a reader meets it. Counted from the
    rows, so it cannot drift from the table above it."""
    out = ui.index_legend(ROWS)
    assert "<b>203/203</b>" in out, out
    assert "2 reports" in out

    one = ui.index_legend([ROWS[0]])
    assert "<b>105/105</b>" in one and "1 report " in one, one


def test_a_row_that_states_no_coverage_is_not_counted_as_zero():
    """A note whose coverage could not be read has an unknown
    coverage, not a coverage of nothing. Averaging it in as zero
    would understate the only number here that matters, and
    inventing one would be worse."""
    mixed = ui.index_legend([ROWS[0], dict(ROWS[1], cited="")])
    assert "<b>105/105</b>" in mixed, mixed

    none = ui.index_legend([dict(r, cited="") for r in ROWS])
    assert "figures across" not in none, (
        "a total was claimed with nothing to total"
    )
    assert "<b>FCF yield</b>" in none, "the terms should still be defined"
