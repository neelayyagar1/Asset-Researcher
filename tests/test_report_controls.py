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


# ------------------------------------------- what the index does NOT explain

def test_the_index_does_not_explain_its_own_columns():
    """There was a legend under the table defining FCF yield, FCF CAGR
    and Cited, and a line totalling the archive's citation coverage.

    It went because of who reads this. The audience is a portfolio
    manager, and free cash flow yield is not a term a portfolio manager
    needs defined - explaining it says, in the politest possible way,
    that the writer was unsure whether the reader would know. The
    coverage total restated the Cited column immediately above it. Four
    sentences of grey prose, under a table, saying what the table had
    just said to someone who did not need it said once.

    The two columns stay. The commentary does not.
    """
    assert not hasattr(ui, "index_legend")
    assert "index_legend" not in APP

    from asset_researcher.ui import theme

    assert ".ar-legend" not in theme._APP_CSS, (
        "the shell still styles a legend it no longer writes"
    )
    # The NOTE's own legend keeps the class and the name. It explains NM
    # and n.d., which are notation this product invented the use of in
    # this context, to a reader meeting them mid-table - a different
    # thing from defining a standard ratio on an index.
    assert ".ar-legend" in theme.document_stylesheet()


def test_the_report_index_bar_does_not_outlive_its_report():
    """`_nav_bridge` copies the note's section index into the SHELL,
    outside the tree Streamlit owns, which is why it survives - and why
    pressing Back from a report left that report's section names
    sitting under Get started on the home screen, linking into a
    document no longer on the page."""
    assert "def _drop_nav(" in APP
    assert "ar-shell-nav" in APP[APP.index("def _drop_nav("):][:1600]
    call = APP.index('if st.session_state.get("view") != "samples":')
    assert "_drop_nav()" in APP[call : call + 200], (
        "the cleanup is defined but not called on the screens with no note"
    )
