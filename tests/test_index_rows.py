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
    # The TITLE of the asked-for report is on the screen, and the other
    # report's is not. There used to be a radio of every note above the
    # document, so following a link to one report handed the reader a
    # six-way picker for a choice they had already made. A link to a
    # document opens that document.
    text = page_text(at)
    assert first.title in text, text[:400]
    assert second.title not in text, text[:400]


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
        "takeaway": "At 23 times free cash flow the price requires 6.8% "
                    "annual growth. The filed record compounded at 12.5% "
                    "over 5 years.",
        "slug": "adp",
    },
]


def test_the_index_carries_the_columns_the_notes_support():
    html = ui.report_rows(WIDE, token="t")
    for header in ("Ticker", "Company, and what the report found", "Price",
                   "Headline", "Filed", "Cited"):
        assert f">{header}<" in html, header
    # FCF yield and the filed CAGR were columns for one round. They are
    # comparable and they are filed, and they are still facts about the
    # COMPANY - and a reader standing in front of an index of reports
    # he has already read is not choosing a name, he is trying to
    # remember which report this was.
    assert ">FCF yield<" not in html
    assert ">FCF CAGR<" not in html
    # "Value" was a header over a column whose unit changed per row -
    # 6.8% is a growth rate and 15.3x a multiple - with the only thing
    # that told them apart in the cell beside it. The figure and its
    # question are one cell now, so the word should be gone.
    assert ">Value<" not in html
    assert ">Headline metric<" not in html


def test_each_row_has_a_cell_for_every_header():
    """Counted with a pattern rather than `count("<th")`, which also
    matched the `<thead>` the header row now sits inside."""
    import re

    html = ui.report_rows(WIDE, token="t")
    head, _, rest = html.partition("</tr>")
    assert len(re.findall(r"<th[ >]", head)) == len(re.findall(r"<td[ >]", rest))


def test_a_figure_the_note_does_not_carry_is_left_blank():
    """An em dash, not a zero and not a number borrowed from the row
    above it."""
    thin = dict(WIDE[0], price="", cited="", filed="")
    html = ui.report_rows([thin], token="t")
    assert html.count("&mdash;") == 3
    # And a note that produced no lead statistic at all gets one dash
    # for the whole finding, rather than a dash beside a label or a
    # label beside a dash.
    none = dict(thin, metric="", value="")
    assert ui.report_rows([none], token="t").count("&mdash;") == 4


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
    one tab stop per CELL would be forty-eight for six reports, and a
    links-list showing forty-eight entries for six destinations."""
    html = ui.report_rows(WIDE, token="t")
    anchors = re.findall(r"<a [^>]*>", html)
    assert len(anchors) == 6, "the row is no longer six cells"
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


def test_a_fresh_visitors_url_stays_clean(monkeypatch, tmp_path):
    """The scope only has to be in the URL once there is something
    under it. A visitor who has generated nothing should be able to
    copy the address bar and send it to someone without wondering what
    `sid` is - and the link they send should not later turn out to
    carry their research list."""
    monkeypatch.setenv("DEMO_PASSPHRASE", PHRASE)
    monkeypatch.delenv("SAMPLES_KEY", raising=False)
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path))
    at = AppTest.from_file(APP, default_timeout=60)
    at = _unlock(at)
    assert not at.exception
    assert "sid" not in at.query_params, (
        f"a scope is in the URL before anything is scoped: "
        f"{dict(at.query_params)}"
    )


def test_once_a_report_exists_the_scope_is_carried(monkeypatch, tmp_path):
    """And once it matters, it has to be there - a row is a link, and
    a link is a page load."""
    at, first, second = _seeded(monkeypatch, tmp_path)
    at = _unlock(at)
    # AppTest hands query params back as lists.
    got = at.query_params.get("sid")
    got = got[0] if isinstance(got, list) else got
    assert got == SCOPE
    assert f"sid={SCOPE}" in rendered_markup(at)


def test_the_row_links_are_bare_for_a_visitor_with_no_reports(
    monkeypatch, tmp_path
):
    """Same rule as the address bar: a link copied out of the table by
    someone who has generated nothing should not carry a parameter
    that would later resolve to their research list."""
    monkeypatch.setenv("DEMO_PASSPHRASE", PHRASE)
    monkeypatch.delenv("SAMPLES_KEY", raising=False)
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path))
    at = AppTest.from_file(APP, default_timeout=60)
    at = _unlock(at)
    assert "sid=" not in rendered_markup(at)


def test_the_scope_reaches_the_url_as_soon_as_a_report_is_saved():
    """The ordering trap in deferring the scope.

    `_session_scope` writes it to the URL only when the store already
    holds something, and the only call during a run happens while
    saving - before the file exists. So the first report a visitor
    generated left the URL bare, and a reload at that point started a
    fresh session with a fresh scope and orphaned it: the report was
    on disk, under a name nothing in the UI could reach again.

    The save has to publish the scope itself.
    """
    import pathlib
    import re

    source = pathlib.Path(APP).read_text(encoding="utf-8")
    saved = source.index('st.session_state["report_slug"] = saved.slug')
    window = source[saved - 900 : saved + 1200]
    assert re.search(r'query_params\[\s*"sid"\s*\]', window), (
        "a successful save does not put the scope in the URL, so the "
        "first report is orphaned by a reload"
    )


def test_the_index_declares_its_header_row_as_a_header():
    """SC 1.3.1. The header was a bare `tr` of `th` concatenated straight
    into the table, with no `thead`, no `tbody` and no `scope`.

    The parser then drops that row into the same implied `tbody` as the
    data rows, so header association is left to the browser's table
    algorithm rather than declared. In table-navigation mode a screen
    reader can read the header row as a data row, and the column
    announcement on each cell becomes unreliable - which on this table
    means Value and Cited are read without the label that gives them
    meaning, on the screen that makes the product's central claim.
    """
    from asset_researcher.ui import components as ui

    html = ui.report_rows([
        {"ticker": "ADP", "company": "Automatic Data Processing Inc.",
         "slug": "adp"},
    ])
    assert "<thead>" in html and "</thead>" in html
    assert "<tbody>" in html and "</tbody>" in html
    assert html.count('scope="col"') == 6, (
        "every column header should declare its scope"
    )
    # The header must be inside thead, not loose in the table.
    head = html[html.index("<thead>"):html.index("</thead>")]
    assert "Ticker" in head and "Cited" in head


def test_the_index_names_itself_for_a_screen_reader():
    """The heading above the table is a sibling, not the table's name."""
    from asset_researcher.ui import components as ui

    html = ui.report_rows([{"ticker": "ADP", "company": "ADP", "slug": "adp"}])
    assert "<caption" in html


def test_the_index_carries_the_report_s_own_opening_sentence():
    """What the row is FOR.

    A reader standing in front of an index of reports he has already
    read is not choosing a company, he is trying to remember which
    report this was - and two ratios cannot tell him that, because they
    are facts about the company rather than about the report. The
    note's own first paragraph can: the multiple, what the price
    requires, and what the record actually did, in two sentences it
    wrote itself.
    """
    html = ui.report_rows(WIDE, token="t")
    assert "At 23 times free cash flow" in html
    # Under the company name, in the same cell, not in a column of its
    # own - a line of prose running 500px between two figure columns is
    # skipped rather than read.
    said = html[html.index('class="co said"'):][:700]
    assert "<b>Automatic Data Processing</b>" in said
    assert "<span>At 23 times" in said


def test_a_note_with_no_opening_sentence_prints_the_name_alone():
    """Not an empty bold tag, not a dash under the name, and above all
    not a sentence borrowed from the row above it."""
    bare = dict(WIDE[0], takeaway="")
    html = ui.report_rows([bare], token="t")
    said = html[html.index('class="co said"'):][:400]
    assert "<b>" not in said and "<span>" not in said
    assert "Automatic Data Processing" in said
