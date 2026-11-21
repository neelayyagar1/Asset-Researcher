"""Constraints a screen-reader user could not hear.

Each field in the form is followed by a sibling `st.caption`, which
renders as an unrelated paragraph. A reader tabbing the form in forms
mode hears "Ticker, edit, AAPL" and nothing else - so the two
constraints that are not visible anywhere else never reach them:

  - `max_chars=8` silently truncates typing, and nothing on the
    screen says so;
  - the URL field takes one per line, and that lives only in a
    placeholder, which disappears on the first keystroke.

Streamlit's `help=` is the one parameter that wires text to a widget
with aria-describedby, so those two go there. The longer captions
stay visible prose rather than becoming tooltips: they are read by
everyone and a tooltip is read by almost nobody.
"""

from __future__ import annotations

import pathlib

APP = pathlib.Path(__file__).resolve().parents[1] / "app.py"


def _controls_source() -> str:
    source = APP.read_text(encoding="utf-8")
    start = source.index("def _controls(")
    return source[start : source.index("\n@st.dialog", start)]


def test_the_ticker_field_states_its_own_length_limit():
    block = _controls_source()
    ticker = block[block.index('st.text_input(\n        "Ticker"'):][:400]
    assert "help=" in ticker, (
        "max_chars=8 truncates typing and nothing tells the reader"
    )
    assert "8" in ticker


def test_the_url_field_states_its_format_outside_the_placeholder():
    block = _controls_source()
    urls = block[block.index('"Other documents to read'):][:400]
    assert "help=" in urls, (
        "the one-per-line format lives only in a placeholder, which "
        "disappears on the first keystroke"
    )


def test_the_long_captions_stay_visible_prose():
    """They are read by everyone where they are. A tooltip is read by
    almost nobody, and this form is already one the owner called
    cluttered."""
    block = _controls_source()
    assert block.count("st.caption(") >= 3
