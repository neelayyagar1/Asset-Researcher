"""The written guide, as the product renders it.

The Markdown subset was built for what the model emits, and the guide is
hand-written, so it used constructs the renderer did not have. The result
was literal syntax in the one section that earns the most credibility: a
reader saw stray angle brackets in the pull quote, backticks around file
names, asterisks around the emphasised words in the sharpest sentence in
the document, and twelve bullets each severed into a one-item list plus
an orphan half-sentence.

None of that is visible from reading either file. It only appears when
the real document goes through the real renderer, which is what this
does.
"""

from __future__ import annotations

import pathlib
import re

import pytest

from asset_researcher.ui import markdown

DOC = pathlib.Path(__file__).resolve().parents[1] / "docs" / "FOR-REVIEWERS.md"


@pytest.fixture(scope="module")
def rendered() -> str:
    return markdown.to_html(DOC.read_text(encoding="utf-8"), base_level=2)


def _text(html: str) -> str:
    """The reader's view: markup stripped, entities left as written."""
    return re.sub(r"<[^>]+>", "", html)


def test_the_guide_exists_and_is_substantial():
    assert DOC.exists()
    assert len(DOC.read_text(encoding="utf-8")) > 2000


def test_no_backticks_survive(rendered):
    assert "`" not in _text(rendered)
    assert "<code>" in rendered


def test_no_blockquote_markers_survive(rendered):
    for line in _text(rendered).splitlines():
        assert not line.lstrip().startswith("&gt;"), line
    assert "<blockquote>" in rendered


def test_no_emphasis_asterisks_survive(rendered):
    """"the interface says *located*, not *verified*" is the sharpest
    sentence in the document and it was printing its own asterisks."""
    assert "*" not in _text(rendered)


def test_every_bullet_is_one_list_item(rendered):
    """A bullet wrapped across source lines was severed into a one-item
    list plus an orphan paragraph starting mid-sentence."""
    source_bullets = sum(
        1
        for line in DOC.read_text(encoding="utf-8").splitlines()
        if line.lstrip().startswith(("- ", "* "))
    )
    assert rendered.count("<li>") == source_bullets


def test_bullets_are_not_fragmented_into_separate_lists(rendered):
    """Twelve consecutive bullets should be one list, not twelve."""
    assert rendered.count("<ul>") < rendered.count("<li>")


def test_the_page_title_outranks_its_own_sections(rendered):
    """`#` mapped below `##`, so the title rendered smaller than the
    headings beneath it and read as a running header."""
    assert "<h2>" in rendered
    if "<h3>" in rendered:
        assert rendered.index("<h2>") < rendered.index("<h3>")


def test_no_table_syntax_is_used_since_it_is_unsupported():
    """The renderer has no table support. If the guide grows one, this
    fails here rather than printing pipes at a reviewer."""
    body = DOC.read_text(encoding="utf-8").split("## Links")[0]
    in_fence = False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if not in_fence and line.lstrip().startswith("|"):
            pytest.fail(f"table syntax the renderer cannot show: {line!r}")


def test_the_claimed_test_count_matches_reality():
    """A reviewer can check this in one command, so a stale number is a
    small lie in a document whose subject is not telling small lies."""
    import subprocess
    import sys

    body = DOC.read_text(encoding="utf-8")
    claimed = re.search(r"(\d{3,4}) tests", body)
    if not claimed:
        pytest.skip("the guide does not claim a test count")

    out = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--collect-only"],
        capture_output=True, text=True,
        cwd=DOC.resolve().parents[1],
    ).stdout
    actual = re.search(r"(\d+) tests? collected", out)
    if not actual:
        pytest.skip("could not count the suite")
    assert int(claimed.group(1)) == int(actual.group(1)), (
        f"guide claims {claimed.group(1)}, suite has {actual.group(1)}"
    )
