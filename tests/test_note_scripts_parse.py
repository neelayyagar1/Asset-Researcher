"""Every script a note carries is run through a JavaScript parser.

This is the test that was missing, and the gap was not small. The jump
script read:

    if (document.readyState === 'complete') fitFrame();arTableStops();
    else window.addEventListener('load', fitFrame);

Unbraced, with a second statement between the `if` and the `else`, so
the `else` belongs to no `if`. That is a SyntaxError, and a SyntaxError
in a classic script costs the WHOLE script: neither function was ever
defined, in any note that has ever shipped.

What it cost, measured in the running app before the repair: the note's
iframe stayed at the 2,000px the host gave it with a 38,959px document
scrolling inside it, so every link in the section index scrolled the
page to a coordinate far past its end and landed, clamped, in the same
place every time - which is exactly how the owner reported it. And the
table wrappers kept whatever tab-stop state the server had guessed,
rather than the state `arTableStops` measures.

Twelve tests across four modules asserted on that script. Every one of
them passed, because every one of them asserted on the STRING: that it
contains `function fitFrame` exactly once, that it is appended when
missing, that it is not appended twice. A string is not a program. The
only thing that can tell you a script runs is a parser, so this module
hands the scripts to one.

`node --check` parses a file as a CommonJS script and reports syntax
errors without executing anything - no network, no DOM, nothing from
the note is run. It skips where node is absent rather than failing,
because a machine without node has nothing to check with; CI and this
repository both have it.
"""

from __future__ import annotations

import re
import shutil
import subprocess

import pytest

from asset_researcher.ui import export, frame

_NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(
    not _NODE, reason="node is not installed; nothing can parse the scripts"
)

_SCRIPT = re.compile(r"<script>(.*?)</script>", re.S)


def _parses(source: str, tmp_path, name: str) -> tuple[bool, str]:
    path = tmp_path / f"{name}.js"
    path.write_text(source, encoding="utf-8")
    done = subprocess.run(
        [_NODE, "--check", str(path)], capture_output=True, text=True
    )
    return done.returncode == 0, (done.stderr or "").strip()


def test_the_jump_script_parses(tmp_path):
    """The one that did not, for the whole life of the product."""
    blocks = _SCRIPT.findall(export._JUMP_SCRIPT)
    assert blocks, "the jump script has no <script> block"
    for i, block in enumerate(blocks):
        ok, err = _parses(block, tmp_path, f"jump{i}")
        assert ok, f"the jump script does not parse:\n{err}"


def test_every_script_a_fresh_note_carries_parses(tmp_path):
    """Not the fragment - the note, as `framed` hands it to the frame.

    A note picks up scripts from three places: the renderer bakes the
    jump script in at build time, and `framed` appends the frame-naming
    script and, for an old note, the jump script again. Any of the three
    can be the broken one, and a broken one anywhere discards only
    itself - which is why the frame-naming script kept working while
    `fitFrame` did not, and why nobody noticed.
    """
    note = frame.framed("<html><body><h1>Testco</h1><p>x</p></body></html>")
    blocks = _SCRIPT.findall(note)
    assert len(blocks) >= 2, f"expected the framed note to carry scripts, got {len(blocks)}"
    for i, block in enumerate(blocks):
        ok, err = _parses(block, tmp_path, f"framed{i}")
        assert ok, f"script {i} in a framed note does not parse:\n{err}"


def test_the_repair_is_what_makes_an_old_note_parse(tmp_path):
    """The six sealed notes carry the broken statement verbatim.

    Rebuilding them costs six API calls and moves every as-of date in
    them, so `frame.repair` replaces the one broken statement on the way
    to the reader. This checks both halves: that the text it looks for
    really is a SyntaxError, and that what it writes in its place really
    is not. Asserting only the second would pass against a repair that
    had stopped matching anything.
    """
    broken = f"(function () {{\n  {frame._BROKEN_ENTRY}\n}})();"
    ok, _ = _parses(broken, tmp_path, "broken")
    assert not ok, (
        "the text `repair` looks for parses cleanly, so either it is no "
        "longer the broken statement or the parser is not checking"
    )

    fixed = f"(function () {{\n  {frame._FIXED_ENTRY}\n}})();"
    ok, err = _parses(fixed, tmp_path, "fixed")
    assert ok, f"the replacement does not parse either:\n{err}"


def test_repairing_a_note_twice_changes_nothing_the_second_time():
    """`framed` runs on every render of every note."""
    note = f"<html><body><script>\n  {frame._BROKEN_ENTRY}\n</script></body></html>"
    once = frame.repair(note)
    assert frame.repair(once) == once
    assert frame._BROKEN_ENTRY not in once
    assert frame._FIXED_ENTRY in once


def test_a_note_built_today_is_left_alone_by_the_repair():
    """The repair is a bridge for six sealed artifacts, not a
    permanent rewriting step. A note the current renderer built has
    nothing to find, and this is what will tell the next person that
    `frame.repair` can be deleted."""
    fresh = export._JUMP_SCRIPT
    assert frame._BROKEN_ENTRY not in fresh
    assert frame.repair(fresh) == fresh
