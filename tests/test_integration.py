"""End-to-end pipeline: bundle -> Call A -> mandate -> Call B -> report.

Only the network transport is faked. Sectioning, proxy extraction, 8-K cover
stripping, XBRL mapping, series building, validation, scoring, comps,
citation verification and rendering all run for real.

This exists because assemble.py had 0% coverage and narrative.py 32%: the
orchestration was verified by running it live against Apple and JPMorgan,
which found real bugs, but nothing protected it from regression afterwards.
"""

from __future__ import annotations

import pytest

from asset_researcher.analysis.assemble import assemble_bundle
from asset_researcher.analysis.mandate import parse_mandate
from asset_researcher.analysis.narrative import generate_narrative
from asset_researcher.analysis.reconcile import generate_reconciliation
from asset_researcher.analysis.report import build_report
from asset_researcher.analysis.statements import build_statement
from asset_researcher.config import get_settings
from asset_researcher.documents.store import DocumentStore
from tests.fakes import TICKER, FakeEdgarClient, FakeFinnhubClient, FakeLLM


@pytest.fixture
def pipeline(tmp_path):
    settings = get_settings()
    edgar, finnhub, llm = FakeEdgarClient(), FakeFinnhubClient(), FakeLLM()
    store = DocumentStore(tmp_path / "documents")
    bundle = assemble_bundle(TICKER, settings, edgar, finnhub, llm, store=store)
    return settings, edgar, finnhub, llm, bundle


# --- bundle assembly ----------------------------------------------------


def test_bundle_gathers_all_three_filing_types(pipeline):
    _, _, _, _, bundle = pipeline
    forms = {p.form for p in bundle.passages}
    assert forms == {"10-K", "DEF 14A", "8-K"}


def test_item_sections_come_from_the_body_not_the_table_of_contents(pipeline):
    """The TOC repeats every Item header; parsing it would produce
    one-line 'sections' that still look populated."""
    _, _, _, _, bundle = pipeline
    business = next(p for p in bundle.passages if p.label.startswith("Item 1."))
    assert "designs and sells industrial widgets" in business.text
    assert business.char_count > 500  # a TOC entry would be a single line


def test_mdna_and_risk_sections_are_present_with_real_content(pipeline):
    _, _, _, _, bundle = pipeline
    labels = {p.label for p in bundle.passages}
    assert any("Item 1A" in label for label in labels)
    assert any("Item 7." in label for label in labels)

    mdna = next(p for p in bundle.passages if p.label.startswith("Item 7."))
    assert "gross margin expansion" in mdna.text


def test_8k_cover_metadata_is_stripped_so_the_disclosure_survives(pipeline):
    """Regression for the bug that silently dropped a CEO succession: the
    inline-XBRL cover block extracts as 'true / NASDAQ / 0000320193'."""
    _, _, _, _, bundle = pipeline
    eightk = next(
        p for p in bundle.passages if p.form == "8-K" and "5.02" in p.label
    )
    assert "Executive Chair" in eightk.text
    assert "NASDAQ" not in eightk.text
    assert eightk.start > 0  # offsets stay relative to the stored document


def test_proxy_extraction_finds_compensation_content_not_the_contents_listing(pipeline):
    _, _, _, _, bundle = pipeline
    proxy = [p for p in bundle.passages if p.form == "DEF 14A"]
    assert proxy
    assert any("stock awards" in p.text for p in proxy)


def test_composite_metric_sums_disjoint_concepts_end_to_end(pipeline):
    """total_debt = LongTermDebt ($90B) + CommercialPaper ($8B)."""
    _, _, _, _, bundle = pipeline
    total_debt = bundle.series.series["total_debt"][-1].value
    assert total_debt == pytest.approx(98e9)


def test_filed_figures_survive_the_pipeline_exactly(pipeline):
    _, _, _, _, bundle = pipeline
    revenue = bundle.series.series["revenue"]
    assert [p.value for p in revenue] == pytest.approx([380e9, 400e9])


def test_validation_passes_on_internally_consistent_filings(pipeline):
    _, _, _, _, bundle = pipeline
    assert bundle.validation is not None
    assert bundle.validation.ok, [i.message for i in bundle.validation.errors]
    assert not bundle.has_errors


def test_health_scores_compute_for_a_standard_filer(pipeline):
    _, _, _, _, bundle = pipeline
    labels = {s.label for s in bundle.health_scores}
    assert {"Altman Z-Score", "Piotroski F-Score", "Beneish M-Score"} <= labels


def test_staleness_is_stated_rather_than_left_to_be_inferred(pipeline):
    _, _, _, _, bundle = pipeline
    assert bundle.staleness_note
    assert "10-K" in bundle.staleness_note


# --- Call A and verification -------------------------------------------


def test_narrative_citations_verify_against_the_real_stored_text(pipeline):
    """The fake locates its quote in the actual document at call time, so the
    verifier does genuine work rather than being handed a agreed answer."""
    _, _, _, llm, bundle = pipeline
    narrative = generate_narrative(bundle, llm)

    report = narrative.verification
    assert report.total_citations == 2
    assert report.citation_validity == 1.0
    assert report.passed, report.summary()


def test_a_citation_pointing_at_the_wrong_offsets_fails_verification(pipeline):
    """Proves the check can fail, otherwise the previous test proves
    nothing."""
    from asset_researcher.llm.provider import Citation, CitedResponse, CitedSpan

    _, _, _, llm, bundle = pipeline

    class Misaligned(FakeLLM):
        def complete_cited(self, *, system, documents, user, effort, max_tokens):
            return CitedResponse(
                [
                    CitedSpan(
                        text="A claim resting on a bad citation.",
                        citations=[
                            Citation(
                                cited_text="text that is nowhere in the filing",
                                document_index=0,
                                document_title=documents[0].label,
                                start_char_index=0,
                                end_char_index=34,
                            )
                        ],
                    )
                ]
            )

    narrative = generate_narrative(bundle, Misaligned())
    assert narrative.verification.citation_validity == 0.0
    assert not narrative.verification.passed


def test_user_supplied_sources_enter_as_tier_c(pipeline):
    from asset_researcher.sources.base import SourceDocument, Tier

    _, _, _, llm, bundle = pipeline
    user_source = SourceDocument(
        text="An analyst argues the margin story is mix, not execution.",
        tier=Tier.C_SECONDARY, label="User source, example",
        source_url="https://example.invalid/note", as_of="",
    )
    narrative = generate_narrative(bundle, llm, user_sources=[user_source])
    assert narrative.documents[-1].tier is Tier.C_SECONDARY


# --- Call B and the finished report ------------------------------------


def test_full_report_assembles_with_divergences_and_a_counter_case(pipeline):
    _, _, _, llm, bundle = pipeline
    narrative = generate_narrative(bundle, llm)
    mandate = parse_mandate("long only, 3-5 years, quality", llm)
    reconciliation = generate_reconciliation(bundle, narrative, mandate, llm)
    report = build_report(bundle, mandate, narrative, reconciliation)

    assert len(report.reconciliation.divergences) == 1
    assert len(report.reconciliation.corroborations) == 1
    assert report.reconciliation.disconfirming_evidence.strip()
    assert report.mandate.horizon_bucket == "years"


def test_verification_banner_reports_success_when_everything_resolves(pipeline):
    _, _, _, llm, bundle = pipeline
    narrative = generate_narrative(bundle, llm)
    mandate = parse_mandate("", llm)
    reconciliation = generate_reconciliation(bundle, narrative, mandate, llm)
    report = build_report(bundle, mandate, narrative, reconciliation)

    level, message = report.verification_banner
    assert level == "success"
    assert "located" in message
    # The banner must not claim more than the check performed: it covers the
    # descriptive note, and locating a quote is not establishing that the
    # quote supports the claim attached to it.
    assert "not that it supports the claim" in message
    assert "descriptive note" in message
    assert "Every figure comes from filed XBRL data" not in message


def test_citations_render_as_openable_footnotes(pipeline):
    _, _, _, llm, bundle = pipeline
    narrative = generate_narrative(bundle, llm)
    mandate = parse_mandate("", llm)
    report = build_report(
        bundle, mandate, narrative,
        generate_reconciliation(bundle, narrative, mandate, llm),
    )

    assert "[1]" in report.narrative_markdown
    assert "⚠" not in report.narrative_markdown
    assert len(report.citations) == 2
    assert all(c.verified for c in report.citations)
    assert all(c.source_url for c in report.citations)


# --- the financials table (previously unverified) ----------------------


def test_financials_table_renders_rows_with_filed_values(pipeline):
    """The most visible surface in the demo; a PM looks at it first."""
    _, _, _, _, bundle = pipeline
    rows = build_statement(bundle.series, bundle.sector_class)

    assert rows, "financials table produced no rows"
    by_label = {row.label: row for row in rows}
    assert by_label["Revenue"].values["FY2025"] == "400,000"
    assert by_label["Net income"].values["FY2025"] == "100,000"


def test_financials_table_marks_a_period_with_no_filed_value(pipeline):
    """A missing value must read as missing, never as zero, and never as
    "not meaningful", which is a claim about the figure rather than about
    the filing."""
    _, _, _, _, bundle = pipeline
    rows = build_statement(bundle.series, bundle.sector_class)
    cogs = next(r for r in rows if r.label == "Cost of goods sold")
    assert cogs.values["FY2024"] == "n.d."
    assert cogs.values["FY2025"] == "220,000"


def test_financials_table_is_empty_rather_than_fabricated_without_xbrl(pipeline):
    _, _, _, _, bundle = pipeline
    bundle.series = None
    assert build_statement(bundle.series, bundle.sector_class) == []


# --- results announcements ----------------------------------------------


def test_a_results_8k_brings_in_its_exhibit_not_just_the_cover_page(pipeline):
    """An Item 2.02 filing's body is a cover page referring the reader to
    Exhibit 99.1, where the quarterly figures actually are. Measured on
    Apple: two such filings ingested at 1,188 and 1,193 characters,
    containing no figure between them, while the 10-K behind them was
    eleven months old."""
    _, _, _, _, bundle = pipeline
    exhibit = next(
        (p for p in bundle.passages if "results announcement" in p.label), None
    )
    assert exhibit is not None, "the exhibit was never fetched"
    assert "quarterly revenue of $94.0 billion" in exhibit.text.lower()
    assert "1.57" in exhibit.text

    cover = next(p for p in bundle.passages if "2.02" in p.label)
    assert "$" not in cover.text
    assert len(exhibit.text) > len(cover.text) * 2


def test_the_exhibit_is_stored_separately_from_the_cover_page(pipeline):
    """They are two documents in one accession and must not overwrite each
    other in the store, or citation offsets resolve against the wrong one."""
    _, _, _, _, bundle = pipeline
    cover = next(p for p in bundle.passages if "2.02" in p.label)
    exhibit = next(p for p in bundle.passages if "results announcement" in p.label)
    assert cover.doc_id != exhibit.doc_id
    assert cover.source_url != exhibit.source_url
    assert "ex991" in exhibit.source_url


def test_an_exhibit_is_only_fetched_for_a_filing_that_announces_results(pipeline):
    """One extra request on the filings where it pays and none elsewhere."""
    _, edgar, _, _, _ = pipeline
    index_calls = [u for u in edgar.requested if u.endswith("/index.json")]
    assert len(index_calls) == 1
    assert "000032019326000004" in index_calls[0]
