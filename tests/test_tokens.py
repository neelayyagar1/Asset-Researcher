"""The tokens a reader should not have to guess at.

"NM" appeared up to 43 times on a single page and was explained nowhere.
The Health table writes "not meaningful for this sector" in full prose,
so the document always knew how to say it; it simply never said it where
the two-letter form is used. Someone reading the shipped notes had to
ask what it meant, which is the proof that it needed saying.
"""

from __future__ import annotations

from asset_researcher.ui import components as ui
from asset_researcher.ui.components import Col


def _cell(value: str) -> str:
    return ui.table([Col("v", "Value", num=True)], [{"v": value}])


def test_nm_carries_a_hover_explanation():
    out = _cell("NM")
    assert '<abbr class="ar-token"' in out
    assert "Not meaningful" in out


def test_no_data_is_distinguished_from_not_meaningful():
    """Three states, three meanings: a ratio that would mislead, a figure
    the filer never reported, and nothing at all."""
    assert "did not report" in _cell("n.d.")
    assert "denominator" in _cell("NM")


def test_a_token_is_also_spoken_not_only_shown():
    assert 'class="ar-sr">, not meaningful' in _cell("NM")
    assert 'class="ar-sr">, no data' in _cell("n.d.")


def test_an_ordinary_figure_is_left_alone():
    out = _cell("11.2x")
    assert "ar-token" not in out
    assert "11.2x" in out


def test_the_legend_explains_only_the_tokens_present():
    assert "NM" in ui.legend(_cell("NM"))
    assert "did not report" not in ui.legend(_cell("NM"))
    assert ui.legend(_cell("11.2x")) == ""


# ------------------------------------------------- empty comps columns

_COLS = [
    Col("Company", "Company", emphasis=True),
    Col("EBITDA", "EBITDA", num=True),
    Col("P/E", "P/E", num=True),
]


def test_a_column_that_refuses_in_every_row_is_dropped():
    """EBITDA is not derivable for any bank, so on a bank page three of
    sixteen columns carried thirty-five refusals and no information."""
    kept, dropped = ui.drop_empty_columns(
        _COLS,
        [
            {"Company": "Truist", "EBITDA": "NM", "P/E": "11.2x"},
            {"Company": "M&T", "EBITDA": "NM", "P/E": "12.0x"},
        ],
    )
    assert [c.label for c in kept] == ["Company", "P/E"]
    assert dropped == ["EBITDA"]


def test_a_column_holding_one_real_figure_is_kept():
    """A refusal beside a real number is information; a column of them is
    not. The distinction is whether anything survived."""
    kept, dropped = ui.drop_empty_columns(
        _COLS,
        [
            {"Company": "Ford", "EBITDA": "12,000", "P/E": "NM"},
            {"Company": "Rivian", "EBITDA": "NM", "P/E": "NM"},
        ],
    )
    assert "EBITDA" in [c.label for c in kept]
    assert dropped == ["P/E"]


def test_a_wholly_blank_column_is_not_treated_as_refused():
    """A spacer column holds nothing anywhere and is structural, not a
    refusal, so it is left in place."""
    kept, dropped = ui.drop_empty_columns(
        _COLS, [{"Company": "A", "EBITDA": "", "P/E": ""}]
    )
    assert dropped == []
    assert len(kept) == 3
