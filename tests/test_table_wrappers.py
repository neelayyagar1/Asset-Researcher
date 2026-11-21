"""Tab stops that scroll nothing and announce that they do.

Every table in a note is wrapped in a focusable `role="group"`
labelled "Table, scrollable when narrow". The wrapper is focusable
unconditionally; the overflow is not - `.ar-table-wrap { overflow-x:
auto }` applies only below 900px, plus the comparables table which
genuinely always overflows.

So at desktop width ten of eleven wrappers were focusable, scrolled
nothing, contained no operable content, and announced a capability
they did not have. The comment beside them says they exist to avoid
"a dozen empty stops", which is what they became above 900px.

The fix is to set it from measurement rather than from markup, in
the script that already runs on load and resize for `fitFrame`.
"""

from __future__ import annotations

from asset_researcher.ui import components as ui
from asset_researcher.ui.export import _JUMP_SCRIPT

ROWS = [{"a": "1", "b": "2"}]
COLS = [ui.Col("a", "A"), ui.Col("b", "B")]


def test_a_wrapper_is_not_focusable_in_the_markup():
    html = ui.table(COLS, ROWS)
    wrapper = html[: html.index("<table")]
    assert "tabindex" not in wrapper, (
        "the wrapper is a tab stop at every width, including those "
        "where it does not scroll"
    )


def test_it_does_not_claim_to_scroll_before_anything_measured_it():
    html = ui.table(COLS, ROWS)
    wrapper = html[: html.index("<table")]
    assert "scrollable when narrow" not in wrapper


def test_the_wrapper_is_still_identifiable_to_the_script():
    html = ui.table(COLS, ROWS)
    assert "ar-table-wrap" in html


def test_the_script_sets_the_stop_from_measurement():
    assert "scrollWidth" in _JUMP_SCRIPT, (
        "nothing measures overflow, so either every wrapper is a stop "
        "or none is"
    )
    assert "tabindex" in _JUMP_SCRIPT


def test_a_scrolling_table_does_not_park_its_header_over_the_first_row():
    """The Peers table, reported broken three times and never reproduced.

    `table.ar-table thead th` is `position: sticky; top: var(--nav-h)`,
    which is 41px - the height of the note's own section bar, so the
    header clears it when the document scrolls. That works for every
    table whose wrapper is `overflow: visible`, because sticky then
    resolves against the page.

    The comparables table is the one table that genuinely overflows, so
    its wrapper carries `overflow-x: auto`. Overflow in one axis forces
    the other to `auto` as well, which makes the wrapper itself the
    nearest scrollport - and a wrapper sized to its own table has no
    vertical travel. So the header never unsticks and never scrolls: it
    parks permanently 41px down from the top of the table, painting over
    the first row of the body.

    On the comparables table the first row of the body is `tr.subject` -
    the company the entire note is about. Measured in the browser on the
    Realty Income note: the header row's own box sat at viewport y 40
    while the cells painted at 81, covering the subject row at 70-101.
    All a reader saw of Realty Income's own figures was the sliver
    above the header.

    The previous session found half of this. It scoped `overflow-x` to
    `:has(> .ar-table-scroll)` so that the other wrappers stay visible
    and their headers work - which fixed seven tables and left the
    eighth, the one that was being reported.
    """
    from asset_researcher.ui import theme

    sheet = theme.document_stylesheet()
    assert ".ar-table-scroll) table.ar-table thead th" in sheet, (
        "nothing stops the sticky header inside the one wrapper that is "
        "itself a scrollport"
    )
