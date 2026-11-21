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










def _sector_stats(report: Report) -> list[Stat]:
    """What a bank or a REIT is actually read on.

    Drawn from the sector-gated derived metrics, so nothing here is a
    figure the taxonomy declares meaningless for this filer.
    """
    derived = report.bundle.derived or {}
    cap = report.bundle.market_cap

    def ratio(label: str, key: str, note: str) -> Stat | None:
        """A supporting ratio. Never the lead.

        This passed lead=True to every ratio it built, so a REIT page
        carried two display-size tiles and the second was net margin -
        a figure the same note calls the least informative line for
        that filer and argues against in two separate sections. Two
        leads is no lead.
        """
        value = derived.get(key)
        return (
            Stat(label, fmt.pct(value), note)
            if value is not None
            else None
        )

    out: list[Stat] = []
    ffo = derived.get("ffo_before_disposals")
    if ffo and cap:
        out.append(Stat(
            "Price / FFO", f"{cap / ffo:,.1f}x",
            "Funds from operations, before gains on disposal", lead=True,
        ))
    out.append(ratio("Return on equity", "roe", "Filed, latest period"))
    out.append(ratio(
        "Net margin", "net_margin", "Filed, latest period"
    ))
    out.append(ratio(
        "Efficiency ratio", "efficiency_ratio", "Costs against revenue"
    ))
    return [s for s in out if s is not None][:3]


def _is_printable_value(value: float | None) -> bool:
    """Is a modelled value per share a figure a reader can act on?

    Equity is an option with a zero floor, so a negative value per
    share is not a conservative output - it is a non-output. The model
    discounts unlevered cash flow to an enterprise value and subtracts
    a net debt stack; for a heavily levered filer the residual goes
    negative on almost any assumption set, which describes the leverage
    rather than a mispricing.

    Lumen's note printed "Modelled value, illustrative ($4.52)" above a
    paragraph explaining why the number meant nothing. Printing a
    figure and disclaiming it underneath is the shape of defect this
    product exists to avoid: the headline is what gets quoted.
    """
    return value is not None and value > 0


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

    # Where no valuation was produced at all - a bank or a REIT, which
    # this tool refuses an enterprise model for - the strip must not
    # simply print the standard five with four of them NM. That is what
    # it did: a yield reader's whole first impression of a REIT page was
    # the tool saying four times that it had nothing, which reads as a
    # broken widget rather than a considered refusal. The sector figures
    # below are already computed and gated; the refusal takes the last
    # cell, where it reads as a judgement rather than as a failure.
    if cases is None or not cases:
        sector_stats = _sector_stats(report)
        if sector_stats:
            return [price_stat, *sector_stats, Stat(
                "Modelled target",
                "Declined",
                "An enterprise model does not describe this sector",
            )]

    # A model is load-bearing only when it was solved AND nothing about it
    # drew a caveat. This read `implied is None or implied.caveat is None`,
    # which treated a FAILED solve as a clean bill of health: when the
    # reverse solve could not run, the strip fell through to the
    # full-confidence branch and led, at the largest size on the page,
    # with a target nothing had checked. That is how Ford shipped a
    # headline of +564% upside and Lumen one of -91%.
    #
    # The second clause is a backstop, not a second opinion. Ordinary
    # disagreement with the market is what the caveat above handles, and a
    # model calling a stock worth 40% of its price is a real call that
    # should still be shown. This catches only the arithmetic that has
    # plainly broken: a target of +564% of the traded price, or one of
    # -91%, is not a mispricing anybody will entertain, and a figure like
    # that on the first screen costs more credibility than the rest of the
    # note can earn back. Both shipped.
    implausible = upside is not None and not (-0.75 < upside < 3.0)
    model_is_load_bearing = (
        implied is not None and implied.caveat is None and not implausible
    )
    if model_is_load_bearing:
        # The implied expectation leads, not the target.
        #
        # Every note tells the reader to treat the implied growth
        # requirement as the valuation finding and the modelled value as
        # a byproduct, and the strip then set the target at the largest
        # size on the page. A reviewer pressed exactly there, and he was
        # right: a hierarchy stated in prose and contradicted in layout
        # is the layout's hierarchy, because the headline is what gets
        # quoted.
        #
        # It is also the sounder figure. The target inherits a discount
        # rate that is the same 8.5% for every filer, which is the
        # weakest input in the model; the implied growth rate is solved
        # back from the traded price and does not depend on it. The
        # target is still shown, in its own rank, because a reader who
        # wants it should not have to leave the page for it.
        return [
            price_stat,
            leading(implied_growth_stat),
            Stat("Probability-weighted target", fmt.usd(target), case_note),
            Stat(
                "Implied upside",
                fmt.signed_pct(upside),
                "Target against traded price",
                tone="pos" if (upside or 0) > 0 else "neg",
            ),
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
            fmt.usd(target) if _is_printable_value(target) else "NM",
            (
                f"{case_note}. See the divergence note below"
                if case_note
                else ""
            )
            if _is_printable_value(target)
            else "The model returns no positive equity value for this "
                 "capital structure",
        ),
    ]
