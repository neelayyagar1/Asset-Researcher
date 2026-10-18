"""Shared types for everything that produces source material for a report.

Every document that ends up in the LLM context, a filing section, a proxy
extract, a user-supplied URL, is wrapped as a SourceDocument before it goes
anywhere near a prompt. The trust tier travels with it end to end (design
plan §4) so the renderer can label Tier C content and the system prompt can
tell the model what authority each block carries.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Tier(str, Enum):
    """A, authoritative (filings, XBRL): any claim, numbers only from here.
    B, primary (company IR, press releases): factual, attributed to company.
    C, secondary (news, user URLs): attributed as opinion, never as fact."""

    A_AUTHORITATIVE = "A"
    B_PRIMARY = "B"
    C_SECONDARY = "C"


@dataclass(frozen=True)
class SourceDocument:
    """One piece of source text, ready to enter the bundle (§6).

    `text` must be the exact string that will be sent to the model, citation
    offsets are only meaningful against this exact text, so nothing downstream
    may re-derive or re-normalize it after this point (see documents/store.py).
    """

    text: str
    tier: Tier
    label: str  # human-readable, e.g. "AAPL 10-K Item 1A (Risk Factors)"
    source_url: str
    as_of: str  # ISO date the underlying fact/filing is dated
