"""Net debt, defined once.

Three places needed this figure and each computed it separately: the
discounted cash flow bridged from enterprise to equity value with it, the
comparables table built enterprise value on it, and the derived metrics
reported it as a line. All three used `total_debt - cash_and_equivalents`.

That definition is wrong for any filer that holds marketable securities,
which is most large ones. Apple carries roughly $98.7B of debt against
$30B of cash and a further ~$125B in short and long-term marketable
securities: net cash by any reading. The old definition reported it as
$62.7B of net debt, printed that in a valuation bridge, and deducted it from
equity value. It is wrong by about $8 a share, and it is wrong in the one
direction a reader checks first.

The figure now lives here, and the components travel with it so a report can
show what was netted rather than asking the reader to trust a single number.

**Long-term securities are netted only for non-financial filers.** For a bank
or an insurer the investment portfolio is the operating business rather than
a cash reserve, and netting it would understate leverage enormously. The
sector classes that permit it are the ones `config/metrics/canonical.yaml`
assigns the metric to.
"""

from __future__ import annotations

from dataclasses import dataclass

from asset_researcher.quant.series import MetricSeries

# Sector classes for which long-term marketable securities are a cash
# equivalent rather than an operating asset.
_NETS_LONG_TERM = {"standard", "energy", "biotech"}


@dataclass(frozen=True)
class NetDebt:
    """Net debt with its components, positive for debt and negative for cash."""

    total_debt: float
    cash: float
    short_term_investments: float
    long_term_investments: float
    nets_long_term: bool

    @property
    def gross_cash(self) -> float:
        """Cash and whatever securities this filer's sector permits netting."""
        total = self.cash + self.short_term_investments
        if self.nets_long_term:
            total += self.long_term_investments
        return total

    @property
    def value(self) -> float:
        """Negative means net cash."""
        return self.total_debt - self.gross_cash

    @property
    def is_net_cash(self) -> bool:
        return self.value < 0

    def components(self) -> list[tuple[str, float]]:
        """The bridge, for display. Signed as they net."""
        rows = [
            ("Total debt", self.total_debt),
            ("Less cash and equivalents", -self.cash),
        ]
        if self.short_term_investments:
            rows.append(
                ("Less short-term investments", -self.short_term_investments)
            )
        if self.nets_long_term and self.long_term_investments:
            rows.append(
                ("Less long-term marketable securities", -self.long_term_investments)
            )
        rows.append(("Net debt" if not self.is_net_cash else "Net cash", self.value))
        return rows

    @property
    def basis(self) -> str:
        """What was netted, for the assumptions table."""
        parts = ["cash and equivalents", "short-term investments"]
        if self.nets_long_term:
            parts.append("long-term marketable securities")
        return (
            "Total debt less " + ", ".join(parts) + ", as filed. "
            "Long-term securities are netted for non-financial filers only."
        )


def _latest(series: MetricSeries, metric: str) -> float:
    points = series.series.get(metric) or []
    return points[-1].value if points else 0.0


def net_debt(series: MetricSeries, sector_class: str = "standard") -> NetDebt:
    """Net debt from the most recent filed balance sheet."""
    return NetDebt(
        total_debt=_latest(series, "total_debt"),
        cash=_latest(series, "cash_and_equivalents"),
        short_term_investments=_latest(series, "short_term_investments"),
        long_term_investments=_latest(series, "long_term_investments"),
        nets_long_term=sector_class in _NETS_LONG_TERM,
    )


def net_debt_from_values(
    total_debt: float | None,
    cash: float | None,
    short_term_investments: float | None = None,
    long_term_investments: float | None = None,
    sector_class: str = "standard",
) -> NetDebt:
    """The same definition over loose values, for the peer rows.

    Peers are fetched at low fidelity and any of these may be absent; a
    missing component contributes zero rather than blocking the row.
    """
    return NetDebt(
        total_debt=total_debt or 0.0,
        cash=cash or 0.0,
        short_term_investments=short_term_investments or 0.0,
        long_term_investments=long_term_investments or 0.0,
        nets_long_term=sector_class in _NETS_LONG_TERM,
    )
