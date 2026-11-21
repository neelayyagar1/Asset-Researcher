"""The note, prepared for the frame it is about to render in.

Lifted out of app.py so it can be tested without standing up a
Streamlit script. Both pieces here run INSIDE the note's own iframe,
which is same-origin: the document sizes its own frame and names its
own frame, because the parent cannot pass either through
`components.html`.
"""

from __future__ import annotations

from asset_researcher.ui.export import _JUMP_SCRIPT

_NAME_FRAME = r"""<script>
(function arNameFrame() {
  // Streamlit's component iframe is titled "st.iframe", so a screen
  // reader announced the frame holding a 35,000px research note by
  // the name of the framework hosting it. `components.html` takes no
  // title and the parent cannot reach in reliably, but the frame is
  // same-origin and the document inside it can name ITSELF - the same
  // `window.frameElement` route `fitFrame` already uses.
  //
  // Appended separately from the jump script, and not behind its
  // guard: every note already built carries `fitFrame`, so anything
  // added inside that script would reach none of them.
  try {
    var frame = window.frameElement;
    if (!frame) return;
    var heading = document.querySelector('h1');
    var name = (heading && heading.textContent.trim())
      || document.title || 'Research note';
    frame.setAttribute('title', name + ' - research note');
  } catch (e) {}
})();
</script>"""


def framed(note_html: str) -> str:
    """A note about to be shown inside the app's frame.

    Notes are artifacts: the six that ship were built by a pipeline run
    and carry whatever scripts the renderer emitted that day. Appending
    the frame-sizing script here rather than only at build time means a
    note built last month behaves like one built this minute, and the
    fix does not cost six API calls to deploy.

    Idempotent. A freshly built note carries the same function from
    `_JUMP_SCRIPT`; running it twice sets the same height twice.
    """
    from asset_researcher.ui.export import _JUMP_SCRIPT

    # The naming script goes on whether or not the jump script is
    # already there. A note built before this carries `fitFrame`, so
    # anything guarded by that check would never reach the six that
    # ship - and those are the ones a reviewer opens.
    extra = "" if "arNameFrame" in note_html else _NAME_FRAME
    if "fitFrame" not in note_html:
        extra = _JUMP_SCRIPT + extra
    if not extra:
        return note_html
    if "</body>" in note_html:
        return note_html.replace("</body>", f"{extra}</body>", 1)
    return note_html + extra


