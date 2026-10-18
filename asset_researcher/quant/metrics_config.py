"""Loads config/metrics/canonical.yaml and health_scores.yaml, and filters
by sector. This is the single place that reads those files, concept
resolution, derived metrics, and health scores all go through here rather
than each parsing YAML independently."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

_METRICS_DIR = Path(__file__).parent.parent / "config" / "metrics"


@dataclass(frozen=True)
class LineItemDef:
    name: str
    label: str
    sectors: list[str]

    def applies_to(self, sector: str) -> bool:
        return "all" in self.sectors or sector in self.sectors


@dataclass(frozen=True)
class DerivedDef:
    name: str
    label: str
    sectors: list[str]
    formula: str

    def applies_to(self, sector: str) -> bool:
        return "all" in self.sectors or sector in self.sectors


@dataclass(frozen=True)
class HealthScoreDef:
    name: str
    label: str
    citation: str
    sectors_applicable: list[str]
    raw: dict  # formula/components/tests/bands, score-specific, read by scores.py

    def applies_to(self, sector: str) -> bool:
        return sector in self.sectors_applicable


@lru_cache(maxsize=1)
def _load_canonical() -> dict:
    with open(_METRICS_DIR / "canonical.yaml") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def _load_health_scores() -> dict:
    with open(_METRICS_DIR / "health_scores.yaml") as f:
        return yaml.safe_load(f)


def line_items_for_sector(sector: str) -> list[LineItemDef]:
    raw = _load_canonical()["line_items"]
    defs = [LineItemDef(name=k, label=v["label"], sectors=v["sectors"]) for k, v in raw.items()]
    return [d for d in defs if d.applies_to(sector)]


def derived_for_sector(sector: str) -> list[DerivedDef]:
    raw = _load_canonical()["derived"]
    defs = [
        DerivedDef(name=k, label=v["label"], sectors=v["sectors"], formula=v["formula"])
        for k, v in raw.items()
    ]
    return [d for d in defs if d.applies_to(sector)]


def health_scores_for_sector(sector: str) -> list[HealthScoreDef]:
    raw = _load_health_scores()
    defs = [
        HealthScoreDef(
            name=k,
            label=v["label"],
            citation=v["citation"],
            sectors_applicable=v["sectors_applicable"],
            raw=v,
        )
        for k, v in raw.items()
    ]
    return [d for d in defs if d.applies_to(sector)]


def all_health_score_defs() -> list[HealthScoreDef]:
    """Unfiltered, used to report 'not meaningful for this sector' explicitly
    for scores that exist but don't apply, rather than omitting them silently."""
    raw = _load_health_scores()
    return [
        HealthScoreDef(
            name=k,
            label=v["label"],
            citation=v["citation"],
            sectors_applicable=v["sectors_applicable"],
            raw=v,
        )
        for k, v in raw.items()
    ]
