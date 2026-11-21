"""Reports a visitor generated, kept where a reload can find them again.

Two things made this necessary at once. The owner asked that a report
they generate join the samples in the index on the first screen, and
that the rows there be clickable. A clickable row is an anchor, an
anchor is a page load, and a page load ends the Streamlit session -
which, while a report lived only in `st.session_state`, meant every
row on the index was a loaded gun pointed at a report that cost a
minute and about a dollar.

Persisting the rendered document defuses that: the row a reader clicks
cannot destroy anything, because the thing is on disk.

The slug is the dangerous surface. It arrives in a query string, so it
is matched against a pattern before it is ever joined to a path.
"""

from __future__ import annotations

import pytest

from asset_researcher import reports_store as store


@pytest.fixture()
def here(tmp_path, monkeypatch):
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path))
    return tmp_path


def test_nothing_saved_lists_nothing(here):
    assert store.listing() == []


def test_a_saved_report_comes_back_whole(here):
    saved = store.save("ADP", "Automatic Data Processing (ADP)", "<html>x</html>")
    again = store.load(saved.slug)
    assert again is not None
    assert again.html == "<html>x</html>"
    assert again.title == "Automatic Data Processing (ADP)"


def test_the_newest_report_is_listed_first(here):
    first = store.save("AAA", "A (AAA)", "<html>1</html>")
    second = store.save("BBB", "B (BBB)", "<html>2</html>")
    assert [s.slug for s in store.listing()] == [second.slug, first.slug]


def test_two_reports_on_one_ticker_do_not_collide(here):
    a = store.save("ADP", "A (ADP)", "<html>1</html>")
    b = store.save("ADP", "A (ADP)", "<html>2</html>")
    assert a.slug != b.slug
    assert len(store.listing()) == 2


@pytest.mark.parametrize(
    "slug",
    ["../../etc/passwd", "..", "a/b", "a\\b", "", "x" * 200, "a b", "a.b"],
)
def test_a_slug_that_is_not_one_is_refused(here, slug):
    assert store.load(slug) is None


def test_a_traversal_cannot_reach_a_file_that_exists(here, tmp_path, monkeypatch):
    """A WELL-FORMED file outside the directory.

    The first version of this test wrote a file the reader would have
    rejected anyway, for a missing field, so it passed with the slug
    check deleted and proved nothing. Confirmed by deleting the check:
    this version fails, the first one did not.
    """
    elsewhere = tmp_path.parent / "elsewhere"
    elsewhere.mkdir(exist_ok=True)
    monkeypatch.setenv("REPORTS_DIR", str(elsewhere))
    planted = store.save("SECRET", "Secret (SECRET)", "<html>secret</html>")
    monkeypatch.setenv("REPORTS_DIR", str(here))

    assert store.load(planted.slug) is None, "reachable by its own name?"
    assert store.load(f"../elsewhere/{planted.slug}") is None
    assert store.load(f"..%2felsewhere%2f{planted.slug}") is None


# ------------------------------------------------------------ one visitor

def test_two_visitors_do_not_see_each_others_reports(here):
    """The store is one directory in one container, and every visitor
    to the deployment shares it. Without a scope, a reviewer who
    generates a report on a name they are considering puts that name
    at the top of the index for every other reviewer holding the
    link - and on this deployment the ticker someone chose to research
    is itself the sensitive thing."""
    mine = store.save("ADP", "A (ADP)", "<html>mine</html>", scope="aaa")
    theirs = store.save("COST", "C (COST)", "<html>theirs</html>", scope="bbb")

    assert [s.slug for s in store.listing(scope="aaa")] == [mine.slug]
    assert [s.slug for s in store.listing(scope="bbb")] == [theirs.slug]


def test_one_visitor_cannot_open_anothers_report_by_its_slug(here):
    theirs = store.save("COST", "C (COST)", "<html>theirs</html>", scope="bbb")
    assert store.load(theirs.slug, scope="aaa") is None
    assert store.load(theirs.slug, scope="bbb") is not None


def test_a_scope_that_is_not_a_slug_is_refused(here):
    """It is joined to a path, so it is checked the same way."""
    store.save("ADP", "A (ADP)", "<html>x</html>", scope="aaa")
    for bad in ("../aaa", "a/b", "..", "", "a.b"):
        assert store.listing(scope=bad) == []
        assert store.load("whatever", scope=bad) is None


def test_an_unscoped_store_still_works(here):
    """Local runs and the tests above use it."""
    saved = store.save("ADP", "A (ADP)", "<html>x</html>")
    assert store.load(saved.slug) is not None
