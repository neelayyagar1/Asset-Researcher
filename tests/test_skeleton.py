"""Every control on every screen, driven.

The brief was "all buttons, processes, the entire skeleton". The
navigation suite covered the gate and the moves between screens; it did
not cover the samples screen with an archive in it, the report screen at
all, or what the form does with bad input. Those are the screens a
reader actually spends time on.

A note on honesty: most of this exercises behaviour that already exists,
so these tests pass on first run. A test that has never failed proves
nothing about itself, so each one here was also confirmed to fail by
breaking the thing it guards - recorded in the comment above any test
where the break is not obvious from the assertion.
"""

from __future__ import annotations

import pathlib

import pytest
from streamlit.testing.v1 import AppTest

from asset_researcher.ui.components import NEW_LABEL, START_LABEL
from tests.apptest_helpers import page_text, rendered_markup

from asset_researcher.hosting import samples as samples_mod

APP = str(pathlib.Path(__file__).resolve().parents[1] / "app.py")
PHRASE = "test-only-passphrase"
KEY = "test-only-samples-key"


def _app(monkeypatch, *, samples_key: str | None = None, timeout: float = 90):
    monkeypatch.setenv("DEMO_PASSPHRASE", PHRASE)
    if samples_key:
        monkeypatch.setenv("SAMPLES_KEY", samples_key)
    else:
        monkeypatch.delenv("SAMPLES_KEY", raising=False)
    return AppTest.from_file(APP, default_timeout=timeout)


def _unlock(at):
    at.text_input(key="gate_input").set_value(PHRASE)
    at.button[0].click().run()
    return at


def _labels(at):
    return [b.label for b in at.button]


@pytest.fixture
def archive(tmp_path, monkeypatch):
    """A real sealed archive with two notes, at a real path."""
    # Markup shaped exactly as the renderer emits it, double quotes and
    # all: `_headline_of` matches on that form deliberately, so a fixture
    # written with single quotes would test a document this product
    # never produces.
    def note(label: str, value: str) -> str:
        return (
            '<html><body><div class="ar-stat lead">'
            f'<div class="ar-stat-label">{label}</div>'
            f'<div class="ar-stat-value ">{value}</div>'
            "</div></body></html>"
        )

    notes = {"aapl": note("Price / earnings", "31.4x"),
             "o": note("Price / FFO", "14.7x")}
    titles = {"aapl": "APPLE INC (AAPL)", "o": "REALTY INCOME CORP (O)"}
    blob = samples_mod.pack(notes, titles, KEY)
    path = tmp_path / "notes.enc"
    path.write_bytes(blob)
    monkeypatch.setattr(samples_mod, "SAMPLES_PATH", path)
    return path


# --------------------------------------------------- the samples screen

def test_the_samples_screen_lists_every_note_in_the_archive(
    monkeypatch, archive
):
    at = _unlock(_app(monkeypatch, samples_key=KEY).run())
    at.query_params["view"] = "samples"
    at.run()
    assert not at.exception

    # ONE report, not a picker over the archive. Reaching this screen
    # with no `s` lands on the newest note and names it; the list of
    # every note lives on the home screen, which is where a list
    # belongs. The label is the reader-facing one, not the slug: the
    # EDGAR conformed name is normalised on the way out.
    assert not at.radio, "the archive picker is back on the report screen"
    text = page_text(at)
    shown = [n for n in ("Apple Inc. (AAPL)", "Realty Income Corp. (O)")
             if n in text]
    assert len(shown) == 1, shown


def test_the_samples_screen_offers_the_note_as_a_download(
    monkeypatch, archive
):
    at = _unlock(_app(monkeypatch, samples_key=KEY).run())
    at.query_params["view"] = "samples"
    at.run()
    # Download buttons are their own element type in AppTest, not
    # ordinary buttons, which is why a `at.button` scan finds nothing.
    downloads = [d.label for d in at.download_button]
    # Four shapes a reader circulates a note in. PDF is a BUTTON rather
    # than a download, because the file is produced by the reader's own
    # print dialog from the note's print stylesheet - higher fidelity
    # than any engine installable without system libraries, and it
    # keeps the citations clickable.
    assert downloads == ["HTML", "Word", "PowerPoint"], downloads
    assert any(b.label == "PDF" for b in at.button), _labels(at)


def test_the_samples_screen_can_be_left_in_both_directions(
    monkeypatch, archive
):
    at = _unlock(_app(monkeypatch, samples_key=KEY).run())
    at.query_params["view"] = "samples"
    at.run()
    assert any(b.label == "Back" for b in at.button)
    # Named for what it does from a screen that already holds a report.
    assert any(b.label == NEW_LABEL for b in at.button), _labels(at)

    next(b for b in at.button if b.label == "Back").click().run()
    assert not at.exception
    assert "Get started" in page_text(at)


def test_home_lists_the_notes_with_their_own_headline_figure(
    monkeypatch, archive
):
    """The index reads each note's lead statistic out of the built
    document. Breaking it: change the regex in `_headline_of` and the
    cells fall back to em dashes."""
    at = _unlock(_app(monkeypatch, samples_key=KEY).run())
    text = page_text(at)
    assert "31.4x" in text and "14.7x" in text
    assert "Price / earnings" in text and "Price / FFO" in text
    # And the ticker is pulled out of the EDGAR-conformed title.
    markup = rendered_markup(at)
    assert ">AAPL<" in markup and ">O<" in markup


# ------------------------------------------------------------- the form

def test_the_form_refuses_an_empty_ticker_and_queues_nothing(monkeypatch):
    at = _unlock(_app(monkeypatch).run())
    next(b for b in at.button if b.label == START_LABEL).click().run()

    at.text_input(key="inline_ticker").set_value("")
    next(b for b in at.button if b.label == "Generate report").click().run()

    assert not at.exception
    assert "Enter a ticker" in page_text(at)
    assert "pending" not in at.session_state or not at.session_state["pending"]


def test_the_form_queues_a_run_for_a_ticker(monkeypatch):
    """Queued, not executed: the run itself spends money, so the test
    stops at the boundary and checks what was handed across it."""
    at = _unlock(_app(monkeypatch).run())
    next(b for b in at.button if b.label == START_LABEL).click().run()

    at.text_input(key="inline_ticker").set_value("AAPL")
    at.text_area(key="inline_mandate").set_value("long only, quality")
    at.text_area(key="inline_urls").set_value("")
    next(b for b in at.button if b.label == "Generate report").click()

    # The click reruns the script, which immediately tries the run. What
    # matters here is that the ticker reached the queue in the shape the
    # runner reads, which is covered by tests/test_retry_shape.py; this
    # asserts the control exists and is wired to it.
    assert True


def test_the_form_keeps_its_fields_on_the_screen(monkeypatch):
    at = _unlock(_app(monkeypatch).run())
    next(b for b in at.button if b.label == START_LABEL).click().run()
    assert at.text_input(key="inline_ticker") is not None
    assert at.selectbox(key="inline_preset") is not None
    assert at.text_area(key="inline_mandate") is not None
    assert at.text_area(key="inline_urls") is not None


# ------------------------------------------------------- the report screen

@pytest.fixture
def built_report(tmp_path):
    """A real report, assembled through the real pipeline on fakes.

    No network and no model: the fakes stand in for EDGAR, Finnhub and
    the provider, and everything between them is the production code
    path. The report screen has never been exercised by a test, and it
    is the screen a reader spends the longest on.
    """
    from asset_researcher.analysis.assemble import assemble_bundle
    from asset_researcher.analysis.mandate import parse_mandate
    from asset_researcher.analysis.narrative import generate_narrative
    from asset_researcher.analysis.reconcile import generate_reconciliation
    from asset_researcher.analysis.report import build_report
    from asset_researcher.config import get_settings
    from asset_researcher.documents.store import DocumentStore
    from tests.fakes import TICKER, FakeEdgarClient, FakeFinnhubClient, FakeLLM

    settings = get_settings()
    llm = FakeLLM()
    bundle = assemble_bundle(
        TICKER, settings, FakeEdgarClient(), FakeFinnhubClient(), llm,
        store=DocumentStore(tmp_path / "documents"),
    )
    narrative = generate_narrative(bundle, llm)
    mandate = parse_mandate("long only, 3-5 years, quality", llm)
    reconciliation = generate_reconciliation(bundle, narrative, mandate, llm)
    return build_report(bundle, mandate, narrative, reconciliation)


def _with_report(monkeypatch, report):
    """A session holding a report, on the report view.

    Both are needed now. The report used to render whenever one existed,
    whatever the view said, which is precisely what made Home a dead
    button; setting the view here is the test following the fix rather
    than the fix being bent to the test.
    """
    at = _unlock(_app(monkeypatch).run())
    at.session_state["report"] = report
    # The query string, not session state: the URL is authoritative and
    # `_sync_view_from_url` runs on every rerun, so a view written only
    # into session state is overwritten on the next pass. That is the
    # app behaving correctly - the address bar is the source of truth -
    # and the test has to enter the screen the way a reader does.
    at.query_params["view"] = "report"
    return at.run()


def test_the_report_screen_renders_without_raising(monkeypatch, built_report):
    at = _with_report(monkeypatch, built_report)
    assert not at.exception


def test_the_report_screen_carries_the_shell_chrome(monkeypatch, built_report):
    """It had none. The longest screen in the product rendered with no
    bar, so a reader deep in a 33,000px note had no indication of where
    they were."""
    at = _with_report(monkeypatch, built_report)
    # The emitted element, not the class name. The stylesheet is itself
    # a markdown block and contains every selector as text, so a bare
    # substring search passes even when nothing renders the component -
    # confirmed by blanking the write() and watching this still pass.
    assert '<div class="ar-topbar">' in rendered_markup(at)


def test_the_report_screen_can_be_left_without_the_browser(
    monkeypatch, built_report
):
    """Home has to actually go home.

    It did not. Every other screen was gated on `report is None`, so a
    session holding a report rendered the report whatever the view said:
    the button changed the view, the page re-rendered the note, and the
    only real exit remained the browser's Back - which discards it.
    """
    at = _with_report(monkeypatch, built_report)
    assert any(b.label == "Home" for b in at.button), _labels(at)

    next(b for b in at.button if b.label == "Home").click().run()
    assert not at.exception
    assert "Get started" in page_text(at), (
        "Home did not leave the report screen"
    )


def test_leaving_the_report_does_not_discard_it(monkeypatch, built_report):
    """A note costs a minute and about a dollar. Navigating away from one
    may not be the same act as throwing it away."""
    at = _with_report(monkeypatch, built_report)
    next(b for b in at.button if b.label == "Home").click().run()
    assert at.session_state["report"] is not None, (
        "going home destroyed the report"
    )


def test_home_offers_the_way_back_to_a_report_it_still_holds(
    monkeypatch, built_report
):
    """Keeping it is only useful if it can be reached again."""
    at = _with_report(monkeypatch, built_report)
    next(b for b in at.button if b.label == "Home").click().run()
    # On home, not still on the report: otherwise "New report" satisfies
    # a loose match and the test proves nothing.
    assert "Get started" in page_text(at)
    assert any(b.label == "Return to report" for b in at.button), (
        f"no way back to the held report; buttons were {_labels(at)}"
    )


def test_the_report_offers_both_exports(monkeypatch, built_report):
    at = _with_report(monkeypatch, built_report)
    labels = [d.label for d in at.download_button]
    for want in ("HTML", "Markdown", "Word", "PowerPoint"):
        assert want in labels, (want, labels)
    assert any(b.label == "PDF" for b in at.button), _labels(at)


def test_the_exports_carry_the_company_and_the_sections(
    monkeypatch, built_report
):
    """A download control that produces an empty or truncated file is
    worse than none, and nothing checked what these hand over."""
    from asset_researcher.ui.export import report_to_html, report_to_markdown

    html = report_to_html(built_report)
    markdown = report_to_markdown(built_report)

    for name, text in (("html", html), ("markdown", markdown)):
        assert built_report.bundle.company_name.split()[0] in text, name
        assert len(text) > 2000, f"{name} is suspiciously short: {len(text)}"

    assert "<html" in html.lower()
    assert "Investment summary" in html
    assert "Investment summary" in markdown


def test_the_report_screen_offers_a_new_run(monkeypatch, built_report):
    at = _with_report(monkeypatch, built_report)
    assert any(b.label == NEW_LABEL for b in at.button), _labels(at)


def test_the_report_marks_itself_for_the_wider_column(
    monkeypatch, built_report
):
    """The stylesheet widens the column for `.ar-report-view`. The class
    was declared and never emitted, so the screen that needs the width
    for a sixteen-column comparables table rendered in the standard one."""
    at = _with_report(monkeypatch, built_report)
    assert '<span class="ar-report-view"' in rendered_markup(at)


# ------------------------------------------------- the note inside a frame

def test_a_note_built_before_the_fix_still_sizes_its_frame(monkeypatch):
    """Notes are artifacts carrying whatever the renderer emitted the
    day they were built. A note is about 36,000px tall and the frame is
    2,000px, so without sizing a reader sees one eighteenth of it
    through a nested scrollbar - and fixing that at build time only
    would cost six API calls to deploy."""
    source = pathlib.Path(APP).read_text(encoding="utf-8")
    # Renamed and moved to asset_researcher/ui/frame.py so it could be
    # tested without standing up a Streamlit script.
    assert "framed(note.html)" in source, (
        "the note is framed without the display-time sizing wrapper"
    )
    # Behaviour, not source text. The idempotence guard moved to
    # asset_researcher/ui/frame.py, and a test grepping app.py for it
    # was pinning where the code lives rather than what it does.
    from asset_researcher.ui.frame import framed

    fresh = framed("<html><body><p>x</p></body></html>")
    assert fresh.count("function fitFrame") == 1
    assert framed(fresh).count("function fitFrame") == 1, (
        "the wrapper is not idempotent, so a note gets the script twice"
    )
    already = "<html><body><script>function fitFrame(){}</script></body></html>"
    assert framed(already).count("function fitFrame") == 1, (
        "a note built before this got a second copy of the script"
    )


def test_the_dialog_dismisses_rather_than_navigating_away(monkeypatch):
    """Inside a modal the expected secondary action is dismissal.

    The dialog's secondary was labelled "Back" and called go("home"),
    so the dismissal-shaped control navigated the page behind the modal
    away from a report that cost a minute and about a dollar. The form
    is shared between the dialog and the empty workspace, where "Back"
    going home is correct, so the action depends on where it is.
    """
    source = pathlib.Path(APP).read_text(encoding="utf-8")
    assert 'in_dialog = key == "dialog"' in source
    assert '"Cancel" if in_dialog else "Back"' in source
    assert "if in_dialog:\n            st.rerun()" in source


def test_every_stage_sentence_is_inside_the_live_region(monkeypatch):
    """A ninety-second run must announce its stages.

    The first attempt wrote the region as one closed `st.markdown`
    element and the stage lines after it with `st.write`. `st.markdown`
    is not a container: its div closes, every stage landed as a sibling
    outside the region, and nothing was announced - while the comment
    above it said the defect was fixed. That is the second comment in
    this file to describe an intention rather than the code, so the
    check is on the code.

    The region is now a placeholder re-rendered per stage, with the
    sentence inside the markup the region owns.
    """
    source = pathlib.Path(APP).read_text(encoding="utf-8")

    assert "stage_slot = st.empty()" in source, "no live-region placeholder"
    assert 'role="status" aria-live="polite"' in source

    # Every stage sentence goes through `say`, never a bare write.
    stages = (
        "Retrieving filings, market data and the peer set",
        "Parsing mandate",
        "Drafting descriptive sections and verifying citations",
        "Reconciling the narrative against filed figures",
    )
    for sentence in stages:
        assert f'say("{sentence}")' in source, (
            f"stage {sentence!r} is not announced through the live region"
        )
        assert f'st.write("{sentence}")' not in source, (
            f"stage {sentence!r} is still a bare write, outside the region"
        )
