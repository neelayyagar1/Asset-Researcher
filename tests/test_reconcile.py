"""Call B: reconciliation structure and the mandatory disconfirming section."""

from __future__ import annotations

from asset_researcher.analysis.bundle import SourceBundle
from asset_researcher.analysis.mandate import MandateProfile
from asset_researcher.analysis.narrative import NarrativeResult
from asset_researcher.analysis.reconcile import (
    Reconciliation,
    ReconciliationReport,
    build_reconciliation_input,
    generate_reconciliation,
)
from asset_researcher.grounding.verify import VerificationReport
from asset_researcher.llm.provider import CitedResponse, CitedSpan
from asset_researcher.quant.comps import CompRow, CompsTable
from asset_researcher.quant.series import MetricPeriod, MetricSeries


def _bundle() -> SourceBundle:
    b = SourceBundle(
        ticker="AAPL", cik=320193, company_name="Apple Inc.",
        sector_class="standard", display_industry="Technology",
        as_of="2026-08-07",
    )
    series = MetricSeries(cik=320193, sector="standard")
    series.series["revenue"] = [
        MetricPeriod("2024-09-28", "FY2024", 391.0e9, "a"),
        MetricPeriod("2025-09-27", "FY2025", 416.2e9, "a"),
    ]
    b.series = series
    b.derived = {"net_margin": 0.269}
    b.filing_dates["10-K"] = "2025-10-31"
    b.comps = CompsTable(subject_ticker="AAPL", peer_source="Finnhub peer list")
    b.comps.rows = [
        CompRow("AAPL", "Apple", True, market_cap=4559e9, net_income=112e9),
        CompRow("HPQ", "HP", False, market_cap=25e9, net_income=2.5e9),
    ]
    return b


def _narrative(text: str = "## Business Overview\n\nApple sells devices.") -> NarrativeResult:
    return NarrativeResult(
        response=CitedResponse([CitedSpan(text=text, citations=[])]),
        documents=[],
        verification=VerificationReport(),
    )


class _FakeLLM:
    def __init__(self, report: ReconciliationReport):
        self._report = report
        self.calls: list[dict] = []

    def complete_structured(self, **kw):
        self.calls.append(kw)
        return self._report

    def complete_cited(self, **kw):  # pragma: no cover
        raise NotImplementedError


def test_divergences_are_separable_from_corroborations():
    report = ReconciliationReport(
        financial_trajectory="x",
        reconciliations=[
            Reconciliation(
                management_claim="margins improving", what_the_data_shows="they did",
                assessment="consistent", agrees=True,
            ),
            Reconciliation(
                management_claim="cost discipline", what_the_data_shows="opex outgrew revenue",
                assessment="gap", agrees=False, materiality="high",
            ),
        ],
    )
    assert len(report.divergences) == 1
    assert len(report.corroborations) == 1
    assert report.divergences[0].materiality == "high"


def test_an_empty_disconfirming_section_is_replaced_with_a_visible_warning():
    """A mandate-aware report that only ever agrees is the echo chamber this
    architecture exists to prevent. Silence here is a defect, not an
    acceptable outcome."""
    llm = _FakeLLM(ReconciliationReport(financial_trajectory="x", disconfirming_evidence="  "))
    report = generate_reconciliation(_bundle(), _narrative(), MandateProfile(), llm)

    assert report.disconfirming_evidence.strip()
    assert "Not produced" in report.disconfirming_evidence
    assert "unchallenged" in report.disconfirming_evidence


def test_a_present_disconfirming_section_is_left_untouched():
    llm = _FakeLLM(
        ReconciliationReport(
            financial_trajectory="x",
            disconfirming_evidence="The evidence base is nine months stale.",
        )
    )
    report = generate_reconciliation(_bundle(), _narrative(), MandateProfile(), llm)
    assert report.disconfirming_evidence == "The evidence base is nine months stale."


def test_input_carries_filed_figures_so_the_model_need_not_invent_any():
    """Numbers appear in the input precisely so none appear in the output."""
    text = build_reconciliation_input(_bundle(), _narrative(), MandateProfile())
    assert "416,200,000,000" in text
    assert "Filed figures" in text


def test_input_carries_the_mandate_and_its_boundary():
    text = build_reconciliation_input(
        _bundle(), _narrative(), MandateProfile(horizon_note="3-5 years")
    )
    assert "3-5 years" in text
    assert "must not change which facts" in text


def test_input_surfaces_gaps_rather_than_hiding_them():
    bundle = _bundle()
    bundle.add_gap("10-K:Item 7", "Incorporated by reference.", severity="error")
    text = build_reconciliation_input(bundle, _narrative(), MandateProfile())
    assert "do not paper over" in text.lower()
    assert "Incorporated by reference." in text


def test_input_includes_staleness_so_the_model_can_weigh_it():
    text = build_reconciliation_input(_bundle(), _narrative(), MandateProfile())
    assert "months ago" in text
    # The parenthesised plural is the loudest machine-written signature a
    # sentence can carry, and this string is rendered to the reader too.
    assert "(s)" not in text


def test_peer_comparison_reaches_the_model_with_its_caveat():
    text = build_reconciliation_input(_bundle(), _narrative(), MandateProfile())
    assert "Peer comparison" in text
    assert "Finnhub peer list" in text


def test_missing_quant_data_is_stated_not_silently_empty():
    bundle = _bundle()
    bundle.series = None
    text = build_reconciliation_input(bundle, _narrative(), MandateProfile())
    assert "No filed financial data available." in text
