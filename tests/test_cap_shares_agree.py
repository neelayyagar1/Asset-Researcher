"""The market capitalisation and the share count have to multiply.

Both come from the market-data provider, independently, and nothing
checked that they agreed. Measured across the six shipped notes, using
each note's own printed figures:

    ADP    +0.2%   COST   +0.7%   CTAS  +0.5%
    O      -3.8%   FAST   -3.9%   LUMN  -8.2%

Lumen prints a traded price of $3.83 and 1,031m shares outstanding,
which is $3.9bn, beside a stated market capitalisation of $4.3bn. The
two are used in different places - every multiple is built on the
market capitalisation, every per-share figure on the share count - so
an eight percent disagreement is eight percent of the enterprise
value, the EV/Revenue, and the equity bridge, against per-share
figures struck on the other one.

The response is disclosure rather than a silent pick. Choosing one
would be inventing a figure the provider did not give; saying they
disagree is what the rest of this product does with a conflict.
"""

from __future__ import annotations

from asset_researcher.quant.market import cap_vs_shares_gap


def test_figures_that_multiply_raise_nothing():
    assert cap_vs_shares_gap(
        market_cap=118.9e9, price=301.71, shares=395e6
    ) is None


def test_a_small_rounding_difference_is_tolerated():
    """The printed figures are rounded, and a provider's cap is struck
    at its own moment. Half a percent is noise, not a conflict."""
    assert cap_vs_shares_gap(
        market_cap=100e9, price=100.0, shares=1.004e9
    ) is None


def test_an_eight_percent_disagreement_is_reported():
    gap = cap_vs_shares_gap(market_cap=4.3e9, price=3.83, shares=1031e6)
    assert gap is not None
    assert "8" in gap


def test_the_message_carries_both_figures_so_it_can_be_checked():
    gap = cap_vs_shares_gap(market_cap=4.3e9, price=3.83, shares=1031e6)
    assert "$4.3B" in gap
    assert "$3.9B" in gap


def test_a_missing_figure_is_not_a_disagreement():
    assert cap_vs_shares_gap(None, 3.83, 1031e6) is None
    assert cap_vs_shares_gap(4.3e9, None, 1031e6) is None
    assert cap_vs_shares_gap(4.3e9, 3.83, None) is None
    assert cap_vs_shares_gap(4.3e9, 3.83, 0) is None


def test_a_zero_market_cap_does_not_divide():
    assert cap_vs_shares_gap(0, 3.83, 1031e6) is None
