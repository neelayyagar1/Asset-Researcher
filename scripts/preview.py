"""Render the report with no model spend, for front-end work.

A live report costs an API call and about two minutes, which is too slow a
loop to lay out a table against. Two modes:

    python scripts/preview.py              fixtures only, no network
    python scripts/preview.py --ticker AAPL  real filings, fixture prose

The second is the useful one for checking figures. It runs the real
retrieval path (EDGAR submissions, XBRL companyfacts, Finnhub quotes and
peers) so every number, chart and comparables row is the genuine article,
and substitutes the fixture model only for the two narrative calls. That
puts real geometry in front of the layout: five fiscal years at Apple's
scale, a peer set containing an outlier, negative net debt.

Neither mode exercises the Streamlit shell (tab bar, sidebar, controls).
Those need the app running.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from asset_researcher.analysis.assemble import assemble_bundle  # noqa: E402
from asset_researcher.analysis.mandate import parse_mandate  # noqa: E402
from asset_researcher.analysis.narrative import generate_narrative  # noqa: E402
from asset_researcher.analysis.reconcile import generate_reconciliation  # noqa: E402
from asset_researcher.analysis.report import build_report  # noqa: E402
from asset_researcher.config import get_settings  # noqa: E402
from asset_researcher.documents.store import DocumentStore  # noqa: E402
from asset_researcher.ui.export import report_to_html, report_to_markdown  # noqa: E402
from tests.fakes import (  # noqa: E402
    TICKER,
    FakeEdgarClient,
    FakeFinnhubClient,
    FakeLLM,
)


def main() -> None:
    out = ROOT / "build"
    out.mkdir(exist_ok=True)

    live = None
    if "--ticker" in sys.argv:
        live = sys.argv[sys.argv.index("--ticker") + 1].upper()

    settings = get_settings()
    llm = FakeLLM()

    if live:
        # Real retrieval, fixture prose. Concept resolution is cached per
        # company, so a ticker reported on before needs no model call here.
        from asset_researcher.sources.edgar.client import EdgarClient
        from asset_researcher.sources.finnhub import FinnhubClient

        edgar, finnhub = EdgarClient(settings), FinnhubClient(settings)
        ticker = live
    else:
        edgar, finnhub = FakeEdgarClient(), FakeFinnhubClient()
        ticker = TICKER

    bundle = assemble_bundle(
        ticker, settings, edgar, finnhub, llm,
        store=DocumentStore(out / "documents"),
    )
    narrative = generate_narrative(bundle, llm)
    mandate = parse_mandate("long only, 3-5 years, quality compounders", llm)
    reconciliation = generate_reconciliation(bundle, narrative, mandate, llm)
    report = build_report(bundle, mandate, narrative, reconciliation)

    # The prose is always fixture text. Combined with a real ticker's real
    # filings, real figures and a real SEC link, the output is a styled,
    # self-contained, export-ready document making fabricated statements
    # about a listed company. It is also the most natural file in the
    # repository to forward as a sample. So it is stamped in the filename
    # and at the top of both files, where nobody can forward it by accident.
    notice = (
        "This file was produced for front-end work. Every figure in it is "
        "real and every narrative sentence is placeholder text from the "
        "test fixtures, so the prose makes false statements about a real "
        "company. It is not research, it is not a draft of research, and it "
        "must not be circulated."
    )
    name = f"FIXTURE-DO-NOT-CIRCULATE-{ticker.lower()}"
    (out / f"{name}.html").write_text(
        report_to_html(report, notice=notice), encoding="utf-8"
    )
    (out / f"{name}.md").write_text(
        report_to_markdown(report, notice=notice), encoding="utf-8"
    )
    print(f"wrote {out / name}.html")
    print(f"wrote {out / name}.md")


if __name__ == "__main__":
    main()
