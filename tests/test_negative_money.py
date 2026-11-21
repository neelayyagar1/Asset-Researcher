"""Negatives in parentheses, everywhere a reader sees a dollar.

The convention is the product's own, recorded in PRODUCT.md and
already honoured by the statements and the projection table: published
research sets a negative figure in parentheses, never with a leading
minus after the dollar sign.

The shipped Lumen note breaks it 113 times. It prints "$-9.56",
"$-5.09", "$-0.88" through the valuation range, the case table and the
sensitivity grid - beside statement rows that set the same kind of
figure as "(33,763)". A document that uses two conventions for one
thing reads as two documents.

The cause is duplication rather than oversight. `ui/format.py` has a
`usd` that gets it right; `ui/document.py` defined a second one, four
lines long, that does not - and the document module's own name
shadowed the correct one at every call site in the note.
"""

from __future__ import annotations

import pytest

from asset_researcher.quant.valuation import Assumption
from asset_researcher.ui import charts, format as fmt
from asset_researcher.quant import comps


def test_the_shared_formatter_already_gets_it_right():
    """The checker, checked."""
    assert fmt.usd(9.56) == "$9.56"
    assert fmt.usd(-9.56) == "($9.56)"


@pytest.mark.parametrize(
    "render",
    [
        pytest.param(lambda v: __import__(
            "asset_researcher.ui.document", fromlist=["usd"]).usd(v),
            id="document.usd"),
        pytest.param(lambda v: comps._price(v), id="comps._price"),
        pytest.param(lambda v: charts._money(v), id="charts._money"),
    ],
)
def test_no_reader_facing_formatter_prints_a_dollar_minus(render):
    for value in (-9.56, -0.88, -1_200_000_000.0):
        rendered = render(value)
        assert "$-" not in rendered, (
            f"{rendered!r} uses a leading minus where the convention is "
            f"parentheses"
        )
        assert rendered.startswith("("), rendered


def test_a_positive_figure_is_untouched():
    assert not charts._money(1.2e9).startswith("(")
    assert not comps._price(9.56).startswith("(")


def test_the_assumption_row_already_honours_it():
    """Pinned: this one was fixed before and must not regress."""
    assert Assumption("Net debt", -33.8e9, "$", "").display().startswith("(")


def test_the_sensitivity_grid_sets_a_negative_in_parentheses():
    """The grid prints one cell per discount rate and terminal growth,
    so on a filer whose model goes negative it is the single largest
    source of mis-set figures in the note."""
    from asset_researcher.quant import valuation

    assert valuation._per_share_cell(-5.09) == "($5.09)"
    assert valuation._per_share_cell(5.09) == "$5.09"


def test_the_valuation_range_labels_a_negative_case_in_parentheses():
    from asset_researcher.ui import charts as c

    assert c._case_label(-9.56) == "($10)"
    assert c._case_label(9.56) == "$10"


def test_the_spoken_chart_description_uses_parentheses_too():
    """The visible tick labels were fixed and this was missed, and it
    is the text a screen reader actually reads."""
    from asset_researcher.ui import charts as c

    assert c._case_money(-9.56) == "($9.56)"
    assert c._case_money(3.83) == "$3.83"
