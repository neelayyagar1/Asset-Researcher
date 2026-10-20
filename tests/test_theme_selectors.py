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
