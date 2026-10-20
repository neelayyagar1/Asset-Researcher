"""Concept resolution for peer companies, without a model call.

The subject of a report gets full LLM-assisted concept resolution and the
deterministic validation that follows it, because every figure attributed to
the company is load-bearing. Peers are different: they exist to give the
subject a valuation context, and each peer contributes at most a handful of
ratios to one table.

Paying a model call per peer cost 9.7 seconds measured, or roughly 78 seconds
across a typical peer set of eight, and that was the single largest component
of report latency. A static priority list covers the tags large filers
actually use. Where it misses, the peer's multiple is absent rather than
wrong, the comps table already renders that as "n/a", and the coverage note
tells the reader how many peers were usable.

The trade is deliberate: slightly thinner peer coverage on unusual filers, in
exchange for removing more than a minute from every report.
"""

from __future__ import annotations

# Ordered by how commonly filers report each tag. First match wins.
PEER_CONCEPT_FALLBACKS: dict[str, list[str]] = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
        "RevenuesNetOfInterestExpense",
    ],
    "net_income": [
        "NetIncomeLoss",
        "ProfitLoss",
        "NetIncomeLossAvailableToCommonStockholdersBasic",
    ],
    "gross_profit": ["GrossProfit"],
    "operating_income": [
        "OperatingIncomeLoss",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    ],
    "total_equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "total_assets": ["Assets"],
    "total_liabilities": ["Liabilities"],
    "cash_and_equivalents": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ],
    # Strictly non-current only, because `short_term_debt` is added to it
    # below. `DebtLongtermAndShorttermCombinedAmount` and `LongTermDebt`
    # both already include the current portion for most filers, so pairing
    # either with a current-debt tag counted the same borrowing twice and
    # overstated every peer's enterprise value, which biases the subject
    # toward looking cheap. The combined tag is kept separately.
    "total_debt": [
        "LongTermDebtNoncurrent",
    ],
    "combined_debt": [
        "DebtLongtermAndShorttermCombinedAmount",
        "LongTermDebt",
    ],
    # Current debt and finance leases are separate tags for most filers.
    # Omitting them understates net debt and therefore enterprise value,
    # which makes EV multiples non-comparable across the peer set.
    "short_term_debt": [
        "LongTermDebtCurrent",
        "DebtCurrent",
        "ShortTermBorrowings",
        "CommercialPaper",
    ],
    "short_term_investments": [
        "MarketableSecuritiesCurrent",
        "ShortTermInvestments",
        "AvailableForSaleSecuritiesCurrent",
        "OtherShortTermInvestments",
    ],
    "long_term_investments": [
        "MarketableSecuritiesNoncurrent",
        "AvailableForSaleSecuritiesNoncurrent",
        "LongTermInvestments",
    ],
    "depreciation_amortization": [
        "DepreciationDepletionAndAmortization",
        "DepreciationAmortizationAndAccretionNet",
        "DepreciationAndAmortization",
    ],
}


def resolve_peer_concepts(available: set[str]) -> dict[str, list[str]]:
    """Map canonical metrics to the first available tag for each.

    `available` is the set of concept names the filer actually reports.
    Metrics with no match are omitted, which the series builder records as
    unmapped and the comps table renders as a missing multiple.
    """
    mapping: dict[str, list[str]] = {}
    for metric, candidates in PEER_CONCEPT_FALLBACKS.items():
        for candidate in candidates:
            if candidate in available:
                mapping[metric] = [candidate]
                break
    return mapping
