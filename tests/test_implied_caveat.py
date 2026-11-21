"""Which model the terminal-share caveat is talking about.

A review reported that `ImpliedExpectations.terminal_share` is taken
from the baseline run rather than from the solve, and called it a
defect. Reading it, it is not: the caveat it feeds sits beside
`model_value_at_defaults`, and both describe the model at the
convention assumptions. Taking the share from the solved run would
have made the two halves of one sentence describe two different runs.

What is true is that the sentence does not say so, and it prints under
a heading that reads "Price-implied expectations" - so a reader can
reasonably take "the modelled value" to mean the figure solved back
from the price. One clause fixes it, and nothing arithmetic changes.
"""

from __future__ import annotations

from asset_researcher.quant.valuation import ImpliedExpectations


def _implied(terminal_share: float) -> ImpliedExpectations:
    return ImpliedExpectations(
        implied_growth=0.068,
        implied_discount_rate=0.085,
        market_price=100.0,
        model_value_at_defaults=110.0,
        terminal_share=terminal_share,
    )


def test_the_terminal_caveat_names_the_run_it_describes():
    caveat = _implied(0.82).caveat
    assert caveat and "default assumptions" in caveat


def test_it_still_fires_only_when_the_terminal_dominates():
    assert _implied(0.60).caveat is None
    assert _implied(0.82).caveat is not None


def test_the_percentage_itself_is_unchanged():
    assert "82%" in _implied(0.82).caveat
