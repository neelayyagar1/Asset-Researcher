"""Call A, cited descriptive sections.

The first of the two model calls (ARCHITECTURE.md §6). Citations are enabled, so
structured output is not available on this call; the response comes back as
prose split into spans, each carrying the offsets of whatever it cites.

Everything here is descriptive. Synthesis, valuation framing, and the
disconfirming case belong to Call B, which runs without citations and reasons
over both this output and the quantitative series.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from asset_researcher.analysis.bundle import SourceBundle
from asset_researcher.config.prompt_loader import load_prompt
from asset_researcher.grounding.verify import VerificationReport, verify_citations
from asset_researcher.llm.provider import CitedResponse, LLMProvider
from asset_researcher.sources.base import SourceDocument, Tier

# Passage labels the model is given, in the order it sees them.
_TIER_BY_FORM = {
    "10-K": Tier.A_AUTHORITATIVE,
    "8-K": Tier.A_AUTHORITATIVE,
    "DEF 14A": Tier.A_AUTHORITATIVE,
}


@dataclass
class NarrativeResult:
    response: CitedResponse
    documents: list[SourceDocument]
    verification: VerificationReport
    sections: dict[str, str] = field(default_factory=dict)

    @property
    def markdown(self) -> str:
        return self.response.full_text


def load_narrative_prompt() -> str:
    return load_prompt("narrative.md")


def bundle_to_documents(
    bundle: SourceBundle, user_sources: list[SourceDocument] | None = None
) -> list[SourceDocument]:
    """Passages as SourceDocuments, in the order the model will see them.

    The order matters beyond presentation: `document_index` on a returned
    citation refers to position in this list, so it must be built once and
    the same list handed to the verifier.
    """
    documents = [
        SourceDocument(
            text=p.text,
            tier=_TIER_BY_FORM.get(p.form, Tier.A_AUTHORITATIVE),
            label=f"{bundle.ticker} {p.label}",
            source_url=p.source_url,
            as_of=p.filing_date,
        )
        for p in bundle.passages
    ]

    # News is Tier C and arrives as many short items; concatenating them into
    # one document keeps the block count manageable while preserving each
    # headline's date and outlet for attribution.
    if bundle.news:
        lines = [
            f"[{item.published}] {item.source}: {item.headline}\n{item.summary}".strip()
            for item in bundle.news
        ]
        documents.append(
            SourceDocument(
                text="\n\n".join(lines),
                tier=Tier.C_SECONDARY,
                label=f"{bundle.ticker} recent news headlines",
                source_url="https://finnhub.io",
                as_of=bundle.as_of,
            )
        )

    # User-supplied sources go last so the filings anchor the model's reading
    # first. They are already Tier C (sources/web.py), and the prompt requires
    # Tier C material to be attributed as opinion rather than stated as fact.
    documents.extend(user_sources or [])

    return documents


def _context_preamble(bundle: SourceBundle) -> str:
    """Non-citable framing: what the company is, what is missing, and the
    explicit reminder that figures are off-limits."""
    lines = [
        f"Company: {bundle.company_name} ({bundle.ticker})",
        f"Industry: {bundle.display_industry}",
        f"Report date: {bundle.as_of}",
    ]
    if bundle.staleness_note:
        lines.append(bundle.staleness_note)

    if bundle.gaps:
        lines.append("")
        lines.append(
            "Known gaps in the source material. Do not paper over these. "
            "where a section depends on missing material, say so:"
        )
        for gap in bundle.gaps:
            lines.append(f"  - [{gap.severity}] {gap.source}: {gap.reason}")

    lines.append("")
    lines.append(
        "Write the five sections described in your instructions, citing the "
        "supplied documents. Remember: no financial figures in your prose. "
        "name the metric and its direction, and the renderer will insert the "
        "filed value."
    )
    return "\n".join(lines)


def _known_figures(bundle: SourceBundle, preamble: str = "") -> set[str]:
    """Digit strings a figure in the prose may legitimately match.

    Two sources, both ours rather than the model's:

    1. Filed XBRL values, at the scales a writer would use.
    2. Numbers appearing in the preamble we supplied. Gap messages carry
       counts ("Truncated to 40,000 of 68,169 characters"), and when the model
       correctly acknowledges that gap it repeats them. Flagging those as
       unsupported financial figures blames the model for quoting us.
    """
    known: set[str] = set()

    if bundle.series:
        for periods in bundle.series.series.values():
            for period in periods:
                value = abs(period.value)
                known.add(str(value))
                known.add(f"{value:.0f}")
                known.add(f"{value / 1e9:.1f}")
                known.add(f"{value / 1e9:.2f}")
                known.add(f"{value / 1e6:.1f}")

    for match in re.finditer(r"[\d,]+(?:\.\d+)?", preamble):
        known.add(re.sub(r"[^\d.]", "", match.group(0)).rstrip("."))

    return known


def generate_narrative(
    bundle: SourceBundle,
    llm: LLMProvider,
    effort: str = "medium",
    max_tokens: int = 16_000,
    user_sources: list[SourceDocument] | None = None,
) -> NarrativeResult:
    """Run Call A and verify every citation it returns."""
    documents = bundle_to_documents(bundle, user_sources)
    if not documents:
        raise ValueError(
            f"No source passages for {bundle.ticker}; nothing to write from."
        )

    preamble = _context_preamble(bundle)
    response = llm.complete_cited(
        system=load_narrative_prompt(),
        documents=documents,
        user=preamble,
        effort=effort,
        max_tokens=max_tokens,
    )

    verification = verify_citations(
        response, documents, known_figures=_known_figures(bundle, preamble)
    )

    return NarrativeResult(
        response=response,
        documents=documents,
        verification=verification,
        sections=_split_sections(response.full_text),
    )


def _split_sections(markdown: str) -> dict[str, str]:
    """Split the response on `##` headings for per-section rendering."""
    sections: dict[str, str] = {}
    current: str | None = None
    buffer: list[str] = []

    for line in markdown.splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(buffer).strip()
            current = line[3:].strip()
            buffer = []
        elif current is not None:
            buffer.append(line)

    if current is not None:
        sections[current] = "\n".join(buffer).strip()
    return sections
