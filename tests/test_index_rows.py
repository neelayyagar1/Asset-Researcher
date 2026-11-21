"""The index on the first screen: what is in it, and how it is opened.

Two owner findings. A reader had to press "Read a sample" to reach a
report whose row was already in front of them, and a report they
generated themselves never joined the list at all.

A row is now a link. That is the part with teeth: a link is a page
load, so every row has to carry the unlock token, and the thing it
points at has to survive the reload. The store is what makes the
second true; these cover the first.
"""

from __future__ import annotations

import re

from asset_researcher.ui import components as ui

ROWS = [
    {
        "ticker": "ADP",
        "company": "Automatic Data Processing",
        "metric": "Price implies FCF growth",
        "value": "6.8%",
        "slug": "adp",
    },
    {
        "ticker": "COST",
        "company": "Costco Wholesale",
        "metric": "Price implies FCF growth",
        "value": "18.7%",
        "slug": "cost",
    },
]


def test_every_row_is_a_link_to_its_own_report():
    html = ui.report_rows(ROWS, token="tok")
    # Four anchors per row, all to one place: one destination per row.
    hrefs = set(re.findall(r'href="([^"]+)"', html))
    assert len(hrefs) == len(ROWS)
    assert any("s=adp" in h for h in hrefs)
    assert any("s=cost" in h for h in hrefs)


def test_a_row_link_carries_the_unlock_token():
    """Without it the click lands on the gate, which is worse than the
    button it replaced."""
    html = ui.report_rows(ROWS, token="tok")
    assert all("k=tok" in h for h in re.findall(r'href="([^"]+)"', html))


def test_a_row_link_goes_to_the_reading_view():
    html = ui.report_rows(ROWS, token="tok")
    assert all("view=samples" in h for h in re.findall(r'href="([^"]+)"', html))


def test_a_token_with_a_url_character_in_it_is_escaped():
    """The token is a signed value, not a word, and it is being put in
    a query string by hand."""
    html = ui.report_rows(ROWS, token="a&b c")
    assert "k=a&b c" not in html
    # urlencode spells a space `+`, which is what a query string wants.
    assert "a%26b+c" in html


def test_the_whole_row_is_the_hit_target_not_one_word():
    """A link wrapping a single cell is a link the reader has to aim
    at. Each cell carries the anchor, so the row reads as one."""
    html = ui.report_rows(ROWS, token="tok")
    first_row = html.split("<tr")[1]
    assert first_row.count("<a ") == first_row.count("<td")


def test_an_empty_index_still_says_so():
    assert "No notes yet" in ui.report_rows([], token="tok")


# ----------------------------------------------------- end to end, no money

import pathlib

from streamlit.testing.v1 import AppTest

from asset_researcher import reports_store
from tests.apptest_helpers import page_text, rendered_markup

APP = str(pathlib.Path(__file__).resolve().parents[1] / "app.py")
PHRASE = "test-only-passphrase"


# The store is scoped per visitor, so a test has to seed into the
# scope the app will read - which it takes from `sid` in the URL.
SCOPE = "0123456789abcdef"


def _seeded(monkeypatch, tmp_path):
    """Two saved reports and no sealed archive, so this costs nothing."""
    monkeypatch.setenv("DEMO_PASSPHRASE", PHRASE)
    monkeypatch.delenv("SAMPLES_KEY", raising=False)
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path))
    first = reports_store.save(
        "AAA", "Alpha Inc. (AAA)", "<html>alpha</html>", scope=SCOPE
    )
    second = reports_store.save(
        "BBB", "Beta Corp. (BBB)", "<html>beta</html>", scope=SCOPE
    )
    at = AppTest.from_file(APP, default_timeout=60)
    at.query_params["sid"] = SCOPE
    return at, first, second


def _unlock(at):
    at = at.run()
    at.text_input(key="gate_input").set_value(PHRASE)
    return at.button[0].click().run()


def test_a_generated_report_appears_on_the_first_screen(monkeypatch, tmp_path):
    at, first, second = _seeded(monkeypatch, tmp_path)
    at = _unlock(at)
    text = page_text(at)
    assert "Alpha Inc." in text
    assert "Beta Corp." in text


def test_the_newest_report_is_the_top_row(monkeypatch, tmp_path):
    at, first, second = _seeded(monkeypatch, tmp_path)
    at = _unlock(at)
    markup = rendered_markup(at)
    assert markup.index("Beta Corp.") < markup.index("Alpha Inc.")


def test_opening_a_row_lands_on_that_report(monkeypatch, tmp_path):
    """The whole point of the link. Entered by URL, which is exactly
    what the anchor does."""
    at, first, second = _seeded(monkeypatch, tmp_path)
    at.query_params["view"] = "samples"
    at.query_params["s"] = first.slug
    at = _unlock(at)
    assert not at.exception
    assert at.radio(key="sample_pick").value == first.slug


def test_a_slug_nobody_shipped_does_not_raise(monkeypatch, tmp_path):
    at, first, second = _seeded(monkeypatch, tmp_path)
    at.query_params["view"] = "samples"
    at.query_params["s"] = "../../etc/passwd"
    at = _unlock(at)
    assert not at.exception


def test_the_reading_screen_does_not_call_a_readers_own_report_a_sample(
    monkeypatch, tmp_path
):
    """It listed generated reports under a heading that said these were
    shipped samples built by the pipeline, which is true of six of
    them and false of everything the reader made."""
    at, first, second = _seeded(monkeypatch, tmp_path)
    at.query_params["view"] = "samples"
    at = _unlock(at)
    text = page_text(at)
    assert "Sample notes" not in text


def test_the_bar_distinguishes_the_index_from_a_report(monkeypatch, tmp_path):
    """Renaming the reading screen to Reports gave it the same bar
    label as the index, so the one piece of chrome that answers "where
    am I" answered the same thing on both."""
    at, first, second = _seeded(monkeypatch, tmp_path)
    home = rendered_markup(_unlock(at))

    at2, _, _ = _seeded(monkeypatch, tmp_path)
    at2.query_params["view"] = "samples"
    reading = rendered_markup(_unlock(at2))

    def where(markup):
        import re
        return re.search(r'class="where"[^>]*>([^<]*)<', markup).group(1)

    assert where(home) != where(reading)


# ------------------------------------------------------ the wider table

WIDE = [
    {
        "ticker": "ADP", "company": "Automatic Data Processing",
        "metric": "Price implies FCF growth", "value": "6.8%",
        "price": "$301.71", "filed": "2026-08-05", "cited": "113/113",
        "slug": "adp",
    },
]


def test_the_index_carries_the_columns_the_notes_support():
    html = ui.report_rows(WIDE, token="t")
    for header in ("Ticker", "Company", "Price", "Headline metric",
                   "Value", "Filed", "Cited"):
        assert f">{header}<" in html, header


def test_each_row_has_a_cell_for_every_header():
    html = ui.report_rows(WIDE, token="t")
    head, _, rest = html.partition("</tr>")
    assert head.count("<th") == rest.count("<td")


def test_a_figure_the_note_does_not_carry_is_left_blank():
    """An em dash, not a zero and not a number borrowed from the row
    above it."""
    thin = dict(WIDE[0], price="", cited="", filed="")
    html = ui.report_rows([thin], token="t")
    assert html.count("&mdash;") == 3


def test_another_visitors_report_is_not_on_this_visitors_index(
    monkeypatch, tmp_path
):
    """The whole point of the scope, exercised through the app rather
    than through the store: a second visitor arrives at the same
    deployment, in the same container, and sees only the samples."""
    at, first, second = _seeded(monkeypatch, tmp_path)
    reports_store.save(
        "ZZZ", "Zeta Holdings (ZZZ)", "<html>zeta</html>",
        scope="fedcba9876543210",
    )
    text = page_text(_unlock(at))
    assert "Alpha Inc." in text
    assert "Zeta Holdings" not in text, (
        "a report generated by another visitor is on this one's index"
    )


def test_a_visitor_with_no_scope_yet_sees_only_the_samples(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("DEMO_PASSPHRASE", PHRASE)
    monkeypatch.delenv("SAMPLES_KEY", raising=False)
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path))
    reports_store.save(
        "ZZZ", "Zeta Holdings (ZZZ)", "<html>zeta</html>",
        scope="fedcba9876543210",
    )
    at = AppTest.from_file(APP, default_timeout=60)
    text = page_text(_unlock(at))
    assert "Zeta Holdings" not in text


def test_the_row_links_carry_the_scope(monkeypatch, tmp_path):
    """Without it, opening a row loses every report the reader made."""
    at, first, second = _seeded(monkeypatch, tmp_path)
    markup = rendered_markup(_unlock(at))
    assert f"sid={SCOPE}" in markup


def test_a_report_saved_now_appears_without_a_restart(monkeypatch, tmp_path):
    """The listing is cached on the directory's modification time, so
    the cache must not outlive a new report. Caching on scope alone
    would have hidden every report after the first."""
    at, first, second = _seeded(monkeypatch, tmp_path)
    assert "Alpha Inc." in page_text(_unlock(at))

    reports_store.save(
        "CCC", "Gamma Ltd. (CCC)", "<html>gamma</html>", scope=SCOPE
    )
    at2 = AppTest.from_file(APP, default_timeout=60)
    at2.query_params["sid"] = SCOPE
    assert "Gamma Ltd." in page_text(_unlock(at2))


# ------------------------------------------------ what a screen reader hears

def test_a_row_is_one_stop_in_the_tab_order_not_seven():
    """Each cell carries its own anchor so the whole row is a hit
    target. That is right for a pointer and wrong for everything else:
    seven tab stops per row, forty-two for six reports, and a
    links-list showing forty-two entries for six destinations."""
    html = ui.report_rows(WIDE, token="t")
    anchors = re.findall(r"<a [^>]*>", html)
    assert len(anchors) == 7, "the row is no longer seven cells"
    focusable = [a for a in anchors if 'tabindex="-1"' not in a]
    assert len(focusable) == 1, (
        f"{len(focusable)} of the row's anchors are in the tab order"
    )


def test_the_one_focusable_anchor_names_the_whole_row():
    """The others announce only their own cell - "6.8%, link" - which
    is SC 2.4.4 outright, not a matter of degree."""
    html = ui.report_rows(WIDE, token="t")
    first = re.search(r"<a [^>]*>", html).group(0)
    assert "aria-label=" in first
    assert "ADP" in first and "Automatic Data Processing" in first


def test_the_silent_anchors_are_out_of_the_accessibility_tree():
    html = ui.report_rows(WIDE, token="t")
    anchors = re.findall(r"<a [^>]*>", html)
    for anchor in anchors[1:]:
        assert 'aria-hidden="true"' in anchor, anchor
        assert 'tabindex="-1"' in anchor, anchor


def test_no_link_is_named_only_by_an_em_dash():
    """A note that declined a lead statistic renders "&mdash;" in that
    cell, so the anchor's entire accessible name was an em dash."""
    thin = dict(WIDE[0], price="", value="", filed="", cited="")
    html = ui.report_rows([thin], token="t")
    for anchor in re.findall(r'<a [^>]*>(?:&mdash;)</a>', html):
        assert 'aria-hidden="true"' in anchor


def test_a_title_without_a_ticker_does_not_fill_the_ticker_column(
    monkeypatch, tmp_path
):
    """`rpartition("(")` on a string with no "(" returns ("", "",
    whole), so the Ticker cell took the entire company name and the
    Company cell was left empty - then fell back to the same name, so
    the row printed it twice. `reports_store.save` always writes
    "Company (TICK)", so this needs a hand-edited or legacy file; it
    is one line to rule out."""
    monkeypatch.setenv("DEMO_PASSPHRASE", PHRASE)
    monkeypatch.delenv("SAMPLES_KEY", raising=False)
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path))
    saved = reports_store.save(
        "WXYZ", "A Company With No Ticker In Its Title",
        "<html>x</html>", scope=SCOPE,
    )
    at = AppTest.from_file(APP, default_timeout=60)
    at.query_params["sid"] = SCOPE
    markup = rendered_markup(_unlock(at))

    row = re.search(r"<tr><td class=\"tk\">.*?</tr>", markup, re.S)
    assert row, "no data row rendered"
    cells = re.findall(r"<td[^>]*>.*?</td>", row.group(0), re.S)
    ticker_cell = re.sub(r"<[^>]+>", "", cells[0]).strip()
    assert "A Company With No Ticker" not in ticker_cell, (
        f"the company name is in the Ticker column: {ticker_cell!r}"
    )
    assert ticker_cell == saved.slug.split("-")[0].upper()


def test_the_figures_are_still_readable_to_a_screen_reader():
    """Taking the row down to one tab stop by marking six anchors
    aria-hidden hid the TEXT inside them as well - the price, the
    metric, the value, the filing date and the citation count are all
    inside those anchors. A financial index whose figures are
    invisible to a screen reader is worse than one with seven tab
    stops, which is what the first version of this shipped.

    The link is an overlay now: the anchor fills the cell and carries
    no text, and the cell's text sits beside it in the open."""
    html = ui.report_rows(WIDE, token="t")
    row = html[html.index("<tr><td"):]
    for figure in ("$301.71", "6.8%", "2026-08-05", "113/113",
                   "Automatic Data Processing"):
        # The LAST occurrence: the company name also appears inside
        # the lead anchor's aria-label, which is the one place it is
        # legitimately inside a tag.
        index = row.rindex(figure)
        before = row[:index]
        opened = before.rfind("<a ")
        closed = before.rfind("</a>")
        assert closed > opened, (
            f"{figure!r} sits inside an anchor; if that anchor is "
            f"aria-hidden the figure is hidden with it"
        )


def test_the_overlay_links_carry_no_text_of_their_own():
    html = ui.report_rows(WIDE, token="t")
    assert "></a>" in html, "the row links still wrap their cell text"
