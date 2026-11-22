"""The page is bounded at both ends, and the column's edges are drawn.

The shell was one flat #f4f6f9 field from the first pixel to the last.
Nothing marked where the page began, nothing marked where it ended, and
the single content column was implied by alignment alone - so every
screen read as a form with subtitles rather than as a publication, and
the foot of each one trailed off into its own bottom padding. That is
what "a lot of whitespace at the bottom" was pointing at: the gap was
never the problem, the page having no ending was.

Three devices answer it, and they are structure rather than decoration:
near-black bands at the top and the foot, hairline rails at the column's
own edges, and a tracked label above each section heading so a page has
chapters instead of paragraphs. All three are inside The Broadsheet
rather than a different direction - the marble, the serif, the one
accent and the no-cards rule are untouched.
"""

from __future__ import annotations

import re

from asset_researcher.ui import components as ui
from asset_researcher.ui import theme

CSS = re.sub(r"/\*.*?\*/", "", theme._APP_CSS, flags=re.S)


def _rule(selector: str) -> str:
    """Every declaration from every rule whose selector list contains
    `selector` exactly, joined, with comments already stripped.

    All of them, not the first. `.block-container` is declared four
    times - the column width, the report-view width, the form width and
    the rails - and reading only the first one made a test about the
    rails report that the rails were missing.
    """
    found = []
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", CSS):
        names = [part.strip() for part in match.group(1).split(",")]
        if selector in names:
            found.append(match.group(2))
    assert found, f"no rule for {selector}"
    return "\n".join(found)


def test_both_bands_are_ink_and_reach_the_window_edge():
    """A dark strip that stops where the text column stops reads as a
    wide heading inside the page. The frame belongs to the window.

    They reach it by different routes, because they are different
    things. The top bar is FIXED to the viewport: it sat 64px down the
    page with marble above it, and the cause was Streamlit's 16px flex
    gap around each of the zero-height bridge frames - a count that
    changes from screen to screen, so no margin could be tuned to it.
    Out of the flow, the question does not arise, and the bar is also
    then present on a 39,000px report rather than scrolling away in the
    first six hundred pixels. The closing band stays in the flow, where
    an ending belongs, and bleeds out with negative inline margins.
    """
    for selector in (".ar-topbar", ".ar-close"):
        assert "var(--shell-ink)" in _rule(selector), f"{selector} is not ink"
        assert "calc(50vw - 50% + var(--shell-gut))" in _rule(selector), (
            f"{selector} does not realign its contents to the column"
        )

    bar = _rule(".ar-topbar")
    assert "position: fixed" in bar and "top: 0" in bar, (
        "the bar is back in the page's flow and will float below the top"
    )
    assert "left: 0" in bar and "right: 0" in bar

    assert "calc(50% - 50vw)" in _rule(".ar-close"), (
        "the closing band stops at the column rather than the window"
    )

    # And the column leaves room for a bar that no longer takes any.
    assert "padding: 112px" in _rule(".block-container"), (
        "the fixed bar will sit on top of the first thing on the page"
    )


def test_streamlit_s_own_toolbar_does_not_sit_on_the_masthead():
    """It lives in a 60px absolute strip at the very top - exactly
    where the bar now is - and carries the framework's Deploy button
    and status pill. On this product that is both the wrong thing to
    see first and the wrong thing to see at all."""
    assert '[data-testid="stToolbar"]' in CSS
    body = _rule('[data-testid="stToolbar"]')
    assert "display: none" in body


def test_a_dark_field_gets_the_pale_rule_and_not_the_neutral_one():
    """`--shell-line` is a hairline for marble; on ink it is invisible,
    and no edge at all lets the band bleed into the page under it."""
    for selector in (".ar-topbar", ".ar-close"):
        body = _rule(selector)
        assert "rgba(255, 255, 255, .22)" in body, selector
        assert "var(--shell-line)" not in body, (
            f"{selector} uses the light-field hairline on a dark field"
        )


def test_our_own_footer_is_not_caught_by_the_rule_that_hides_streamlit_s():
    """`footer { display: none !important }` hid Streamlit's "Made with
    Streamlit" mark - and then hid ours, silently and with `!important`,
    the moment the shell grew a real closing band. It rendered into the
    page and computed to display:none.

    A footer is the right element for a page's ending, so the rule is
    narrowed rather than the landmark downgraded to a div.
    """
    assert "footer:not(.ar-close)" in CSS, (
        "the hide rule is not scoped, so the closing band is invisible"
    )
    assert not re.search(r"(^|,)\s*footer\s*(,|\{)", CSS, re.M), (
        "a bare `footer` selector is back and will hide the closing band"
    )
    assert "<footer" in ui.closing(["x"])


def test_the_column_draws_its_own_edges():
    """Every rule in the shell ran horizontally, so nothing on screen
    said where the one column began or ended."""
    body = _rule(".block-container")
    assert "border-inline" in body, "the chassis rails are gone"
    assert ".5px" in body, "a rail at 1px is a border round the page"


def test_the_actions_are_square_and_flat():
    """The rounded rectangle with a drop shadow is the default shape of
    every framework's button, and this shell was wearing it on its most
    looked-at control. The corner matches the rules, the table and the
    two bands, all of which are square."""
    body = _rule(".stButton > button")
    assert "border-radius: 0" in body, "the actions are rounded again"
    assert "box-shadow: none" in body, "the actions have a lift again"


def test_the_eyebrow_is_tracked_capitals_like_the_shell_s_other_labels():
    """Capitals are how this shell already marks a LABEL - the SAMPLE
    tag, the panel label and the section index all use them - so the
    eyebrow reads as one rather than as a second heading competing with
    the heading beneath it.

    The tracking is the part that has to be right. Capitals at normal
    tracking set tight and read as shouting; 0.14em is what makes a
    row of small capitals legible as a label.
    """
    body = _rule(".ar-brow")
    assert "text-transform: uppercase" in body
    assert "letter-spacing: .14em" in body
    assert "font-size: 11px" in body, (
        "an eyebrow at heading size is a second heading"
    )

    # And every other set of capitals in the shell is tracked too, so
    # none of them is the tight all-caps that reads as shouting.
    for match in re.finditer(r"([^{}]+)\{([^{}]*text-transform:\s*uppercase"
                             r"[^{}]*)\}", CSS):
        assert "letter-spacing" in match.group(2), (
            f"{match.group(1).strip()} sets capitals with no tracking"
        )


def test_a_section_without_an_eyebrow_still_renders_one_heading():
    """It is optional. A screen with a single section has nothing to
    distinguish it from, and a label above the only heading on a page
    is a rank invented for its own sake."""
    plain = ui.head("Reports")
    assert "ar-brow" not in plain
    assert "<h2>Reports</h2>" in plain

    labelled = ui.head("Reports", eyebrow="Archive")
    assert '<div class="ar-brow">Archive</div><h2>Reports</h2>' in labelled


def test_the_closing_band_states_only_what_it_is_given():
    """It takes its lines, so a screen says what is true of that screen
    and nothing states anything on another screen's behalf."""
    out = ui.closing(["One.", "", "Two."])
    assert out.count("<p>") == 2, "an empty line was printed as a paragraph"
    assert "One." in out and "Two." in out
    assert "Asset Researcher" in out


def test_the_home_screen_ends_on_the_band_and_labels_its_sections():
    import pathlib

    app = (pathlib.Path(__file__).resolve().parents[1] / "app.py").read_text(
        encoding="utf-8"
    )
    assert 'ui.head("Get started", eyebrow="How it works")' in app
    assert 'ui.head("Reports", eyebrow="Archive")' in app
    assert "ui.closing([" in app
    # The provenance line the top bar used to carry on every screen,
    # including the ones that have read no filing, now sits at the foot
    # of the screen that lists the reports it is true of.
    closing = app[app.index("ui.closing(["):][:900]
    assert "SEC EDGAR" in closing and "XBRL" in closing
    assert "not investment advice" in closing


def test_the_closing_band_stacks_on_a_phone():
    """It is a row of two: the mark, then the text. At 375px that row
    gave the text about 120px and set it one or two words to the line,
    which is worse than having no ending at all. Measured in the
    running page before and after: 120px, then 261px.
    """
    phone = CSS[CSS.index("@media (max-width: 700px)"):]
    assert ".ar-close" in phone, "the closing band is unanswered on a phone"
    block = phone[phone.index(".ar-close"):][:260]
    assert "flex-direction: column" in block
    # And the 620px measure that keeps the lines readable on a desktop
    # is a cap the phone has to drop, or it does nothing and the text
    # still cannot use the width it has.
    assert "max-width: none" in phone[phone.index(".ar-close .said"):][:120]


def test_the_form_narrows_its_fields_and_not_the_page():
    """A field stretched across 1120px is unpleasant to type into, so
    the form is capped - but capping the CONTAINER capped the page: the
    rails came in to hug the form, and the screen sat as a 760px strip
    in the middle of the window with 340px of nothing either side. It
    was the one screen whose edges did not match the product.

    Measured after: page 1120 at left 160, fields 760 on the column's
    own left edge.
    """
    assert ".block-container:has(.ar-form-head) {" not in CSS, (
        "the form screen narrows the whole page again"
    )
    body = _rule('.block-container:has(.ar-form-head) > '
                 '[data-testid="stVerticalBlock"]')
    assert "max-width: 760px" in body


def test_every_screen_with_a_foot_has_an_ending():
    """The home screen and the form screen both end on the band. A
    screen that simply stops is what produced the complaint about dead
    space at the bottom, and the band is an ending rather than filler -
    each one states the two things true of ITS screen."""
    import pathlib

    app = (pathlib.Path(__file__).resolve().parents[1] / "app.py").read_text(
        encoding="utf-8"
    )
    assert app.count("ui.closing([") == 2, (
        f"{app.count('ui.closing([')} screens end on the band"
    )
    # Not the same two lines on both, or one of them is stating
    # something on the other screen's behalf.
    first = app.index("ui.closing([")
    second = app.index("ui.closing([", first + 1)
    assert app[first:first + 400] != app[second:second + 400]
