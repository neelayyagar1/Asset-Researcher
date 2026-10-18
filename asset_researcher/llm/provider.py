"""LLM provider interface.

Every analysis module calls the model through this interface, never through
the Anthropic SDK directly. That is the entire mechanism by which "self-hosted
is a swap, not a rewrite" (ARCHITECTURE.md §3, §10) stays true, a fund that
requires an on-prem model needs a new class implementing this interface and
nothing else changes.

Two methods, matching the two call shapes the design requires (§6): citations
and structured output cannot be combined in one request, so they are two
distinct methods rather than one method with a flag.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel

from asset_researcher.sources.base import SourceDocument

T = TypeVar("T", bound=BaseModel)

Effort = str  # "low" | "medium" | "high" | "xhigh" | "max"


@dataclass(frozen=True)
class Citation:
    """One citation attached to a span of generated text.

    The offsets are the whole point: `cited_text` alone proves only that the
    model produced a plausible-looking quote, whereas start/end let the
    verifier check that the quote actually appears at that position in the
    exact document that was sent (grounding/verify.py).
    """

    cited_text: str
    document_index: int  # position in the documents list passed to the call
    document_title: str | None
    start_char_index: int | None
    end_char_index: int | None


@dataclass(frozen=True)
class CitedSpan:
    text: str
    # A span may carry several citations, or none. All are kept: dropping the
    # extras would hide a claim that rests on more than one source, and
    # discarding uncited spans would hide exactly what the coverage check
    # exists to surface.
    citations: list[Citation]

    @property
    def is_cited(self) -> bool:
        return bool(self.citations)


@dataclass(frozen=True)
class CitedResponse:
    spans: list[CitedSpan]

    @property
    def full_text(self) -> str:
        return "".join(s.text for s in self.spans)

    @property
    def all_citations(self) -> list[Citation]:
        return [c for span in self.spans for c in span.citations]


class LLMProvider(ABC):
    @abstractmethod
    def complete_structured(
        self,
        *,
        system: str,
        user: str,
        output_model: type[T],
        effort: Effort,
        max_tokens: int,
    ) -> T:
        """Schema-enforced call, no citations. Used for concept resolution,
        mandate parsing, and reconciliation (Call B)."""

    @abstractmethod
    def complete_cited(
        self,
        *,
        system: str,
        documents: list[SourceDocument],
        user: str,
        effort: Effort,
        max_tokens: int,
    ) -> CitedResponse:
        """Citations-enabled call, no structured output. Used for Call A
        (narrative sections). Every returned span traces back to a specific
        document and offset, see grounding/citations.py for how that gets
        turned into verifiable Claim objects."""
