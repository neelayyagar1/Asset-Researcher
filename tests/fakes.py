"""In-memory stand-ins for the network clients.

These fake only the *transport*. Every parsing, mapping, sectioning, scoring
and verification path runs for real, which is the point: the orchestration in
assemble.py and narrative.py had no regression protection at all (0% and 32%
covered) despite being the code most likely to break when something upstream
changes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from asset_researcher.llm.provider import (
    Citation,
    CitedResponse,
    CitedSpan,
    LLMProvider,
)
from asset_researcher.sources.finnhub import CompanyProfile, NewsItem, Quote

CIK = 320193
TICKER = "TEST"

# --- canned filing HTML -------------------------------------------------
# Shaped like a real filing: a table of contents that repeats every Item
# header, then the body. split_items() must reject the TOC.

_TOC = """
<p>Item 1. Business</p><p>Item 1A. Risk Factors</p><p>Item 7. Management's
Discussion and Analysis of Financial Condition and Results of Operations</p>
<p>Item 7A. Quantitative and Qualitative Disclosures About Market Risk</p>
<p>Item 8. Financial Statements</p>
"""

_BODY = """
<p>Item 1. Business</p>
<p>Testco designs and sells industrial widgets through two segments, Widgets
and Services. The Company operates in 14 countries and sells through direct
and channel partners. Its fiscal year ends on the last Saturday of December.</p>
{filler1}
<p>Item 1A. Risk Factors</p>
<p>The Company depends on a limited number of contract manufacturers. A
disruption at any one of them could materially affect the ability to meet
demand. Competition in widgets is intense and pricing pressure is persistent.</p>
{filler2}
<p>Item 7. Management's Discussion and Analysis of Financial Condition and
Results of Operations</p>
<p>Revenue grew during the period, driven primarily by Services. Management
attributes gross margin expansion to improved supply chain execution and a
favourable mix shift toward higher-margin offerings.</p>
{filler3}
<p>Item 7A. Quantitative and Qualitative Disclosures About Market Risk</p>
<p>The Company is exposed to interest rate risk on its investment portfolio
and to foreign exchange risk on non-dollar revenue.</p>
{filler4}
<p>Item 8. Financial Statements</p>
<p>See the consolidated financial statements.</p>
"""

TENK_HTML = "<html><body>" + _TOC + _BODY.format(
    filler1="<p>Additional business detail. </p>" * 40,
    filler2="<p>Additional risk detail. </p>" * 40,
    filler3="<p>Additional MD&amp;A detail. </p>" * 40,
    filler4="<p>Additional market risk detail. </p>" * 20,
) + "</body></html>"

# 8-K: inline-XBRL cover metadata first, disclosure after, the shape that
# caused a CEO succession to be silently dropped.
EIGHTK_HTML = (
    "<html><body>"
    + "<p>true</p><p>NASDAQ</p><p>0000320193</p><p>2026-04-17</p>" * 60
    + "<p>Item 5.02 Departure of Directors or Certain Officers.</p>"
    + "<p>On April 20, 2026, Testco announced that its Chief Executive Officer "
      "will transition to Executive Chair effective September 1, 2026.</p>"
    + "</body></html>"
)

PROXY_HTML = (
    "<html><body>"
    + "<p>I. Summary compensation table</p><p>63</p>" * 20  # contents listing
    + (
        "<p>Total compensation for the named executive officers reflects "
        "salary of $1,200,000, stock awards valued at $18,400,000, and all "
        "other compensation. The compensation committee approved a target "
        "award reflecting performance share vesting and a clawback provision. "
        "Director nominees are evaluated by the nominating committee; the "
        "board oversight framework is reviewed annually and each independent "
        "director serves on at least one committee.</p>"
    ) * 40
    + "</body></html>"
)


def _fact(end: str, val: float, start: str | None = None) -> dict:
    return {
        "start": start, "end": end, "val": val, "accn": "0000320193-26-000001",
        "fy": int(end[:4]), "fp": "FY", "form": "10-K",
        "filed": f"{int(end[:4]) + 1}-02-01", "frame": f"CY{end[:4]}",
    }


def _duration(end: str, val: float) -> dict:
    return _fact(end, val, start=f"{int(end[:4])}-01-01")


# Internally consistent so validate() passes: Assets = Liabilities + Equity,
# Revenue > NetIncome.
COMPANY_FACTS = {
    "facts": {
        "us-gaap": {
            "RevenueFromContractWithCustomerExcludingAssessedTax": {
                "units": {"USD": [_duration("2024-12-28", 380e9), _duration("2025-12-27", 400e9)]}
            },
            "NetIncomeLoss": {"units": {"USD": [_duration("2024-12-28", 90e9), _duration("2025-12-27", 100e9)]}},
            "GrossProfit": {"units": {"USD": [_duration("2024-12-28", 168e9), _duration("2025-12-27", 180e9)]}},
            "OperatingIncomeLoss": {"units": {"USD": [_duration("2024-12-28", 110e9), _duration("2025-12-27", 120e9)]}},
            "CostOfGoodsAndServicesSold": {"units": {"USD": [_duration("2025-12-27", 220e9)]}},
            "Assets": {"units": {"USD": [_fact("2024-12-28", 380e9), _fact("2025-12-27", 400e9)]}},
            "Liabilities": {"units": {"USD": [_fact("2024-12-28", 290e9), _fact("2025-12-27", 300e9)]}},
            "StockholdersEquity": {"units": {"USD": [_fact("2024-12-28", 90e9), _fact("2025-12-27", 100e9)]}},
            "AssetsCurrent": {"units": {"USD": [_fact("2025-12-27", 150e9)]}},
            "LiabilitiesCurrent": {"units": {"USD": [_fact("2025-12-27", 130e9)]}},
            "RetainedEarningsAccumulatedDeficit": {"units": {"USD": [_fact("2025-12-27", 20e9)]}},
            "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": [_fact("2025-12-27", 30e9)]}},
            "NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": [_duration("2025-12-27", 110e9)]}},
            "LongTermDebt": {"units": {"USD": [_fact("2025-12-27", 90e9)]}},
            "CommercialPaper": {"units": {"USD": [_fact("2025-12-27", 8e9)]}},
            "DepreciationDepletionAndAmortization": {"units": {"USD": [_duration("2025-12-27", 12e9)]}},
            "AccountsReceivableNetCurrent": {"units": {"USD": [_fact("2025-12-27", 60e9)]}},
            "PaymentsToAcquirePropertyPlantAndEquipment": {"units": {"USD": [_duration("2025-12-27", 11e9)]}},
            "InterestExpense": {"units": {"USD": [_duration("2025-12-27", 3e9)]}},
            "WeightedAverageNumberOfDilutedSharesOutstanding": {
                "units": {"shares": [_duration("2025-12-27", 15e9)]}
            },
        }
    }
}

SUBMISSIONS = {
    "name": "Testco Inc.",
    "sic": "3571",
    "sicDescription": "Electronic Computers",
    "filings": {
        "recent": {
            "form": ["10-K", "DEF 14A", "8-K"],
            "filingDate": ["2026-02-01", "2026-03-01", "2026-04-20"],
            "reportDate": ["2025-12-27", "", ""],
            "accessionNumber": [
                "0000320193-26-000001", "0000320193-26-000002", "0000320193-26-000003",
            ],
            "primaryDocument": ["tenk.htm", "proxy.htm", "eightk.htm"],
            "items": ["", "", "5.02"],
        },
        "files": [],
    },
}


class FakeEdgarClient:
    """Dispatches on URL. Every parser downstream runs for real."""

    def __init__(self) -> None:
        self.requested: list[str] = []

    def get_json(self, url: str, cache_key: str, ttl_seconds: float | None) -> dict:
        self.requested.append(url)
        if "company_tickers" in url:
            return {"0": {"cik_str": CIK, "ticker": TICKER, "title": "Testco Inc."}}
        if "submissions" in url:
            return json.loads(json.dumps(SUBMISSIONS))
        if "companyfacts" in url:
            return json.loads(json.dumps(COMPANY_FACTS))
        raise AssertionError(f"unexpected JSON url: {url}")

    def get_text(self, url: str, cache_key: str, ttl_seconds: float | None) -> str:
        self.requested.append(url)
        if "tenk.htm" in url:
            return TENK_HTML
        if "proxy.htm" in url:
            return PROXY_HTML
        if "eightk.htm" in url:
            return EIGHTK_HTML
        raise AssertionError(f"unexpected text url: {url}")


class FakeFinnhubClient:
    def __init__(self, peers: list[str] | None = None) -> None:
        self.peers = peers if peers is not None else []

    def get_quote(self, symbol: str) -> Quote:
        return Quote(symbol=symbol, price=100.0, as_of="2026-08-07")

    def get_profile(self, symbol: str) -> CompanyProfile:
        return CompanyProfile(
            symbol=symbol, name="Testco Inc.", market_cap=1500e9,
            shares_outstanding=15e9, industry="Technology", exchange="NASDAQ",
        )

    def get_peers(self, symbol: str) -> list[str]:
        return list(self.peers)

    def get_news(self, symbol: str, days: int = 45, limit: int = 15) -> list[NewsItem]:
        return [
            NewsItem(
                headline="Testco names new chief executive",
                summary="The company announced a leadership transition.",
                url="https://news.invalid/1", source="Reuters",
                published="2026-04-21",
            )
        ]


@dataclass
class FakeLLM(LLMProvider):
    """Returns schema-valid objects and a citation that genuinely resolves.

    The cited span is located in the real document text at call time, so the
    verifier does actual work rather than being handed a pre-agreed answer.
    """

    cited_calls: int = 0
    structured_calls: int = 0

    def complete_structured(self, *, system, user, output_model, effort, max_tokens):
        self.structured_calls += 1
        name = output_model.__name__

        if name == "_ConceptResolutionResult":
            from asset_researcher.quant.resolve import _MetricMapping

            mapping = {
                "revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax"],
                "net_income": ["NetIncomeLoss"],
                "gross_profit": ["GrossProfit"],
                "operating_income": ["OperatingIncomeLoss"],
                "cogs": ["CostOfGoodsAndServicesSold"],
                "total_assets": ["Assets"],
                "total_liabilities": ["Liabilities"],
                "total_equity": ["StockholdersEquity"],
                "current_assets": ["AssetsCurrent"],
                "current_liabilities": ["LiabilitiesCurrent"],
                "retained_earnings": ["RetainedEarningsAccumulatedDeficit"],
                "cash_and_equivalents": ["CashAndCashEquivalentsAtCarryingValue"],
                "operating_cash_flow": ["NetCashProvidedByUsedInOperatingActivities"],
                "total_debt": ["LongTermDebt", "CommercialPaper"],
                "depreciation_amortization": ["DepreciationDepletionAndAmortization"],
                "accounts_receivable": ["AccountsReceivableNetCurrent"],
                "capital_expenditures": ["PaymentsToAcquirePropertyPlantAndEquipment"],
                "interest_expense": ["InterestExpense"],
                "shares_diluted": ["WeightedAverageNumberOfDilutedSharesOutstanding"],
                "eps_diluted": ["EarningsPerShareDiluted"],
                "pretax_income": [
                    "IncomeLossFromContinuingOperationsBeforeIncomeTaxes"
                    "ExtraordinaryItemsNoncontrollingInterest"
                ],
                "income_tax_expense": ["IncomeTaxExpenseBenefit"],
                "share_based_compensation": ["ShareBasedCompensation"],
                # The components that make net debt a real figure rather than
                # debt less petty cash.
                "short_term_investments": ["MarketableSecuritiesCurrent"],
                "long_term_investments": ["MarketableSecuritiesNoncurrent"],
            }
            return output_model(
                mappings=[
                    _MetricMapping(
                        canonical_metric=k, xbrl_concepts=v, confidence="high"
                    )
                    for k, v in mapping.items()
                ]
            )

        if name == "MandateProfile":
            return output_model(
                horizon_bucket="years", horizon_note="3-5 years",
                instruments=["equity_long"], style_tags=["quality"],
            )

        if name == "ReconciliationReport":
            from asset_researcher.analysis.reconcile import Catalyst, Reconciliation

            return output_model(
                financial_trajectory="Revenue grew and margins expanded.",
                reconciliations=[
                    Reconciliation(
                        management_claim="Supply chain execution improved margins.",
                        what_the_data_shows="Gross profit grew faster than revenue.",
                        assessment="Corroborated by the filed figures.",
                        agrees=True, materiality="high",
                    ),
                    Reconciliation(
                        management_claim="Cost discipline is a priority.",
                        what_the_data_shows="Receivables grew faster than revenue.",
                        assessment="Working capital is absorbing cash.",
                        agrees=False, materiality="medium",
                    ),
                ],
                valuation_context="Trades above the peer median on earnings.",
                catalysts=[
                    Catalyst(
                        description="Leadership transition completes.",
                        timeframe="Next two quarters",
                        confirming_evidence="An 8-K confirming the effective date.",
                    )
                ],
                bull_case="Mix shift toward Services is durable.",
                bear_case="Manufacturer concentration is unhedged.",
                disconfirming_evidence="The filing is months old and one segment "
                "carries the entire margin story.",
                questions_for_management=["What drove the receivables build?"],
                data_limitations="Only two fiscal years were available.",
            )

        raise AssertionError(f"unexpected output_model: {name}")

    def complete_cited(self, *, system, documents, user, effort, max_tokens):
        self.cited_calls += 1
        # Cite a phrase that genuinely exists, at its genuine offsets.
        target = "Testco designs and sells industrial widgets"
        index, start = 0, -1
        for i, document in enumerate(documents):
            position = document.text.find(target)
            if position != -1:
                index, start = i, position
                break
        if start == -1:  # fall back to the opening of the first document
            index, start, target = 0, 0, documents[0].text[:40]

        return CitedResponse(
            [
                CitedSpan(text="## Business Overview\n\n", citations=[]),
                CitedSpan(
                    text="The company sells industrial widgets through two segments.",
                    citations=[
                        Citation(
                            cited_text=target,
                            document_index=index,
                            document_title=documents[index].label,
                            start_char_index=start,
                            end_char_index=start + len(target),
                        )
                    ],
                ),
                CitedSpan(text="\n\n## Risk Factors\n\n", citations=[]),
                CitedSpan(
                    text="Manufacturing is concentrated among few suppliers.",
                    citations=[
                        Citation(
                            cited_text=target,
                            document_index=index,
                            document_title=documents[index].label,
                            start_char_index=start,
                            end_char_index=start + len(target),
                        )
                    ],
                ),
            ]
        )
