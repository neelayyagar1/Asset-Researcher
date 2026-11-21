"""The one sentence under "Current valuation", which drew a conclusion
it had not checked.

It read, on every note: "The price therefore rests on expectations not
present in the filed cash flow history." That follows only when the
price implies MORE growth than the filed record delivered. Measured on
the shipped notes it was false on two of the four that print it - ADP
requires 6.8% against 12.5% of filed history, and Realty Income is
capitalised at 14 times against 28.4% compounded - so the note told a
portfolio manager to interrogate optimism in a price that embeds
pessimism. Backwards, in the section a reader goes to first.

The figures were right throughout. The inference was asserted rather
than made.
"""

from __future__ import annotations

from asset_researcher.quant.valuation import CashFlowContext


def _context(cagr: float) -> CashFlowContext:
    return CashFlowContext(
        latest_fcf=100.0,
        average_fcf=100.0,
        fcf_cagr=cagr,
        years_observed=5,
        market_cap=2300.0,          # 23x
    )


def test_it_states_the_two_figures_whatever_it_concludes():
    sentence = _context(0.125).summary(implied_growth=0.068)
    assert "23 times" in sentence
    assert "12.5%" in sentence


def test_a_price_demanding_more_than_history_says_so():
    sentence = _context(0.118).summary(implied_growth=0.187)
    assert "not present in the filed cash flow history" in sentence


def test_a_price_demanding_less_than_history_does_not_claim_the_opposite():
    """ADP: 6.8% required against 12.5% delivered."""
    sentence = _context(0.125).summary(implied_growth=0.068)
    assert "not present in the filed cash flow history" not in sentence
    assert "less than" in sentence


def test_a_price_that_extrapolates_history_is_called_that():
    sentence = _context(0.120).summary(implied_growth=0.1205)
    assert "not present" not in sentence
    assert "less than" not in sentence


def test_a_shrinking_record_the_price_does_not_share_still_reads_forward():
    """Lumen: -33.2% filed, 2.8% required. The price does demand more
    than the record delivered, even though 2.8% is a small number."""
    sentence = _context(-0.332).summary(implied_growth=0.028)
    assert "not present in the filed cash flow history" in sentence


def test_without_a_modelled_rate_it_states_the_figures_and_stops():
    """Realty Income declines the discounted cash flow, so there is no
    implied growth to compare. A sentence with nothing to compare must
    not reach for the conclusion anyway - which is exactly how the
    unconditional version came to be wrong."""
    sentence = _context(0.284).summary(implied_growth=None)
    assert "14 times" not in sentence  # this fixture is 23x
    assert "28.4%" in sentence
    assert "not present in the filed cash flow history" not in sentence
    assert "less than" not in sentence


def test_it_declines_when_it_has_no_figures():
    empty = CashFlowContext(None, None, None, 0, None)
    assert empty.summary(implied_growth=0.1) is None


# ------------------------------------------- and the page has to ask for it

def test_the_document_passes_the_modelled_rate_into_the_sentence():
    """A default argument makes a fix that never reaches the page.
    `summary()` with nothing passed still returns the no-model wording,
    which is wrong for every filer that HAS a model - so the caller is
    the half of this that matters."""
    import pathlib
    import re

    source = pathlib.Path(
        "asset_researcher/ui/document.py"
    ).read_text(encoding="utf-8")
    calls = re.findall(r"context\.summary\(([^)]*)\)", source)
    assert calls, "the document no longer calls summary()"
    assert all(call.strip() for call in calls), (
        "the document calls summary() with no implied growth, so every "
        "note would read as though no model was produced"
    )
