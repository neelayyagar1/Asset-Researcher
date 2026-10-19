"""Validation is the safety net for LLM-assisted concept resolution, the one
place a wrong number could otherwise reach the report. These tests pin both
directions: it must stay silent on legitimate data, and must still fire on
real error classes.
"""

import copy

import pytest

from asset_researcher.quant.series import MetricPeriod, MetricSeries
from asset_researcher.quant.validate import validate


def _series(**metrics: list[tuple[str, float]]) -> MetricSeries:
    s = MetricSeries(cik=1, sector="standard")
    for name, points in metrics.items():
        s.series[name] = [
            MetricPeriod(end=end, frame_label=f"FY{end[:4]}", value=val, accn="x")
            for end, val in points
        ]
    return s


def _healthy() -> MetricSeries:
    # Shape mirrors real Apple data: consistent ~1yr gaps, identity holds.
    return _series(
        revenue=[("2023-09-30", 383.3e9), ("2024-09-28", 391.0e9), ("2025-09-27", 416.2e9)],
        net_income=[("2023-09-30", 97.0e9), ("2024-09-28", 93.7e9), ("2025-09-27", 112.0e9)],
        total_assets=[("2023-09-30", 352.6e9), ("2024-09-28", 365.0e9), ("2025-09-27", 359.2e9)],
        total_liabilities=[("2023-09-30", 290.4e9), ("2024-09-28", 308.0e9), ("2025-09-27", 285.5e9)],
        total_equity=[("2023-09-30", 62.1e9), ("2024-09-28", 57.0e9), ("2025-09-27", 73.7e9)],
    )


def test_healthy_series_passes_clean():
    assert validate(_healthy()).ok


def test_near_zero_crossing_is_not_flagged():
    """Regression: Apple's retained earnings legitimately crossed zero via
    buybacks (-$0.21B -> -$19.15B, a 90x ratio). The original ratio-only
    magnitude check fired on this real, correct data. A validator that cries
    wolf trains the reader to ignore it, so sign changes and immaterial
    values are now skipped."""
    s = _healthy()
    s.series["retained_earnings"] = [
        MetricPeriod("2023-09-30", "FY2023", -0.214e9, "x"),
        MetricPeriod("2024-09-28", "FY2024", -19.154e9, "x"),
        MetricPeriod("2025-09-27", "FY2025", -14.264e9, "x"),
    ]
    assert validate(s).ok


def test_unit_error_is_caught():
    """Revenue reported in thousands instead of units, the classic XBRL
    unit trap. Shows no year-over-year jump (every period is wrong by the
    same factor), so only the scale check can catch it."""
    s = _healthy()
    s.series["revenue"] = [
        MetricPeriod(p.end, p.frame_label, p.value * 1000, p.accn)
        for p in s.series["revenue"]
    ]
    result = validate(s)
    assert not result.ok
    assert any(i.check == "scale_plausibility" for i in result.errors)


def test_balance_sheet_mismap_is_caught():
    s = _healthy()
    s.series["total_equity"] = [
        MetricPeriod(p.end, p.frame_label, p.value * 0.3, p.accn)
        for p in s.series["total_equity"]
    ]
    result = validate(s)
    assert not result.ok
    assert any(i.check == "accounting_identity" for i in result.errors)


def test_negative_revenue_is_an_error():
    s = _healthy()
    s.series["revenue"] = [
        MetricPeriod(p.end, p.frame_label, -p.value, p.accn) for p in s.series["revenue"]
    ]
    result = validate(s)
    assert not result.ok
    assert any(i.check == "revenue_vs_net_income" for i in result.errors)


def test_missing_required_metric_is_an_error():
    s = _healthy()
    del s.series["net_income"]
    result = validate(s)
    assert not result.ok
    assert any(i.check == "required_metrics" for i in result.errors)


def test_fiscal_gap_irregularity_warns_but_does_not_block():
    s = _healthy()
    s.series["revenue"] = [
        MetricPeriod("2023-09-30", "FY2023", 383.3e9, "x"),
        MetricPeriod("2025-09-27", "FY2025", 416.2e9, "x"),  # ~2 year gap
    ]
    result = validate(s)
    assert any(i.check == "period_alignment" for i in result.issues)
    assert result.ok  # warning only, does not block display


def test_identity_tolerates_minor_rounding():
    s = _healthy()
    s.series["total_equity"][-1] = MetricPeriod("2025-09-27", "FY2025", 73.7e9 * 1.005, "x")
    assert validate(s).ok


def test_quarterly_facts_are_excluded_from_annual_series():
    """Regression, found live on Realty Income: quarterly facts (90-91 day
    durations) are tagged form='10-K', fp='FY' and sit alongside the real
    365-day annual value. Filtering on form/fp alone mixes a $78M quarter
    into a series of $309M years, a plausible number that is simply wrong."""
    from asset_researcher.quant.series import build_metric_series
    from asset_researcher.sources.edgar.facts import Fact, RawXbrlFacts

    quarterly = Fact(
        start="2020-07-01", end="2020-09-30", val=77e6, accn="a",
        fy=2020, fp="FY", form="10-K", filed="2021-02-01", frame=None,
    )
    annual = Fact(
        start="2020-01-01", end="2020-12-31", val=309e6, accn="a",
        fy=2020, fp="FY", form="10-K", filed="2021-02-01", frame=None,
    )
    facts = RawXbrlFacts(
        cik=726728, entity_name="Test",
        concepts={"InterestExpense": {"USD": [quarterly, annual]}},
    )
    series = build_metric_series(
        facts, {"interest_expense": ["InterestExpense"]}, "reit", ["interest_expense"]
    )
    values = [p.value for p in series.series["interest_expense"]]
    assert values == [309e6], "quarterly fact leaked into the annual series"


def test_instant_balance_sheet_facts_are_not_duration_filtered():
    """Balance-sheet facts carry no start date; the duration check must
    exempt them or every balance sheet disappears."""
    from asset_researcher.quant.series import build_metric_series
    from asset_researcher.sources.edgar.facts import Fact, RawXbrlFacts

    instant = Fact(
        start=None, end="2025-09-27", val=359.2e9, accn="a",
        fy=2025, fp="FY", form="10-K", filed="2025-10-31", frame=None,
    )
    facts = RawXbrlFacts(cik=1, entity_name="T", concepts={"Assets": {"USD": [instant]}})
    series = build_metric_series(facts, {"total_assets": ["Assets"]}, "standard", ["total_assets"])
    assert series.series["total_assets"][0].value == 359.2e9


def _instant(end: str, val: float) -> "Fact":  # noqa: F821
    from asset_researcher.sources.edgar.facts import Fact

    return Fact(
        start=None, end=end, val=val, accn="a",
        fy=int(end[:4]), fp="FY", form="10-K", filed=f"{int(end[:4])+1}-01-01", frame=None,
    )


def test_composite_metric_sums_disjoint_concepts():
    """total_debt = LongTermDebt + CommercialPaper. Verified live on Apple:
    LongTermDebt alone ($90.7B) omits commercial paper ($8.0B), understating
    real total debt by ~8%."""
    from asset_researcher.quant.series import build_metric_series
    from asset_researcher.sources.edgar.facts import RawXbrlFacts

    facts = RawXbrlFacts(
        cik=320193, entity_name="Apple",
        concepts={
            "LongTermDebt": {"USD": [_instant("2025-09-27", 90.7e9)]},
            "CommercialPaper": {"USD": [_instant("2025-09-27", 8.0e9)]},
        },
    )
    series = build_metric_series(
        facts, {"total_debt": ["LongTermDebt", "CommercialPaper"]}, "standard", ["total_debt"]
    )
    assert series.series["total_debt"][0].value == pytest.approx(98.7e9)


def test_component_reported_in_only_one_year_does_not_create_a_phantom_period():
    """A component present in a single year must not add a period the primary
    concept doesn't cover, that period would contain only the fragment and
    read as a collapse in the series."""
    from asset_researcher.quant.series import build_metric_series
    from asset_researcher.sources.edgar.facts import RawXbrlFacts

    facts = RawXbrlFacts(
        cik=1, entity_name="T",
        concepts={
            "LongTermDebt": {"USD": [_instant("2024-09-28", 96.7e9), _instant("2025-09-27", 90.7e9)]},
            "CommercialPaper": {"USD": [_instant("2019-09-28", 6.0e9), _instant("2025-09-27", 8.0e9)]},
        },
    )
    series = build_metric_series(
        facts, {"total_debt": ["LongTermDebt", "CommercialPaper"]}, "standard", ["total_debt"]
    )
    ends = [p.end for p in series.series["total_debt"]]
    assert "2019-09-28" not in ends
    assert series.series["total_debt"][-1].value == pytest.approx(98.7e9)


# --- fiscal year labelling ----------------------------------------------


def test_a_period_label_comes_from_its_end_not_from_the_filing():
    """XBRL's `fy` identifies the fiscal year of the filing a fact appeared
    in, not of the period it covers. Verified against HP: the year ending
    2022-10-31 carries fy=2022 in its own 10-K and fy=2023 as the
    comparative in the next one. Since the most recently filed fact wins,
    trusting `fy` labelled every period a year late."""
    from asset_researcher.quant.series import _fiscal_labels

    labels = _fiscal_labels(["2023-10-31", "2024-10-31", "2025-10-31"])
    assert list(labels.values()) == ["FY2023", "FY2024", "FY2025"]


def test_a_year_end_in_the_first_days_of_january_belongs_to_the_prior_year():
    """A 52/53-week filer whose year ends on the Friday nearest 31 December
    calls the year ending 2021-01-01 fiscal 2020."""
    from asset_researcher.quant.series import _fiscal_labels

    assert _fiscal_labels(["2021-01-01"])["2021-01-01"] == "FY2020"


def test_a_retailers_late_january_year_end_keeps_the_end_year():
    """A fiscal year running February 2024 to January 2025 is called 2025 by
    the filers that use it, so the January rule cuts at the first week."""
    from asset_researcher.quant.series import _fiscal_labels

    assert _fiscal_labels(["2025-01-31"])["2025-01-31"] == "FY2025"


def test_a_52_week_year_crossing_new_year_does_not_collide_with_the_next():
    """Fiscal 2020 ending 2021-01-01 and fiscal 2021 ending 2021-12-31 both
    became "FY2021". Downstream code keys on the label, so the earlier year
    was overwritten and vanished from the report with no warning."""
    from asset_researcher.quant.series import _fiscal_labels

    labels = _fiscal_labels(["2021-01-01", "2021-12-31"])
    assert labels == {"2021-01-01": "FY2020", "2021-12-31": "FY2021"}


def test_a_genuine_label_collision_is_disambiguated_rather_than_merged():
    """A filer changing its year-end can report two annual periods ending in
    one calendar year. Both map to the same label, so the end date is added
    and the collision becomes visible rather than lossy."""
    from asset_researcher.quant.series import _fiscal_labels

    labels = _fiscal_labels(["2024-03-31", "2024-12-31"])
    assert len(set(labels.values())) == 2
    assert all(label.startswith("FY2024") for label in labels.values())
    assert any("2024-03-31" in label for label in labels.values())


# --- the derived metrics mean what they are named ------------------------


def test_every_declared_derived_metric_is_actually_computed():
    """canonical.yaml calls itself the documented source of truth for what
    each metric computes, so a declaration nothing implements is a false
    entry in the one file a reader would check."""
    from pathlib import Path

    import yaml

    from asset_researcher.quant.derived import compute_derived
    from asset_researcher.quant.series import MetricPeriod, MetricSeries

    declared = set(
        yaml.safe_load(
            Path("asset_researcher/config/metrics/canonical.yaml").read_text()
        )["derived"]
    )

    rich = MetricSeries(cik=1, sector="standard")
    for name in (
        "revenue", "cogs", "gross_profit", "operating_income", "net_income",
        "pretax_income", "income_tax_expense", "total_assets", "total_equity",
        "total_debt", "cash_and_equivalents", "current_assets",
        "current_liabilities", "operating_cash_flow", "capital_expenditures",
        "depreciation_amortization", "interest_expense",
        "net_interest_income", "noninterest_income", "noninterest_expense",
        "nonperforming_loans",
    ):
        rich.series[name] = [
            MetricPeriod("2025-09-30", "FY2025", 100e6, "a"),
            MetricPeriod("2024-09-30", "FY2024", 90e6, "a"),
        ]

    computed = set(compute_derived(rich))
    assert declared - computed == set(), (
        f"declared but never computed: {sorted(declared - computed)}"
    )


def test_return_on_invested_capital_is_unavailable_without_a_filed_tax_rate():
    """A return computed at a guessed tax rate is a number nobody can check,
    and the point of this layer is that every figure traces to a filing."""
    from asset_researcher.quant.derived import compute_derived
    from asset_researcher.quant.series import MetricPeriod, MetricSeries

    def _series(**metrics):
        s = MetricSeries(cik=1, sector="standard")
        for name, value in metrics.items():
            s.series[name] = [MetricPeriod("2025-09-30", "FY2025", value, "a")]
        return s

    untaxed = _series(
        operating_income=130e9, net_income=110e9,
        total_debt=100e9, total_equity=70e9, cash_and_equivalents=30e9,
        total_assets=360e9,
    )
    assert compute_derived(untaxed)["roic"] is None

    taxed = _series(
        operating_income=130e9, net_income=110e9,
        pretax_income=132e9, income_tax_expense=22e9,
        total_debt=100e9, total_equity=70e9, cash_and_equivalents=30e9,
        total_assets=360e9,
    )
    roic = compute_derived(taxed)["roic"]
    # NOPAT of 130 * (1 - 22/132) over invested capital of 140.
    assert roic == pytest.approx(130e9 * (1 - 22 / 132) / 140e9)
    # Measurably different from the net income version it replaced.
    assert roic != pytest.approx(110e9 / 140e9)
