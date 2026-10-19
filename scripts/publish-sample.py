"""Build a static, publishable sample note.

The live application takes about a minute per report and costs an API
call, which is the wrong thing to put behind a link in a cold email: the
reader waits, and every click spends money. A pre-rendered note loads
instantly, costs nothing to serve, needs no API key, and is the actual
deliverable anyway.

    python scripts/publish-sample.py --ticker AAPL

Writes `build/site/` as a complete static site: one page per ticker plus an
index. Deploy that directory anywhere that serves files.

This runs the REAL pipeline, so it needs working credentials and it spends
the API call once rather than once per visitor. Run
`python scripts/check-credentials.py` first.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from asset_researcher.analysis.assemble import assemble_bundle  # noqa: E402
from asset_researcher.analysis.mandate import (  # noqa: E402
    load_presets,
    parse_mandate,
)
from asset_researcher.analysis.narrative import generate_narrative  # noqa: E402
from asset_researcher.analysis.reconcile import generate_reconciliation  # noqa: E402
from asset_researcher.analysis.report import build_report  # noqa: E402
from asset_researcher.config import get_settings  # noqa: E402
from asset_researcher.llm.claude import ClaudeProvider  # noqa: E402
from asset_researcher.sources.edgar.client import EdgarClient  # noqa: E402
from asset_researcher.sources.finnhub import FinnhubClient  # noqa: E402
from asset_researcher.ui import theme  # noqa: E402
from asset_researcher.ui.export import report_to_html, report_to_markdown  # noqa: E402


def build(ticker: str, mandate_text: str, out: Path) -> tuple[str, str]:
    settings = get_settings()
    edgar = EdgarClient(settings)
    finnhub = FinnhubClient(settings)
    llm = ClaudeProvider(settings)

    print(f"  retrieving filings for {ticker}")
    bundle = assemble_bundle(ticker, settings, edgar, finnhub, llm)
    print(f"  {len(bundle.passages)} passages, "
          f"{bundle.total_passage_chars:,} characters")

    mandate = parse_mandate(mandate_text, llm)
    print("  drafting and verifying citations")
    narrative = generate_narrative(
        bundle, llm, effort=settings.llm.effort.get("narrative", "medium")
    )
    print("  reconciling against filed figures")
    reconciliation = generate_reconciliation(
        bundle, narrative, mandate, llm,
        effort=settings.llm.effort.get("reconciliation", "high"),
    )
    report = build_report(bundle, mandate, narrative, reconciliation)

    slug = ticker.lower()
    (out / f"{slug}.html").write_text(report_to_html(report), encoding="utf-8")
    (out / f"{slug}.md").write_text(report_to_markdown(report), encoding="utf-8")
    print(f"  cost so far ${llm.usage.cost_usd:,.2f}")
    return bundle.company_name, slug


def write_index(out: Path, notes: list[tuple[str, str]]) -> None:
    """A plain index. One link per note, and what the reader is looking at."""
    rows = "".join(
        f'<li><a href="{slug}.html">{escape(name)}</a>'
        f'<span>{escape(slug.upper())}</span></li>'
        for name, slug in notes
    )
    out.joinpath("index.html").write_text(
        "<!doctype html>"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Asset Researcher, sample notes</title>"
        f"{theme.document_stylesheet()}"
        "<style>body{margin:0;background:var(--paper);color:var(--ink);"
        "font-family:var(--sans)}"
        ".ar-page{max-width:62ch;margin:0 auto;padding:4rem 2rem}"
        "ul{list-style:none;padding:0;margin:2rem 0 0;"
        "border-top:1px solid var(--rule)}"
        "li{display:flex;justify-content:space-between;align-items:baseline;"
        "padding:0.9rem 0;border-bottom:1px solid var(--rule-soft)}"
        "li span{font-family:var(--mono);font-size:var(--t-micro);"
        "color:var(--ink-muted)}</style></head>"
        '<body><div class="ar-page">'
        "<h1>Asset Researcher</h1>"
        '<p class="lede">Equity research built from the filings themselves. '
        "Every figure below is read from the company's own XBRL submissions "
        "to the SEC, and every narrative claim carries a citation resolved "
        "against the source text.</p>"
        f"<ul>{rows}</ul>"
        f'<p class="ar-foot">Generated {date.today().isoformat()}. '
        "Research assistance, not investment advice.</p>"
        "</div></body></html>",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", action="append", required=True,
                        help="repeatable, one note per ticker")
    parser.add_argument("--mandate", default="")
    args = parser.parse_args()

    presets = load_presets()
    mandate_text = args.mandate or (presets[0].description if presets else "")

    out = ROOT / "build" / "site"
    out.mkdir(parents=True, exist_ok=True)

    notes = []
    for ticker in args.ticker:
        print(f"{ticker}:")
        notes.append(build(ticker.upper(), mandate_text, out))

    write_index(out, notes)
    print(f"\nwrote {len(notes)} note(s) to {out}")
    print("deploy with:  npx wrangler pages deploy build/site")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
