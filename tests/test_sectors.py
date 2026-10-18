from asset_researcher.config import get_settings
from asset_researcher.quant.sectors import classify_sic

settings = get_settings()


def test_reit_sic_code_classified_correctly():
    # 6798 is the real SIC code for Real Estate Investment Trusts. This range
    # was wrong during initial build (omitted 6798 entirely, catching only
    # the broader "real estate operators" band) and silently misclassified
    # Realty Income (O) as standard, caught by live verification, not by
    # a test, which is exactly why this test now exists.
    assert classify_sic("6798", settings) == "reit"


def test_bank_classified_as_financial():
    assert classify_sic("6021", settings) == "financial"  # JPM


def test_petroleum_refining_classified_as_energy():
    assert classify_sic("2911", settings) == "energy"  # XOM's real SIC


def test_pharma_classified_as_biotech():
    assert classify_sic("2834", settings) == "biotech"


def test_unknown_sic_falls_back_to_default():
    assert classify_sic("9999", settings) == "standard"


def test_empty_or_nonnumeric_sic_falls_back_to_default():
    assert classify_sic("", settings) == "standard"
    assert classify_sic("N/A", settings) == "standard"
