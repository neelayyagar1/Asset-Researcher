"""The sealed notes carry the stylesheet the code currently generates.

`export.report_to_html` bakes `theme.document_stylesheet()` into each
note at build time, so the six sealed samples hold a COPY of that
function's output taken on the day they were rendered. Every other
document-sheet test in this suite asserts against the function. Nothing
asserted against the copy, and the copy is what a reader opens: the
samples screen renders it in an iframe, and the download button hands it
over as a file.

The gap has cost something twice now. The Peers sticky-header defect was
fixed in theme.py and stayed live in all six notes on the demo site
until it was noticed by hand. Then a review of this branch found the
blob a second rule behind - the hardened `.ar-skip` - with the whole
suite green, because there was still nothing comparing them.

So this compares them. `scripts/restyle-samples.py` is the repair, and
`scripts/pack-samples.py` re-seals the result.

It needs SAMPLES_KEY, which the rest of the suite deliberately runs
WITHOUT - several modules delete it from the environment to prove the
app degrades honestly when the blob cannot be opened. So this skips when
the key is absent rather than failing: on a machine or a CI runner with
no key there is nothing here to check, and a skip says that, where a
failure would say the samples are wrong.
"""

from __future__ import annotations

import os
import re

import pytest

from asset_researcher.ui import theme

_KEY = os.environ.get("SAMPLES_KEY", "")

pytestmark = pytest.mark.skipif(
    not _KEY, reason="SAMPLES_KEY is not set; the sealed blob cannot be opened"
)

_BLOCK = re.compile(r"<style>(.*?)</style>", re.S)


def _sealed():
    from asset_researcher.hosting import samples

    return samples.load(_KEY)


def test_the_blob_opens_and_holds_every_note():
    notes = _sealed()
    assert len(notes) == 6, f"expected six sealed notes, found {len(notes)}"


def test_each_sealed_note_carries_the_current_document_stylesheet():
    """Byte-identical, not merely similar.

    A single rule's worth of drift is exactly what went unnoticed twice,
    and `in` or a length check would have passed both times. The
    comparison is against the whole generated block, because that block
    is generated wholesale and there is no legitimate reason for a
    shipped copy to differ from it by anything at all.
    """
    current = _BLOCK.search(theme.document_stylesheet())
    assert current, "the document stylesheet has no <style> block"
    expected = current.group(1)

    behind = []
    for note in _sealed():
        blocks = _BLOCK.findall(note.html)
        assert blocks, f"{note.slug} carries no stylesheet at all"
        if not any(block == expected for block in blocks):
            sizes = [len(b) for b in blocks]
            behind.append(f"{note.slug} (blocks {sizes}, current {len(expected)})")

    assert not behind, (
        "sealed notes are not carrying the stylesheet this code "
        "generates: " + "; ".join(behind) + ". Repair with "
        "`python scripts/restyle-samples.py` then "
        "`SAMPLES_KEY=... python scripts/pack-samples.py`."
    )


def test_the_sealed_notes_never_carry_a_shell_only_rule():
    """The other direction of the same seam.

    The shell's tokens and its display face are deliberately kept out of
    `_root()` so that a shell change cannot restyle six sealed notes. If
    a shell rule ever reaches the document sheet, the restyle script
    would then bake it into every one of them - so the drift check above
    would pass while the notes were wrong.
    """
    for note in _sealed():
        for token in ("--shell-bg", "--shell-display", "Newsreader"):
            assert token not in note.html, (
                f"{note.slug} carries the shell-only {token}"
            )


def test_the_repair_script_ships_with_the_repository():
    """It was a scratch file for its first two uses, which is how the
    second drift became possible: the only way to repair the blob lived
    outside the repository and did not survive the session."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "restyle-samples.py"
    assert script.is_file(), "scripts/restyle-samples.py is missing"
    body = script.read_text()
    assert "document_stylesheet" in body
    assert "REFUSED" in body, (
        "the script no longer refuses when a note's body would change, "
        "which is the check that makes it a re-render and not an edit"
    )


def test_every_sealed_note_is_repaired_before_it_reaches_a_reader():
    """The six carry a script the browser cannot parse.

    `export.py` is fixed, which fixes notes built from now on and
    reaches none of these: they were sealed months ago. `frame.framed`
    replaces the broken statement on the way to the frame, so this
    checks the thing that matters - that what a reader is handed
    parses - rather than that a function was called.

    When these six are next rebuilt the first assertion below starts
    failing, and that is the signal that `frame.repair` has become dead
    weight and can go.
    """
    import shutil
    import subprocess
    import tempfile

    from asset_researcher.ui import frame

    node = shutil.which("node")

    for note in _sealed():
        assert frame._BROKEN_ENTRY in note.html, (
            f"{note.slug} no longer carries the broken script - if the "
            "samples have been rebuilt, delete frame.repair and this test"
        )
        shown = frame.framed(note.html)
        assert frame._BROKEN_ENTRY not in shown, (
            f"{note.slug} reaches the reader unrepaired"
        )
        if not node:
            continue
        for i, block in enumerate(re.findall(r"<script>(.*?)</script>",
                                             shown, re.S)):
            with tempfile.NamedTemporaryFile(
                "w", suffix=".js", delete=False
            ) as fh:
                fh.write(block)
                path = fh.name
            done = subprocess.run(
                [node, "--check", path], capture_output=True, text=True
            )
            assert done.returncode == 0, (
                f"{note.slug} script {i} does not parse:\n{done.stderr}"
            )


def test_a_downloaded_sample_is_repaired_too():
    """A reader who saves the file should not be saving the broken one.

    `fitFrame` has no frame to size outside the app, but `arTableStops`
    still has tables to mark, and both died in the same SyntaxError.
    """
    from asset_researcher.ui import frame

    for note in _sealed():
        assert frame._BROKEN_ENTRY not in frame.repair(note.html)
