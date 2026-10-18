"""Filing index. SIC code, sector description, and document references for the
forms this project cares about (10-K, 8-K, DEF 14A, Form 4).

Reads the submissions API's "recent" filings block. For most filers this is
sufficient; a very frequent filer (many Form 4s) could in principle push older
filings out of the 1000-entry recent window before a needed 10-K/DEF14A drops
out of it, but that's rare enough in practice that we handle it by falling
back to one additional page (submissions API paginates older filings into
files[] for CIKs with deep history) rather than building full pagination.
"""

from __future__ import annotations

from dataclasses import dataclass

from asset_researcher.sources.edgar.client import EdgarClient
from asset_researcher.sources.edgar.resolve import cik_to_padded

_SUBMISSIONS_TTL_SECONDS = 6 * 3600  # filings arrive throughout the trading day


@dataclass(frozen=True)
class FilingRef:
    form: str
    filing_date: str
    accession_number: str
    primary_document: str
    items: str  # 8-K item codes, e.g. "2.02,9.01"; empty for other forms

    def document_url(self, cik: int) -> str:
        accession_nodash = self.accession_number.replace("-", "")
        return (
            f"https://www.sec.gov/Archives/edgar/data/{cik}/"
            f"{accession_nodash}/{self.primary_document}"
        )


@dataclass(frozen=True)
class FilingIndex:
    cik: int
    company_name: str
    sic: str
    sic_description: str
    all_filings: list[FilingRef]

    def latest(self, form: str) -> FilingRef | None:
        matches = [f for f in self.all_filings if f.form == form]
        return matches[0] if matches else None  # already sorted newest-first

    def recent(self, form: str, limit: int) -> list[FilingRef]:
        return [f for f in self.all_filings if f.form == form][:limit]


def _parse_recent_block(recent: dict) -> list[FilingRef]:
    n = len(recent["form"])
    refs = [
        FilingRef(
            form=recent["form"][i],
            filing_date=recent["filingDate"][i],
            accession_number=recent["accessionNumber"][i],
            primary_document=recent["primaryDocument"][i],
            items=recent.get("items", [""] * n)[i],
        )
        for i in range(n)
    ]
    return sorted(refs, key=lambda r: r.filing_date, reverse=True)


class NoOperatingFilingsError(Exception):
    """The resolved CIK exists on EDGAR but has never filed a 10-K.

    This is a real trap, not a hypothetical: SEC's own ticker->CIK map
    (company_tickers.json) can point a well-known ticker at a non-operating
    holding-company shell rather than the entity that actually files
    financials, verified during build for XOM, which company_tickers.json
    maps to CIK 2115436 "ExxonMobil Holdings Corp" (8-Ks only), not the real
    "EXXON MOBIL CORP" (CIK 34088) that files the 10-K investors expect.
    We do not try to guess the "real" entity, that would risk confidently
    resolving to the wrong company, which is worse than an honest failure
    (the project's core principle: caught, never silently wrong)."""


class ForeignPrivateIssuerError(Exception):
    """Files 20-F (annual report for foreign private issuers) instead of a
    10-K, a different, incompatible XBRL/document shape this project does
    not support in v1. Distinct from NoOperatingFilingsError: this is a real
    company filing correctly under different rules, not a resolution mistake."""


def require_operating_filer(index: FilingIndex) -> None:
    if index.latest("10-K") is not None:
        return
    if index.latest("20-F") is not None:
        raise ForeignPrivateIssuerError(
            f"'{index.company_name}' is a foreign private issuer that files "
            f"Form 20-F rather than a 10-K. This project currently supports "
            f"US domestic filers only."
        )
    raise NoOperatingFilingsError(
        f"'{index.company_name}' (CIK {index.cik}) has no 10-K in its EDGAR "
        f"filing history. This sometimes happens when a ticker resolves to "
        f"a non-operating holding entity rather than the company that "
        f"actually files financials, if this looks wrong, try searching "
        f"EDGAR directly for the company name to find the correct filer."
    )


def get_filing_index(client: EdgarClient, cik: int) -> FilingIndex:
    padded = cik_to_padded(cik)
    url = f"https://data.sec.gov/submissions/{padded}.json"
    data = client.get_json(url, f"submissions-{padded}", _SUBMISSIONS_TTL_SECONDS)

    filings = _parse_recent_block(data["filings"]["recent"])

    # Fallback: if none of our target forms are present at all, this filer's
    # recent window may be dominated by something else (e.g. very frequent
    # Form 4s pushing everything back). Pull one older page and merge.
    target_forms = {"10-K", "8-K", "DEF 14A", "4"}
    if not (target_forms & {f.form for f in filings}):
        older_files = data["filings"].get("files", [])
        if older_files:
            older_name = older_files[0]["name"]
            older_url = f"https://data.sec.gov/submissions/{older_name}"
            older_data = client.get_json(
                older_url, f"submissions-{older_name}", _SUBMISSIONS_TTL_SECONDS
            )
            filings = sorted(
                filings + _parse_recent_block(older_data),
                key=lambda r: r.filing_date,
                reverse=True,
            )

    return FilingIndex(
        cik=cik,
        company_name=data["name"],
        sic=data.get("sic", ""),
        sic_description=data.get("sicDescription", ""),
        all_filings=filings,
    )
