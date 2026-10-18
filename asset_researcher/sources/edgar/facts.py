"""Raw XBRL fact fetch, companyfacts JSON, parsed into a plain structure.

Deliberately does no interpretation: this module knows nothing about canonical
metric names or which concept means "revenue". That's quant/resolve.py's job.
Keeping this layer dumb means it's trivially correct and the LLM-assisted
resolution logic is the only place a mapping mistake can happen.
"""

from __future__ import annotations

from dataclasses import dataclass

from asset_researcher.sources.edgar.client import EdgarClient
from asset_researcher.sources.edgar.resolve import cik_to_padded

_FACTS_TTL_SECONDS = 6 * 3600


@dataclass(frozen=True)
class Fact:
    start: str | None  # None for instant (balance-sheet) facts; set for durations
    end: str
    val: float
    accn: str  # accession number of the filing that reported this
    fy: int
    fp: str  # "FY", "Q1", "Q2", "Q3", "Q4"
    form: str  # "10-K" or "10-Q"
    filed: str
    frame: str | None  # e.g. "CY2024", present for standardized annual/quarterly periods


@dataclass(frozen=True)
class RawXbrlFacts:
    cik: int
    entity_name: str
    # concept name -> unit ("USD", "shares", "USD/shares", ...) -> facts
    concepts: dict[str, dict[str, list[Fact]]]

    def available_concept_names(self) -> list[str]:
        """Names only, this is what gets sent to the LLM for concept
        resolution. Cheap: no values, just the ~500 tag names a filer uses."""
        return sorted(self.concepts.keys())


def _parse_fact(raw: dict) -> Fact:
    return Fact(
        start=raw.get("start"),
        end=raw["end"],
        val=raw["val"],
        accn=raw["accn"],
        fy=raw["fy"],
        fp=raw["fp"],
        form=raw["form"],
        filed=raw["filed"],
        frame=raw.get("frame"),
    )


def get_raw_facts(client: EdgarClient, cik: int) -> RawXbrlFacts:
    padded = cik_to_padded(cik)
    url = f"https://data.sec.gov/api/xbrl/companyfacts/{padded}.json"
    data = client.get_json(url, f"companyfacts-{padded}", _FACTS_TTL_SECONDS)

    us_gaap = data.get("facts", {}).get("us-gaap", {})
    concepts: dict[str, dict[str, list[Fact]]] = {}
    for concept_name, concept_data in us_gaap.items():
        units = concept_data.get("units", {})
        concepts[concept_name] = {
            unit: [_parse_fact(f) for f in facts_list]
            for unit, facts_list in units.items()
        }

    return RawXbrlFacts(
        cik=cik, entity_name=data.get("entityName", ""), concepts=concepts
    )
