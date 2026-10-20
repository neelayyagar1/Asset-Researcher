"""Peer comparison table, valuation multiples across a peer set.

Multiples are the one part of the report that needs both halves of the data
layer: earnings and book values come from XBRL (exact, as filed), price and
share count come from Finnhub. Neither is model-generated, so a multiple is
arithmetic on two sourced numbers rather than an estimate.

**Peers are Finnhub's list, not ours.** Choosing a peer set is an analytical
judgment, arguably *the* analytical judgment in relative valuation, and
inventing one would be exactly the kind of unsourced opinion this project
keeps out of the quantitative layer. Finnhub's list is attributable, and the
report says where it came from so a PM can disagree with it.

**Peers are fetched at low fidelity on purpose.** A full concept resolution
per peer would mean an LLM call and a 4MB XBRL download for each of ~8
companies. Peers exist to give the subject company context, so they get
market data plus whatever XBRL is cheaply available, and any peer that fails
is dropped from the table rather than blocking the report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from asset_researcher.quant.capital import net_debt_from_values
from asset_researcher.quant.series import MetricSeries


# "Not meaningful": the convention for a ratio whose denominator is negative
# or near zero. Printing the arithmetic result instead would show a negative
# P/E, which reads as cheap rather than as broken.
NM = "NM"

# Thresholds above which a multiple reflects a collapsed denominator rather
# than a market view. Chosen to be well clear of any defensible valuation:
# a genuinely expensive large-cap trades at 60-80x, not 200x.
_EXTREME_PE = 200.0
_EXTREME_EV_EBITDA = 100.0


@dataclass(frozen=True)
class CompRow:
    ticker: str
    company_name: str
    is_subject: bool

    market_cap: float | None = None
    price: float | None = None

    # Trailing fundamentals, as filed.
    revenue: float | None = None
    net_income: float | None = None
    total_equity: float | None = None
    total_debt: float | None = None
    short_term_debt: float | None = None
    # The combined long-and-short tag, kept apart from the non-current one
    # so the two are never added together.
    combined_debt: float | None = None
    # Decides whether long-term securities net against debt: for a bank the
    # investment portfolio is the operating business, not a cash reserve.
    sector_class: str = "standard"
    cash: float | None = None
    short_term_investments: float | None = None
    long_term_investments: float | None = None
    ebitda: float | None = None

    note: str | None = None  # why a row is thin, shown rather than hidden

    # The period these fundamentals came from. Peers have different fiscal
    # year ends, so without it a January filer and a September filer sit in
    # one table up to twelve months apart with nothing saying so.
    period_end: str = ""

    # Basis for inclusion. A peer list with no stated rationale is just a
    # list; an analyst cannot accept or reject it.
    sic: str = ""
    sic_description: str = ""
    shares_outstanding: float | None = None

    # --- multiples: arithmetic over two sourced numbers, never estimated ---

    @property
    def pe(self) -> float | None:
        """Trailing P/E. Undefined for negative earnings, a negative P/E is
        not a cheap stock, it is a meaningless ratio, and printing one
        invites exactly the wrong read."""
        if self.market_cap is None or not self.net_income or self.net_income <= 0:
            return None
        return self.market_cap / self.net_income

    @property
    def price_to_sales(self) -> float | None:
        if self.market_cap is None or not self.revenue or self.revenue <= 0:
            return None
        return self.market_cap / self.revenue

    @property
    def price_to_book(self) -> float | None:
        if self.market_cap is None or not self.total_equity or self.total_equity <= 0:
            return None
        return self.market_cap / self.total_equity

    @property
    def gross_debt(self) -> float:
        """Borrowings, counted once.

        A filer tags either a combined long-and-short amount or a
        non-current amount beside a current one. Adding a current-debt tag
        to a combined one counts the same borrowing twice, so the combined
        figure wins outright where it exists.
        """
        if self.combined_debt is not None:
            return self.combined_debt
        return (self.total_debt or 0.0) + (self.short_term_debt or 0.0)

    @property
    def net_debt(self) -> float:
        """The shared definition, so a peer row and the subject's valuation
        bridge cannot disagree about what net debt means."""
        return net_debt_from_values(
            total_debt=self.gross_debt,
            cash=self.cash,
            short_term_investments=self.short_term_investments,
            long_term_investments=self.long_term_investments,
            sector_class=self.sector_class,
        ).value

    @property
    def enterprise_value(self) -> float | None:
        if self.market_cap is None:
            return None
        return self.market_cap + self.net_debt

    @property
    def ev_to_ebitda(self) -> float | None:
        ev = self.enterprise_value
        if ev is None or not self.ebitda or self.ebitda <= 0:
            return None
        return ev / self.ebitda

    @property
    def net_margin(self) -> float | None:
        if not self.revenue or self.revenue <= 0 or self.net_income is None:
            return None
        return self.net_income / self.revenue

    @property
    def ebitda_margin(self) -> float | None:
        if not self.revenue or self.revenue <= 0 or self.ebitda is None:
            return None
        return self.ebitda / self.revenue

    @property
    def ev_to_revenue(self) -> float | None:
        ev = self.enterprise_value
        if ev is None or not self.revenue or self.revenue <= 0:
            return None
        return ev / self.revenue

    def inclusion_basis(self, subject: "CompRow | None") -> str:
        """Why this company sits in the table.

        Industry classification comes from the filer's own SEC SIC code, and
        relative size from market capitalisation. Both are facts about the
        company rather than an assertion that it is a good comparable, which
        remains the analyst's call.
        """
        if self.is_subject:
            return "Subject"

        parts = []
        if subject and self.sic and subject.sic:
            if self.sic == subject.sic:
                parts.append(f"Same SIC ({self.sic})")
            elif self.sic[:2] == subject.sic[:2]:
                parts.append(f"Adjacent SIC ({self.sic})")
            else:
                parts.append(f"Different SIC ({self.sic})")
        elif self.sic_description:
            parts.append(self.sic_description[:34])

        if subject and subject.market_cap and self.market_cap:
            ratio = self.market_cap / subject.market_cap
            if ratio >= 0.5:
                parts.append("comparable scale")
            elif ratio >= 0.1:
                parts.append(f"{ratio:.0%} of subject cap")
            else:
                # Against a mega-cap every peer is small, so the percentage
                # alone says little. The absolute figure is what an analyst
                # actually weighs.
                parts.append(f"${self.market_cap / 1e9:,.0f}B cap")
        return ", ".join(parts) or "Peer list"

    @property
    def outlier_multiples(self) -> list[str]:
        """Multiples extreme enough that they describe collapsed earnings
        rather than valuation.

        Observed live: Hewlett Packard Enterprise screened at 1,218x trailing
        P/E against Apple. That is arithmetically correct and analytically
        useless, the denominator nearly vanished. Such values are shown
        (suppressing them would be editing the data) but marked, so a reader
        scanning the column does not read one as a valuation signal.
        """
        flagged = []
        if self.pe is not None and self.pe > _EXTREME_PE:
            flagged.append("pe")
        if self.ev_to_ebitda is not None and self.ev_to_ebitda > _EXTREME_EV_EBITDA:
            flagged.append("ev_to_ebitda")
        return flagged


@dataclass
class CompsTable:
    subject_ticker: str
    peer_source: str  # attribution, e.g. "Finnhub peer list"
    rows: list[CompRow] = field(default_factory=list)
    excluded: list[str] = field(default_factory=list)  # ticker -> shown with reason

    @property
    def subject(self) -> CompRow | None:
        return next((r for r in self.rows if r.is_subject), None)

    @property
    def peers(self) -> list[CompRow]:
        return [r for r in self.rows if not r.is_subject]

    def peer_values(
        self, multiple: str, exclude_outliers: bool = True
    ) -> list[float]:
        """Every usable peer value for one multiple, sorted.

        **Exclusion is per value, not per row.** A peer flagged for a
        collapsed-earnings P/E still has a perfectly good EV/Revenue, and
        dropping the whole row removed it from columns where nothing was
        wrong: the printed "Peer low EV/Revenue" read 1.0x while the body of
        the table showed that same peer at 0.83x.
        """
        values = []
        for row in self.peers:
            value = getattr(row, multiple, None)
            if value is None:
                continue
            if exclude_outliers and multiple in row.outlier_multiples:
                continue
            values.append(value)
        return sorted(values)

    def excluded_from(self, multiple: str) -> list[str]:
        """Peers whose value for this multiple was left out of the statistics."""
        return [
            row.ticker for row in self.peers
            if getattr(row, multiple, None) is not None
            and multiple in row.outlier_multiples
        ]

    def median(self, multiple: str, exclude_outliers: bool = True) -> float | None:
        """Median of a multiple across peers only.

        Excludes the subject, so "trades above the peer median" is a genuine
        comparison rather than one partly against itself. Median, not mean,
        because a single peer with near-zero earnings produces an enormous
        multiple that would drag a mean anywhere.

        **One definition, used everywhere.** This function used to include
        outliers while the printed summary row excluded them, so the table
        said the peer median P/E was 15.3x, the chart beneath it drew a
        dashed line labelled 23.9x, and the model was handed the 23.9x. The
        chart's own subtitle said extreme multiples were excluded, and it was
        the one including them.
        """
        values = self.peer_values(multiple, exclude_outliers)
        if not values:
            return None
        mid = len(values) // 2
        if len(values) % 2 == 1:
            return values[mid]
        return (values[mid - 1] + values[mid]) / 2

    def subject_vs_median(self, multiple: str) -> float | None:
        """Subject's multiple as a ratio to the peer median. 1.15 means a 15%
        premium. None when either side is unavailable, an absent comparison
        is reported as absent, never as parity."""
        subject = self.subject
        if subject is None:
            return None
        own = getattr(subject, multiple, None)
        median = self.median(multiple)
        if own is None or median is None or median == 0:
            return None
        return own / median

    def misaligned_peers(self, quarters: int = 2) -> list[str]:
        """Peers whose fiscal year end is far enough from the subject's that
        their multiples rest on a materially different trading period.

        Two quarters is the threshold at which a comparison stops being a
        comparison: a peer reporting six months earlier than the subject is
        being valued on a different half of the cycle.
        """
        subject = self.subject
        if subject is None or not subject.period_end:
            return []
        try:
            anchor = date.fromisoformat(subject.period_end)
        except ValueError:
            return []

        drifted = []
        for row in self.peers:
            if not row.period_end:
                continue
            try:
                end = date.fromisoformat(row.period_end)
            except ValueError:
                continue
            if abs((end - anchor).days) > quarters * 92:
                drifted.append(row.ticker)
        return drifted

    @property
    def coverage_note(self) -> str | None:
        """One-line caveats when the table should not be leaned on."""
        notes: list[str] = []

        usable = sum(
            1 for r in self.peers if r.pe is not None or r.ev_to_ebitda is not None
        )
        if usable == 0:
            return "No peer had usable multiples; relative valuation unavailable."
        if usable < 3:
            noun = "peer had" if usable == 1 else "peers had"
            notes.append(
                f"Only {usable} {noun} usable multiples, so the median is "
                f"indicative rather than representative."
            )

        for label, attribute in (("P/E", "pe"), ("EV/EBITDA", "ev_to_ebitda")):
            excluded = self.excluded_from(attribute)
            if excluded:
                verb = _subject_verb(excluded, "is", "are")
                whose = _subject_verb(excluded, "Its value remains", "Their values remain")
                included = _subject_verb(excluded, "it is", "they are")
                notes.append(
                    f"{', '.join(excluded)} {verb} excluded from the {label} "
                    f"statistics, where a collapsed denominator produces a "
                    f"multiple describing the earnings rather than the "
                    f"valuation. {whose} in the table body, and {included} "
                    f"included in every other column."
                )

        # The subject and its peers do not come from the same concept
        # resolver, and the asymmetry falls on exactly the inputs that build
        # an enterprise value. Stated rather than left for a reader to find.
        notes.append(
            "Peer fundamentals are read from a fixed tag list rather than the "
            "per-company concept resolution used for the subject, so a peer's "
            "debt and EBITDA may omit components the subject's include. Treat "
            "enterprise-value multiples as indicative across the set."
        )

        misaligned = self.misaligned_peers()
        if misaligned:
            verb = _subject_verb(misaligned, "reports", "report")
            whose = _subject_verb(misaligned, "its multiples rest", "their multiples rest")
            notes.append(
                f"{', '.join(misaligned)} {verb} on a fiscal year ending more "
                f"than two quarters from the subject's, so {whose} on a "
                f"different trading period. The FYE column dates every row."
            )

        impossible = [
            r.ticker for r in self.peers
            if r.net_margin is not None and r.ebitda_margin is not None
            and r.net_margin > r.ebitda_margin
        ]
        if impossible:
            verb = _subject_verb(impossible, "reports", "report")
            whose = _subject_verb(impossible, "its", "their")
            margins = _subject_verb(impossible, "That margin", "Those margins")
            notes.append(
                f"{', '.join(impossible)} {verb} a net margin above {whose} "
                f"EBITDA margin, which means the two lines come from "
                f"different periods or the year carried a material one-off. "
                f"{margins} should not be read as operating performance."
            )

        negative = [
            r.ticker
            for r in self.peers
            if r.net_income is not None and r.net_income <= 0
        ]
        if negative:
            verb = _subject_verb(negative, "had", "had")
            whom = _subject_verb(negative, "it", "them")
            notes.append(
                f"{', '.join(negative)} {verb} non-positive trailing earnings, "
                f"so no P/E is shown for {whom}."
            )

        return " ".join(notes) if notes else None


def _subject_verb(tickers: list[str], singular: str, plural: str) -> str:
    """One ticker takes a singular verb. "P are excluded" and "WDC report a
    net margin" are the kind of slip that reads as machine-written."""
    return singular if len(tickers) == 1 else plural


def _latest_period_end(series: MetricSeries) -> str:
    """The most recent period end anywhere in the series.

    Taken from revenue where available, since that is the line every row's
    multiples ultimately rest on, and falling back to the latest end across
    all metrics for a filer that does not report one.
    """
    revenue = series.series.get("revenue")
    if revenue:
        return revenue[-1].end
    ends = [p.end for points in series.series.values() for p in points]
    return max(ends) if ends else ""


def _latest(series: MetricSeries, metric: str) -> float | None:
    periods = series.series.get(metric)
    return periods[-1].value if periods else None


def build_comp_row(
    ticker: str,
    company_name: str,
    is_subject: bool,
    market_cap: float | None,
    price: float | None,
    series: MetricSeries | None,
    note: str | None = None,
) -> CompRow:
    """One row from whatever data was available. Missing inputs yield missing
    multiples rather than substituted values."""
    if series is None:
        return CompRow(
            ticker=ticker,
            company_name=company_name,
            is_subject=is_subject,
            market_cap=market_cap,
            price=price,
            note=note or "No XBRL data available; market data only.",
        )

    operating_income = _latest(series, "operating_income")
    d_and_a = _latest(series, "depreciation_amortization")
    # EBITDA is approximated as operating income + D&A. Both are as-filed;
    # the sum is a convention, not a reported figure, so it is labelled as an
    # approximation wherever it is displayed.
    ebitda = None
    if operating_income is not None:
        ebitda = operating_income + (d_and_a or 0.0)

    return CompRow(
        ticker=ticker,
        company_name=company_name,
        is_subject=is_subject,
        market_cap=market_cap,
        price=price,
        period_end=_latest_period_end(series),
        revenue=_latest(series, "revenue"),
        net_income=_latest(series, "net_income"),
        total_equity=_latest(series, "total_equity"),
        total_debt=_latest(series, "total_debt"),
        short_term_debt=_latest(series, "short_term_debt"),
        combined_debt=_latest(series, "combined_debt"),
        sector_class=series.sector,
        cash=_latest(series, "cash_and_equivalents"),
        short_term_investments=_latest(series, "short_term_investments"),
        long_term_investments=_latest(series, "long_term_investments"),
        ebitda=ebitda,
        note=note,
    )


# --- presentation -------------------------------------------------------
#
# Column order, grouping and summary statistics follow the standard output
# format for a comparable company analysis: identifiers, market data,
# operating metrics, then multiples, with mean / median / high / low beneath
# the peer set and the subject separated from it.
#
# The conventions are not decoration. An analyst reads dozens of these a
# week and finds a number by its position; a table that orders columns
# differently costs them time even when every figure in it is correct.

def _millions(value: float | None) -> str:
    """Dollars in millions to one decimal, negatives in parentheses."""
    if value is None:
        return NM
    scaled = value / 1e6
    if scaled < 0:
        return f"({abs(scaled):,.1f})"
    return f"{scaled:,.1f}"


def _multiple(value: float | None) -> str:
    """One decimal and a trailing x. NM where the denominator is negative or
    near zero, which is the convention rather than showing a negative
    multiple that reads as cheap."""
    if value is None:
        return NM
    return f"{value:,.1f}x"


def _percent(value: float | None) -> str:
    if value is None:
        return NM
    return f"{value * 100:,.1f}%"


def _price(value: float | None) -> str:
    return f"${value:,.2f}" if value is not None else NM


_MONTHS = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)


def _fiscal_year_end(period_end: str) -> str:
    """The month and year of the period these figures came from.

    Abbreviated because the column exists to let a reader spot a mismatch
    at a glance, not to date the figures to the day.
    """
    if not period_end or len(period_end) < 7:
        return NM
    try:
        return f"{_MONTHS[int(period_end[5:7]) - 1]} {period_end[:4]}"
    except (ValueError, IndexError):
        return NM

# Column order is fixed and mirrors the standard layout.
COMP_COLUMNS = [
    "Company", "Ticker", "FYE", "Share price", "Equity value", "Net debt",
    "Enterprise value", "Revenue", "EBITDA", "EBITDA margin", "Net margin",
    "EV/Revenue", "EV/EBITDA", "P/E", "P/B", "Basis for inclusion",
]


def _row_cells(row: CompRow, subject: CompRow | None) -> dict[str, str]:
    has_balance_sheet = any(
        value is not None
        for value in (
            row.total_debt, row.cash,
            row.short_term_investments, row.long_term_investments,
        )
    )
    net = row.net_debt if has_balance_sheet else None
    return {
        "Company": row.company_name[:28],
        "Ticker": row.ticker,
        "FYE": _fiscal_year_end(row.period_end),
        "Share price": _price(row.price),
        "Equity value": _millions(row.market_cap),
        "Net debt": _millions(net),
        "Enterprise value": _millions(row.enterprise_value),
        "Revenue": _millions(row.revenue),
        "EBITDA": _millions(row.ebitda),
        "EBITDA margin": _percent(row.ebitda_margin),
        "Net margin": _percent(row.net_margin),
        "EV/Revenue": _multiple(row.ev_to_revenue),
        "EV/EBITDA": _multiple(row.ev_to_ebitda),
        "P/E": _multiple(row.pe),
        "P/B": _multiple(row.price_to_book),
        "Basis for inclusion": row.inclusion_basis(subject),
    }


def _statistic(values: list[float], how: str) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if how == "high":
        return ordered[-1]
    if how == "low":
        return ordered[0]
    if how == "mean":
        return sum(ordered) / len(ordered)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def format_comp_table(table: "CompsTable") -> list[dict[str, str]]:
    """Rows for display: subject, a separator, peers, then summary statistics.

    Summary rows are computed across peers only. Including the subject in its
    own benchmark would flatter or penalise it depending on where it sits.
    """
    if not table.rows:
        return []

    subject = table.subject
    rows: list[dict[str, str]] = []

    if subject is not None:
        rows.append(_row_cells(subject, subject))
        rows.append({column: "" for column in COMP_COLUMNS})  # visual break

    for peer in table.peers:
        rows.append(_row_cells(peer, subject))

    multiples = [
        ("EV/Revenue", "ev_to_revenue"),
        ("EV/EBITDA", "ev_to_ebitda"),
        ("P/E", "pe"),
        ("P/B", "price_to_book"),
    ]
    # Extreme multiples are excluded from the statistics but stay visible in
    # their own row. A 1,218x P/E is arithmetically true and tells a reader
    # nothing about where the group trades. The exclusion is per value: a
    # peer flagged on P/E still counts in every other column.
    margins = [("EBITDA margin", "ebitda_margin"), ("Net margin", "net_margin")]

    for label in ("Mean", "Median", "High", "Low"):
        summary = {column: "" for column in COMP_COLUMNS}
        summary["Company"] = f"Peer {label.lower()}"
        for column, attribute in multiples:
            values = table.peer_values(attribute)
            summary[column] = _multiple(_statistic(values, label.lower()))
        # Margins carry the same four statistics as the multiples. A lone
        # mean EBITDA margin on the Mean row, with the Median, High and Low
        # rows blank beneath it, invited the reader to compare a mean against
        # medians in the columns either side of it.
        for column, attribute in margins:
            values = table.peer_values(attribute)
            summary[column] = _percent(_statistic(values, label.lower()))
        rows.append(summary)

    return rows
