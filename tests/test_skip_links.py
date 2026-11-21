"""Where a skip link actually lands.

Every screen offers one as its first tab stop, and on three of the
four the target span was written BEFORE the topbar - so activating the
link moved focus to a point above everything it was supposed to
bypass. On the form screen it landed above the topbar, the heading and
any failure message, rather than at the Ticker field. The mechanism
existed and did not work, which is the shape SC 2.4.1 cares about.

On the report screen - the longest in the product, where a bypass is
worth most - the link was emitted after the four action buttons, so it
was the fifth tab stop rather than the first.

Asserted on the order of the markup the page emits, not on the order
of the calls in the source.
"""

from __future__ import annotations

import pathlib
import re

from streamlit.testing.v1 import AppTest

from tests.apptest_helpers import rendered_markup

APP = str(pathlib.Path(__file__).resolve().parents[1] / "app.py")
PHRASE = "test-only-passphrase"


def _screen(monkeypatch, view: str):
    monkeypatch.setenv("DEMO_PASSPHRASE", PHRASE)
    monkeypatch.delenv("SAMPLES_KEY", raising=False)
    at = AppTest.from_file(APP, default_timeout=60)
    if view:
        at.query_params["view"] = view
    at = at.run()
    at.text_input(key="gate_input").set_value(PHRASE)
    return at.button[0].click().run()


def _order(markup: str, *needles: str) -> list[int]:
    found = []
    for needle in needles:
        index = markup.find(needle)
        assert index >= 0, f"{needle!r} is not in the page"
        found.append(index)
    return found


def test_home_skips_past_the_bar_it_is_meant_to_bypass(monkeypatch):
    markup = rendered_markup(_screen(monkeypatch, "home"))
    bar, target = _order(markup, 'class="ar-topbar"', 'id="ar-home"')
    assert target > bar, (
        "the skip target sits above the topbar, so the link moves "
        "focus backwards past everything it should skip"
    )


def test_the_form_skips_to_the_form(monkeypatch):
    markup = rendered_markup(_screen(monkeypatch, "tool"))
    bar, head, target = _order(
        markup, 'class="ar-topbar"', "ar-form-head", 'id="ar-form"'
    )
    assert target > bar, "the skip target is above the topbar"
    assert target > head, (
        "the skip target is above the screen's own heading, so the "
        "link lands before the form rather than at it"
    )


def test_the_reading_screen_skips_past_its_bar(monkeypatch):
    markup = rendered_markup(_screen(monkeypatch, "samples"))
    bar, target = _order(markup, 'class="ar-topbar"', 'id="ar-samples"')
    assert target > bar


def test_the_report_screen_offers_the_bypass_before_its_controls():
    """Source order, because rendering this screen needs a live report
    - which costs a minute and about a dollar. The four controls are
    Streamlit widgets and the skip link is markup, so their relative
    order in the script is their order in the tab sequence."""
    source = pathlib.Path(APP).read_text(encoding="utf-8")
    tail = source[source.index('write(ui.topbar("report"))'):]
    skip = tail.index('_skip_link("ar-report"')
    actions = tail.index("actions = st.columns(")
    assert skip < actions, (
        "the bypass is offered after New report, Home, HTML and "
        "Markdown, on the longest screen in the product"
    )
