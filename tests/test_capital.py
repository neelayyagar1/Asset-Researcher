"""Net debt, which three modules used to compute three ways.

The definition that shipped was `total_debt - cash_and_equivalents`. For any
filer holding marketable securities, which is most large ones, that reports a
net-cash company as carrying net debt, prints it in a valuation bridge, and
deducts it from equity value.
"""

from __future__ import annotations

from asset_researcher.quant.capital import net_debt, net_debt_from_values
from asset_researcher.quant.series import MetricPeriod, MetricSeries


def _series(**metrics: float) -> MetricSeries:
    return MetricSeries(
        cik=320193,
        sector="standard",
        series={
            name: [
                MetricPeriod(
                    end="2025-09-27", frame_label="FY2025", value=value, accn="x"
                )
            ]
            for name, value in metrics.items()
        },
    )


def _apple_like() -> MetricSeries:
    """Roughly Apple's filed balance sheet: debt against a much larger
    securities portfolio."""
    return _series(
        total_debt=98_700e6,
        cash_and_equivalents=35_900e6,
        short_term_investments=35_200e6,
        long_term_investments=91_500e6,
    )


def test_a_company_holding_securities_is_reported_as_net_cash():
    position = net_debt(_apple_like())
    assert position.is_net_cash
    assert position.value < 0
    # 98.7 - (35.9 + 35.2 + 91.5)
    assert round(position.value / 1e9) == -64


def test_the_old_definition_would_have_called_it_net_debt():
    """The regression this module exists to prevent: counting only cash and
    equivalents reports $62.8B of net debt for a company with $162.6B of
    liquid assets against $98.7B of borrowings."""
    series = _apple_like()
    cash_only = (
        series.series["total_debt"][0].value
        - series.series["cash_and_equivalents"][0].value
    )
    assert cash_only > 0
    assert net_debt(series).value < 0


def test_a_genuinely_levered_company_still_reports_net_debt():
    position = net_debt(
        _series(total_debt=40_000e6, cash_and_equivalents=2_000e6)
    )
    assert not position.is_net_cash
    assert position.value == 38_000e6


def test_long_term_securities_are_not_netted_for_a_financial_filer():
    """For a bank the investment portfolio is the operating business, not a
    cash reserve. Netting it would understate leverage enormously."""
    series = _series(
        total_debt=300_000e6,
        cash_and_equivalents=20_000e6,
        short_term_investments=10_000e6,
        long_term_investments=900_000e6,
    )
    bank = net_debt(series, "financial")
    industrial = net_debt(series, "standard")

    assert not bank.nets_long_term
    assert bank.value == 270_000e6
    assert industrial.nets_long_term
    assert industrial.value < 0


def test_missing_components_contribute_zero_rather_than_blocking():
    """Peers are fetched at low fidelity and any component may be absent."""
    position = net_debt_from_values(total_debt=10e9, cash=None)
    assert position.value == 10e9
    assert net_debt_from_values(None, None).value == 0.0


def test_the_components_travel_with_the_figure():
    """A single netted number asks the reader to trust it. The bridge shows
    what was netted."""
    rows = net_debt(_apple_like()).components()
    labels = [label for label, _ in rows]
    assert labels[0] == "Total debt"
    assert "Less cash and equivalents" in labels
    assert "Less short-term investments" in labels
    assert "Less long-term marketable securities" in labels
    assert labels[-1] == "Net cash"
    # The components reconcile to the reported figure.
    assert round(sum(v for _, v in rows[:-1])) == round(rows[-1][1])


def test_a_component_the_filer_does_not_report_is_left_out_of_the_bridge():
    rows = net_debt(_series(total_debt=10e9, cash_and_equivalents=1e9)).components()
    labels = [label for label, _ in rows]
    assert "Less short-term investments" not in labels
    assert labels[-1] == "Net debt"


def test_the_basis_names_what_was_netted():
    """It is shown in the assumptions table, where a reviewer decides
    whether to accept the figure."""
    basis = net_debt(_apple_like()).basis
    assert "short-term investments" in basis
    assert "long-term marketable securities" in basis

    bank_basis = net_debt(_apple_like(), "financial").basis
    assert "long-term marketable securities" not in bank_basis
