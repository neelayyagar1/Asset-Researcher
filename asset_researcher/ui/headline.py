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

from dataclasses import replace

from asset_researcher.analysis.report import Report
from asset_researcher.quant.valuation import probability_weighted_target
from asset_researcher.ui import format as fmt
from asset_researcher.ui.components import Stat










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
        case_note = f"Bear {fmt.usd(low)} to bull {fmt.usd(high)}"

    price_stat = Stat(
        "Traded price", fmt.usd(price), f"Market cap {fmt.scaled_usd(bundle.market_cap)}"
    )
    cash_stat = Stat(
        "Market cap / free cash flow",
        f"{context.multiple_of_fcf:,.0f}x"
        if context and context.multiple_of_fcf
        else "NM",
        f"Filed FCF CAGR {fmt.pct(context.fcf_cagr)}"
        if context and context.fcf_cagr is not None
        else "",
    )
    implied_growth_stat = Stat(
        "Price implies FCF growth",
        fmt.pct(implied.implied_growth) if implied else "NM",
        "Solved back from the traded price",
    )

    def leading(stat: Stat) -> Stat:
        """The figure this report authored, set a rank above the handed ones."""
        return replace(stat, lead=True)

    model_is_load_bearing = implied is None or implied.caveat is None
    if model_is_load_bearing:
        return [
            price_stat,
            Stat("Probability-weighted target", fmt.usd(target), case_note,
                 lead=True),
            Stat(
                "Implied upside",
                fmt.signed_pct(upside),
                "Target against traded price",
                tone="pos" if (upside or 0) > 0 else "neg",
            ),
            implied_growth_stat,
            cash_stat,
        ]

    return [
        price_stat,
        cash_stat,
        leading(implied_growth_stat),
        Stat(
            "Price implies discount rate",
            fmt.pct(implied.implied_discount_rate)
            if implied and implied.implied_discount_rate is not None
            else "NM",
            "The return the price is priced to deliver",
        ),
        Stat(
            "Modelled value, illustrative",
            fmt.usd(target),
            f"{case_note}. See the divergence note below" if case_note else "",
        ),
    ]
