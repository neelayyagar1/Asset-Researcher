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

import re

import pathlib

from streamlit.testing.v1 import AppTest

from asset_researcher.ui import components as ui
from asset_researcher.ui import theme
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

def test_the_opening_and_the_controls_name_the_same_thing():
    """One document, one word for it.

    The opening line went out saying "Research notes" and "The note"
    while every control, the bar and the index said report. It was
    caught on the deployed site by the person it was written for, which
    is the right outcome arriving by the wrong route: a reader meets
    the thing twice before touching it and is told it is two things.

    Both halves are tested now - what the screen calls the document,
    and what the controls call it - because the fault was the gap
    between them rather than either one on its own.
    """
    said = ui.home().lower()
    assert "note" not in said, "the opening screen calls the report a note"
    assert "report" in said
    assert "report" in ui.START_LABEL.lower()
    assert "report" in ui.NEW_LABEL.lower()


def test_the_opening_says_what_the_product_makes_and_on_what_terms():
    """The display line is the claim, not a description of the buttons.

    It read "Read a report, or generate a new one", which named the two
    controls directly beneath it and said nothing about what is on the
    other side of them. A stranger four seconds into this screen needs
    the product's terms - filings, and every figure sourced - because
    that is the only thing that makes the rest worth reading.

    Still short. A display line that runs past a breath is a paragraph
    set large, which is the fault the 42px rank was given to avoid.
    """
    lead = ui.home()
    assert "Research reports from the filings" in lead
    assert "Every figure sourced" in lead
    said = re.search(r'<p class="lead">(.*?)</p>', lead).group(1)
    assert len(re.sub(r"<[^>]+>", "", said).split()) < 14, said


def test_the_opening_carries_what_the_steps_used_to_say():
    """The three load-bearing facts from the deleted Get started block:
    what a reader supplies, where the figures are read from, and how
    long a run takes. Deleting a section is only safe if what it was
    actually for survives it."""
    sub = re.search(r'<p class="sub">(.*?)</p>', ui.home(), re.S).group(1)
    assert "ticker" in sub and "how you invest" in sub
    assert "SEC filings" in sub
    # One word for one document. The first draft said "The note" here
    # and "Research notes" above, while every control, the bar and the
    # index say report - so a reader met the thing twice under two
    # names before touching it.
    assert "note" not in sub.lower()
    assert "five minutes" in sub


def test_the_home_screen_prints_no_numbered_instructions():
    """Get started is gone, and so is the component that drew it. A
    screen that still rendered the steps would be printing the same
    three facts twice, forty pixels apart."""
    assert not hasattr(ui, "steps"), "the steps component outlived its screen"
    assert "ar-steps" not in theme.stylesheet(), (
        "the stylesheet still carries rules for a block nothing renders"
    )


# ------------------------------------------------------- the two buttons

def test_the_home_action_and_the_form_action_have_different_names(monkeypatch):
    at = _open(monkeypatch)
    home_label = at.button(key="enter").label
    at.button(key="enter").click().run()
    form_label = at.button(key="inline_run").label
    assert home_label != form_label


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


def test_the_bar_does_not_claim_to_be_a_destination():
    """`aria-current="page"` belongs on a link in a set of navigation
    links, marking which one you are on. The bar's screen name is a
    label - the docstring is explicit that the clickable-looking pills
    were removed because nothing there was clickable - so announcing
    "current page" on it invites the same reach the pills did."""
    assert "aria-current" not in ui.topbar("reports")
    assert "Home" in ui.topbar("reports")


def test_the_strategy_box_is_driven_by_state_alone(monkeypatch):
    """Streamlit warns, on every single render, when a keyed widget
    carries a `value=` AND has that key written in session state - and
    it is right to: the two are different sources of truth for one
    field, and `value=` is the one it ignores after the first render.

    Session state is the one that works here, because it is what lets
    a changed selection replace the box while an edited description
    survives a rerun. So `value=` goes, rather than being left as a
    decoration that generates a warning and does nothing.
    """
    import pathlib
    import re

    source = pathlib.Path(
        pathlib.Path(__file__).resolve().parents[1] / "app.py"
    ).read_text(encoding="utf-8")
    block = source[source.index("def _controls("):]
    # Up to the next top-level definition. This read "\n@st.dialog",
    # the New report dialog that used to follow `_controls`; that dialog
    # is gone, so the anchor failed and this test stopped being about
    # the strategy box at all.
    block = block[: block.index("\ndef ", 1)]
    area = block[block.index('st.text_area(\n        "How you invest"'):][:300]
    assert "value=" not in area, (
        "the strategy box still passes a default alongside the state "
        "that overrides it"
    )

