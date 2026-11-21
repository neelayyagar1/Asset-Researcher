"""Summary statistics that contradicted the caption printed above them.

Under every peer table: "Summary statistics are computed across peers
only, excluding the subject and extreme multiples." The screen behind
that sentence covered two columns, P/E and EV/EBITDA, and the table
prints four more.

Measured on the shipped Realty Income note: Kimco reports revenue of
$16.8m - against a real figure near $1.7bn, a denominator wrong by two
orders of magnitude - which produced a net margin of 3,473.2% and an
EV/Revenue of 1,432.7x. Neither was screened, so the printed peer mean
net margin read 462.8% and the mean EV/Revenue 189.6x, in a row
captioned as excluding exactly that.

A reader who trusts the caption reads 462.8% as the peer group's
margin. The figures are arithmetically right and analytically
worthless, which is the definition the screen already used for P/E.
"""

from __future__ import annotations

from asset_researcher.quant.comps import CompRow, CompsTable


def _row(ticker: str, **kwargs) -> CompRow:
    base = dict(
        ticker=ticker, company_name=ticker, is_subject=False,
        market_cap=1e9, price=10.0, revenue=1e8, net_income=1e7,
        total_equity=5e8,
    )
    base.update(kwargs)
    return CompRow(**base)


def test_a_margin_above_one_hundred_percent_is_treated_as_extreme():
    """Net income cannot exceed revenue on a sound denominator. Kimco
    printed 3,473.2%."""
    row = _row("KIM", revenue=16.8e6, net_income=583e6)
    assert row.net_margin > 1.0
    assert "net_margin" in row.outlier_multiples


def test_an_ordinary_fat_margin_is_not_extreme():
    """Simon Property files 84.3%, which is real for a REIT booking
    disposal gains. The screen must not swallow it."""
    row = _row("SPG", revenue=6364.5e6, net_income=5365e6)
    assert 0.8 < row.net_margin < 0.9
    assert "net_margin" not in row.outlier_multiples


def test_a_revenue_multiple_in_the_hundreds_is_extreme():
    # Enterprise value is derived, so the cap is what is set.
    row = _row("KIM", revenue=16.8e6, market_cap=24121e6)
    assert row.ev_to_revenue > 1000
    assert "ev_to_revenue" in row.outlier_multiples


def test_an_ordinary_revenue_multiple_is_not():
    row = _row("SPG", revenue=6364.5e6, market_cap=72870e6)
    assert "ev_to_revenue" not in row.outlier_multiples


def test_the_peer_mean_leaves_the_extreme_out():
    """The defect as it reached the page."""
    table = CompsTable(
        subject_ticker="O", peer_source="Finnhub peer list",
        rows=[
            _row("SPG", revenue=6364.5e6, net_income=5365e6),
            _row("KIM", revenue=16.8e6, net_income=583e6),
            _row("REG", revenue=1553.5e6, net_income=528e6),
        ],
    )
    values = table.peer_values("net_margin")
    assert all(v < 1.0 for v in values), (
        f"an impossible margin is still in the statistics: {values}"
    )


def test_a_loss_making_peer_is_still_counted():
    """Macerich files -19.4%. A loss is information, not an outlier,
    and dropping it would flatter the peer group."""
    row = _row("MAC", revenue=1014e6, net_income=-197e6)
    assert row.net_margin < 0
    assert "net_margin" not in row.outlier_multiples
