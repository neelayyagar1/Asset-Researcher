"""Builds a SourceBundle for a ticker.

Deliberately fail-soft. Any single source may be unavailable, a company with
no proxy, a filing whose MD&A is a cross-reference, a Finnhub endpoint not on
the free tier, and none of those should abort a report. Each failure is
recorded as a Gap and the report shows it. The one exception is the 10-K: with
no primary filing there is nothing to analyse, so that raises.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from datetime import date
from pathlib import Path

from asset_researcher.analysis.bundle import SourceBundle, SourcePassage
from asset_researcher.config import Settings
from asset_researcher.documents.fetch import fetch_filing_document
from asset_researcher.documents.proxy import extract_proxy_sections
from asset_researcher.documents.sections import (
    extract_8k_content,
    recover_cross_referenced_section,
    split_items,
)
from asset_researcher.documents.store import DocumentStore
from asset_researcher.llm.provider import LLMProvider
from asset_researcher.quant.comps import CompsTable, build_comp_row
from asset_researcher.quant.derived import compute_derived
from asset_researcher.quant.metrics_config import line_items_for_sector
from asset_researcher.quant.peer_metrics import resolve_peer_concepts
from asset_researcher.quant.resolve import resolve_concepts
from asset_researcher.quant.scores import compute_health_scores
from asset_researcher.quant.sectors import classify_sic, display_industry
from asset_researcher.quant.series import build_metric_series
from asset_researcher.quant.validate import validate
from asset_researcher.quant.valuation import (
    build_cases,
    cash_flow_context,
    NO_ENTERPRISE_DCF,
    derive_dcf_inputs,
    implied_expectations,
    run_dcf,
)
from asset_researcher.sources.edgar.client import EdgarClient
from asset_researcher.sources.edgar.facts import get_raw_facts
from asset_researcher.sources.edgar.filings import exhibit_filename, get_filing_index
from asset_researcher.sources.edgar.resolve import resolve_ticker
from asset_researcher.sources.finnhub import FinnhubClient

# Narrative Items worth citing, and how they are labelled in the report.
_ITEM_LABELS = {
    "1": "Item 1. Business",
    "1A": "Item 1A. Risk Factors",
    "7": "Item 7. Management's Discussion and Analysis",
    "7A": "Item 7A. Market Risk",
}

_MAX_PEERS = 8

# EDGAR's documented ceiling is 10 requests/second and the client already
# rate-limits; this bounds concurrency without approaching it.
_PEER_WORKERS = 6


def assemble_bundle(
    ticker: str,
    settings: Settings,
    edgar: EdgarClient,
    finnhub: FinnhubClient,
    llm: LLMProvider,
    store: DocumentStore | None = None,
    peer_override: list[str] | None = None,
) -> SourceBundle:
    store = store or DocumentStore(Path("data/documents"))
    ticker = ticker.strip().upper()

    cik, company_name = resolve_ticker(edgar, ticker)
    index = get_filing_index(edgar, cik)
    sector = classify_sic(index.sic, settings)

    profile = _safe(lambda: finnhub.get_profile(ticker))
    bundle = SourceBundle(
        ticker=ticker,
        cik=cik,
        company_name=company_name,
        sector_class=sector,
        display_industry=display_industry(
            index.sic_description, profile.industry if profile else None
        ),
        as_of=date.today().isoformat(),
    )

    _add_market_data(bundle, finnhub, ticker, profile)
    series = _add_quantitative(bundle, settings, edgar, llm, cik, sector)
    _add_filing_text(bundle, settings, edgar, store, cik, index)
    _add_proxy_text(bundle, settings, edgar, store, cik, index)
    _add_recent_events(bundle, settings, edgar, store, cik, index, finnhub, ticker)
    _add_comps(
        bundle, settings, edgar, finnhub, llm, ticker, company_name, series,
        subject_sic=index.sic, subject_sic_description=index.sic_description,
        peer_override=peer_override,
    )
    _add_valuation(bundle, series, profile)

    return bundle


def _add_valuation(bundle, series, profile=None) -> None:
    """Run the cash flow model, its cases, and the reverse solve.

    A forward DCF on a highly rated company routinely lands far from the
    market, so the implied expectations are the primary output and the target
    is illustrative. See quant/valuation.py.
    """
    if series is None:
        bundle.add_gap("valuation", "No filed data; no valuation model produced.")
        return

    # Current shares outstanding, not last year's weighted-average diluted
    # count. Equity value is a figure as at today and dividing it by an
    # average over a fiscal year mixes a duration with an instant: on Apple
    # the filed diluted count of 15,005m against the 14,596m the market
    # capitalisation implies understates value per share by 2.8%, and on a
    # filer that retired a tenth of its shares mid-year the error is a tenth.
    #
    # Weighted-average diluted shares remain the right denominator for
    # per-share earnings, and are still used there.
    shares_outstanding = profile.shares_outstanding if profile else None
    shares_basis = "Current shares outstanding, from the market data provider"

    if not shares_outstanding and bundle.market_cap and bundle.quote:
        shares_outstanding = bundle.market_cap / bundle.quote.price
        shares_basis = "Implied by market capitalisation over the traded price"

    if not shares_outstanding:
        filed = series.series.get("shares_diluted") or []
        shares_outstanding = filed[-1].value if filed else None
        shares_basis = (
            "Weighted-average diluted shares for the last filed year. This "
            "is a fiscal-year average compared against an equity value as at "
            "today, so it ignores any share count change since"
        )

    # Computed regardless of whether a cash flow model is possible: the
    # multiple the market pays is informative even when the model is not.
    bundle.cash_context = cash_flow_context(series, bundle.market_cap)

    inputs = derive_dcf_inputs(
        series, shares_outstanding, sector_class=bundle.sector_class
    )
    if inputs is None:
        # Name the actual reason. Banks and REITs are refused on principle
        # rather than for missing data, and reporting a sector exclusion as
        # "capital expenditure is unavailable" is true of the filing but
        # misleading about the decision: a reader would go looking for the
        # missing tag instead of understanding that an enterprise model
        # does not describe the business.
        if bundle.sector_class in NO_ENTERPRISE_DCF:
            bundle.add_gap(
                "valuation",
                f"No discounted cash flow is modelled for this filer. The "
                f"model discounts unlevered free cash flow to an enterprise "
                f"value and bridges to equity across net debt, which does "
                f"not describe a {'deposit-funded balance sheet' if bundle.sector_class == 'financial' else 'company valued on funds from operations against asset value'}. "
                f"Comparables, the statement table and the health screens "
                f"still apply.",
            )
        else:
            bundle.add_gap(
                "valuation",
                "Filed statements do not support a discounted cash flow "
                "model (operating cash flow, capital expenditure or share "
                "count is unavailable, or free cash flow is negative).",
            )
        return

    # The share count's provenance travels with the model, because which
    # count was used changes the per-share answer and a reviewer cannot tell
    # from the number alone.
    inputs.basis["shares_outstanding"] = shares_basis
    bundle.dcf_inputs = inputs
    bundle.dcf = run_dcf(inputs)
    bundle.valuation_cases = build_cases(inputs)
    if bundle.quote:
        bundle.implied = implied_expectations(inputs, bundle.quote.price)


def _safe(fn):
    """Best-effort call for an optional source."""
    try:
        return fn()
    except Exception:
        return None


# --- market data --------------------------------------------------------


def _add_market_data(bundle, finnhub, ticker, profile) -> None:
    quote = _safe(lambda: finnhub.get_quote(ticker))
    if quote is None:
        bundle.add_gap("price", "Quote unavailable; valuation multiples omitted.")
    bundle.quote = quote
    if profile is not None:
        bundle.market_cap = profile.market_cap
    else:
        bundle.add_gap("profile", "Company profile unavailable from Finnhub.")


# --- quantitative -------------------------------------------------------


def _add_quantitative(bundle, settings, edgar, llm, cik, sector):
    facts = _safe(lambda: get_raw_facts(edgar, cik))
    if facts is None:
        bundle.add_gap(
            "xbrl",
            "No XBRL company facts available; no financial figures can be shown.",
            severity="error",
        )
        return None

    mapping = resolve_concepts(llm, settings, cik, sector, facts)
    names = [li.name for li in line_items_for_sector(sector)]
    # Six years retained, five displayed. The sixth is the lookback the
    # earliest growth rate is computed against; without it the first column
    # of every growth row printed blank. The facts are already downloaded,
    # so the extra year costs nothing.
    series = build_metric_series(facts, mapping, sector, names, years=6)

    bundle.series = series
    bundle.derived = compute_derived(series, sector=series.sector)
    bundle.health_scores = compute_health_scores(series, sector, bundle.market_cap)
    bundle.validation = validate(series)

    # Every validation issue is surfaced, not only the fatal ones. Warnings
    # were computed and discarded, so `check_period_alignment` was dead from
    # the reader's point of view and a filer reporting zero revenue against
    # a hundred billion of net income exported as a clean note carrying a
    # price target. Nothing is silently missing is the first rule here, and
    # a check that fires into a field nobody reads is worse than no check.
    if bundle.validation:
        for issue in bundle.validation.issues:
            bundle.add_gap(
                f"xbrl:{issue.check}", issue.message, severity=issue.severity
            )

    if series.unmapped:
        bundle.add_gap(
            "xbrl:unmapped",
            f"Could not map {len(series.unmapped)} "
            f"{'metric' if len(series.unmapped) == 1 else 'metrics'} "
            f"for this filer: "
            f"{', '.join(sorted(series.unmapped)[:6])}.",
        )
    return series


# --- filing text --------------------------------------------------------


def _add_filing_text(bundle, settings, edgar, store, cik, index) -> None:
    tenk = index.latest("10-K")
    if tenk is None:
        bundle.add_gap("10-K", "No 10-K on file.", severity="error")
        return

    doc = fetch_filing_document(edgar, store, cik, tenk)
    bundle.filing_dates["10-K"] = doc.filing_date

    budget = settings.bundle.token_budget.get("filing_items", 40_000) * 4
    sections = split_items(doc.text)
    if not sections:
        bundle.add_gap(
            "10-K:sections",
            "Could not split the 10-K into Items; narrative unavailable.",
            severity="error",
        )
        return

    per_item = budget // max(len(_ITEM_LABELS), 1)

    for item, label in _ITEM_LABELS.items():
        section = sections.get(item)

        if section is None:
            bundle.add_gap(f"10-K:Item {item}", "Item not found in this filing.")
            continue

        if section.is_cross_reference:
            # JPMorgan's Item 7 is a 398-char pointer; the MD&A lives outside
            # the Item sequence. Recover it by content or say it is missing.
            recovered = recover_cross_referenced_section(
                doc.text, item, char_budget=per_item
            )
            if not recovered:
                bundle.add_gap(
                    f"10-K:Item {item}",
                    "Item incorporated by reference and its content could not "
                    "be located; this section of the report has no filing "
                    "narrative behind it.",
                    severity="error",
                )
                continue
            bundle.add_gap(
                f"10-K:Item {item}",
                "Item incorporated by reference; content recovered from "
                "elsewhere in the filing by content matching.",
            )
            for part in recovered:
                bundle.passages.append(
                    _passage(doc, label, part.start, part.end, part.text)
                )
            continue

        text = section.text[:per_item]
        if len(section.text) > per_item:
            bundle.add_gap(
                f"10-K:Item {item}",
                f"Truncated to {per_item:,} of {len(section.text):,} characters "
                f"to fit the context budget.",
            )
        bundle.passages.append(
            _passage(doc, label, section.start, section.start + len(text), text)
        )


def _passage(doc, label, start, end, text, tier="A") -> SourcePassage:
    return SourcePassage(
        doc_id=doc.doc_id,
        source_url=doc.source_url,
        form=doc.form,
        filing_date=doc.filing_date,
        label=label,
        tier=tier,
        start=start,
        end=end,
        text=text,
    )


# --- proxy --------------------------------------------------------------


def _add_proxy_text(bundle, settings, edgar, store, cik, index) -> None:
    proxy = index.latest("DEF 14A")
    if proxy is None:
        bundle.add_gap(
            "DEF 14A",
            "No proxy statement on file; compensation and board analysis "
            "unavailable.",
        )
        return

    doc = fetch_filing_document(edgar, store, cik, proxy)
    bundle.filing_dates["DEF 14A"] = doc.filing_date

    budget = settings.bundle.token_budget.get("proxy_extract", 12_000) * 4
    sections = extract_proxy_sections(doc.text, char_budget=budget)
    if not sections:
        bundle.add_gap(
            "DEF 14A",
            "Proxy statement found but no compensation or governance content "
            "scored above threshold.",
        )
        return

    for section in sections:
        bundle.passages.append(
            _passage(
                doc,
                f"Proxy. {section.title}",
                section.start,
                section.end,
                section.text,
            )
        )


# --- recent events ------------------------------------------------------


def _add_recent_events(
    bundle, settings, edgar, store, cik, index, finnhub, ticker
) -> None:
    """8-Ks and news, the only cover for a 10-K that may be a year old."""
    budget = settings.bundle.token_budget.get("form_8k", 3_000) * 4
    recent_8k = index.recent("8-K", limit=4)

    share = budget // max(len(recent_8k), 1)

    for filing in recent_8k:
        doc = _safe(lambda f=filing: fetch_filing_document(edgar, store, cik, f))
        if doc is None:
            continue
        # Skip the inline-XBRL cover block, which is metadata rather than
        # disclosure. Offsets stay relative to the stored document so
        # citations still resolve.
        content = extract_8k_content(doc.text)
        offset = len(doc.text) - len(content)
        label = f"8-K filed {doc.filing_date}" + (
            f" (items {filing.items})" if filing.items else ""
        )
        bundle.passages.append(
            _passage(doc, label, offset, offset + len(content[:share]),
                     content[:share])
        )

        exhibit = _earnings_exhibit(edgar, store, cik, filing, bundle)
        if exhibit is not None:
            body = extract_8k_content(exhibit.text)
            start = len(exhibit.text) - len(body)
            bundle.passages.append(
                _passage(
                    exhibit,
                    f"8-K exhibit filed {exhibit.filing_date} "
                    f"(results announcement)",
                    start,
                    start + len(body[:share]),
                    body[:share],
                )
            )

    if recent_8k:
        bundle.filing_dates["8-K"] = recent_8k[0].filing_date
    else:
        bundle.add_gap("8-K", "No recent 8-K filings found.")

    news = _safe(lambda: finnhub.get_news(ticker)) or []
    if not news:
        bundle.add_gap("news", "No recent news available.")
    bundle.news = news


def _earnings_exhibit(edgar, store, cik, filing, bundle):
    """The press release attached to a results announcement.

    An Item 2.02 8-K's primary document is a cover page referring the reader
    to Exhibit 99.1, where the quarterly figures actually are. Measured on
    Apple: two such filings ingested at 1,188 and 1,193 characters, neither
    containing a single figure, while the 10-K behind them was eleven
    months old. The exhibit is the only current financial disclosure the
    pipeline can reach.

    Only fetched for filings that announce results, so this costs one extra
    request on the filings where it pays and none anywhere else.
    """
    if not filing.reports_results:
        return None

    name = _safe(lambda: exhibit_filename(edgar, cik, filing))
    if not name:
        bundle.add_gap(
            "8-K exhibit",
            f"The results announcement filed {filing.filing_date} lists no "
            f"readable exhibit, so only its cover page was read.",
        )
        return None

    exhibit = _safe(
        lambda: fetch_filing_document(
            edgar, store, cik, filing,
            title=f"8-K exhibit filed {filing.filing_date}",
            filename=name,
        )
    )
    if exhibit is None:
        bundle.add_gap(
            "8-K exhibit",
            f"Exhibit {name} from the results announcement filed "
            f"{filing.filing_date} could not be retrieved.",
        )
    return exhibit


# --- comps --------------------------------------------------------------


def _add_comps(
    bundle, settings, edgar, finnhub, llm, ticker, company_name, series,
    subject_sic: str = "", subject_sic_description: str = "",
    peer_override: list[str] | None = None,
) -> None:
    """The comparables table.

    `peer_override` pins the set. Choosing comparables is the analytical
    judgment in relative valuation, and the vendor list is a starting point
    rather than an answer: on Apple it returns Everpure at 158x EV/EBITDA
    and Hewlett Packard Enterprise at 1,284x trailing earnings, and the
    median is then computed across businesses nobody would pair. Every
    reviewer who looked at that table asked to be able to replace it.
    """
    if peer_override:
        peers = [p.upper() for p in peer_override if p.upper() != ticker]
        source = "Analyst-specified peer set"
    else:
        peers = _safe(lambda: finnhub.get_peers(ticker)) or []
        source = "Finnhub peer list, not screened"
    peers = peers[:_MAX_PEERS]

    table = CompsTable(subject_ticker=ticker, peer_source=source)
    subject_row = build_comp_row(
        ticker=ticker,
        company_name=company_name,
        is_subject=True,
        market_cap=bundle.market_cap,
        price=bundle.quote.price if bundle.quote else None,
        series=series,
    )
    table.rows.append(
        replace(subject_row, sic=subject_sic, sic_description=subject_sic_description)
    )

    # Peers are independent of one another, so they are fetched concurrently.
    # Sequentially this was the dominant cost of a report: each peer needed a
    # filing index, a 4MB companyfacts download and (previously) its own model
    # call, measured at 9.7s each.
    if peers:
        with ThreadPoolExecutor(max_workers=_PEER_WORKERS) as pool:
            futures = {
                pool.submit(_peer_row, settings, edgar, finnhub, peer): peer
                for peer in peers
            }
            for future in as_completed(futures):
                peer = futures[future]
                try:
                    table.rows.append(future.result())
                except Exception:
                    table.excluded.append(peer)

        # Concurrency reorders results; restore the peer list's own order so
        # the table is stable between runs.
        order = {ticker_name: i for i, ticker_name in enumerate(peers)}
        table.rows.sort(key=lambda r: -1 if r.is_subject else order.get(r.ticker, 99))

    if table.excluded:
        bundle.add_gap(
            "comps",
            f"Excluded {len(table.excluded)} "
            f"{'peer' if len(table.excluded) == 1 else 'peers'} "
            f"with no usable data: "
            f"{', '.join(table.excluded)}.",
        )
    if not peers:
        bundle.add_gap("comps", "No peer list available; relative valuation omitted.")

    bundle.comps = table


def _peer_row(settings, edgar, finnhub, peer_ticker):
    profile = finnhub.get_profile(peer_ticker)
    quote = finnhub.get_quote(peer_ticker)
    market_cap = profile.market_cap if profile else None
    name = profile.name if profile else peer_ticker

    peer_series = None
    peer_sic = ""
    peer_sic_description = ""
    try:
        cik, _ = resolve_ticker(edgar, peer_ticker)
        index = get_filing_index(edgar, cik)
        peer_sic, peer_sic_description = index.sic, index.sic_description
        sector = classify_sic(index.sic, settings)
        facts = get_raw_facts(edgar, cik)
        # Static tag resolution, not a model call. See quant/peer_metrics.py:
        # a peer contributes a few ratios to one table, and a missing tag
        # yields an absent multiple rather than a wrong one.
        mapping = resolve_peer_concepts(set(facts.available_concept_names()))
        names = [li.name for li in line_items_for_sector(sector)]
        peer_series = build_metric_series(facts, mapping, sector, names, years=2)
    except Exception:
        peer_series = None

    row = build_comp_row(
        ticker=peer_ticker,
        company_name=name,
        is_subject=False,
        market_cap=market_cap,
        price=quote.price if quote else None,
        series=peer_series,
    )
    return replace(row, sic=peer_sic, sic_description=peer_sic_description)
