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
