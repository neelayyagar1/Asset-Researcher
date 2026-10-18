"""The five figures at the top, decided once.

The screen and the exported file both open with a stat strip, and they were
building it separately. That is how the page came to demote a disowned
valuation target while the file a reader actually forwards still led with it.

**What the strip shows depends on whether the model is load-bearing.** A
single-stage discounted cash flow on a highly rated company routinely lands
far from the market, and the valuation layer detects that and says so. Where
it has, setting the modelled target at the largest type size on the page with
a caveat beneath it disowning that same number is not a presentation anyone
can act on: the first thing a reader sees is a figure the second thing tells
them to ignore.

So the strip leads with what survives the caveat, and the target moves to the
end labelled as illustrative. It is not removed. The target is what a reader
came for, hiding it would be its own kind of dishonesty, and a reader who
wants it should not have to open a tab to find out that the tool declined to
show it.
"""

from __future__ import annotations

from asset_researcher.analysis.report import Report
from asset_researcher.quant.valuation import probability_weighted_target
from asset_researcher.ui.components import Stat


def _pct(value: float | None, digits: int = 1) -> str:
    return f"{value * 100:,.{digits}f}%" if value is not None else "NM"


def _signed_pct(value: float | None) -> str:
    """Upside carries an explicit sign: the direction is the point."""
    if value is None:
        return "NM"
    return f"{'+' if value >= 0 else ''}{value * 100:,.1f}%"


def _usd(value: float | None) -> str:
    return f"${value:,.2f}" if value is not None else "NM"


def _billions(value: float | None) -> str:
    return f"${value / 1e9:,.0f}B" if value else "NM"


def headline_stats(report: Report) -> list[Stat]:
    bundle = report.bundle
    price = bundle.quote.price if bundle.quote else None
    cases = bundle.valuation_cases
    target = probability_weighted_target(cases) if cases else None
    upside = (target / price - 1) if (target and price) else None
    implied = bundle.implied
    context = bundle.cash_context

    case_note = ""
    if cases:
        low = min(c.value_per_share for c in cases)
        high = max(c.value_per_share for c in cases)
        case_note = f"Bear {_usd(low)} to bull {_usd(high)}"

    price_stat = Stat(
        "Traded price", _usd(price), f"Market cap {_billions(bundle.market_cap)}"
    )
    cash_stat = Stat(
        "Market cap / free cash flow",
        f"{context.multiple_of_fcf:,.0f}x"
        if context and context.multiple_of_fcf
        else "NM",
        f"Filed FCF CAGR {_pct(context.fcf_cagr)}"
        if context and context.fcf_cagr is not None
        else "",
    )
    implied_growth_stat = Stat(
        "Price implies FCF growth",
        _pct(implied.implied_growth) if implied else "NM",
        "Solved back from the traded price",
    )

    model_is_load_bearing = implied is None or implied.caveat is None
    if model_is_load_bearing:
        return [
            price_stat,
            Stat("Probability-weighted target", _usd(target), case_note),
            Stat(
                "Implied upside",
                _signed_pct(upside),
                "Target against traded price",
                tone="pos" if (upside or 0) > 0 else "neg",
            ),
            implied_growth_stat,
            cash_stat,
        ]

    return [
        price_stat,
        cash_stat,
        implied_growth_stat,
        Stat(
            "Price implies discount rate",
            _pct(implied.implied_discount_rate)
            if implied and implied.implied_discount_rate is not None
            else "NM",
            "The return the price is priced to deliver",
        ),
        Stat(
            "Modelled value, illustrative",
            _usd(target),
            f"{case_note}. See the divergence note below" if case_note else "",
        ),
    ]
