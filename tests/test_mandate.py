"""Mandate profile: presets, defaults, and the objectivity boundary."""

from __future__ import annotations

from asset_researcher.analysis.mandate import (
    HORIZON_BUCKETS,
    MandateProfile,
    default_profile,
    load_presets,
    parse_mandate,
)


class _FakeLLM:
    """Returns a fixed profile; records what it was asked."""

    def __init__(self, profile: MandateProfile):
        self._profile = profile
        self.calls: list[dict] = []

    def complete_structured(self, **kw):
        self.calls.append(kw)
        return self._profile

    def complete_cited(self, **kw):  # pragma: no cover - not used here
        raise NotImplementedError


def test_presets_load_and_are_usable_as_prefill_text():
    presets = load_presets()
    assert len(presets) >= 4
    ids = {p.id for p in presets}
    assert {"long_only_quality", "long_short_equity", "event_driven"} <= ids
    for p in presets:
        # The description pre-fills the textarea, so it must read as prose a
        # PM would actually write, not as a label.
        assert len(p.description) > 100
        assert "\n" not in p.description


def test_empty_text_returns_the_default_without_calling_the_model():
    llm = _FakeLLM(MandateProfile())
    profile = parse_mandate("   ", llm)
    assert llm.calls == []
    assert profile.assumptions  # says plainly that nothing was supplied


def test_default_profile_admits_that_nothing_was_supplied():
    """A report must never imply it was tailored when no mandate was given."""
    assumptions = " ".join(default_profile().assumptions).lower()
    assert "no mandate" in assumptions


def test_unrecognised_horizon_is_corrected_and_disclosed():
    """A bucket outside the fixed set would silently break horizon-dependent
    framing downstream."""
    llm = _FakeLLM(MandateProfile(horizon_bucket="fortnightly"))
    profile = parse_mandate("something", llm)
    assert profile.horizon_bucket == "quarters"
    assert any("fortnightly" in a for a in profile.assumptions)


def test_valid_horizon_is_left_alone():
    for bucket in HORIZON_BUCKETS:
        llm = _FakeLLM(MandateProfile(horizon_bucket=bucket))
        assert parse_mandate("x", llm).horizon_bucket == bucket


def test_capability_flags_drive_framing_not_facts():
    long_short = MandateProfile(instruments=["equity_long", "equity_short"])
    assert long_short.is_short_capable

    options = MandateProfile(instruments=["equity_long", "options"])
    assert options.uses_options
    assert not options.is_short_capable

    assert MandateProfile(horizon_bucket="multi_year").is_long_horizon
    assert not MandateProfile(horizon_bucket="weeks").is_long_horizon


def test_briefing_states_the_objectivity_boundary_explicitly():
    """The briefing is what Call B actually reads. If it ever stops saying
    that inconvenient findings are still reported, the mandate becomes a
    bias vector."""
    briefing = MandateProfile(
        horizon_note="3-5 years",
        style_tags=["quality"],
        thesis_killers=["capital allocation turns value-destructive"],
    ).briefing()

    assert "must not change which facts" in briefing
    assert "still reported" in briefing
    assert "3-5 years" in briefing
    assert "capital allocation turns value-destructive" in briefing


def test_briefing_omits_sections_the_user_never_supplied():
    """Empty fields are left out rather than rendered as empty prompts, which
    would read as 'the user cares about nothing here'."""
    briefing = MandateProfile().briefing()
    assert "What makes them exit" not in briefing
    assert "Metrics they watch" not in briefing


def test_summary_is_a_single_readable_line():
    summary = MandateProfile(
        horizon_note="3-5 years",
        style_tags=["quality", "compounder"],
        instruments=["equity_long"],
    ).summary()
    assert "3-5 years" in summary
    assert "\n" not in summary
