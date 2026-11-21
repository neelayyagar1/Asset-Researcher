"""What a screen reader calls the thing holding the research note.

Measured in the running app: the iframe carrying a 35,691px note is
announced as "st.iframe" - Streamlit's default title - so the single
most important region in the product is named after the framework
that happens to host it. The zero-height frame carrying the Back
bridge gets the same name, and announces itself as a frame despite
holding nothing a reader can use.

`components.html` takes no title, and `_JUMP_SCRIPT` already travels
inside every built note, so `_framed` skips injecting it - which means
a fix inside that script would reach nothing already built. Both
frames are same-origin, so each can name or hide ITSELF through
`window.frameElement`, which is the mechanism `fitFrame` already uses
successfully. That works on a note built last month.
"""

from __future__ import annotations

import pathlib

APP = pathlib.Path(__file__).resolve().parents[1] / "app.py"


from asset_researcher.ui.frame import framed as _framed


BUILT = "<html><body><p>x</p><script>function fitFrame(){}</script></body></html>"
FRESH = "<html><body><p>x</p></body></html>"


def test_a_note_names_its_own_frame():
    assert "frameElement" in _framed(FRESH)
    assert "title" in _framed(FRESH)


def test_a_note_built_before_this_still_names_its_frame():
    """The guard that stops the jump script being injected twice must
    not stop this, or the six notes already sealed keep the default
    name."""
    out = _framed(BUILT)
    assert "frameElement" in out
    assert out.count("function fitFrame") == 1, "the jump script was doubled"


def test_naming_twice_does_not_stack():
    once = _framed(FRESH)
    assert _framed(once).count("arNameFrame") == once.count("arNameFrame")


def test_the_back_bridge_hides_its_own_frame():
    """It is a zero-height script carrier. It should not be a frame a
    reader is offered."""
    source = APP.read_text(encoding="utf-8")
    bridge = source[source.index("def _back_bridge("):]
    bridge = bridge[: bridge.index("\n\n\n")]
    assert "aria-hidden" in bridge
