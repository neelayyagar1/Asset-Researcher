"""Deterministic validation of a resolved metric series (ARCHITECTURE.md §5).

This is the safety net for concept resolution: it never trusts the LLM
mapping's own stated confidence, and it never trusts a single "looks right"
number in isolation. A wrong mapping should be *caught here*, not silently
displayed, that is the whole point of separating this from resolve.py.

Every check is arithmetic on values already fetched from XBRL. Nothing in
this file calls a model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from asset_researcher.quant.series import MetricSeries

# Universally required regardless of sector, all four are tagged
# sectors:[all] in canonical.yaml, so a sector-appropriate filer should
# always report them. Their total absence signals resolution failed broadly,
# not just on one line item.
_REQUIRED_METRICS = ["revenue", "net_income", "total_assets", "total_equity"]

# A year-over-year jump of more than this multiple, with both values nonzero,
# is far more likely a unit error (thousands vs. millions) or a mismapped
# concept than a real business result.
_MAGNITUDE_JUMP_THRESHOLD = 50.0

# Balance-sheet identity tolerance, real filings have minor rounding/
# reclassification noise; this is not a bug hunt for cent-level drift.
_IDENTITY_TOLERANCE = 0.02


@dataclass(frozen=True)
class ValidationIssue:
    check: str
    message: str
    severity: str  # "error", metric should not be trusted/displayed as-is
    # "warning", worth surfacing, does not block display


@dataclass
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def add(self, check: str, message: str, severity: str) -> None:
        self.issues.append(ValidationIssue(check=check, message=message, severity=severity))


def _latest_value(series: MetricSeries, metric: str) -> float | None:
    periods = series.series.get(metric)
    return periods[-1].value if periods else None


def check_accounting_identity(series: MetricSeries, result: ValidationResult) -> None:
    assets = _latest_value(series, "total_assets")
    liabilities = _latest_value(series, "total_liabilities")
    equity = _latest_value(series, "total_equity")
    if assets is None or liabilities is None or equity is None:
        return  # nothing to check, absence is handled by required-metrics check
    if assets == 0:
        return
    drift = abs(assets - (liabilities + equity)) / abs(assets)
    if drift > _IDENTITY_TOLERANCE:
        result.add(
            "accounting_identity",
            f"Assets (${assets:,.0f}) != Liabilities + Equity "
            f"(${liabilities + equity:,.0f}), drift {drift:.1%}. "
            f"One of total_assets / total_liabilities / total_equity is "
            f"likely mismapped.",
            severity="error",
        )


def check_revenue_exceeds_net_income(series: MetricSeries, result: ValidationResult) -> None:
    revenue = _latest_value(series, "revenue")
    net_income = _latest_value(series, "net_income")
    if revenue is None or net_income is None:
        return
    if revenue < net_income:
        result.add(
            "revenue_vs_net_income",
            f"Revenue (${revenue:,.0f}) is less than Net Income "
            f"(${net_income:,.0f}). Possible on rare one-time-gain years, "
            f"but far more often a sign revenue or net_income is mismapped.",
            severity="warning",
        )
    if revenue < 0:
        result.add(
            "revenue_vs_net_income",
            f"Revenue is negative (${revenue:,.0f}), revenue is almost "
            f"certainly mismapped to a contra or non-revenue concept.",
            severity="error",
        )


def check_period_alignment(series: MetricSeries, result: ValidationResult) -> None:
    """Consecutive annual periods should be ~1 fiscal year apart. series.py
    dedupes by end-date, so duplicates can't occur here by construction.
    what this actually catches is a fiscal-calendar irregularity (a changed
    fiscal year-end) or a duration concept whose 'annual' facts don't
    actually span a year, both of which would otherwise silently distort
    year-over-year comparisons in the financial table."""
    for metric, periods in series.series.items():
        for prev, curr in zip(periods, periods[1:]):
            prev_date = date.fromisoformat(prev.end)
            curr_date = date.fromisoformat(curr.end)
            gap_days = (curr_date - prev_date).days
            if not (330 <= gap_days <= 400):
                result.add(
                    "period_alignment",
                    f"'{metric}' periods {prev.end} -> {curr.end} are "
                    f"{gap_days} days apart, not ~1 year. Possible fiscal "
                    f"year-end change or a mismapped concept.",
                    severity="warning",
                )


def check_magnitude_jumps(series: MetricSeries, result: ValidationResult) -> None:
    """Detect unit errors (thousands vs. millions) and cross-period concept
    mismaps via implausible year-over-year jumps.

    Two guards prevent false positives, both added after this check fired
    incorrectly on real Apple data during build:

    1. Sign changes are skipped. Apple's retained earnings legitimately
       crossed zero (buybacks drove it to an accumulated deficit), passing
       through -$0.21B, a ratio against a near-zero value is arithmetically
       meaningless, not evidence of a bug.
    2. Both values must be material relative to company scale. A metric
       that is a rounding error next to total assets can swing by any
       multiple without indicating a mapping problem.

    A validator that cries wolf is worse than no validator, because it
    trains the reader to ignore it, so this errs toward silence and relies
    on check_scale_plausibility for the absolute-magnitude case.
    """
    scale = _latest_value(series, "total_assets")
    if scale is None or scale <= 0:
        return
    materiality_floor = abs(scale) * 0.01

    for metric, periods in series.series.items():
        for prev, curr in zip(periods, periods[1:]):
            if prev.value == 0 or curr.value == 0:
                continue
            if (prev.value > 0) != (curr.value > 0):
                continue  # guard 1: sign change
            if abs(prev.value) < materiality_floor or abs(curr.value) < materiality_floor:
                continue  # guard 2: immaterial relative to company scale
            ratio = abs(curr.value / prev.value)
            if ratio > _MAGNITUDE_JUMP_THRESHOLD or ratio < 1 / _MAGNITUDE_JUMP_THRESHOLD:
                result.add(
                    "magnitude_jump",
                    f"'{metric}' jumps {ratio:.0f}x between {prev.frame_label} "
                    f"(${prev.value:,.0f}) and {curr.frame_label} (${curr.value:,.0f}). "
                    f"Likely a unit mismatch (e.g. thousands vs. millions) or "
                    f"a concept mismapped across periods.",
                    severity="error",
                )


def check_scale_plausibility(series: MetricSeries, result: ValidationResult) -> None:
    """Catches the absolute-magnitude case that check_magnitude_jumps
    deliberately ignores: a metric consistently wrong by a unit factor across
    every period would show no year-over-year jump at all, but would be
    wildly out of scale against the rest of the balance sheet."""
    assets = _latest_value(series, "total_assets")
    revenue = _latest_value(series, "revenue")
    if assets is None or revenue is None or assets <= 0:
        return
    # No real operating company turns over its entire asset base 100x/yr;
    # a ratio that extreme means one of the two is off by a unit factor.
    if revenue / assets > 100:
        result.add(
            "scale_plausibility",
            f"Revenue (${revenue:,.0f}) is {revenue / assets:.0f}x total assets "
            f"(${assets:,.0f}). One of the two is likely off by a unit factor "
            f"(thousands vs. units).",
            severity="error",
        )


def check_required_metrics_present(series: MetricSeries, result: ValidationResult) -> None:
    for metric in _REQUIRED_METRICS:
        if metric not in series.series or not series.series[metric]:
            result.add(
                "required_metrics",
                f"'{metric}' has no resolved data for this filer at all.",
                severity="error",
            )


_ALL_CHECKS = [
    check_accounting_identity,
    check_revenue_exceeds_net_income,
    check_period_alignment,
    check_magnitude_jumps,
    check_scale_plausibility,
    check_required_metrics_present,
]


def validate(series: MetricSeries) -> ValidationResult:
    result = ValidationResult()
    for check in _ALL_CHECKS:
        check(series, result)
    return result
