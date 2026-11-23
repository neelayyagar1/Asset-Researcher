"""How long the tool says a report takes, against how long it takes.

Measured tonight, on this machine, against the real APIs:

  - eighteen sample notes built across three full rebuilds, at five to
    seven minutes each;
  - two reports generated through the interface itself, at about seven
    minutes each, timed from the click to the file landing on disk.

The interface said "about a minute". A reader who presses the button
on that promise and is still waiting six minutes later concludes the
thing has hung - which is the exact impression the progress bar was
added to prevent, and the reason it was given an honest ceiling.

The owner's standing instruction about this kind of claim: if it says
it does something, make sure that is true.
"""

from __future__ import annotations

import re

from asset_researcher.ui import components as ui
from asset_researcher.ui import theme


# The claim moved. It was step three of four on the home screen; the
# steps are gone and the sentence under the opening line carries it, so
# these read the sentence. What is tested is the claim, not where it
# happens to be printed.

def test_the_opening_screen_does_not_promise_a_minute():
    said = ui.home().lower()
    assert "about a minute" not in said, (
        "the home screen still promises a minute for a run measured at "
        "five to seven"
    )


def test_the_opening_screen_gives_an_honest_order_of_magnitude():
    said = ui.home().lower()
    assert "minutes" in said, "the home screen no longer says how long"


def test_the_progress_estimate_matches_the_measured_run():
    """The bar's first phase is a time estimate. At 75 seconds it was
    finishing in a twentieth of the run and then holding, which reads
    as hung."""
    css = theme.stylesheet()
    match = re.search(r"animation:\s*ar-fill\s+(\d+)s", css)
    assert match, "the progress bar no longer declares its estimate"
    seconds = int(match.group(1))
    assert seconds >= 240, (
        f"the bar fills in {seconds}s against a run measured at five "
        f"to seven minutes"
    )
