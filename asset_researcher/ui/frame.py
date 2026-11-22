"""The note, prepared for the frame it is about to render in.

Lifted out of app.py so it can be tested without standing up a
Streamlit script. Both pieces here run INSIDE the note's own iframe,
which is same-origin: the document sizes its own frame and names its
own frame, because the parent cannot pass either through
`components.html`.
"""

from __future__ import annotations

import re

from asset_researcher.ui import format as fmt
from asset_researcher.ui.export import NEW_CLICK, OLD_CLICK, _JUMP_SCRIPT

# Only inside a chip's own text, so nothing in the note's prose or in
# any table of filing dates is touched.
_CHIP_DATE = re.compile(r">Filed (\d{4}-\d{2}-\d{2})<")

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


# The exact broken statement, as every note built before the repair
# carries it, and what it should have said.
_BROKEN_ENTRY = (
    "if (document.readyState === 'complete') fitFrame();arTableStops();\n"
    "  else window.addEventListener('load', fitFrame);\n"
    "  window.addEventListener('resize', fitFrame);"
)
_FIXED_ENTRY = (
    "function arFit() { fitFrame(); arTableStops(); }\n"
    "  if (document.readyState === 'complete') { arFit(); }\n"
    "  else { window.addEventListener('load', arFit); }\n"
    "  window.addEventListener('resize', arFit);"
)


def repair(note_html: str) -> str:
    """Make an already-built note's script parse.

    Notes are artifacts. The six that ship were sealed months ago and
    carry whatever the renderer emitted that day - and what it emitted
    was an unbraced `if` followed by a second statement and an `else`,
    which is a SyntaxError. The browser threw the whole script away, so
    no note that has ever shipped sized its own frame or marked its own
    scrollable tables.

    Fixing `export.py` fixes notes built from now on. It reaches none
    of the six, and rebuilding those costs six API calls and moves
    every as-of date in them for a reason that has nothing to do with
    their figures. So the one broken statement is replaced here, on the
    way to the reader, exactly as `framed` already appends the scripts
    an old note is missing.

    A note built after the repair does not contain the broken text and
    comes back untouched, so this costs one failed substring search and
    disappears on its own once the six are next rebuilt.
    """
    if _BROKEN_ENTRY in note_html:
        note_html = note_html.replace(_BROKEN_ENTRY, _FIXED_ENTRY)
    # The second one, for the same reason: a sealed note's click handler
    # reaches only the section bar, so the masthead's own chips still
    # resolve against the parent page and load the whole application
    # into the frame. Replaced here rather than rebuilt, exactly as
    # above.
    if OLD_CLICK in note_html:
        note_html = note_html.replace(OLD_CLICK, NEW_CLICK)
    # And the filing date in the masthead chip, which the six carry as
    # the ISO day the renderer wrote that month. ISO is right for a key
    # and wrong for a line of prose beside a company's name, and the
    # index beside these notes now prints the long form; two spellings
    # of one filing date make a reader check whether they are looking
    # at the same filing.
    note_html = _CHIP_DATE.sub(
        lambda m: f">Filed {fmt.filed_date(m.group(1))}<", note_html
    )
    return note_html


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

    # Before anything is appended: an old note's own script has to be
    # made to parse, or the `fitFrame` it carries is a function that
    # never comes into existence and the guard below reads its NAME in
    # a script the browser discarded.
    note_html = repair(note_html)

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


