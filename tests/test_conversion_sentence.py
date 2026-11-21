"""Where the comparison figure in the cash-conversion line comes from.

Cintas: "Cash conversion is 113.8% of net income, down from 124.4%
across the filed window." 124.4% is the FIRST year of the five, not
the window's average, which is 121.4%. "Across the filed window" reads
as a property of the window, so a reader checking it against the
Operating cash flow / net income row - 124.4, 117.7, 131.6, 119.5,
113.8 - finds the number in the first column and has to work out which
one was meant.

Its own sibling clause already gets this right: the flat branch says
"level with X at the start of the filed window". One phrasing, used
for both.
"""

from __future__ import annotations

from asset_researcher.ui.summary import conversion_sentence


def _line(values: dict[str, str]) -> str:
    return conversion_sentence(values, {})


def test_a_falling_series_names_the_start_rather_than_the_window():
    line = _line({
        "FY2022": "124.4%", "FY2023": "117.7%", "FY2024": "131.6%",
        "FY2025": "119.5%", "FY2026": "113.8%",
    })
    assert "124.4%" in line
    assert "across the filed window" not in line
    assert "at the start of the filed window" in line


def test_a_flat_series_is_unchanged():
    line = _line({"FY2025": "120.0%", "FY2026": "120.0%"})
    assert "level with" in line
    assert "at the start of the filed window" in line


def test_the_latest_figure_is_still_the_subject():
    line = _line({"FY2025": "124.4%", "FY2026": "113.8%"})
    assert line.startswith("Cash conversion is 113.8%")
