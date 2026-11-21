"""The report screen vanished on the next interaction.

Found by running a real report through the browser, which is the only
way it could be found: the suite never clicks Generate, because that
queues a paid run.

`_run_pending` sets `st.session_state["view"] = "report"` when a
report lands, and never touches the query string. `_sync_view_from_url`
runs at the top of every rerun and adopts whatever the URL says - and
the URL still said `view=tool`, because the form screen put it there.
So the report rendered once, and the first rerun after it - any
button, any widget - set the view back to `tool` and drew the empty
form. The document was safe on disk; the screen the visitor had just
waited ninety seconds for was gone.

Observed exactly that: `ar-report` present with `data-saved="1"`, then
after one click the page offered "Generate report" and "Back" with no
report anywhere.

The view and the address bar have to be set together. `go()` already
does both; this was the one place that set the view without it.
"""

from __future__ import annotations

import pathlib
import re

APP = pathlib.Path(__file__).resolve().parents[1] / "app.py"


def _run_pending_source() -> str:
    source = APP.read_text(encoding="utf-8")
    start = source.index("def _run_pending(")
    return source[start : source.index("\n# ", start)]


def test_landing_on_the_report_puts_it_in_the_address_bar():
    block = _run_pending_source()
    assert 'st.session_state["view"] = "report"' in block
    assert re.search(r'query_params\[\s*"view"\s*\]\s*=\s*"report"', block), (
        "the view is set in session state only, so the next rerun "
        "reads `view=tool` off the URL and discards the report screen"
    )


def test_every_place_that_sets_the_view_also_sets_the_url():
    """The contract, not just this instance. `_sync_view_from_url`
    treats the URL as the source of truth on every rerun, so any
    assignment to the view that does not write the URL is a screen
    that survives exactly one render."""
    source = APP.read_text(encoding="utf-8")
    for match in re.finditer(r'st\.session_state\["view"\] = ("?\w+"?)', source):
        line_start = source.rfind("\n", 0, match.start())
        window = source[line_start : match.end() + 400]
        value = match.group(1)
        if value == "requested":
            continue  # `_sync_view_from_url` itself, adopting the URL
        if value == '"tool"':
            continue  # the fallback when a held report is gone
        assert re.search(r'query_params\[\s*"view"\s*\]', window), (
            f"the view is set to {value} without the URL following, at "
            f"character {match.start()}"
        )
