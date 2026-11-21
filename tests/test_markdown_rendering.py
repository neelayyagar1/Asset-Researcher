"""The Markdown subset, tested against the renderer rather than a document.

These checks were written against a hand-written guide that the product
used to render on a How it works page. That page is gone - its
instructions live on the home screen now - so rendering that file is no
longer a code path anyone exercises.

The renderer itself still matters: `markdown.to_html` renders the
descriptive prose of every note. So the same defects are pinned here
directly, as fixtures, where they cannot rot when a document is
retired. Each case is one the renderer actually shipped: a reader saw
backticks, stray angle brackets, literal asterisks in the sharpest
sentence in the document, and twelve bullets severed into twelve
one-item lists with an orphan half-sentence after each.
"""

from __future__ import annotations

import pathlib
import re

from asset_researcher.ui import markdown


def _text(html: str) -> str:
    """The reader's view: markup stripped, entities left as written."""
    return re.sub(r"<[^>]+>", "", html)


def test_backticks_become_code_and_do_not_survive_as_characters():
    html = markdown.to_html("Read `app.py` for the view layer.")
    assert "<code>" in html
    assert "`" not in _text(html)


def test_a_blockquote_renders_as_one_and_keeps_no_marker():
    html = markdown.to_html("> The cost-of-capital claim is contradicted.")
    assert "<blockquote>" in html
    assert not _text(html).lstrip().startswith("&gt;")
    assert ">" not in _text(html).replace("&gt;", "")


def test_emphasis_does_not_print_its_own_asterisks():
    """The sentence this was found in is the product's central claim:
    the interface says *located*, not *verified*."""
    html = markdown.to_html("It says *located*, not *verified*.")
    assert "*" not in _text(html)
    assert "<em>" in html


def test_a_bullet_wrapped_across_lines_is_one_item():
    """A wrapped bullet was severed into a one-item list plus an orphan
    paragraph starting mid-sentence."""
    source = (
        "- The model may not write a number, and a verifier flags\n"
        "  any figure that appears in prose without a filing behind it.\n"
    )
    html = markdown.to_html(source)
    assert html.count("<li>") == 1
    assert "verifier flags" in _text(html)
    assert _text(html).count("any figure") == 1


def test_consecutive_bullets_are_one_list():
    source = "- first\n- second\n- third\n"
    html = markdown.to_html(source)
    assert html.count("<li>") == 3
    assert html.count("<ul>") == 1


def test_a_title_outranks_the_sections_beneath_it():
    """`#` mapped below `##`, so a title rendered smaller than the
    headings under it and read as a running header."""
    html = markdown.to_html("# Title\n\n## Section\n", base_level=2)
    assert "<h2>" in html
    if "<h3>" in html:
        assert html.index("<h2>") < html.index("<h3>")


def test_the_claimed_test_count_in_the_owner_notes_matches_reality():
    """NOTES.md is the one document written for the owner, and a reader
    can check this number in one command. A stale count is a small lie
    in a document whose subject is not telling small lies."""
    import subprocess
    import sys

    notes = pathlib.Path(__file__).resolve().parents[1] / "NOTES.md"
    body = notes.read_text(encoding="utf-8")
    claimed = re.search(r"(\d{3,4}) tests, no network", body)
    assert claimed, "NOTES.md no longer states a test count"

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--collect-only"],
        capture_output=True, text=True,
        cwd=str(pathlib.Path(__file__).resolve().parents[1]),
    )
    actual = re.search(r"(\d+) tests collected", result.stdout)
    assert actual, result.stdout[-400:]
    assert int(claimed.group(1)) == int(actual.group(1)), (
        f"NOTES.md claims {claimed.group(1)} tests; the suite collects "
        f"{actual.group(1)}"
    )
