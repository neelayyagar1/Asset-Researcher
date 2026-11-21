"""Checks on the market data itself, before anything is built on it.

The filings are validated line by line. The market figures were not,
and they are load-bearing in a different way: every multiple in the
note is built on the market capitalisation, and every per-share figure
on the share count. Those arrive from the provider independently, and
nothing asked whether they agreed.
"""

from __future__ import annotations

from asset_researcher.ui.format import scaled_usd

# The printed figures are rounded and a provider strikes its market
# capitalisation at its own moment, so a small difference is noise. Two
# percent is comfortably above that and well below the eight percent
# the shipped Lumen note carried.
_TOLERANCE = 0.02


def cap_vs_shares_gap(
    market_cap: float | None,
    price: float | None,
    shares: float | None,
) -> str | None:
    """A sentence when the two disagree, None when they do not.

    Reported rather than reconciled. Picking one would be inventing a
    figure the provider did not give, and this product's response to a
    conflict between two sources is to say so.
    """
    if not market_cap or not price or not shares:
        return None
    implied = price * shares
    drift = implied / market_cap - 1
    if abs(drift) <= _TOLERANCE:
        return None
    return (
        f"The market capitalisation from the provider "
        f"({scaled_usd(market_cap)}) and its own share count at the traded "
        f"price ({scaled_usd(implied)}) differ by {abs(drift) * 100:,.0f}%. "
        f"Multiples in this note are built on the first and per-share "
        f"figures on the second, so treat comparisons between them as "
        f"carrying that difference."
    )
