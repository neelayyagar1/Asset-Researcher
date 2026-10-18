"""Peer comps: multiples arithmetic, median behaviour, and honest caveats."""

from __future__ import annotations

import pytest

from asset_researcher.quant.comps import CompRow, CompsTable, build_comp_row
from asset_researcher.quant.series import MetricPeriod, MetricSeries


def _row(ticker: str, is_subject: bool = False, **kw) -> CompRow:
    base = dict(
        market_cap=100e9, revenue=50e9, net_income=5e9,
        total_equity=20e9, total_debt=10e9, cash=4e9, ebitda=12e9,
    )
    base.update(kw)
    return CompRow(
        ticker=ticker, company_name=ticker, is_subject=is_subject, **base
    )


def test_negative_earnings_yield_no_pe_rather_than_a_negative_one():
    """A negative P/E is not a cheap stock, it is a meaningless ratio.
    printing one invites exactly the wrong read."""
    assert _row("X", net_income=-2e9).pe is None
    assert _row("X", net_income=0).pe is None


def test_enterprise_value_adds_debt_and_subtracts_cash():
    row = _row("X", market_cap=100e9, total_debt=10e9, cash=4e9)
    assert row.enterprise_value == pytest.approx(106e9)
    assert row.ev_to_ebitda == pytest.approx(106e9 / 12e9)


def test_missing_inputs_produce_missing_multiples_not_substitutes():
    row = CompRow(ticker="X", company_name="X", is_subject=False)
    assert row.pe is None
    assert row.price_to_book is None
    assert row.enterprise_value is None
    assert row.ev_to_ebitda is None


def test_median_excludes_the_subject():
    """Otherwise 'trades above the peer median' is partly a comparison
    against itself."""
    table = CompsTable(subject_ticker="S", peer_source="test")
    table.rows = [
        _row("S", is_subject=True, market_cap=1000e9),  # P/E 200
        _row("A", market_cap=100e9),  # P/E 20
        _row("B", market_cap=200e9),  # P/E 40
        _row("C", market_cap=300e9),  # P/E 60
    ]
    assert table.median("pe") == pytest.approx(40.0)
    assert table.subject_vs_median("pe") == pytest.approx(200.0 / 40.0)


def test_median_is_unmoved_by_one_extreme_peer():
    """Verified live: HPE screened at 1,218x P/E in Apple's peer set. A mean
    would be dragged anywhere; the median is why that is tolerable."""
    table = CompsTable(subject_ticker="S", peer_source="test")
    table.rows = [
        _row("S", is_subject=True),
        _row("A", market_cap=100e9),  # P/E 20
        _row("B", market_cap=200e9),  # P/E 40
        _row("C", net_income=0.05e9),  # P/E 2000, collapsed denominator
    ]
    peer_pes = [r.pe for r in table.peers]
    assert sorted(peer_pes) == pytest.approx([20.0, 40.0, 2000.0])

    # The collapsed denominator is excluded outright, so the median is taken
    # over the two real peers.
    assert table.median("pe") == pytest.approx(30.0)
    assert table.peer_values("pe") == pytest.approx([20.0, 40.0])
    assert table.excluded_from("pe") == ["C"]

    # Including it changes the answer, which is why one definition is used
    # everywhere rather than one per renderer.
    assert table.median("pe", exclude_outliers=False) == pytest.approx(40.0)

    # The whole point: a mean would land nowhere near any real peer.
    assert sum(peer_pes) / len(peer_pes) > 600


def test_outlier_exclusion_is_per_value_not_per_row():
    """A peer flagged on P/E still has a usable EV/Revenue. Dropping the
    whole row removed it from columns where nothing was wrong: the printed
    "Peer low EV/Revenue" read above a lower value sitting in the body."""
    table = CompsTable(subject_ticker="S", peer_source="test")
    table.rows = [
        _row("S", is_subject=True),
        _row("A", market_cap=100e9),
        _row("B", market_cap=200e9),
        _row("C", net_income=0.05e9),  # flagged on P/E only
    ]
    flagged = next(r for r in table.peers if r.ticker == "C")
    assert flagged.outlier_multiples == ["pe"]
    # Excluded from P/E, counted everywhere else.
    assert "C" in table.excluded_from("pe")
    assert table.excluded_from("price_to_sales") == []
    assert len(table.peer_values("price_to_sales")) == 3


def test_extreme_multiples_are_flagged_but_still_shown():
    """Suppressing them would be editing the data; showing them unmarked
    invites reading one as a valuation signal."""
    row = _row("HPE", net_income=0.08e9)  # 1250x
    assert "pe" in row.outlier_multiples
    assert row.pe is not None  # still reported

    assert _row("OK").outlier_multiples == []


def test_coverage_note_explains_absent_and_extreme_values():
    table = CompsTable(subject_ticker="S", peer_source="test")
    table.rows = [
        _row("S", is_subject=True),
        _row("A"),
        _row("B"),
        _row("LOSS", net_income=-1e9),
        _row("WILD", net_income=0.05e9),
    ]
    note = table.coverage_note
    assert note and "LOSS" in note and "WILD" in note


def test_thin_table_is_labelled_indicative():
    table = CompsTable(subject_ticker="S", peer_source="test")
    table.rows = [_row("S", is_subject=True), _row("A")]
    assert "indicative" in (table.coverage_note or "")


def test_no_usable_peers_says_so_rather_than_implying_parity():
    table = CompsTable(subject_ticker="S", peer_source="test")
    table.rows = [_row("S", is_subject=True)]
    assert table.median("pe") is None
    assert table.subject_vs_median("pe") is None
    assert "unavailable" in (table.coverage_note or "")


def test_build_row_without_xbrl_keeps_market_data_and_notes_why():
    row = build_comp_row(
        ticker="X", company_name="X Corp", is_subject=False,
        market_cap=10e9, price=5.0, series=None,
    )
    assert row.market_cap == 10e9
    assert row.revenue is None
    assert row.note and "No XBRL" in row.note


def test_ebitda_is_operating_income_plus_dna():
    series = MetricSeries(cik=1, sector="standard")
    series.series["operating_income"] = [MetricPeriod("2025-12-31", "FY2025", 10e9, "a")]
    series.series["depreciation_amortization"] = [
        MetricPeriod("2025-12-31", "FY2025", 2e9, "a")
    ]
    row = build_comp_row("X", "X", False, 100e9, 5.0, series)
    assert row.ebitda == pytest.approx(12e9)
