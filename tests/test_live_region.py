"""The region that announces a ninety-second run.

`aria-busy="true"` tells assistive technology to withhold changes
until it becomes false. It was set on the status region on every
render and never cleared, so a conforming screen reader announced
none of the stages - on the one screen where the system is working
silently for a minute and a half and the reader has nothing else to
go on.

This is the third time this region has been wrong. The first version
had no live region at all while a comment claimed one; the second
wrote the stage lines as siblings OUTSIDE the region, because
`st.markdown` is not a container and its div closes. Both are
recorded in the docstring above it. Hence a test.
"""

from __future__ import annotations

import pathlib
import re

APP = pathlib.Path(__file__).resolve().parents[1] / "app.py"


def _region() -> str:
    """The markup `say()` emits, recovered from the syntax tree.

    Read from the AST rather than by slicing the file, because a
    comment explaining why `aria-busy` is absent contains the word
    `aria-busy` - and the first version of this test failed on its own
    explanation. The same mistake, in the same week, as a test that
    grepped a module for wording its comment quoted.
    """
    import ast

    tree = ast.parse(APP.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != "say":
            continue
        pieces = []
        for inner in ast.walk(node):
            if isinstance(inner, ast.Constant) and isinstance(
                inner.value, str
            ):
                pieces.append(inner.value)
            elif isinstance(inner, ast.JoinedStr):
                pieces.append(
                    "".join(
                        v.value
                        for v in inner.values
                        if isinstance(v, ast.Constant)
                    )
                )
        return "".join(pieces)
    raise AssertionError("say() is gone from app.py")


def test_the_region_does_not_declare_itself_busy():
    assert "aria-busy" not in _region(), (
        "the status region marks itself busy, which instructs "
        "assistive technology not to announce its contents"
    )


def test_it_is_still_a_polite_atomic_status_region():
    region = _region()
    assert 'role="status"' in region
    assert 'aria-live="polite"' in region
    assert 'aria-atomic="true"' in region


def test_the_stage_text_is_inside_the_region():
    """The second iteration of this defect: the region was written as
    one closed element and the stage lines landed after it."""
    region = _region()
    opened = region.index('role="status"')
    text = region.index("ar-stage")
    closed = region.index("</div>", opened)
    assert opened < text < closed, (
        "the stage line is outside the element carrying aria-live"
    )


def test_the_progress_bar_is_not_announced():
    """It is a time estimate, not measured progress, so it must not
    present itself as a progressbar to a screen reader."""
    region = _region()
    assert 'class="ar-progress" aria-hidden="true"' in region
    assert 'role="progressbar"' not in region
