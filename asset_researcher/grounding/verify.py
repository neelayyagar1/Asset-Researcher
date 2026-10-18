"""Checks every citation against the exact text the model was given.

This is the enforcement layer of the grounding approach (ARCHITECTURE.md §6).
Prompting a model to cite its sources produces citations; it does not produce
*correct* citations. The API returns character offsets, and those offsets can
be checked mechanically, so they are, on every report, not only in evaluation.

Three checks, in decreasing order of how damning a failure is:

1. **Offset integrity.** Does the quoted text actually appear at the claimed
   position in the document that was sent? A failure means the citation is
   fabricated or misaligned, and the claim resting on it is unsupported.
2. **Numeric support.** Every figure in a claim must appear in its cited span
   or match a filed XBRL value. This is the last line of defence for the
   project's central promise, that no number is model-generated.
3. **Coverage.** What share of the generated prose carries any citation at
   all. An uncited sentence is not necessarily false, but it is unverifiable
   and must be shown as such.

**Failures degrade the display; they never silently drop content.** A reader
who can see that one claim failed verification is better served than one shown
a clean report with a quiet hole in it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

from asset_researcher.llm.provider import Citation, CitedResponse
from asset_researcher.sources.base import SourceDocument


class CitationStatus(str, Enum):
    VERIFIED = "verified"  # quote found at the stated offsets
    OFFSET_MISMATCH = "offset_mismatch"  # quote real, but not where claimed
    TEXT_NOT_FOUND = "text_not_found"  # quote does not appear in the document
    NO_OFFSETS = "no_offsets"  # citation carried no location to check
    UNKNOWN_DOCUMENT = "unknown_document"  # document_index out of range

    @property
    def is_failure(self) -> bool:
        return self is not CitationStatus.VERIFIED


@dataclass(frozen=True)
class CitationCheck:
    status: CitationStatus
    cited_text: str
    document_label: str | None
    start: int | None
    end: int | None
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.status is CitationStatus.VERIFIED


@dataclass
class VerificationReport:
    citation_checks: list[CitationCheck] = field(default_factory=list)
    unsupported_numbers: list[str] = field(default_factory=list)
    cited_span_count: int = 0
    uncited_span_count: int = 0
    cited_chars: int = 0
    uncited_chars: int = 0

    @property
    def total_citations(self) -> int:
        return len(self.citation_checks)

    @property
    def verified_citations(self) -> int:
        return sum(1 for c in self.citation_checks if c.ok)

    @property
    def failures(self) -> list[CitationCheck]:
        return [c for c in self.citation_checks if not c.ok]

    @property
    def citation_validity(self) -> float:
        """Share of citations that resolve. Target is 1.0, anything less is
        a defect, not a tuning parameter."""
        if not self.citation_checks:
            return 0.0
        return self.verified_citations / self.total_citations

    @property
    def coverage(self) -> float:
        """Share of generated prose, by character, sitting under a citation.

        Measured in characters rather than spans. The API splits text at
        citation boundaries, so a sentence stitched from three cited clauses
        yields uncited spans of ";" and ", alongside" between them. Counting
        spans made Apple's note read as 50% uncited when 73% of its prose was
        in fact cited, the metric was wrong, not the output.
        """
        total = self.cited_chars + self.uncited_chars
        if total == 0:
            return 0.0
        return self.cited_chars / total

    @property
    def passed(self) -> bool:
        """Whether this output is safe to present without qualification."""
        return (
            self.citation_validity == 1.0
            and not self.unsupported_numbers
            and self.total_citations > 0
        )

    def summary(self) -> str:
        return (
            f"{self.verified_citations}/{self.total_citations} citations verified, "
            f"{self.coverage:.0%} of prose cited, "
            f"{len(self.unsupported_numbers)} unsupported figure(s)"
        )


# Figures a claim might assert: currency, percentages, and large bare numbers.
#
# A bare decimal is deliberately NOT matched. An earlier version treated any
# "\d+\.\d+" as a financial figure and flagged "Item 2.02" and "Item 5.02".
# SEC 8-K item codes, as unsupported numbers. Bare decimals carry no unit and
# are as likely to be a section reference as a ratio; currency and percentages
# are where the actual risk of an invented figure lives.
_FIGURE = re.compile(
    r"""
    (?<![\w.])            # not mid-identifier
    (?:
        \$\s?[\d,]+(?:\.\d+)?(?:\s?(?:billion|million|thousand|bn|mm|k))?
      | [\d,]+(?:\.\d+)?\s?%
      | [\d,]{4,}(?:\.\d+)?        # large bare numbers
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)

_YEAR = re.compile(r"^(?:19|20)\d{2}$")

# "Item 2.02", "Item 5.07", form structure, not financial claims.
_ITEM_CODE = re.compile(r"\bitems?\s+[\d.,\s]*$", re.IGNORECASE)


def _normalize_number(raw: str) -> str:
    """Compare figures by their digits, so '$1,234.5 million' and
    '1234.5' are recognised as the same assertion."""
    return re.sub(r"[^\d.]", "", raw).rstrip(".")


def _figures_in(text: str) -> list[str]:
    out = []
    for match in _FIGURE.finditer(text):
        raw = match.group(0).strip()
        digits = _normalize_number(raw)
        if not digits or _YEAR.match(digits):
            continue
        # Skip numbers introduced as a form item reference.
        if _ITEM_CODE.search(text[: match.start()]):
            continue
        out.append(raw)
    return out


def verify_citations(
    response: CitedResponse,
    documents: list[SourceDocument],
    known_figures: set[str] | None = None,
) -> VerificationReport:
    """Check a cited response against the documents it was generated from.

    known_figures: normalized digit strings for values sourced from XBRL, so a
    figure the renderer legitimately spliced in is not reported as unsupported.
    """
    report = VerificationReport()
    known = known_figures or set()

    for span in response.spans:
        # Punctuation and connective fragments between two cited clauses
        # ("; ", ", alongside") are artefacts of where the API split the
        # text, not uncited assertions. Counting them would understate
        # coverage without telling a reader anything.
        substantive = _is_substantive(span.text)

        if span.is_cited:
            report.cited_span_count += 1
            report.cited_chars += len(span.text)
        elif substantive:
            report.uncited_span_count += 1
            report.uncited_chars += len(span.text)

        for citation in span.citations:
            report.citation_checks.append(_check_citation(citation, documents))

        # A figure is supported if it appears in any of this span's cited
        # quotes, or matches a filed XBRL value.
        cited_digits = {
            _normalize_number(f)
            for c in span.citations
            for f in _figures_in(c.cited_text)
        }
        for figure in _figures_in(span.text):
            digits = _normalize_number(figure)
            if digits in cited_digits or digits in known:
                continue
            report.unsupported_numbers.append(figure)

    return report


def _check_citation(
    citation: Citation, documents: list[SourceDocument]
) -> CitationCheck:
    index = citation.document_index
    if index < 0 or index >= len(documents):
        return CitationCheck(
            status=CitationStatus.UNKNOWN_DOCUMENT,
            cited_text=citation.cited_text,
            document_label=citation.document_title,
            start=citation.start_char_index,
            end=citation.end_char_index,
            detail=f"document_index {index} outside 0..{len(documents) - 1}",
        )

    document = documents[index]
    start, end = citation.start_char_index, citation.end_char_index

    if start is None or end is None:
        return CitationCheck(
            status=CitationStatus.NO_OFFSETS,
            cited_text=citation.cited_text,
            document_label=document.label,
            start=start,
            end=end,
            detail="citation carried no character offsets to check",
        )

    actual = document.text[start:end]
    if _equivalent(actual, citation.cited_text):
        return CitationCheck(
            status=CitationStatus.VERIFIED,
            cited_text=citation.cited_text,
            document_label=document.label,
            start=start,
            end=end,
        )

    # The quote may still be genuine but positioned wrongly, which is a
    # different (and less alarming) failure than a fabricated quote.
    if citation.cited_text and citation.cited_text.strip() in document.text:
        return CitationCheck(
            status=CitationStatus.OFFSET_MISMATCH,
            cited_text=citation.cited_text,
            document_label=document.label,
            start=start,
            end=end,
            detail=(
                f"text appears in the document but not at [{start}:{end}], "
                f"which holds {actual[:60]!r}"
            ),
        )

    return CitationCheck(
        status=CitationStatus.TEXT_NOT_FOUND,
        cited_text=citation.cited_text,
        document_label=document.label,
        start=start,
        end=end,
        detail="quoted text does not appear in the cited document",
    )


def _is_substantive(text: str) -> bool:
    """Whether a span asserts anything.

    Markdown headings are excluded too: "## Risk Factors" is structure, and
    demanding a citation for it would permanently cap coverage below 100%
    for no benefit.
    """
    stripped = text.strip()
    if not stripped:
        return False
    if stripped.startswith("#"):
        return False
    # Needs at least a few letters to be a claim rather than a joiner.
    return sum(1 for c in stripped if c.isalpha()) >= 15


def _equivalent(a: str, b: str) -> bool:
    """Whitespace-insensitive comparison.

    Filings are full of newlines introduced by block-level HTML, and the API
    may return a quote with those collapsed. Treating that as a mismatch would
    fail correct citations en masse, so only the visible characters are
    compared.
    """
    return " ".join(a.split()) == " ".join(b.split())
