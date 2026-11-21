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


def _seeded(monkeypatch, tmp_path):
    """Two saved reports and no sealed archive, so this costs nothing."""
    monkeypatch.setenv("DEMO_PASSPHRASE", PHRASE)
    monkeypatch.delenv("SAMPLES_KEY", raising=False)
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path))
    first = reports_store.save("AAA", "Alpha Inc. (AAA)", "<html>alpha</html>")
    second = reports_store.save("BBB", "Beta Corp. (BBB)", "<html>beta</html>")
    at = AppTest.from_file(APP, default_timeout=60)
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
