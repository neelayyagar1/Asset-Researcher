import pytest

from asset_researcher.sources.edgar.filings import (
    FilingIndex,
    FilingRef,
    ForeignPrivateIssuerError,
    NoOperatingFilingsError,
    require_operating_filer,
)


def make_index(forms: list[str]) -> FilingIndex:
    refs = [
        FilingRef(
            form=form,
            filing_date=f"2026-01-{i+1:02d}",
            accession_number=f"0000000000-26-00000{i}",
            primary_document="doc.htm",
            items="",
        )
        for i, form in enumerate(forms)
    ]
    return FilingIndex(
        cik=1, company_name="Test Co", sic="3571", sic_description="", all_filings=refs
    )


def test_require_operating_filer_passes_when_10k_present():
    idx = make_index(["10-K", "8-K"])
    require_operating_filer(idx)  # should not raise


def test_require_operating_filer_flags_foreign_issuer_distinctly():
    idx = make_index(["20-F", "8-K"])
    with pytest.raises(ForeignPrivateIssuerError):
        require_operating_filer(idx)


def test_require_operating_filer_flags_shell_entity():
    # No 10-K and no 20-F, the XOM-shell case found during build, where
    # company_tickers.json resolves the ticker to a non-operating entity.
    idx = make_index(["8-K"])
    with pytest.raises(NoOperatingFilingsError):
        require_operating_filer(idx)


def test_latest_returns_newest_first():
    idx = make_index(["10-K", "10-K", "8-K"])
    # both entries are "10-K"; filing_date increases with index in make_index,
    # so latest() must return the LAST one constructed (newest date) once
    # sorted, sorting happens in get_filing_index, so build directly here
    # sorted to match real usage.
    refs = sorted(idx.all_filings, key=lambda r: r.filing_date, reverse=True)
    idx = FilingIndex(idx.cik, idx.company_name, idx.sic, idx.sic_description, refs)
    assert idx.latest("10-K").filing_date == "2026-01-02"


def test_document_url_strips_dashes_from_accession():
    ref = FilingRef(
        form="10-K",
        filing_date="2026-01-01",
        accession_number="0000320193-25-000079",
        primary_document="aapl-20250927.htm",
        items="",
    )
    url = ref.document_url(320193)
    assert url == (
        "https://www.sec.gov/Archives/edgar/data/320193/"
        "000032019325000079/aapl-20250927.htm"
    )
