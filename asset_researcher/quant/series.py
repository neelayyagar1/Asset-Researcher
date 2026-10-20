"""Combines raw XBRL facts + resolved concept mapping into a clean, canonical
multi-year metric series, the thing everything else (validation, derived
metrics, health scores, the financial table) actually reads.

Period extraction deliberately does NOT filter on XBRL's `frame` field.
Verified live against Apple's Assets concept during build: the most recent
fiscal year's balance-sheet facts report with frame=None in their own 10-K,
and only get a populated frame (e.g. "CY2024Q3I") a year later when they
reappear as the prior-year comparative in the *next* 10-K. Filtering on
`frame is not None`, which looks correct and works fine for income-statement
facts like revenue, would silently drop the single most recent balance
sheet from every report. Instead we group by the fact's `end` date directly,
which is always present, and dedupe by picking whichever fact for that
end-date was filed most recently (later filings are the most authoritative
restated value for a given period).

Only annual (form="10-K", fp="FY") periods are extracted for v1's financial
table, validation, and health scores, quarterly XBRL data is available for
free from the same payload but isn't wired into MetricSeries yet; adding it
is a matter of relaxing the form/fp filter below, not a new fetch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from asset_researcher.sources.edgar.facts import Fact, RawXbrlFacts


@dataclass(frozen=True)
class MetricPeriod:
    end: str  # ISO date, e.g. "2025-09-27"
    frame_label: str  # display label, e.g. "FY2025", derived from end's year
    value: float
    accn: str  # accession number of the filing this value came from


@dataclass
class MetricSeries:
    cik: int
    sector: str
    series: dict[str, list[MetricPeriod]] = field(default_factory=dict)
    # Canonical metrics with a resolved XBRL concept but zero extractable
    # annual facts (concept exists, no 10-K FY data under it, rare but
    # possible for a newly-added tag).
    resolved_but_empty: list[str] = field(default_factory=list)
    # Canonical metrics with no resolved concept at all.
    unmapped: list[str] = field(default_factory=list)


def _is_annual_duration(fact: Fact) -> bool:
    """Duration facts must actually span a year.

    form="10-K" and fp="FY" are NOT sufficient. Verified on Realty Income's
    filings: quarterly interest-expense facts (90 and 91 day durations) are
    tagged form=10-K, fp=FY and sit alongside the real 365-day annual value.
    Without this check a single series mixes a $78M quarter with a $309M
    year, a plausible-looking number that is simply wrong, and the kind of
    error no reader would catch by eye.

    Instant facts (balance-sheet items) carry no start date and are exempt.
    """
    if fact.start is None:
        return True
    try:
        span = (date.fromisoformat(fact.end) - date.fromisoformat(fact.start)).days
    except ValueError:
        return False
    return 330 <= span <= 400


def _annual_facts_by_end_date(facts_by_unit: dict[str, list[Fact]]) -> dict[str, Fact]:
    """One fact per end-date, preferring USD, falling back to any other unit
    present (e.g. "shares" for share-count concepts). Dedupes by keeping the
    most-recently-filed fact for each end-date."""
    unit = "USD" if "USD" in facts_by_unit else next(iter(facts_by_unit), None)
    if unit is None:
        return {}

    by_end: dict[str, Fact] = {}
    for f in facts_by_unit[unit]:
        # startswith, so 10-K/A and 10-KT count. The policy here is that
        # the most recently filed value for a period wins, which is the
        # restated one; an exact match on "10-K" filtered out amendments,
        # which are the vehicle restatements arrive in. A filer that
        # restated via 10-K/A kept showing the original until the figure
        # reappeared as a comparative a year later.
        if not f.form.startswith("10-K") or f.fp != "FY":
            continue
        if not _is_annual_duration(f):
            continue
        existing = by_end.get(f.end)
        if existing is None or f.filed > existing.filed:
            by_end[f.end] = f
    return by_end


def build_metric_series(
    facts: RawXbrlFacts,
    mapping: dict[str, list[str]],
    sector: str,
    canonical_metric_names: list[str],
    years: int = 5,
) -> MetricSeries:
    """Builds the canonical series. A metric may map to several XBRL concepts
    (e.g. total_debt = LongTermDebt + CommercialPaper), in which case values
    are summed per period."""
    result = MetricSeries(cik=facts.cik, sector=sector)

    for canonical_name in canonical_metric_names:
        concept_names = mapping.get(canonical_name) or []
        if not concept_names:
            result.unmapped.append(canonical_name)
            continue

        # end-date -> (summed value, accession of the primary component)
        combined: dict[str, tuple[float, str]] = {}
        primary_ends: set[str] | None = None

        for concept_name in concept_names:
            facts_by_unit = facts.concepts.get(concept_name)
            if not facts_by_unit:
                continue
            by_end = _annual_facts_by_end_date(facts_by_unit)
            if not by_end:
                continue
            if primary_ends is None:
                # The first concept that has data defines which periods this
                # metric covers. Later components only add to periods that
                # already exist, otherwise a component reported in just one
                # year would create a period where the metric is really just
                # that fragment, which reads as a collapse in the series.
                primary_ends = set(by_end)
                for end, f in by_end.items():
                    combined[end] = (f.val, f.accn)
            else:
                for end, f in by_end.items():
                    if end in combined:
                        value, accn = combined[end]
                        combined[end] = (value + f.val, accn)

        if not combined:
            result.resolved_but_empty.append(canonical_name)
            continue

        ordered = sorted(combined.items())
        labels = _fiscal_labels([end for end, _ in ordered])
        result.series[canonical_name] = [
            MetricPeriod(end=end, frame_label=labels[end], value=value, accn=accn)
            for end, (value, accn) in ordered
        ][-years:]

    return result


def _fiscal_labels(ends: list[str]) -> dict[str, str]:
    """A display label per period end, guaranteed unique.

    The label used to be the calendar year of the period end. That breaks on
    any 52/53-week filer whose year-end floats across 31 December: fiscal
    2020 ending 2021-01-01 and fiscal 2021 ending 2021-12-31 both became
    "FY2021". Downstream code keys its lookup on the label, so the earlier
    year was overwritten and vanished from the report with no column, no gap
    and no validation warning. A table that is missing a year while looking
    complete is the worst failure mode available to this project.

    **The fact's own `fy` field cannot be used for this.** It identifies the
    fiscal year of the *filing* the fact appeared in, not of the period the
    fact covers. Verified against HP: the year ending 2022-10-31 carries
    fy=2022 in its own 10-K and fy=2023 when it reappears as the prior-year
    comparative in the next one. Because the most recently filed fact wins,
    taking `fy` labelled every period a year late, and every comparative
    column in the report inherited the latest fiscal year.

    So the label comes from the period end, with one adjustment. A year
    ending in the first days of January closed a fiscal year that ran
    through the previous calendar year, and the filer names it for that
    year. A year ending late in January does not: a retailer's fiscal 2025
    runs February 2024 to January 2025 and is called 2025. The cut is the
    first week.

    Any label still colliding is disambiguated with its end date, so a
    collision becomes visible rather than lossy.
    """
    provisional: dict[str, str] = {}
    for end in ends:
        year = int(end[:4])
        if end[5:7] == "01" and int(end[8:10]) <= 7:
            year -= 1
        provisional[end] = f"FY{year}"

    counts: dict[str, int] = {}
    for label in provisional.values():
        counts[label] = counts.get(label, 0) + 1

    return {
        end: (label if counts[label] == 1 else f"{label} (to {end})")
        for end, label in provisional.items()
    }
