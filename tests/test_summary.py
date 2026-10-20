"""The summary block, which is the only place in the note that states a
figure inside a sentence.

This module had no behavioural tests, and a mutation run showed every
mutant of it surviving: inverting the growth direction, reporting the
oldest period as the latest, swapping the located and total citation
counts and scaling a percentage by ten all passed the suite. The sentences
here are what a reader takes away before deciding whether to keep reading,
so they are pinned.
"""

from __future__ import annotations

from asset_researcher.ui.summary import _as_number, _multiple, conversion_sentence


# -------------------------------------------------- cash conversion

def test_a_falling_series_is_described_as_falling():
    assert "down from 126.0%" in conversion_sentence(
        {"FY23": "126.0%", "FY24": "99.0%"}, {}
    )


def test_a_rising_series_is_described_as_rising():
    assert "up from 99.0%" in conversion_sentence(
        {"FY23": "99.0%", "FY24": "126.0%"}, {}
    )


def test_an_unchanged_series_is_not_described_as_rising():
    """`latest < first` with no equality branch called a flat series
    "up from" its own value."""
    sentence = conversion_sentence({"FY23": "130.0%", "FY24": "130.0%"}, {})
    assert "up from" not in sentence
    assert "down from" not in sentence
    assert "level with 130.0%" in sentence


def test_a_trough_inside_the_window_is_named():
    """Endpoints alone hid the accrual build this line exists to catch: a
    series running 130, 60, 40, 55, 130 is flat on its ends."""
    sentence = conversion_sentence(
        {
            "FY20": "130.0%", "FY21": "60.0%", "FY22": "40.0%",
            "FY23": "55.0%", "FY24": "130.0%",
        },
        {},
    )
    assert "fallen to 40.0% in FY22" in sentence


def test_a_monotonic_series_does_not_claim_a_trough():
    assert "fallen to" not in conversion_sentence(
        {"FY22": "130.0%", "FY23": "110.0%", "FY24": "99.0%"}, {}
    )


def test_a_stale_figure_is_dated_rather_than_stated_as_current():
    """Filtering to measurable periods and then reporting in the present
    tense presented a four-year-old figure as the position today."""
    sentence = conversion_sentence(
        {
            "FY20": "200.0%", "FY21": "NM", "FY22": "NM",
            "FY23": "NM", "FY24": "NM",
        },
        {},
    )
    assert "in FY20" in sentence
    assert "was" in sentence


def test_five_filed_years_are_not_called_one_year_only():
    sentence = conversion_sentence(
        {"FY20": "200.0%", "FY21": "NM", "FY22": "NM", "FY23": "NM"}, {}
    )
    assert "one year" not in sentence
    assert "the only period in which it could be measured" in sentence


def test_the_latest_measurable_period_is_reported_not_the_oldest():
    assert "is 99.0%" in conversion_sentence(
        {"FY22": "126.0%", "FY23": "110.0%", "FY24": "99.0%"}, {}
    )


def test_the_accrual_ratio_carries_the_period_it_belongs_to():
    sentence = conversion_sentence(
        {"FY23": "126.0%", "FY24": "99.0%"}, {"FY24": "(7.5%)"}
    )
    assert "accrual ratio of (7.5%) in FY24" in sentence


def test_an_unmeasurable_accrual_ratio_is_left_out():
    assert "accrual" not in conversion_sentence(
        {"FY23": "126.0%", "FY24": "99.0%"}, {"FY24": "NM"}
    )


def test_a_series_with_nothing_measurable_produces_no_sentence():
    assert conversion_sentence({"FY23": "NM", "FY24": "n.d."}, {}) == ""


# ------------------------------------------------------- multiples

def test_a_multiple_below_one_is_not_rounded_to_zero():
    """`,.0f` rendered 0.4x as "At 0 times free cash flow"."""
    assert _multiple(0.4) == "0.4"


def test_a_large_multiple_drops_the_decimal():
    assert _multiple(33.4) == "33"


def test_a_non_finite_multiple_is_refused():
    assert _multiple(float("nan")) is None
    assert _multiple(float("inf")) is None
    assert _multiple(None) is None


# ------------------------------------------------- rendered parsing

def test_parentheses_are_read_as_negative():
    assert _as_number("(7.5%)") == -7.5


def test_a_thousands_separator_does_not_defeat_parsing():
    assert _as_number("1,234.5%") == 1234.5
