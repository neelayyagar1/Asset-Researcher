"""The Back guard, after reports started surviving a reload."""
from __future__ import annotations

import pathlib
import re

APP = pathlib.Path(__file__).resolve().parents[1] / "app.py"


def _script() -> str:
    return APP.read_text(encoding="utf-8")


def test_the_marker_says_whether_the_report_was_saved():
    """The guard asks before a reload because a reload used to destroy
    the report. It no longer does: the rendered document is written to
    disk before the screen draws, and the index links to it. The only
    case left where leaving really loses something is a save that
    failed, so the page has to say which it is."""
    assert 'data-saved=' in _script()


def test_the_bridge_reads_that_flag_rather_than_asking_every_time():
    script = _script()
    assert "dataset.saved" in script or "getAttribute('data-saved')" in script


def test_the_warning_does_not_claim_a_saved_report_is_lost():
    script = _script()
    warning = re.search(r"host\.confirm\((.*?)\)\)", script, re.S)
    assert warning, "no leave warning found"
    text = warning.group(1)
    assert "could not be saved" in text, (
        "the warning does not say the save is what failed"
    )
    assert "will discard the report" not in text, (
        "the warning still claims leaving discards a report that is on "
        "disk and linked from the first screen"
    )
