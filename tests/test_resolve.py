"""Concept resolution plumbing, caching and override precedence, tested
with a fake provider so no API key or network is needed."""

from pathlib import Path

import yaml

from asset_researcher.config import get_settings
from asset_researcher.quant.resolve import _ConceptResolutionResult, _MetricMapping, resolve_concepts
from asset_researcher.sources.edgar.facts import RawXbrlFacts


class _FakeProvider:
    """Records how many times the model was actually called, so the cache
    behaviour can be asserted rather than assumed."""

    def __init__(self, mappings: dict[str, list[str]]):
        self.call_count = 0
        self._mappings = mappings

    def complete_structured(self, *, system, user, output_model, effort, max_tokens):
        self.call_count += 1
        return _ConceptResolutionResult(
            mappings=[
                _MetricMapping(canonical_metric=k, xbrl_concepts=v, confidence="high")
                for k, v in self._mappings.items()
            ]
        )

    def complete_cited(self, **kwargs):  # pragma: no cover - not used here
        raise NotImplementedError


def _facts() -> RawXbrlFacts:
    return RawXbrlFacts(cik=999999, entity_name="Test Co", concepts={"Revenues": {}})


def _clear_cache(cik: int) -> None:
    settings = get_settings()
    # Globbed, because the key carries a fingerprint of the metric taxonomy
    # after the company id: `cik-999999-a1b2c3d4e5f6.body`.
    cache_dir = Path(settings.resolved_cache_dir(settings.quant.resolution_cache_dir))
    for p in cache_dir.glob(f"cik-{cik}*"):
        p.unlink()


def test_resolution_result_is_cached_and_not_recomputed():
    settings = get_settings()
    _clear_cache(999999)
    provider = _FakeProvider({"revenue": ["Revenues"], "net_income": ["NetIncomeLoss"]})

    first = resolve_concepts(provider, settings, 999999, "standard", _facts())
    second = resolve_concepts(provider, settings, 999999, "standard", _facts())

    assert first == second
    assert first["revenue"] == ["Revenues"]
    # Cached forever per company (ARCHITECTURE.md §6), a second report on the
    # same company must not pay for resolution again.
    assert provider.call_count == 1
    _clear_cache(999999)


def test_empty_concept_lists_are_dropped_not_stored():
    settings = get_settings()
    _clear_cache(999998)
    provider = _FakeProvider({"revenue": ["Revenues"], "cogs": []})

    mapping = resolve_concepts(provider, settings, 999998, "standard", _facts())

    assert "revenue" in mapping
    assert "cogs" not in mapping  # unmapped, rather than mapped to None
    _clear_cache(999998)


def test_human_override_wins_over_model_mapping(tmp_path, monkeypatch):
    """A wrong mapping is fixed by pinning it in config/overrides, never by
    patching output downstream (config/overrides/README.md)."""
    import asset_researcher.quant.resolve as resolve_mod

    settings = get_settings()
    _clear_cache(999997)
    monkeypatch.setattr(resolve_mod, "_OVERRIDES_DIR", tmp_path)
    (tmp_path / f"{999997:010d}.yaml").write_text(
        yaml.safe_dump({"revenue": "PinnedRevenueConcept"})
    )
    provider = _FakeProvider({"revenue": ["ModelChoseThis"]})

    mapping = resolve_concepts(provider, settings, 999997, "standard", _facts())

    assert mapping["revenue"] == ["PinnedRevenueConcept"]
    _clear_cache(999997)


def test_adding_a_metric_to_the_taxonomy_re_resolves_rather_than_reusing():
    """The cache never expires, so a mapping made before a metric existed
    would be returned forever and the new metric would silently never
    resolve. Found when short-term and long-term investments were added to
    fix net debt: every caller was updated, the basis string was rewritten
    to say the securities were netted, and the figure did not move."""
    from asset_researcher.quant.resolve import _taxonomy_fingerprint

    standard = _taxonomy_fingerprint("standard")
    assert standard == _taxonomy_fingerprint("standard")  # stable
    assert standard != _taxonomy_fingerprint("financial")  # different metrics
    assert len(standard) == 12
