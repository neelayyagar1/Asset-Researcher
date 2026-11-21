"""Inline JavaScript shipped from Python string literals.

A browser-Back listener shipped broken while the suite was green. The
JavaScript lived in a non-raw Python triple-quoted string and contained
`\\n` escapes meant for a JS string literal. Python consumed them first,
so the browser was served a single-quoted JavaScript string with two
real newlines inside it - a SyntaxError. The whole listener failed to
parse and browser Back silently did nothing, while the in-app Back
buttons kept working because those are server-side widgets.

These tests read the **evaluated** string, not the source text. That
distinction is the entire point: in `app.py` the characters are a
backslash followed by an `n`, so quotes balance and a source scan sees
nothing wrong. The defect exists only in the value Python hands the
browser. A first version of this file scanned the source, passed
against the known-bad commit, and would have shipped the bug twice.
"""

from __future__ import annotations

import ast
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]

FILES = (
    ROOT / "app.py",
    ROOT / "asset_researcher" / "ui" / "export.py",
)


def _emitted_scripts() -> list[tuple[str, str]]:
    """Every evaluated string constant that carries a <script> block."""
    found: list[tuple[str, str]] = []
    for path in FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "<script>" in node.value:
                    found.append((path.name, node.value))
    return found


def _unbalanced_quote_line(js: str) -> tuple[int, str] | None:
    """The first line that opens a JS string and does not close it."""
    for number, line in enumerate(js.splitlines(), 1):
        code = line.split("//", 1)[0]
        for quote in ("'", '"'):
            count = code.count(quote) - code.count("\\" + quote)
            if count % 2:
                return number, line
    return None


def test_inline_scripts_are_found_at_all():
    """If this fails the other tests are vacuous."""
    assert _emitted_scripts(), "no <script> constants found to check"


def test_no_emitted_script_has_a_newline_inside_a_string_literal():
    for where, js in _emitted_scripts():
        bad = _unbalanced_quote_line(js)
        assert bad is None, (
            f"{where}: line {bad[0]} of an emitted <script> opens a "
            f"JavaScript string and never closes it: {bad[1].strip()!r}\n"
            f"A JS string cannot span lines. If the text needs a line "
            f"break, the Python literal must be raw (r\"\"\"...\"\"\") so the "
            f"browser receives a backslash and an n, not a newline."
        )


def test_the_detector_catches_the_original_defect():
    """The scanner is itself checked, against the exact shipped bug.

    Without this, a scanner that silently stopped matching would look
    identical to a codebase with no defects.
    """
    broken = (
        "<script>\n"
        "  window.confirm('Leaving discards the report.\n\n'\n"
        "    + 'Leave anyway?');\n"
        "</script>"
    )
    assert _unbalanced_quote_line(broken) is not None

    fixed = (
        "<script>\n"
        "  window.confirm('Leaving discards the report.\\n\\n'\n"
        "    + 'Leave anyway?');\n"
        "</script>"
    )
    assert _unbalanced_quote_line(fixed) is None


def test_the_back_bridge_binds_to_the_window_that_owns_the_address_bar():
    """On Streamlit Cloud the app itself runs inside an iframe.

    The bridge bound `popstate` to `window.parent`, which from a
    component iframe is the APP window. That is correct on a directly
    served app, where the app window owns the address bar, and wrong on
    Streamlit Cloud, where the app is framed inside
    `//<app>.streamlit.app/~/+/` and Back fires on the TOP window.

    The consequence was the original complaint, unfixed in production
    while passing every local check: the address bar went back and the
    page stayed put. Local verification could not see it because a
    directly served Streamlit is not framed - window.top and
    window.parent are the same object there, so the same code passes.

    Both frames are same-origin, so the top window is reachable; the
    reach is guarded because a cross-origin top throws.
    """
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    bridge = re.search(r"components\.html\(\s*r?\"\"\"(.*?)\"\"\"", source, re.S)
    assert bridge, "the back bridge's script block was not found"
    js = bridge.group(1)

    assert "window.top" in js, (
        "the bridge does not reach for the top window, so it cannot hear "
        "Back on a framed deployment"
    )
    assert "try" in js and "catch" in js, (
        "reaching for a cross-origin top throws and must be guarded"
    )
