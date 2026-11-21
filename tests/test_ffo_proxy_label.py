"""The lead statistic on the Realty Income note described a deduction
it does not make.

The masthead reads "Price / FFO 15.3x - Funds from operations, before
gains on disposal". Gains on disposal are IN net income, and the
computation is net income plus depreciation and amortisation, so the
figure includes exactly what its label says it comes before. The
note's own body says so, four sections down: "the proxy used here, net
income plus depreciation and amortisation, excludes the gain and
impairment adjustments ... that AFFO strips out."

So the first figure a reader meets - the one on the index table and on
the masthead - was described backwards, and contradicted by the
document beneath it. For a REIT that sold property during the year it
also runs high, which is the direction that flatters.

The arithmetic is defensible as a proxy and stays. It is now named for
what it computes, which the code comment beside it already claimed it
was.
"""

from __future__ import annotations

import pathlib

import yaml

from asset_researcher.ui.headline import headline_stats


def _label_in_yaml() -> str:
    data = yaml.safe_load(
        pathlib.Path(
            "asset_researcher/config/metrics/canonical.yaml"
        ).read_text(encoding="utf-8")
    )
    for section in data.values():
        if isinstance(section, dict) and "ffo_before_disposals" in section:
            return section["ffo_before_disposals"]["label"]
    raise AssertionError("ffo_before_disposals is not in canonical.yaml")


def test_the_canonical_label_does_not_claim_a_deduction_it_skips():
    label = _label_in_yaml().lower()
    assert "before gains" not in label, (
        f"{label!r} claims gains on disposal are excluded; they are in "
        f"net income, which is the first term of the formula"
    )


def test_the_canonical_label_says_what_it_computes():
    label = _label_in_yaml().lower()
    assert "net income" in label and (
        "depreciation" in label or "d&a" in label
    ), label


def test_the_formula_is_unchanged():
    data = yaml.safe_load(
        pathlib.Path(
            "asset_researcher/config/metrics/canonical.yaml"
        ).read_text(encoding="utf-8")
    )
    for section in data.values():
        if isinstance(section, dict) and "ffo_before_disposals" in section:
            assert section["ffo_before_disposals"]["formula"] == (
                "net_income + depreciation_amortization"
            )
            return


def test_the_masthead_caption_describes_the_proxy_it_prints():
    """The figure a reader meets first, on the masthead and on the
    index table of the first screen. Asserted on the caption the page
    emits, not on the module source: the first version of this grepped
    the file and failed on a comment quoting the wording it bans."""
    from asset_researcher.ui.headline import FFO_PROXY_LABEL, FFO_PROXY_NOTE

    assert "before gains on disposal" not in FFO_PROXY_NOTE.lower()
    assert "net income" in FFO_PROXY_NOTE.lower()
    assert "depreciation" in FFO_PROXY_NOTE.lower()
    assert "proxy" in FFO_PROXY_NOTE.lower() or "proxy" in FFO_PROXY_LABEL.lower()


def test_the_masthead_caption_says_which_way_it_errs():
    """It runs high for a REIT that sold property, and that is the
    direction that flatters."""
    from asset_researcher.ui.headline import FFO_PROXY_NOTE

    assert "gains on property sales" in FFO_PROXY_NOTE
