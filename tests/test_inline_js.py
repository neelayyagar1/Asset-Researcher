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
