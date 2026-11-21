"""The section index, lifted into the scrollport that actually scrolls.

`position: sticky` resolves against an element's own scrollport.
`fitFrame` sizes the note's iframe to the full height of the document
inside it - 35,691px for ADP - so the page scrolls once rather than
through a nested scrollbar. The cost, found only by measuring, is
that the note's document never scrolls, so nothing in it can stick:
the section index sat at viewport-top 773 at the top of the note and
-19,227 twenty thousand pixels down. On the longest screen in the
product there was no navigation past the first screen.

Two traps on the way to the fix, both of which produced a nav that
rendered, looked right and did nothing - the worst available outcome.
Both are pinned here.
"""

from __future__ import annotations

import pathlib

APP = pathlib.Path(__file__).resolve().parents[1] / "app.py"


def _bridge() -> str:
    source = APP.read_text(encoding="utf-8")
    start = source.index("def _nav_bridge(")
    return source[start : source.index("\ndef ", start + 10)]


def test_the_handler_is_installed_into_the_parent_realm():
    """The first version used addEventListener from inside the
    component iframe. Those closures belong to that iframe's realm,
    and Streamlit discards it on the next rerun, so every link went
    dead while still looking like a link."""
    bridge = _bridge()
    assert "__arNavGo" in bridge
    assert "createElement('script')" in bridge, (
        "the scroll handler is not installed as parent-realm code"
    )
    assert "onclick" in bridge, (
        "the links do not call it through an inline handler, so they "
        "depend on the bridge frame surviving"
    )


def test_it_does_not_ask_for_a_smooth_scroll():
    """Measured on this container: `scrollTo` with behavior "smooth"
    is a silent no-op - scrollTop stays where it was - while the same
    call without it lands exactly. A navigation that does not navigate
    is worse than one that does not animate."""
    assert 'behavior: "smooth"' not in _bridge()


def test_the_id_from_the_note_is_checked_before_it_is_interpolated():
    """It is read out of the note's own markup and written into an
    inline handler, which is a string the parent evaluates."""
    assert "/^[A-Za-z0-9_-]+$/" in _bridge()


def test_the_original_index_is_hidden_rather_than_left_to_print_twice():
    assert "source.style.display = 'none'" in _bridge()


def test_the_reading_screen_installs_it():
    """Called, not merely defined - and before the frame it reads."""
    source = APP.read_text(encoding="utf-8")
    after = source[source.index("def _nav_bridge("):]
    call = after.index("    _nav_bridge()")
    frame = after.index("components.html(framed(note.html)")
    assert call < frame, "the bridge runs after the note it reads"
