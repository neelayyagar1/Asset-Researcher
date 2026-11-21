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
        """Names only. Kept for callers that want the bare list."""
        return sorted(self.concepts.keys())

    def concept_listing(self) -> list[str]:
        """Each concept with the last year the filer reported it.

        A bare list of names cannot distinguish a tag abandoned in 2011
        from the one the filer uses now, and the resolver has no other
        signal to go on. It chose `LongTermDebtNoncurrent` for ADP's
        total debt - last filed in FY2011 at $37m, against real debt
        near $3bn - and every figure bridged across net debt inherited
        that. Lumen's capital expenditure went the same way, stopping at
        FY2013.

        Still cheap: one integer per tag, no values.
        """
        out = []
        for name in sorted(self.concepts.keys()):
            years = [
                int(fact.end[:4])
                for facts in self.concepts[name].values()
                for fact in facts
                if fact.end and len(fact.end) >= 4 and fact.end[:4].isdigit()
            ]
            out.append(f"{name} (through {max(years)})" if years else name)
        return out


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
