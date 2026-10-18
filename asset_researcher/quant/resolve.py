"""LLM-assisted XBRL concept resolution (ARCHITECTURE.md §5).

The model sees only concept NAMES (never values) and maps them onto the
canonical metric taxonomy. Cached forever per company once resolved, a bad
mapping is fixed with a human-authored override, not by re-running
resolution. This is the one place a wrong number could sneak in via a bad
mapping, which is exactly why quant/validate.py exists as an independent,
deterministic check downstream of this.
"""

from __future__ import annotations

import hashlib

from pathlib import Path

import yaml
from pydantic import BaseModel

from asset_researcher.config import Settings
from asset_researcher.config.prompt_loader import load_prompt
from asset_researcher.llm.provider import LLMProvider
from asset_researcher.quant.metrics_config import line_items_for_sector
from asset_researcher.sources._cache import DiskCache
from asset_researcher.sources.edgar.facts import RawXbrlFacts

_OVERRIDES_DIR = Path(__file__).parent.parent / "config" / "overrides"


class _MetricMapping(BaseModel):
    canonical_metric: str
    # A list, because some canonical metrics are the sum of several disjoint
    # XBRL concepts. total_debt is the motivating case: Apple's `LongTermDebt`
    # ($90.7B) excludes `CommercialPaper` ($8.0B), so a single-concept mapping
    # understates real total debt by ~8%. The prompt carries an explicit
    # warning about double-counting, since overlapping concepts would produce
    # a confidently wrong figure.
    xbrl_concepts: list[str]
    confidence: str  # "high" | "medium" | "low", not filtered on yet; see validate.py


class _ConceptResolutionResult(BaseModel):
    mappings: list[_MetricMapping]


def _load_override(cik: int) -> dict[str, list[str]]:
    """Overrides accept either a single concept name or a list, so a human
    pinning a fix doesn't have to remember which form the metric uses."""
    path = _OVERRIDES_DIR / f"{cik:010d}.yaml"
    if not path.exists():
        return {}
    with open(path) as f:
        data = yaml.safe_load(f)
    if not data:
        return {}
    return {k: ([v] if isinstance(v, str) else list(v)) for k, v in data.items()}


def _call_llm(
    provider: LLMProvider,
    settings: Settings,
    sector: str,
    available_concepts: list[str],
) -> dict[str, list[str]]:
    line_items = line_items_for_sector(sector)
    canonical_list = "\n".join(f"- {li.name}: {li.label}" for li in line_items)
    concepts_list = "\n".join(f"- {c}" for c in available_concepts)

    template = load_prompt("concept_resolution.md")
    user_prompt = template.format(
        canonical_metrics=canonical_list, available_concepts=concepts_list
    )

    result = provider.complete_structured(
        system="You are a precise financial-statement analyst.",
        user=user_prompt,
        output_model=_ConceptResolutionResult,
        effort=settings.llm.effort["concept_resolution"],
        max_tokens=4096,
    )

    return {
        m.canonical_metric: m.xbrl_concepts
        for m in result.mappings
        if m.xbrl_concepts
    }


def _taxonomy_fingerprint(sector: str) -> str:
    """A short, stable digest of the metric names requested for a sector."""
    names = sorted(li.name for li in line_items_for_sector(sector))
    return hashlib.sha256("|".join(names).encode("utf-8")).hexdigest()[:12]


def resolve_concepts(
    provider: LLMProvider,
    settings: Settings,
    cik: int,
    sector: str,
    facts: RawXbrlFacts,
) -> dict[str, list[str]]:
    """canonical_metric_name -> the XBRL concepts that compose it.

    A metric may map to several concepts, which series.py sums: Apple's total
    debt is LongTermDebtNoncurrent plus CommercialPaper plus the current
    portion. The return type is a list per metric for that reason, and the
    annotation said `str` for both this function and `_call_llm` while both
    returned lists.

    Missing canonical metrics are simply absent from the result; callers
    decide how to handle an absence.
    """
    cache = DiskCache(settings.resolved_cache_dir(settings.quant.resolution_cache_dir))
    # The key carries a fingerprint of the metrics being asked for, so adding
    # one to config/metrics/canonical.yaml re-resolves rather than returning a
    # mapping that predates it.
    #
    # Found the hard way. Short-term investments and long-term marketable
    # securities were added to the taxonomy to fix net debt, every caller was
    # updated, the basis string was rewritten to say the securities were
    # netted, and the figure did not move: the cache never expires, so no
    # company already resolved was ever asked about the new concepts.
    cache_key = f"cik-{cik}-{_taxonomy_fingerprint(sector)}"

    cached = cache.get(cache_key, ttl_seconds=None)  # forever, see module docstring
    mapping: dict[str, list[str]] | None = None
    if cached is not None:
        mapping = yaml.safe_load(cached.decode("utf-8")) or None

    if mapping is None:
        mapping = _call_llm(
            provider, settings, sector, facts.available_concept_names()
        )
        # Only a non-empty result is cached, and the cache never expires. One
        # call that came back with no mappings would otherwise write an empty
        # dict to disk permanently, and that company could never produce a
        # figure again until someone found and deleted the cache file.
        if mapping:
            cache.put(cache_key, yaml.safe_dump(mapping).encode("utf-8"))

    override = _load_override(cik)
    mapping.update(override)  # human pins always win, per config/overrides/README.md
    return mapping
