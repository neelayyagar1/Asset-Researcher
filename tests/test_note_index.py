"""What the index on the first screen can honestly say about a note.

The owner's finding was that the landing page is mostly empty and the
table on it carries four columns when the documents behind it carry
far more. The constraint is the one this product is built around: the
index may not be the one place where a figure appears without a filing
behind it. So every column here is READ OUT of the built document and
none is recomputed - if the note does not say it, the cell is empty.

Parsed by content rather than by position. The chips differ between
notes: a filer whose model declined prints a third chip and the two
that matter move, so anything counting chips would read the wrong one
on three of the six shipped notes.
"""

from __future__ import annotations

import pathlib

import pytest

from asset_researcher.ui import note_index

SITE = pathlib.Path(__file__).resolve().parents[1] / "build" / "site"

NOTE = (
    '<div class="ar-chips">'
    '<a class="warn" href="#s-provenance">113/113 cited</a>'
    '<a class="" href="#s-provenance">Filed 2026-08-05</a></div>'
    '<div class="ar-stats">'
    '<div class="ar-stat"><div class="ar-stat-label">Traded price</div>'
    '<div class="ar-stat-value ">$301.71</div></div>'
    '<div class="ar-stat lead"><div class="ar-stat-label">Price implies '
    'FCF growth</div><div class="ar-stat-value ">6.8%</div></div></div>'
)


def test_it_reads_the_traded_price():
    assert note_index.summarise(NOTE)["price"] == "$301.71"


def test_it_reads_the_filing_date():
    assert note_index.summarise(NOTE)["filed"] == "2026-08-05"


def test_it_reads_the_citation_coverage():
    assert note_index.summarise(NOTE)["cited"] == "113/113"


def test_it_reads_the_lead_statistic():
    out = note_index.summarise(NOTE)
    assert out["metric"] == "Price implies FCF growth"
    assert out["value"] == "6.8%"


def test_a_third_chip_does_not_move_the_other_two():
    """Three of the six shipped notes carry a "Model" chip between the
    two this reads. Anything positional reads it as the filing date."""
    with_model = NOTE.replace(
        '<a class="" href="#s-provenance">Filed',
        '<a class="" href="#s-provenance">Model -233%</a>'
        '<a class="" href="#s-provenance">Filed',
    )
    out = note_index.summarise(with_model)
    assert out["filed"] == "2026-08-05"
    assert out["cited"] == "113/113"


def test_a_note_missing_a_field_leaves_it_empty():
    """Not a zero, not a dash, not a borrowed figure from elsewhere."""
    out = note_index.summarise("<html><body>nothing here</body></html>")
    assert out == {"price": "", "filed": "", "cited": "", "metric": "",
                   "value": "", "yield": "", "cagr": ""}


def test_markup_inside_a_value_does_not_reach_the_cell():
    html = NOTE.replace("$301.71", '<span class="x">$301.71</span>')
    assert note_index.summarise(html)["price"] == "$301.71"


# ------------------------------------------------ against the real notes

BUILT = sorted(p for p in SITE.glob("*.html")) if SITE.is_dir() else []


@pytest.mark.skipif(not BUILT, reason="no built notes in build/site")
@pytest.mark.parametrize("path", [p for p in BUILT if p.stem != "index"],
                         ids=lambda p: p.stem)
def test_every_shipped_note_fills_every_column(path):
    """Calibration. A parser that works on the example above and not on
    the documents it will actually meet is a parser that silently
    empties the table."""
    out = note_index.summarise(path.read_text(encoding="utf-8"))
    missing = [k for k, v in out.items() if not v]
    assert not missing, f"{path.stem} gave nothing for {missing}"
