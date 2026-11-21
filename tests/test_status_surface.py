"""The status block is a document component that the shell also renders.

`ui.status` carries the note's own warnings - "Against this thesis",
"Model divergence", "Source currency", "Filing age", "No finding" - and
is declared in the document rules, in document tokens. The shell renders
the same component for the gate's "Refused", the throttle's "Slow down",
the workspace's failure panel and the samples warning, where the note's
warm cream-world neutrals sit wrong on the cold marble ground.

The remap for that was first written as `[data-testid="stMarkdown"]
.ar-status`, on the reasoning that the shell writes its statuses through
`st.markdown`. So does the note: a freshly generated report is written
INLINE into the page, block by block, through the same call. So the rule
reached the document's own five, and repainted them in shell tokens on
the live report screen while the samples iframe, the downloaded HTML and
the PDF kept the document's. Measured in the running app: body text
rgb(80, 83, 92) inline against rgb(64, 60, 51) framed, and the info
block's left rule rgb(226, 228, 233) against rgb(222, 217, 204).

The identical document rendering two ways depending on which door the
reader came through is the exact defect the host's table borders were
fixed for one commit earlier, and the one the reader pays for is the
live one.

No CSS container can tell the two apart - both are one `st.markdown`
block with nothing structural between them - so the surface is declared
at the call site, and these tests hold that line.
"""

from __future__ import annotations

import re
from pathlib import Path

from asset_researcher.ui import components, theme

ROOT = Path(__file__).resolve().parents[1]


def test_the_document_status_block_carries_no_shell_class():
    for level in ("success", "warning", "error", "info"):
        markup = components.status(level, "Tag", "message")
        assert "ar-status-shell" not in markup, (
            f"the document's {level} status is declaring itself the shell's"
        )


def test_the_shell_status_block_declares_its_surface():
    for level in ("success", "warning", "error", "info"):
        markup = components.shell_status(level, "Tag", "message")
        assert "ar-status-shell" in markup
        # And it is still the same component underneath: the severity
        # class is what carries the meaning and must survive the wrap.
        assert "ar-status " in markup


def test_the_shell_status_keeps_the_severity_class():
    """The severity hues are semantic. They mean the same thing on both
    surfaces and are measured for contrast on both, so only the NEUTRALS
    are ever remapped - a wrap that dropped `.bad` would take the one
    thing the left border exists to say."""
    assert "bad" in components.shell_status("error", "Refused", "no")
    assert "warn" in components.shell_status("warning", "Slow down", "no")
    assert "ok" in components.shell_status("success", "Verified", "no")


def _rules(css: str) -> str:
    """The sheet with its comments taken out.

    Checked against the declarations rather than the text, because the
    comment above this very rule quotes the selector it replaced - and
    the wrong version of this test matched its own explanation. The
    suite has been here before: an assertion on the word "stMarkdown"
    once matched an unrelated `stMarkdownContainer` rule.
    """
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def test_the_remap_is_keyed_on_the_shell_class_and_not_on_the_host():
    sheet = _rules(theme.stylesheet())
    assert ".ar-status-shell {" in sheet, "the shell's status has no rule"
    assert '[data-testid="stMarkdown"] .ar-status' not in sheet, (
        "the status remap is scoped to the host's markdown container "
        "again, which is also how the note is written inline - it would "
        "repaint the document's own status blocks on the live report "
        "screen and nowhere else"
    )


def test_the_remap_never_travels_with_an_export():
    """An exported note carries no shell, so a shell rule in the document
    sheet is dead weight on every download."""
    assert "ar-status-shell" not in _rules(theme.document_stylesheet())


def test_the_shell_screens_use_the_shell_status():
    """app.py is the shell. Every status it writes is the gate's, the
    workspace's or the index's - none of them the note's - so a bare
    `ui.status` there is a block that will wear the document's neutrals
    on the marble ground."""
    app = (ROOT / "app.py").read_text()
    stray = re.findall(r"ui\.status\(", app)
    assert not stray, (
        f"{len(stray)} shell status call(s) in app.py still use the "
        "document surface; use ui.shell_status"
    )
    assert "ui.shell_status(" in app


def test_the_document_screens_use_the_document_status():
    """And the other direction. document.py builds the note, which is
    read in an iframe, as a file and in print, where the shell's tokens
    are not declared at all."""
    doc = (ROOT / "asset_researcher" / "ui" / "document.py").read_text()
    assert "shell_status" not in doc, (
        "the note is declaring a status block as the shell's; in an "
        "export the shell tokens do not exist"
    )
