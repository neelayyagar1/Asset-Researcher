"""Filing document -> stored, extracted text.

Ties the pieces together: pull the primary document for a FilingRef, strip it
to text (extract.py), and persist that text verbatim (store.py) so citation
offsets stay valid for the life of the report.

Documents are stored under their accession number, which is immutable on
EDGAR, a filing's content never changes once accepted. So a document already
in the store is never re-fetched, and its text is never re-derived.
"""

from __future__ import annotations

from asset_researcher.documents.extract import html_to_text
from asset_researcher.documents.store import (
    DocumentStore,
    StoredDocument,
    compute_sha256,
    make_doc_id,
)
from asset_researcher.sources.edgar.client import EdgarClient
from asset_researcher.sources.edgar.filings import FilingRef

# Filing documents are immutable once accepted, so the HTTP layer may cache
# them indefinitely.
_FILING_TTL_SECONDS = None


def fetch_filing_document(
    client: EdgarClient,
    store: DocumentStore,
    cik: int,
    filing: FilingRef,
    title: str | None = None,
) -> StoredDocument:
    """Fetch, extract, and store one filing document. Returns the stored copy,
    re-using it when already present."""
    doc_id = make_doc_id(cik, filing.accession_number, filing.form)

    existing = store.load(doc_id)
    if existing is not None:
        return existing

    url = filing.document_url(cik)
    raw_html = client.get_text(
        url,
        cache_key=f"doc/{cik}/{filing.accession_number}/{filing.primary_document}",
        ttl_seconds=_FILING_TTL_SECONDS,
    )
    text = html_to_text(raw_html)

    doc = StoredDocument(
        doc_id=doc_id,
        cik=cik,
        form=filing.form,
        filing_date=filing.filing_date,
        accession_number=filing.accession_number,
        source_url=url,
        title=title or f"{filing.form} filed {filing.filing_date}",
        text=text,
        sha256=compute_sha256(text),
    )
    return store.put(doc)
