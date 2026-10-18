"""SIC code -> *financial statement model*, not business sector.

Free and deterministic: the submissions API returns a filer's SIC code in the
same call that gives us its filing index (ARCHITECTURE.md §3, verified, not
assumed).

**This is not a business-sector taxonomy and must not be displayed as one.**
It answers exactly one question: which financial metrics and health scores
are meaningful for this filer's statements? Apple, Coca-Cola and Ford all
share the "standard" model, revenue, COGS, gross profit, a conventional
balance sheet, despite being in three different GICS sectors. Banks are
separate because their statements are structurally different (net interest
margin, loan-loss provisions), REITs because of FFO, and so on.

An earlier version named the default class "industrial", which read as a
claim that Apple is an industrials company. For anything user-facing, use
`display_industry()`, driven by the SIC description and Finnhub's industry
label, and keep this class internal.
"""

from __future__ import annotations

from asset_researcher.config import Settings

# The filer's statement model: standard | financial | reit | energy | biotech.
# Determines applicable metrics and scores. NOT a business-sector label.
SectorClass = str


def classify_sic(sic: str, settings: Settings) -> SectorClass:
    if not sic or not sic.isdigit():
        return settings.sectors.default

    code = int(sic)
    for sector_name, ranges in settings.sectors.ranges.items():
        for low, high in ranges:
            if low <= code <= high:
                return sector_name
    return settings.sectors.default


def display_industry(sic_description: str, finnhub_industry: str | None) -> str:
    """The business description shown to a reader, as opposed to the
    statement model returned by classify_sic().

    Prefers Finnhub's label ("Technology") because it matches how an analyst
    talks, and appends the SEC's own SIC description for provenance, since
    that is what the filing itself is classified under.
    """
    sic_part = sic_description.strip()
    if finnhub_industry and sic_part:
        return f"{finnhub_industry} ({sic_part})"
    return finnhub_industry or sic_part or "Not classified"
