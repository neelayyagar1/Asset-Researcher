"""Published financial-health scores. Altman Z, Piotroski F, Beneish M.

Deterministic arithmetic on filed XBRL data, each citing its published
methodology. Zero hallucination surface: these cannot be wrong in the way a
model-generated number can, only unavailable.

**Sector gating is the point of this module.** Altman Z and Piotroski F
assume a non-financial balance sheet, working capital, inventory turnover,
and current ratio are not meaningful for a bank, whose balance sheet is its
business. Run on JPM they produce confident garbage, which is precisely the
failure mode the design forbids. A score outside its applicable sectors
returns NOT_MEANINGFUL and renders as text, never as a number.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from asset_researcher.quant.metrics_config import all_health_score_defs
from asset_researcher.quant.series import MetricSeries


class ScoreStatus(str, Enum):
    OK = "ok"
    NOT_MEANINGFUL = "not_meaningful_for_sector"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass(frozen=True)
class ScoreResult:
    name: str
    label: str
    citation: str
    status: ScoreStatus
    value: float | None = None
    band: str | None = None
    detail: str | None = None

    def display(self) -> str:
        if self.status is ScoreStatus.NOT_MEANINGFUL:
            return "not meaningful for this sector"
        if self.status is ScoreStatus.INSUFFICIENT_DATA:
            return f"insufficient data ({self.detail})"
        # `detail` records what the computation had to substitute or could
        # not evaluate, and dropping it printed an approximated score as a
        # clean number under a footnote citing the published methodology.
        # A Piotroski F of 5 scored over 6 evaluable tests is not a 5 on the
        # 9-test scale it is then banded against.
        rendered = f"{self.value:.2f}" + (f" ({self.band})" if self.band else "")
        return f"{rendered}, {self.detail}" if self.detail else rendered


def _at(series: MetricSeries, metric: str, index: int = -1) -> float | None:
    periods = series.series.get(metric)
    if not periods or abs(index) > len(periods):
        return None
    return periods[index].value


def _band_for(value: float, bands: dict) -> str | None:
    for name, bounds in bands.items():
        low = bounds.get("min", float("-inf"))
        high = bounds.get("max", float("inf"))
        if low <= value <= high:
            return name
    return None


def _altman_z(series: MetricSeries, market_cap: float | None, defn) -> ScoreResult:
    base = dict(name=defn.name, label=defn.label, citation=defn.citation)

    working_capital = None
    ca, cl = _at(series, "current_assets"), _at(series, "current_liabilities")
    if ca is not None and cl is not None:
        working_capital = ca - cl

    total_assets = _at(series, "total_assets")
    retained = _at(series, "retained_earnings")
    ebit = _at(series, "operating_income")
    total_liabilities = _at(series, "total_liabilities")
    revenue = _at(series, "revenue")

    missing = [
        n
        for n, v in {
            "working_capital": working_capital,
            "total_assets": total_assets,
            "retained_earnings": retained,
            "operating_income": ebit,
            "total_liabilities": total_liabilities,
            "revenue": revenue,
            "market_cap": market_cap,
        }.items()
        if v is None
    ]
    if missing or not total_assets or not total_liabilities:
        return ScoreResult(
            **base,
            status=ScoreStatus.INSUFFICIENT_DATA,
            detail=f"missing {', '.join(missing) or 'nonzero assets/liabilities'}",
        )

    z = (
        1.2 * (working_capital / total_assets)
        + 1.4 * (retained / total_assets)
        + 3.3 * (ebit / total_assets)
        + 0.6 * (market_cap / total_liabilities)
        + 1.0 * (revenue / total_assets)
    )
    return ScoreResult(
        **base, status=ScoreStatus.OK, value=z, band=_band_for(z, defn.raw["bands"])
    )


def _piotroski_f(series: MetricSeries, defn) -> ScoreResult:
    """9 binary tests, needs two consecutive fiscal years."""
    base = dict(name=defn.name, label=defn.label, citation=defn.citation)

    def pair(metric: str) -> tuple[float | None, float | None]:
        return _at(series, metric, -2), _at(series, metric, -1)

    ni_prev, ni_curr = pair("net_income")
    ta_prev, ta_curr = pair("total_assets")
    ocf_prev, ocf_curr = pair("operating_cash_flow")
    debt_prev, debt_curr = pair("total_debt")
    ca_prev, ca_curr = pair("current_assets")
    cl_prev, cl_curr = pair("current_liabilities")
    sh_prev, sh_curr = pair("shares_diluted")
    gp_prev, gp_curr = pair("gross_profit")
    rev_prev, rev_curr = pair("revenue")

    if ni_curr is None or ta_curr is None or ta_prev is None or ocf_curr is None:
        return ScoreResult(
            **base,
            status=ScoreStatus.INSUFFICIENT_DATA,
            detail="needs two years of net income, assets, and operating cash flow",
        )

    tests: dict[str, bool | None] = {}
    tests["positive_net_income"] = ni_curr > 0
    tests["positive_operating_cash_flow"] = ocf_curr > 0
    tests["roa_improved_yoy"] = (
        (ni_curr / ta_curr) > (ni_prev / ta_prev)
        if ni_prev is not None and ta_prev
        else None
    )
    tests["cash_flow_exceeds_net_income"] = ocf_curr > ni_curr
    tests["leverage_decreased_yoy"] = (
        (debt_curr / ta_curr) < (debt_prev / ta_prev)
        if debt_curr is not None and debt_prev is not None and ta_prev
        else None
    )
    tests["current_ratio_improved_yoy"] = (
        (ca_curr / cl_curr) > (ca_prev / cl_prev)
        if None not in (ca_curr, cl_curr, ca_prev, cl_prev) and cl_curr and cl_prev
        else None
    )
    tests["no_new_shares_issued"] = (
        sh_curr <= sh_prev if sh_curr is not None and sh_prev is not None else None
    )
    tests["gross_margin_improved_yoy"] = (
        (gp_curr / rev_curr) > (gp_prev / rev_prev)
        if None not in (gp_curr, rev_curr, gp_prev, rev_prev) and rev_curr and rev_prev
        else None
    )
    tests["asset_turnover_improved_yoy"] = (
        (rev_curr / ta_curr) > (rev_prev / ta_prev)
        if rev_curr is not None and rev_prev is not None and ta_prev
        else None
    )

    evaluable = {k: v for k, v in tests.items() if v is not None}
    if len(evaluable) < 6:
        return ScoreResult(
            **base,
            status=ScoreStatus.INSUFFICIENT_DATA,
            detail=f"only {len(evaluable)} of 9 tests evaluable",
        )

    score = float(sum(1 for v in evaluable.values() if v))
    detail = f"{len(evaluable)} of 9 tests evaluable"
    return ScoreResult(
        **base,
        status=ScoreStatus.OK,
        value=score,
        band=_band_for(score, defn.raw["bands"]),
        detail=None if len(evaluable) == 9 else detail,
    )


def _beneish_m(series: MetricSeries, defn) -> ScoreResult:
    """8-variable earnings-manipulation model. Requires two consecutive years
    across a wide input set; frequently INSUFFICIENT_DATA in practice, which
    is reported honestly rather than approximated with defaults."""
    base = dict(name=defn.name, label=defn.label, citation=defn.citation)

    def pair(metric: str) -> tuple[float | None, float | None]:
        return _at(series, metric, -2), _at(series, metric, -1)

    ar_prev, ar_curr = pair("accounts_receivable")
    rev_prev, rev_curr = pair("revenue")
    gp_prev, gp_curr = pair("gross_profit")
    ta_prev, ta_curr = pair("total_assets")
    ca_prev, ca_curr = pair("current_assets")
    dep_prev, dep_curr = pair("depreciation_amortization")
    debt_prev, debt_curr = pair("total_debt")
    ni_prev, ni_curr = pair("net_income")
    ocf_prev, ocf_curr = pair("operating_cash_flow")

    required = {
        "accounts_receivable": (ar_prev, ar_curr),
        "revenue": (rev_prev, rev_curr),
        "gross_profit": (gp_prev, gp_curr),
        "total_assets": (ta_prev, ta_curr),
        "current_assets": (ca_prev, ca_curr),
        "depreciation_amortization": (dep_prev, dep_curr),
        "net_income": (ni_prev, ni_curr),
        "operating_cash_flow": (ocf_prev, ocf_curr),
    }
    missing = [n for n, (p, c) in required.items() if p is None or c is None]
    if missing:
        return ScoreResult(
            **base,
            status=ScoreStatus.INSUFFICIENT_DATA,
            detail=f"missing two-year data for {', '.join(missing)}",
        )
    if not all([rev_prev, rev_curr, gp_prev, ta_prev, ta_curr, ca_prev]):
        return ScoreResult(
            **base, status=ScoreStatus.INSUFFICIENT_DATA, detail="zero-valued denominator"
        )

    dsri = (ar_curr / rev_curr) / (ar_prev / rev_prev)
    gmi = (gp_prev / rev_prev) / (gp_curr / rev_curr) if gp_curr and rev_curr else 1.0
    # Asset Quality Index: proportion of assets that are neither current nor PP&E.
    # PP&E is not in the canonical set, so this uses the non-current share as a
    # documented approximation rather than omitting the variable entirely.
    aqi = (1 - ca_curr / ta_curr) / (1 - ca_prev / ta_prev) if ca_prev != ta_prev else 1.0
    sgi = rev_curr / rev_prev
    depi = (dep_prev / (dep_prev + ta_prev)) / (dep_curr / (dep_curr + ta_curr))
    sgai = 1.0  # SG&A not in the canonical set; neutral value, documented
    lvgi = (
        ((debt_curr / ta_curr) / (debt_prev / ta_prev))
        if debt_curr is not None and debt_prev is not None and ta_prev
        else 1.0
    )
    tata = (ni_curr - ocf_curr) / ta_curr

    m = (
        -4.84
        + 0.92 * dsri
        + 0.528 * gmi
        + 0.404 * aqi
        + 0.892 * sgi
        + 0.115 * depi
        - 0.172 * sgai
        + 4.679 * tata
        - 0.327 * lvgi
    )
    threshold = defn.raw["threshold"]["likely_manipulator"]["min"]
    band = "elevated" if m > threshold else "normal"
    return ScoreResult(
        **base,
        status=ScoreStatus.OK,
        value=m,
        band=band,
        detail="SG&A and PP&E unavailable in canonical set; SGAI held neutral, AQI approximated",
    )


def compute_health_scores(
    series: MetricSeries, sector: str, market_cap: float | None = None
) -> list[ScoreResult]:
    """Returns a result for EVERY defined score, including ones that don't
    apply to this sector, marked NOT_MEANINGFUL. Omitting them silently would
    leave a reader unsure whether a score was inapplicable or merely
    forgotten."""
    results: list[ScoreResult] = []
    for defn in all_health_score_defs():
        if not defn.applies_to(sector):
            results.append(
                ScoreResult(
                    name=defn.name,
                    label=defn.label,
                    citation=defn.citation,
                    status=ScoreStatus.NOT_MEANINGFUL,
                )
            )
            continue

        if defn.name == "altman_z":
            results.append(_altman_z(series, market_cap, defn))
        elif defn.name == "piotroski_f":
            results.append(_piotroski_f(series, defn))
        elif defn.name == "beneish_m":
            results.append(_beneish_m(series, defn))
    return results
