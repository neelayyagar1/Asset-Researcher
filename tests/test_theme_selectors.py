"""Every Streamlit hook the stylesheet reaches for must actually exist.

This guards a class of bug that has now happened twice and is invisible
both to the test suite and to a screenshot: a rule targeting a test id
Streamlit does not emit styles nothing, silently, and the surface keeps
Streamlit's own defaults. The last instance left the progress block a
reader watches for the whole of a ninety-second run as the one unthemed
surface in the product, carrying an 8px radius in a design system with no
rounded corners anywhere else.

Streamlit's test ids are not a public API, so the check reads the shipped
front-end assets rather than trusting a list written here. A Streamlit
upgrade that renames or drops a hook fails this test instead of quietly
removing the styling.
"""

from __future__ import annotations

import pathlib
import re

import pytest
import streamlit

from asset_researcher.ui import theme

_TESTID = re.compile(r'\[data-testid="(st[A-Za-z0-9]+)"\]')


def _shipped_test_ids() -> set[str]:
    static = pathlib.Path(streamlit.__file__).parent / "static"
    found: set[str] = set()
    for path in static.rglob("*.js"):
        # Bare tokens, not quoted ones: the bundle is minified and the
        # ids appear in several syntactic positions. A word boundary is
        # what keeps `stStatus` from matching inside `stStatusWidget`,
        # which is the exact pair that hid the last dead rule.
        found.update(re.findall(r'\bst[A-Z][A-Za-z0-9]*\b', path.read_text(
            encoding="utf-8", errors="ignore"
        )))
    return found


def test_every_streamlit_test_id_in_the_stylesheet_is_one_streamlit_emits():
    shipped = _shipped_test_ids()
    if not shipped:
        pytest.skip("Streamlit's static assets are not present in this install")

    used = set(_TESTID.findall(theme.stylesheet()))
    assert used, "the stylesheet should reach into the Streamlit shell"

    missing = sorted(used - shipped)
    assert not missing, (
        "the stylesheet targets Streamlit test ids that this build does not "
        f"emit, so those rules style nothing: {missing}. Either the hook was "
        "renamed upstream or it never existed."
    )


_AR_CLASS = re.compile(r"\.(ar-[a-z0-9-]+)")


def _classes_the_code_emits() -> set[str]:
    """Every `ar-*` class any Python module actually writes into markup."""
    root = pathlib.Path(__file__).resolve().parents[1]
    emitted: set[str] = set()
    sources = list((root / "asset_researcher").rglob("*.py")) + [root / "app.py"]
    for path in sources:
        if path.name == "theme.py":
            continue  # the stylesheet declares; it does not emit
        emitted.update(
            re.findall(r"\bar-[a-z0-9-]+", path.read_text(encoding="utf-8"))
        )
    return emitted


def test_the_stylesheet_has_no_rules_for_classes_nothing_emits():
    """Dead rules are worse than missing ones.

    When the editorial shell was replaced, `.ar-about`, `.ar-doors`,
    `.ar-claims` and `.ar-workspace` rules stayed behind with nothing in
    Python emitting those classes. They styled nothing, and the real
    cost is the next surface: a new component that happens to use one of
    those names inherits a layout from a world that was deliberately
    discarded.
    """
    # Comments first: a rule's own removal note names the class it
    # removed, and matching that would report the fix as the defect.
    strip = lambda css: re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    declared = set(_AR_CLASS.findall(strip(theme.stylesheet())))
    declared |= set(_AR_CLASS.findall(strip(theme.document_stylesheet())))
    emitted = _classes_the_code_emits()

    orphans = sorted(declared - emitted)
    assert not orphans, (
        "the stylesheet declares rules for classes no Python module "
        f"writes into markup: {orphans}. Either something stopped "
        "emitting them, or they outlived the surface they were built for."
    )


_CH_WIDTH = re.compile(r"(max-width|width|min-width)\s*:\s*[\d.]+ch")


def test_no_shell_width_is_expressed_in_ch():
    """The one-column rule, enforced rather than trusted.

    A `ch` resolves against a proportional face and lands on a
    fraction. The shell this replaced carried 394.017px, 528.62px and
    630.59px that way - three container edges no two blocks could ever
    share - which is what produced the three competing centre axes.

    The rule was then broken twice by the person who wrote it: once by a
    lead paragraph at `62ch`, which measured 531.067px in the live DOM
    and put a second container width back on the home screen.

    The note is exempt and keeps `ch` for its prose measures, which is
    what `ch` is for: a reading measure is a count of characters. This
    checks the shell only.
    """
    # The app sheet is the document sheet plus the shell block, both
    # wrapped in one <style>, so subtracting the rendered document sheet
    # leaves its closing tag behind and none of its rules. The shell
    # block itself is what to read.
    shell_only = theme._APP_CSS
    assert shell_only.strip(), "the shell stylesheet could not be isolated"
    assert "ar-topbar" in shell_only, "that is not the shell block"

    offenders = _CH_WIDTH.findall(shell_only)
    found = [m.group(0) for m in _CH_WIDTH.finditer(shell_only)]
    assert not offenders, (
        f"the shell declares widths in `ch`, which resolve to fractions "
        f"and break the one-column rule: {found}"
    )


def test_the_reports_table_sheds_the_right_columns_on_a_phone():
    """Seven columns do not fit 375px, and four did not either.

    On the deployed site at phone width the four-column table already
    overflowed: the header wrapped to "Headlin e metric", the Value
    column was clipped and the right edge was cut off.

    The columns are named here rather than numbered. The previous
    version pinned `nth-child(3)`, which was the metric label when it
    was written and became Price the day the table widened - so it
    would have gone on passing while the phone hid the wrong column.
    It now resolves the index against the header row the component
    actually emits.
    """
    from asset_researcher.ui import components as ui

    html = ui.report_rows(
        [{"ticker": "A", "company": "B", "metric": "C", "value": "D",
          "price": "E", "filed": "F", "cited": "G", "slug": "a"}],
        token="t",
    )
    headers = re.findall(r"<th[^>]*>(.*?)</th>", html)
    assert headers, "no header row to check against"

    css = theme._APP_CSS
    phone = css[css.index("@media (max-width: 700px)"):]
    hidden = {
        headers[int(n) - 1]
        for n in re.findall(r"table\.ar-list td:nth-child\((\d+)\)", phone)
        if int(n) <= len(headers)
    }

    # What a reader on a phone came for.
    assert "Ticker" not in hidden
    assert "Company" not in hidden
    assert "Value" not in hidden
    # What explains a figure rather than being one, or is context the
    # note itself carries.
    for context in ("Price", "Headline metric", "Filed", "Cited"):
        assert context in hidden, f"{context} still shown at 375px"


def _strip(css: str) -> str:
    """CSS with comments removed, scanned rather than regexed."""
    out, at = [], 0
    while True:
        opened = css.find("/*", at)
        if opened < 0:
            out.append(css[at:])
            return "".join(out)
        closed = css.find("*/", opened + 2)
        assert closed >= 0
        out.append(css[at:opened])
        at = closed + 2


def test_the_stylesheet_is_not_broken_by_its_own_comments():
    """This caught a real one within an hour of being written.

    An edit to the phone rules left two sentences of prose sitting
    outside a comment with a dangling `*/` after them. CSS does not
    fail loudly: the browser discarded everything from that point to
    the next closing brace, so the whole phone table rule silently
    stopped applying and the home table went back to overflowing a
    375px screen. The suite was green throughout, because every test
    about that rule asked whether the TEXT was present in the
    stylesheet - and it was, inside the wreckage.

    The stylesheet carries a great deal of explanatory comment by
    design, which is exactly why it needs this.
    """
    css = theme.stylesheet()

    # Scanned the way a browser scans it, rather than counted. CSS
    # comments do not nest: a `/*` inside a comment body is ordinary
    # prose, and one of these comments genuinely contains one while
    # discussing dead rules. Counting markers called that a defect.
    stripped = []
    at = 0
    while True:
        opened = css.find("/*", at)
        if opened < 0:
            stripped.append(css[at:])
            break
        closed = css.find("*/", opened + 2)
        assert closed >= 0, (
            f"a comment opens at {opened} and never closes, so the rest "
            "of the stylesheet is inside it"
        )
        stripped.append(css[at:opened])
        at = closed + 2
    body = "".join(stripped)

    assert "*/" not in body, (
        "a `*/` survives comment-stripping, so some prose is sitting in "
        "the stylesheet as if it were CSS"
    )

    # Braces balance, and never go negative - which is what a stray
    # `}` inside what was meant to be prose would do.
    depth = 0
    for char in body:
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            assert depth >= 0, "a closing brace with nothing open"
    assert depth == 0, f"{depth} rule(s) left unclosed"


def test_no_rule_in_the_dark_block_is_overridden_later_in_the_sheet():
    """A media query adds no specificity.

    The dark block set `[data-testid="stDialog"] div[role="dialog"]`
    to the dark panel, and the same selector at the same specificity
    appeared again further down, outside any media query, painting it
    `var(--paper)`. The later one won in both schemes, so the New
    report dialog stayed cream while its labels were painted from dark
    tokens - every label on that form unreadable, from a rule that
    looked right where it was written.

    Checked structurally, because the next such collision will not
    look wrong either.
    """
    css = _strip(theme.stylesheet())
    start = css.index("@media (prefers-color-scheme: dark)")
    depth, end = 0, None
    for i in range(start, len(css)):
        if css[i] == "{":
            depth += 1
        elif css[i] == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    assert end, "the dark block never closes"
    dark, after = css[start:end], css[end + 1:]

    selectors = {
        s.strip()
        for block in re.findall(r"([^{}]+)\{", dark)
        for s in block.split(",")
        if s.strip() and not s.strip().startswith("@")
    }
    later = {
        s.strip()
        for block in re.findall(r"([^{}]+)\{", after)
        for s in block.split(",")
        if s.strip() and not s.strip().startswith("@")
    }
    clashes = sorted(selectors & later)
    assert not clashes, (
        f"these selectors are set in the dark block and set again "
        f"later at the same specificity, so the later rule wins in "
        f"both schemes: {clashes}"
    )
