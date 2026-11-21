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


def test_the_reports_table_sheds_a_column_on_a_phone():
    """Four columns do not fit 375px, and it showed.

    On the deployed site at phone width the home table overflowed its
    container: the header wrapped to "Headlin e metric", the Value
    column was clipped and the right edge was cut off. A table a reader
    cannot read is worse than one column fewer.

    The metric LABEL is the column to drop. A reader on a phone wants
    the ticker and the figure; the label explains the figure and can be
    read on the note itself.
    """
    css = theme._APP_CSS
    phone = css[css.index("@media (max-width: 700px)"):]
    assert "table.ar-list th:nth-child(3)" in phone, (
        "the metric label column is not dropped at phone width"
    )
    assert "table.ar-list td:nth-child(3)" in phone
