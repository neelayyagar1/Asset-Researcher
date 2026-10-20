"""Assembles the finished report and renders citations for display.

Brings together the two model calls and the deterministic data into one
object the interface can render without knowing anything about how it was
produced.

The citation renderer is what makes the grounding visible. A claim with a
footnote a reader can open, seeing the exact quoted sentence and a link to
the filing, is the difference between a research tool and a chatbot that
says it read the filing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from asset_researcher.analysis.bundle import SourceBundle
from asset_researcher.analysis.mandate import MandateProfile
from asset_researcher.analysis.narrative import NarrativeResult
from asset_researcher.analysis.reconcile import ReconciliationReport
from asset_researcher.grounding.verify import CitationCheck


@dataclass(frozen=True)
class RenderedCitation:
    """A source reference, rendered inline as a hyperlink."""

    number: int
    quote: str
    source_label: str
    source_url: str
    verified: bool
    status: str


@dataclass
class Report:
    bundle: SourceBundle
    mandate: MandateProfile
    narrative: NarrativeResult
    reconciliation: ReconciliationReport
    citations: list[RenderedCitation] = field(default_factory=list)
    narrative_markdown: str = ""

    @property
    def ticker(self) -> str:
        return self.bundle.ticker

    @property
    def verification_banner(self) -> tuple[str, str]:
        """(level, message) for the status shown above the report.

        Three things this has to get right, each of which it previously got
        wrong.

        **It covers the descriptive note only.** The report is two model
        calls and only the first carries citations; the second produces the
        thesis, the variant views, the cases and the counter-argument, which
        is most of what a reader acts on. A single badge over the whole page
        reading "100% of the narrative is cited" claimed coverage of work
        that was never checked.

        **Located, not verified.** The check establishes that the quoted text
        sits at the stated offsets in the stated document. It says nothing
        about whether the claim built on that quote is a fair reading of it,
        and the wording no longer implies otherwise.

        **The unsupported-figure check is reported.** `unsupported_numbers`
        was computed on every run and consumed by nothing, so a report
        containing a figure the verifier had already flagged still carried a
        clean banner. That banner also asserted "every figure comes from
        filed XBRL data" directly above a header block in which the price,
        the market capitalisation and every modelled output are not filed
        figures at all.
        """
        v = self.narrative.verification
        scope = (
            "Checks cover the descriptive note; the analysis, cases and "
            "valuation are synthesis over it and carry no citations."
        )

        if v.total_citations == 0:
            return (
                "error",
                "No citations were produced. Nothing in the descriptive note "
                f"has been traced to a source; treat all of it as "
                f"unverified. {scope}",
            )

        if v.unsupported_numbers:
            shown = ", ".join(sorted(v.unsupported_numbers)[:5])
            return (
                "warning",
                f"{len(v.unsupported_numbers)} "
                f"{'figure' if len(v.unsupported_numbers) == 1 else 'figures'} "
                f"in the prose could "
                f"not be matched to a filed value ({shown}). Figures in the "
                f"tables are as filed; treat any number in the prose as "
                f"unsupported. {scope}",
            )

        if v.failures:
            return (
                "warning",
                f"{len(v.failures)} of {v.total_citations} citations could not "
                f"be located in the source text and are marked below. "
                f"{v.coverage:.0%} of the note's prose sits under a "
                f"citation. {scope}",
            )

        return (
            "success",
            f"All {v.total_citations} citations located in their source "
            f"documents, covering {v.coverage:.0%} of the note's prose. "
            f"Located means the quoted text is present at the stated place, "
            f"not that it supports the claim. {scope}",
        )


_SENTENCE_END = re.compile(r"(?<=[.!?])(\s|$)")


def build_report(
    bundle: SourceBundle,
    mandate: MandateProfile,
    narrative: NarrativeResult,
    reconciliation: ReconciliationReport,
) -> Report:
    markdown, citations = render_with_citations(narrative)
    return Report(
        bundle=bundle,
        mandate=mandate,
        narrative=narrative,
        reconciliation=reconciliation,
        citations=citations,
        narrative_markdown=markdown,
    )


def render_with_citations(
    narrative: NarrativeResult,
) -> tuple[str, list[RenderedCitation]]:
    """Prose with numbered footnote markers, plus the footnotes themselves.

    Each marker is a hyperlink to the source document, placed at the point
    of the claim. A separate footnote list below the prose makes a reader
    break stride to check anything, so the link sits inline instead.

    A citation that failed verification is labelled "unverified" in the
    marker. The failure is shown, never silently dropped.
    """
    checks_by_index = _checks_by_citation_index(narrative)

    parts: list[str] = []
    citations: list[RenderedCitation] = []
    citation_index = 0

    for span in narrative.response.spans:
        parts.append(span.text)

        markers: list[str] = []
        for citation in span.citations:
            check = checks_by_index.get(citation_index)
            verified = check.ok if check else False
            citation_index += 1

            number = len(citations) + 1
            document = _document_for(narrative, citation.document_index)
            citations.append(
                RenderedCitation(
                    number=number,
                    quote=" ".join(citation.cited_text.split()),
                    source_label=document.label if document else "unknown source",
                    source_url=document.source_url if document else "",
                    verified=verified,
                    status=check.status.value if check else "unchecked",
                )
            )
            # Inline and hyperlinked. A footnote list below the prose forces
            # the reader to break stride and scroll; a link at the point of
            # the claim does not. Unverified citations are marked "unverified"
            # in words rather than with a symbol.
            url = document.source_url if document else ""
            label = f"{number}" if verified else f"{number}, unverified"
            # The visible marker stays "[1]". Its accessible name was the
            # literal "[1", an unclosed bracket announced as "link, left
            # bracket one", which told a reader nothing about where it
            # went. The title carries the source instead.
            source = document.label if document else "source"
            markers.append(
                f'[[{label}]({url} "Citation {number}: {source}")]'
                if url
                else f"[{label}]"
            )

        if markers:
            parts.append(" " + "".join(markers))

    return "".join(parts), citations


def _checks_by_citation_index(narrative: NarrativeResult) -> dict[int, CitationCheck]:
    """Citation checks are produced in the same order the citations appear,
    so position is the join key."""
    return dict(enumerate(narrative.verification.citation_checks))


def _document_for(narrative: NarrativeResult, index: int):
    if 0 <= index < len(narrative.documents):
        return narrative.documents[index]
    return None


def _format_value(value: float | None) -> str:
    """Dollars at an automatic scale, negatives in parentheses.

    Parentheses rather than a leading minus sign, which is the convention in
    published statements: "-$63.0B" reads as a typo next to "$1,611.0B", and
    a minus sign is easily lost in a right-aligned column.
    """
    if value is None:
        return "n/a"
    if value < 0:
        return f"({_format_value(abs(value)).lstrip()})"
    magnitude = abs(value)
    if magnitude >= 1e9:
        return f"${value / 1e9:,.1f}B"
    if magnitude >= 1e6:
        return f"${value / 1e6:,.1f}M"
    if magnitude >= 1e3:
        return f"${value / 1e3:,.1f}K"
    return f"{value:,.2f}"


def format_projection_table(bundle: SourceBundle) -> list[dict[str, str]]:
    """The forecast the discounted cash flow actually runs on.

    A valuation that shows only its output asks the reader to take the
    arithmetic on trust. Published models show the projection, so the reader
    can see the year-by-year cash flows, the discount factor applied to each,
    and the terminal value sitting at the end.

    Every figure here is computed, not filed, which is why the caller labels
    the block as a model rather than as data.
    """
    if bundle.dcf is None or bundle.dcf_inputs is None:
        return []

    rate = bundle.dcf_inputs.discount_rate
    rows: list[dict[str, str]] = []

    for year, cash_flow, discounted in bundle.dcf.projected_fcf:
        rows.append(
            {
                "Year": f"Y{year}",
                "Free cash flow": _format_value(cash_flow),
                "Discount factor": f"{1 / ((1 + rate) ** year):.3f}",
                "Present value": _format_value(discounted),
            }
        )

    rows.append(
        {
            "Year": "Terminal",
            "Free cash flow": "Perpetuity",
            "Discount factor": f"{1 / ((1 + rate) ** bundle.dcf_inputs.forecast_years):.3f}",
            "Present value": _format_value(bundle.dcf.pv_terminal),
        }
    )
    rows.append(
        {
            "Year": "Enterprise value",
            "Free cash flow": "",
            "Discount factor": "",
            "Present value": _format_value(bundle.dcf.enterprise_value),
        }
    )
    rows.append(
        {
            "Year": "Less net debt",
            "Free cash flow": "",
            "Discount factor": "",
            "Present value": _format_value(-bundle.dcf_inputs.net_debt),
        }
    )
    rows.append(
        {
            "Year": "Equity value",
            "Free cash flow": "",
            "Discount factor": "",
            "Present value": _format_value(bundle.dcf.equity_value),
        }
    )
    return rows
