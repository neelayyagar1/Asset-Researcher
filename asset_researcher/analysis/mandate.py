"""The investor mandate profile, free text in, structured profile out.

"Actionable insights" are meaningless without knowing how the reader makes
money. Margin compression is a thesis question to a three-year holder, a
positioning question to an options desk, and noise to an income mandate. A
report that ignores this produces generic findings, and a PM reading generic
findings concludes the tool does not understand how they trade.

**Why free text rather than a dropdown.** Real mandates are idiosyncratic and
combinatorial; no fixed taxonomy covers them, and a wrong taxonomy signals
that the author does not know the domain. The model parses prose into
structure, the user confirms and edits, and the confirmed profile is what
gets used, never a silent guess.

**The objectivity boundary** (ARCHITECTURE.md §4). The profile shapes emphasis,
ordering, and framing. It never changes which figures are reported, which
citations are attached, or which discrepancies the reconciliation detects.
Without that rule this becomes a machine for telling people what they want to
hear, which for a research tool is worse than useless.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from asset_researcher.config.prompt_loader import load_prompt
from asset_researcher.llm.provider import LLMProvider

_PRESETS_PATH = (
    Path(__file__).resolve().parent.parent / "config" / "mandates" / "presets.yaml"
)

HORIZON_BUCKETS = ("days", "weeks", "quarters", "years", "multi_year")


class MandateProfile(BaseModel):
    """Parsed mandate. Every field is editable by the user after parsing."""

    horizon_bucket: str = "quarters"
    horizon_note: str = ""
    instruments: list[str] = Field(default_factory=lambda: ["equity_long"])
    concentration: str = "unspecified"
    style_tags: list[str] = Field(default_factory=list)
    key_metrics: list[str] = Field(default_factory=list)
    thesis_killers: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    # What the model filled in without direct support. Surfaced in the
    # confirmation step so the user can correct it rather than discover it
    # later in a report written against assumptions they never made.
    assumptions: list[str] = Field(default_factory=list)

    @property
    def is_short_capable(self) -> bool:
        return "equity_short" in self.instruments

    @property
    def uses_options(self) -> bool:
        return "options" in self.instruments or "derivatives" in self.instruments

    @property
    def is_long_horizon(self) -> bool:
        return self.horizon_bucket in ("years", "multi_year")

    def summary(self) -> str:
        """One line, for showing the reader what the report was written for."""
        parts = [self.horizon_note or self.horizon_bucket.replace("_", "-")]
        if self.style_tags:
            parts.append("/".join(self.style_tags[:3]))
        if self.instruments:
            parts.append(", ".join(i.replace("equity_", "") for i in self.instruments))
        return " · ".join(p for p in parts if p)

    def briefing(self) -> str:
        """The block handed to Call B.

        Written as context about the reader, never as instruction about what
        to conclude, the wording matters, because a prompt that says "this
        reader is bullish" would produce exactly the bias this design
        forbids.
        """
        lines = [
            "The reader's mandate, which determines what is relevant to them:",
            f"  - Holding period: {self.horizon_note or self.horizon_bucket}",
            f"  - Instruments: {', '.join(self.instruments) or 'unspecified'}",
            f"  - Portfolio construction: {self.concentration}",
        ]
        if self.style_tags:
            lines.append(f"  - Style: {', '.join(self.style_tags)}")
        if self.key_metrics:
            lines.append(f"  - Metrics they watch: {', '.join(self.key_metrics)}")
        if self.thesis_killers:
            lines.append(f"  - What makes them exit: {', '.join(self.thesis_killers)}")
        if self.constraints:
            lines.append(f"  - Constraints: {', '.join(self.constraints)}")

        lines.append("")
        lines.append(
            "Use this to decide what to surface first and how to frame risk "
            "and catalysts. It must not change which facts you report, which "
            "figures you cite, or which discrepancies you disclose. A finding "
            "that is inconvenient for this mandate is still reported."
        )
        return "\n".join(lines)


@dataclass(frozen=True)
class MandatePreset:
    id: str
    name: str
    description: str


def load_presets() -> list[MandatePreset]:
    data = yaml.safe_load(_PRESETS_PATH.read_text(encoding="utf-8")) or {}
    return [
        MandatePreset(
            id=p["id"], name=p["name"], description=" ".join(p["description"].split())
        )
        for p in data.get("presets", [])
    ]


def default_profile() -> MandateProfile:
    """Used when a reader declines to describe a mandate at all.

    Deliberately neutral rather than a stand-in for a typical fund: the
    assumptions list says plainly that nothing was supplied, so a report
    never implies it was tailored when it was not.
    """
    return MandateProfile(
        assumptions=[
            "No mandate was provided; the report is written for a generalist "
            "fundamental reader with a multi-quarter horizon."
        ]
    )


def parse_mandate(
    text: str,
    llm: LLMProvider,
    effort: str = "low",
    max_tokens: int = 4_000,
) -> MandateProfile:
    """Free text -> structured profile. Schema-enforced, no citations."""
    if not text or not text.strip():
        return default_profile()

    profile = llm.complete_structured(
        system=load_prompt("mandate_parse.md"),
        user=f"Mandate description:\n\n{text.strip()}",
        output_model=MandateProfile,
        effort=effort,
        max_tokens=max_tokens,
    )

    # The model is asked for a bucket from a fixed set; a value outside it
    # would silently break horizon-dependent framing downstream.
    if profile.horizon_bucket not in HORIZON_BUCKETS:
        profile.assumptions.append(
            f"Unrecognised horizon '{profile.horizon_bucket}' was replaced with "
            f"'quarters'; please correct it."
        )
        profile.horizon_bucket = "quarters"

    return profile
