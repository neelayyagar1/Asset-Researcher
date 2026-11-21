"""What the first two screens say, and the one widget that lied.

Four defects the owner found by reading the screens, each of which is a
copy or state fault rather than a layout one:

  - the lead sentence called the output a "research note", a term the
    rest of the product does not use, and described the tool rather
    than telling a reader what to provide;
  - Get started began at step two: it opened with "Enter a ticker",
    which is impossible on the screen it is printed on, because the
    form is one button away;
  - both the home button and the form's primary action read "Generate
    a report", so the instructions could not name either of them
    unambiguously;
  - choosing "Describe my own" left the previous preset's text in the
    box. Streamlit ignores `value=` once a keyed widget exists, so the
    computed empty prefill never reached the field.
"""

from __future__ import annotations

import pathlib

from streamlit.testing.v1 import AppTest

from asset_researcher.ui import components as ui
from tests.apptest_helpers import rendered_markup

APP = str(pathlib.Path(__file__).resolve().parents[1] / "app.py")
PHRASE = "test-only-passphrase"


def _open(monkeypatch):
    monkeypatch.setenv("DEMO_PASSPHRASE", PHRASE)
    monkeypatch.delenv("SAMPLES_KEY", raising=False)
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.text_input(key="gate_input").set_value(PHRASE)
    return at.button[0].click().run()


# ------------------------------------------------------------- the lead

def test_the_lead_calls_the_output_a_report():
    lead = ui.home()
    assert "research note" not in lead
    assert "report" in lead


def test_the_lead_tells_the_reader_what_to_provide():
    assert "Provide" in ui.home()


# ------------------------------------------------------- the two buttons

def test_the_home_action_and_the_form_action_have_different_names(monkeypatch):
    at = _open(monkeypatch)
    home_label = at.button(key="enter").label
    at.button(key="enter").click().run()
    form_label = at.button(key="inline_run").label
    assert home_label != form_label


def test_get_started_begins_with_the_button_on_this_screen(monkeypatch):
    at = _open(monkeypatch)
    home_label = at.button(key="enter").label
    first_step = ui.STEPS[0]
    assert home_label in first_step


# ------------------------------------------------------- the form's head

def test_the_form_head_carries_no_second_sentence():
    assert "<p>" not in ui.workspace_intro()


# ------------------------------------------------------ the strategy box

def test_choosing_describe_my_own_clears_the_strategy_text(monkeypatch):
    at = _open(monkeypatch)
    at.button(key="enter").click().run()
    seeded = at.text_area(key="inline_mandate").value
    assert seeded.strip(), "a named preset should seed the box"
    at.selectbox(key="inline_preset").set_value("Describe my own").run()
    assert at.text_area(key="inline_mandate").value == ""


def test_an_edited_description_survives_a_rerun(monkeypatch):
    """The clearing fix writes into session state, which is the one
    place a reader's own typing also lives. Writing it on every rerun
    rather than only on a change would silently overwrite them."""
    at = _open(monkeypatch)
    at.button(key="enter").click().run()
    at.text_area(key="inline_mandate").set_value("Mine, typed by hand.").run()
    at.text_input(key="inline_ticker").set_value("MSFT").run()
    assert at.text_area(key="inline_mandate").value == "Mine, typed by hand."


def test_the_bar_names_the_screen_the_reader_is_on(monkeypatch):
    """The form screen reported "Reports". `topbar` has carried a
    "tool" case since it was written and no caller ever passed it, so
    the one piece of persistent chrome named the wrong screen on the
    only screen a reader spends time filling in."""
    at = _open(monkeypatch)
    at.button(key="enter").click().run()
    assert "New report" in rendered_markup(at)
