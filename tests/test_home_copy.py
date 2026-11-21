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


def test_the_lead_names_both_ways_on_without_explaining_the_product():
    """The opening line is an instruction, not a description.

    It used to be a three-line paragraph explaining what the tool does,
    set left at 560px under a centred heading - two centre axes and a
    wall of prose on the screen a reader spends four seconds on. The
    owner's note was blunt and correct. The screen offers exactly two
    things, so the line names exactly those two.
    """
    lead = ui.home()
    assert "Read a report" in lead
    assert "generate a new one" in lead
    # Short enough to be read rather than skipped.
    text = re.sub(r"<[^>]+>", "", lead).strip()
    assert len(text.split()) < 20, text


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
    block = block[: block.index("\n@st.dialog")]
    area = block[block.index('st.text_area(\n        "How you invest"'):][:300]
    assert "value=" not in area, (
        "the strategy box still passes a default alongside the state "
        "that overrides it"
    )


def test_the_steps_are_a_list_in_the_markup_not_only_in_the_paint():
    """SC 1.3.1. `steps()` says in its own docstring that instructions
    are a numbered list because that is what instructions are - and then
    emitted four sibling divs whose numbers came only from a CSS
    `counter()` on a `:before`.

    Generated content is announced by some AT and browser pairs and not
    others, so the order was at best unreliable and at worst four
    unrelated paragraphs. The ordering IS the content here: step three
    does not make sense before step two.
    """
    from asset_researcher.ui import components as ui

    html = ui.steps(("First thing", "Second thing"))
    assert "<ol" in html and "</ol>" in html
    assert html.count("<li") == 2
    # Safari strips the list role when list-style is none.
    assert 'role="list"' in html


def test_the_steps_do_not_wear_the_hosts_list_item_box():
    """Making the steps a real `ol` handed the host two selectors, not one.

    The first pass fixed the container: Streamlit ships
    `.st-emotion-cache-... > ol { display: block; width: fit-content }`
    and `ol.ar-steps` had to take `!important` to keep four columns.

    It styles the ITEMS too - `margin-left: 1.15rem`, `padding-left:
    .3rem`, `margin-block: .2rem` - and out-specifies `.ar-step` at
    (0,1,0). Measured in the running page after the container was fixed:
    the `ol` box started at x 28 with the opening line, both section
    heads and the index, and all four steps sat at 46.4 inside it, so
    step one's prose began at 51.2 - 23px right of every other left edge
    on the page. A single left edge for the column is the one thing this
    direction rests on, and the Get started block was the only thing
    breaking it. `.ar-step`'s own `padding: 2px 20px 2px 0` was
    discarded with it: computed padding-top and padding-right were 0.

    `ol.ar-steps > li.ar-step` is (0,2,2), which clears the host without
    `!important` - verified by injecting exactly this rule into the
    running page and re-measuring at x 28.
    """
    from asset_researcher.ui import theme

    sheet = theme.stylesheet()
    rule = re.search(
        r"ol\.ar-steps > li\.ar-step \{([^}]*)\}", sheet
    )
    assert rule, "nothing takes the host's list-item box off the steps"
    body = rule.group(1)
    assert "margin: 0" in body, (
        "the steps keep the host's margin-left, which indents the whole "
        "column group off the page's left edge"
    )
    assert "padding: 2px 20px 2px 0" in body, (
        "the step's own padding is not restored, so the column gutter "
        "the design declares is not applied"
    )


def test_the_phone_step_rules_can_still_win():
    """The fix above raised the base rule to (0,2,2), so the narrow
    viewport block had to follow it up. A bare `.ar-step` there at
    (0,1,0) now loses, and the four steps would stack while keeping
    their desktop gutters - a regression introduced by a fix, which is
    the pattern this file keeps catching."""
    from asset_researcher.ui import theme

    sheet = theme.stylesheet()
    phone = sheet[sheet.index("grid-template-columns: minmax(0, 1fr)"):]
    phone = phone[:1200]
    assert "ol.ar-steps > li.ar-step { padding-right: 0" in phone, (
        "the phone rule is written at a specificity the base rule beats"
    )


def test_each_step_is_a_list_item_to_a_screen_reader():
    """`role="list"` on the container was half the fix.

    WebKit drops the `listitem` role from an `li` whose `display` is not
    `list-item`, and `.ar-step` is `display: grid` so the number and the
    prose can stack. A role on the container with none on the items is a
    list announced with no members - the original defect wearing an ARIA
    attribute, and it reads as fixed, which is worse.
    """
    from asset_researcher.ui import components

    markup = components.steps(["one", "two", "three", "four"])
    assert markup.count('role="listitem"') == 4, (
        "the steps are a list whose items carry no role, which WebKit "
        "strips because they are display: grid"
    )
    assert 'role="list"' in markup
