"""What a jump lands on, and what the index says about a report.

Both were reported from the running app by the owner, and both were
things no test here could have caught, because every test asserted on a
string rather than on what a browser does with it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from asset_researcher.ui import components as ui
from asset_researcher.ui import frame, note_index, theme
from asset_researcher.ui import format as fmt
from asset_researcher.ui.export import NEW_CLICK, OLD_CLICK, _JUMP_SCRIPT

SITE = Path(__file__).resolve().parents[1] / "build" / "site"
BUILT = sorted(p for p in SITE.glob("*.html") if p.stem != "index") \
    if SITE.is_dir() else []


def _rule(selector: str, sheet: str) -> str:
    """Every rule with this selector, joined. A selector that appears
    twice has its declarations split across both, and reading only the
    first reports a property as missing when it is simply later."""
    found = re.findall(
        re.escape(selector) + r"\s*\{(.*?)\}", sheet, re.S
    )
    return "\n".join(found)


# ------------------------------------------------------- the frame's links


def test_the_handler_reaches_every_fragment_link_in_the_note():
    """Not only the section bar.

    A note rendered in the app is the srcdoc of an iframe, and a srcdoc
    document inherits its base URL from the parent page - so "#s-..."
    resolves against the APPLICATION's URL. Scoped to `nav.ar-nav`, the
    handler left the masthead chips resolving that way, and clicking
    "Filed Aug 5, 2026" loaded the entire site, top bar and all, into
    the box where the note should be.
    """
    assert 'closest(\'a[href^="#"]\')' in _JUMP_SCRIPT
    assert "nav.ar-nav a" not in _JUMP_SCRIPT


def test_the_chips_are_still_links_to_somewhere_real():
    """The fix is that they work, not that they were taken away. Each
    chip points at the provenance section, which is where the full
    wording of what it compresses actually lives."""
    html = ui.chips([("105/105 cited", "ok"), ("Filed Aug 5, 2026", "")])
    assert html.count('href="#s-provenance"') == 2


def test_a_jump_clears_the_shell_bar_it_cannot_see():
    """The note is a full-height frame inside a page whose top bar is
    fixed and 56px tall. The frame does not scroll; the page does. So
    the bar is a piece of the viewport the document knows nothing
    about, and a section landing flush at the top of the window landed
    under it."""
    margin = _rule(".ar-sec", theme.document_stylesheet())
    assert "scroll-margin-top: calc(var(--nav-h) + 72px)" in margin


def test_the_destination_marks_itself_and_then_stops():
    sheet = theme.document_stylesheet()
    assert "@keyframes ar-hit" in sheet
    # It has to leave nothing behind: a wash that persists reads as a
    # state the section is in rather than as an arrival.
    hit = _rule(".ar-hit", sheet)
    assert "animation: ar-hit 2.4s" in hit
    assert "to   { background: transparent; }" in sheet
    # `:target` cannot do this. The handler prevents the navigation, so
    # the fragment never changes and the pseudo-class never matches -
    # the class has to be added by the same handler that scrolls.
    assert "arFlash(target);" in NEW_CLICK
    assert "classList.add('ar-hit')" in NEW_CLICK


def test_reduced_motion_keeps_the_cue_and_drops_the_fade():
    sheet = theme.document_stylesheet()
    block = sheet[sheet.index("prefers-reduced-motion: reduce) {\n  .ar-hit"):]
    assert "animation: none" in block[:200]
    assert "background: var(--accent-soft)" in block[:200]


# ------------------------------------------------------- the sealed notes


@pytest.mark.skipif(not BUILT, reason="no built notes in build/site")
@pytest.mark.parametrize("path", BUILT, ids=lambda p: p.stem)
def test_repair_reaches_a_note_that_was_sealed_before_the_fix(path):
    """The six that ship were sealed before any of this. Rebuilding
    them costs six API calls and moves every as-of date in them, so the
    two broken strings are replaced on the way to the reader."""
    raw = path.read_text(encoding="utf-8")
    assert OLD_CLICK in raw, "this note no longer needs the repair"
    fixed = frame.repair(raw)
    assert OLD_CLICK not in fixed and NEW_CLICK in fixed
    assert not re.search(r">Filed \d{4}-\d{2}-\d{2}<", fixed)
    assert re.search(r">Filed [A-Z][a-z]{2} \d{1,2}, \d{4}<", fixed)


def test_repair_leaves_a_note_that_does_not_need_it_alone():
    assert frame.repair("<p>nothing to do</p>") == "<p>nothing to do</p>"


def test_only_the_chip_date_is_rewritten():
    """A filing date inside a sentence or a table is prose the note
    wrote, not a chip this module owns."""
    html = "<td>2026-08-05</td><p>filed 2026-08-05 in the period</p>"
    assert frame.repair(html) == html


# ------------------------------------------------------------ the index


def test_the_filed_date_is_written_the_way_a_reader_writes_one():
    assert fmt.filed_date("2026-08-05") == "Aug 5, 2026"
    assert fmt.filed_date("2026-10-07") == "Oct 7, 2026"
    # Anything this cannot parse is a date it has no business touching.
    assert fmt.filed_date("n.d.") == "n.d."
    assert fmt.filed_date("2026-13-01") == "2026-13-01"


@pytest.mark.skipif(not BUILT, reason="no built notes in build/site")
def test_the_finding_column_says_something_different_in_every_row():
    """The whole reason the opening paragraph was the wrong sentence.

    It is a template with two numbers in it - "At N times free cash
    flow the price requires X% annual growth" - so a column of six read
    as one statement repeated, and the one question an index of read
    reports has to answer, which of these was the one about the
    deleveraging, was the question it could not answer.
    """
    findings = [
        note_index.summarise(p.read_text(encoding="utf-8"))["takeaway"]
        for p in BUILT
    ]
    assert all(findings), "a note gave no finding at all"
    openings = {f.split(",")[0][:40] for f in findings}
    assert len(openings) == len(findings), f"repeated openings: {findings}"
    assert not any(
        f.startswith("At ") and "times free cash flow" in f for f in findings
    ), "the template sentence is back"
    assert not any(
        f.startswith("Where this departs") for f in findings
    ), "the section's own label is not a finding about a company"


@pytest.mark.skipif(not BUILT, reason="no built notes in build/site")
def test_the_price_implied_growth_is_shown_against_the_filed_record():
    """A required growth rate on its own cannot be judged. 18.7% is
    alarming or unremarkable entirely according to what the company has
    actually done, and the index did not say which."""
    pairs = {
        p.stem: note_index.summarise(p.read_text(encoding="utf-8"))
        for p in BUILT
    }
    assert pairs["lumn"]["value"] == "2.8%"
    assert pairs["lumn"]["record"] == "-33.2%"
    assert pairs["cost"]["record"] == "11.8%"
    # The REIT leads on a multiple rather than a growth rate and has no
    # comparable compound. The cell names the multiple instead of
    # borrowing a figure from somewhere else in the document.
    assert pairs["o"]["record"] == ""
    assert pairs["o"]["metric"] == "Price / FFO proxy"

    rows = [dict(ticker=k.upper(), company=k, slug=k, **v)
            for k, v in pairs.items()]
    html = ui.report_rows(rows, token="t")
    assert "against -33.2% filed" in html
    assert "Price / FFO proxy" in html


# ------------------------------------------------------------- the shell


def test_an_element_that_paints_nothing_does_not_take_a_gap():
    """Streamlit's vertical block is a flex column with a 16px gap
    between every child, and a child that renders nothing is still a
    child. Five of them open the home screen, so 80px of invisible
    stack sat between the top bar and the first word."""
    sheet = theme.stylesheet()
    for selector in (
        '[data-testid="stElementContainer"][height="0px"]',
        '[data-testid="stElementContainer"]:has(.ar-topbar)',
        '[data-testid="stElementContainer"]:has(.ar-skip)',
        '[data-testid="stElementContainer"]'
        ':has(span[role="group"][tabindex="-1"])',
    ):
        assert selector in sheet, selector
    assert "margin-bottom: -16px" in sheet


def test_the_gate_is_a_page_with_an_object_on_it():
    """Capping the container at 320px capped the whole screen: the
    chassis rails came in to hug the form and the first thing a
    stranger saw was a phone-width strip of product in the middle of a
    desktop window."""
    sheet = theme.stylesheet()
    gate = _rule(".block-container:has(.ar-gate)", sheet)
    assert "max-width: var(--shell-col)" in gate
    assert "max-width: 320px" not in gate
    inner = _rule(
        '.block-container:has(.ar-gate) > div,\n'
        '.block-container:has(.ar-gate) [data-testid="stVerticalBlock"]',
        sheet,
    )
    assert "max-width: 320px" in inner and "margin-inline: auto" in inner


# --------------------------------------- a report that was just generated


@pytest.mark.skipif(not BUILT, reason="no built notes in build/site")
def test_a_generated_report_reaches_the_index_with_every_column(
    tmp_path, monkeypatch
):
    """The samples are sealed artifacts and a generated report is not,
    so "the index works" has been proved on six documents that take a
    different path to the screen than the one a visitor's own report
    takes. This takes that path.

    No API call: the figures the index prints are parsed out of the
    RENDERED note, and a note built by `report_to_html` is the same
    document whichever run produced it. What is being checked here is
    the store, the listing and the parse - the three steps between a
    report being saved and a row appearing.
    """
    from asset_researcher import reports_store

    monkeypatch.setenv("REPORTS_DIR", str(tmp_path))
    html = (SITE / "lumn.html").read_text(encoding="utf-8")
    saved = reports_store.save(
        "LUMN", "Lumen Technologies, Inc. (LUMN)", html, scope="s1"
    )

    listed = reports_store.listing(scope="s1")
    assert [s.slug for s in listed] == [saved.slug]

    figures = note_index.summarise(listed[0].html)
    for field in ("price", "filed", "cited", "metric", "value",
                  "takeaway", "record"):
        assert figures[field], f"the index would show nothing for {field}"

    row = dict(ticker="LUMN", company="Lumen Technologies, Inc.",
               slug=saved.slug, **figures)
    rendered = ui.report_rows([row], token="t", scope="s1")
    assert "2.8%" in rendered and "against -33.2% filed" in rendered
    assert "Feb 20, 2026" in rendered
    assert "The deleveraging is real" in rendered
    # The scope travels in the link, or the reader lands on the reading
    # screen having lost every report they generated.
    assert "sid=s1" in rendered
