"""The exported file.

The deliverable is a document someone keeps, so these tests run the real
pipeline over faked transport and then assert on the bytes that leave: that
the file stands alone, that it carries the caveats the screen carries, and
that nothing from a filing or a model reaches it as markup.
"""

from __future__ import annotations

import re

import pytest

from asset_researcher.analysis.assemble import assemble_bundle
from asset_researcher.analysis.mandate import parse_mandate
from asset_researcher.analysis.narrative import generate_narrative
from asset_researcher.analysis.reconcile import generate_reconciliation
from asset_researcher.analysis.report import build_report
from asset_researcher.config import get_settings
from asset_researcher.documents.store import DocumentStore
from asset_researcher.ui.export import report_to_html, report_to_markdown
from tests.fakes import TICKER, FakeEdgarClient, FakeFinnhubClient, FakeLLM


@pytest.fixture
def report(tmp_path):
    settings = get_settings()
    edgar, finnhub, llm = FakeEdgarClient(), FakeFinnhubClient(), FakeLLM()
    bundle = assemble_bundle(
        TICKER,
        settings,
        edgar,
        finnhub,
        llm,
        store=DocumentStore(tmp_path / "documents"),
    )
    narrative = generate_narrative(bundle, llm)
    mandate = parse_mandate("long only, 3-5 years, quality", llm)
    reconciliation = generate_reconciliation(bundle, narrative, mandate, llm)
    return build_report(bundle, mandate, narrative, reconciliation)


# ----------------------------------------------------------------- HTML


def test_the_html_export_is_a_complete_document(report):
    html = report_to_html(report)
    assert html.startswith("<!doctype html>")
    assert html.rstrip().endswith("</html>")
    assert '<meta charset="utf-8">' in html
    assert "<title>" in html


def test_the_stylesheet_travels_with_the_file(report):
    """A note forwarded to an analyst has to render on their machine with no
    access to this application."""
    html = report_to_html(report)
    assert "<style>" in html
    assert ".ar-stats" in html
    assert "ar-page" in html


def test_charts_travel_as_inline_svg_rather_than_image_references(report):
    html = report_to_html(report)
    assert "<svg viewBox=" in html
    assert "<img" not in html


def test_the_export_carries_the_headline_figures(report):
    html = report_to_html(report)
    for label in (
        "Traded price",
        "Probability-weighted target",
        "Implied upside",
        "Market cap / free cash flow",
    ):
        assert label in html


def test_the_export_carries_the_verification_state_and_the_counter_case(report):
    """A circulated note detached from the application is exactly where a
    reader most needs the caveats, so they travel with it."""
    html = report_to_html(report)
    assert "Citations verified" in html or "Citations partial" in html
    assert "Disconfirming evidence" in html
    assert "Against this thesis" in html


def test_the_disclaimer_travels_with_the_file(report):
    html = report_to_html(report)
    assert "not investment advice" in html
    assert report.bundle.as_of in html


def test_the_export_carries_its_sources_and_citations(report):
    html = report_to_html(report)
    assert "Documents used" in html
    assert "Citations" in html
    assert "sec.gov" in html or "example" in html


def test_print_rules_keep_findings_from_splitting_across_pages(report):
    """The export is read on screen and printed to PDF, and a divergence
    broken across a page break loses the comparison that is the finding."""
    html = report_to_html(report)
    assert "@media print" in html
    assert "break-inside:avoid" in html


def test_model_and_filing_text_cannot_reach_the_export_as_markup(report):
    report.reconciliation.disconfirming_evidence = (
        "<script>alert('x')</script> The thesis rests on one segment."
    )
    report.bundle.company_name = "Widget & Co <b>Holdings</b>"
    html = report_to_html(report)
    assert "<script>" not in html
    assert "<b>Holdings</b>" not in html
    assert "Widget &amp; Co" in html


def test_an_absent_dcf_is_stated_rather_than_left_blank(report):
    report.bundle.dcf = None
    report.bundle.dcf_inputs = None
    html = report_to_html(report)
    assert "No discounted cash flow model was produced" in html


def test_an_absent_peer_set_is_stated_rather_than_silently_dropped(report):
    """The page says so and the export used to skip the section entirely, so
    a reader of the file could not tell whether the peer set was absent or
    simply never attempted. Nothing is silently missing."""
    report.bundle.comps = None
    html = report_to_html(report)
    assert "Comparable companies" in html
    assert "No peer comparison is available" in html


def test_the_export_carries_the_sensitivity_grid(report):
    """A model review does not pass without one, and it existed only on the
    screen while the file is the thing that gets circulated."""
    html = report_to_html(report)
    assert "Sensitivity" in html
    assert "WACC" in html


def test_the_export_and_the_page_read_one_disclaimer(report):
    """Two texts for one legal notice is how they end up saying different
    things, with the divergence appearing in the file somebody forwards."""
    from asset_researcher.config import get_settings

    configured = " ".join(get_settings().report.disclaimer.split())
    assert configured[:60] in report_to_html(report)


# ------------------------------------------------------------- Markdown


def test_the_markdown_export_opens_with_the_company_and_its_provenance(report):
    text = report_to_markdown(report)
    lines = text.splitlines()
    assert lines[0].startswith("# ")
    assert report.bundle.ticker in lines[0]
    assert report.bundle.as_of in text


def test_the_markdown_export_carries_the_argument_not_only_the_figures(report):
    text = report_to_markdown(report)
    for heading in (
        "## Headline",
        "## Financial trajectory",
        "## Narrative against reported figures",
        "## Bull case",
        "## Bear case",
        "## Disconfirming evidence",
        "## Sources",
    ):
        assert heading in text


def test_the_markdown_financial_summary_is_a_table_in_statement_order(report):
    text = report_to_markdown(report)
    summary = text.split("## Financial summary", 1)[1]
    revenue = summary.index("| Revenue |")
    net_income = summary.index("| Net income |")
    assert revenue < net_income
    assert "USD millions" in summary


def test_model_and_filing_text_cannot_reach_the_markdown_export_as_markup(report):
    """Most Markdown renderers (wikis, issue trackers, chat clients) pass
    inline HTML straight through, so a .md file is as much a delivery
    surface as the .html one.

    The previous version of this test grepped for `<(div|span|table|svg|p)`
    against a fixture containing no adversarial text, so it passed on a
    payload that did reach the file verbatim."""
    report.bundle.company_name = "Evil Co <script>alert(1)</script>"
    report.reconciliation.disconfirming_evidence = (
        "<img src=x onerror=alert(1)> The thesis rests on one segment."
    )
    report.reconciliation.bull_case = "<iframe src=//evil></iframe>"
    text = report_to_markdown(report)

    # The property that matters is that no tag can form. The attribute text
    # surviving as literal characters is correct: it is prose at that point,
    # and stripping it would silently alter what a filing said.
    assert "<" not in text
    assert ">" not in text
    assert "&lt;script&gt;" in text
    # The content still travels; only the markup is neutralised.
    assert "The thesis rests on one segment." in text


def test_a_pipe_in_a_company_name_does_not_break_the_tables(report):
    """One unescaped pipe silently destroys every row of the table it lands
    in, and a reader sees a mangled statement rather than an error."""
    report.bundle.company_name = "Smith | Jones Holdings"
    text = report_to_markdown(report)
    assert "Smith \\| Jones Holdings" in text


def test_the_markdown_export_ends_with_the_disclaimer(report):
    text = report_to_markdown(report)
    assert text.rstrip().endswith("Report date " + report.bundle.as_of + ".")


def test_a_fixture_run_can_stamp_the_file_so_it_cannot_be_forwarded_by_mistake(
    report,
):
    """Fixture prose against a real ticker's real filings produces a styled,
    self-contained document making false statements about a listed company,
    and it is the most natural file in the repository to forward as a
    sample."""
    notice = "This file was produced for front-end work."
    html = report_to_html(report, notice=notice)
    text = report_to_markdown(report, notice=notice)

    assert "Not a research note" in html
    # Compared inside the body: the stylesheet in the head also mentions
    # every class name, so searching the whole document finds the CSS rule.
    body = html.split("<body>", 1)[1]
    assert body.index(notice) < body.index("ar-masthead")
    assert text.startswith("> **NOT A RESEARCH NOTE.**")


def test_a_normal_report_carries_no_such_banner(report):
    assert "Not a research note" not in report_to_html(report)
    assert "NOT A RESEARCH NOTE" not in report_to_markdown(report)
