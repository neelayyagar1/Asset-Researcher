"""The screens, the buttons between them, and the gate in front.

`app.py` had no tests at all. Its own reviewers' guide said so, and the
consequence was that three separate navigation faults shipped: the
browser's Back changed the address bar without changing the page, the
form screen had no way out, and the samples button vanished silently
when a secret was missing. None of those are subtle. All of them were
invisible to a suite that never ran the view layer.

`AppTest` runs the real script in-process, so these exercise the actual
widgets and the actual state machine rather than a description of them.
No network, no API calls, no money.
"""

from __future__ import annotations

import pathlib

import pytest
from streamlit.testing.v1 import AppTest

APP = str(pathlib.Path(__file__).resolve().parents[1] / "app.py")
PHRASE = "test-only-passphrase"


def _app(monkeypatch, *, passphrase: str | None = PHRASE, timeout: float = 60):
    monkeypatch.setenv("DEMO_PASSPHRASE", passphrase or "")
    # No samples archive in tests: the samples path is covered by
    # test_deployment_safety.py, and leaving it unset keeps these runs
    # free of a scrypt derivation each.
    monkeypatch.delenv("SAMPLES_KEY", raising=False)
    return AppTest.from_file(APP, default_timeout=timeout)


def _labels(at) -> list[str]:
    return [b.label for b in at.button]


def _unlock(at):
    at.text_input(key="gate_input").set_value(PHRASE)
    at.button[0].click().run()
    return at


# ------------------------------------------------------------- the gate

def test_the_gate_stops_an_unauthenticated_visitor(monkeypatch):
    at = _app(monkeypatch).run()
    text = " ".join(m.value for m in at.markdown)
    assert "Asset Researcher" in text
    # Nothing that spends money is on the page.
    assert not any("Generate a report" in lab for lab in _labels(at))


def test_the_right_passphrase_opens_it(monkeypatch):
    at = _unlock(_app(monkeypatch).run())
    assert any("Generate a report" in lab for lab in _labels(at))


def test_a_wrong_passphrase_does_not(monkeypatch):
    at = _app(monkeypatch).run()
    at.text_input(key="gate_input").set_value("not the phrase")
    at.button[0].click().run()
    assert not any("Generate a report" in lab for lab in _labels(at))


def test_an_en_dash_is_forgiven(monkeypatch):
    """A mail client turns a hyphen into an en dash, and the reader
    pastes what the mail client gave them."""
    monkeypatch.setenv("DEMO_PASSPHRASE", "ar-26")
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.text_input(key="gate_input").set_value("ar–26")
    at.button[0].click().run()
    assert any("Generate a report" in lab for lab in _labels(at))


def test_no_passphrase_configured_leaves_it_open(monkeypatch):
    at = _app(monkeypatch, passphrase=None).run()
    assert any("Generate a report" in lab for lab in _labels(at))


def test_the_gate_raises_nothing_on_any_of_these(monkeypatch):
    """compare_digest raises TypeError on non-ASCII str, which would have
    shown a visitor a traceback instead of a refusal."""
    for attempt in ("", "   ", "pässwörd", "x" * 500, "Ar_26\n"):
        at = _app(monkeypatch).run()
        at.text_input(key="gate_input").set_value(attempt)
        at.button[0].click().run()
        assert not at.exception, f"{attempt!r} raised"


# ------------------------------------------------- moving between views

def test_the_home_button_reaches_the_form(monkeypatch):
    """Home has one primary action now. The "How it works" page was
    deleted and its instructions moved onto home as Get started, so a
    reader learns how to drive the tool without leaving the first
    screen."""
    at = _unlock(_app(monkeypatch).run())
    next(b for b in at.button if b.label == "Generate a report").click().run()
    assert not at.exception
    assert "Generate a report" in " ".join(m.value for m in at.markdown)


def test_home_carries_the_instructions_itself(monkeypatch):
    at = _unlock(_app(monkeypatch).run())
    text = " ".join(m.value for m in at.markdown)
    assert "Get started" in text
    assert "US-listed ticker" in text


def test_the_how_it_works_page_is_gone(monkeypatch):
    """Pinned: it duplicated the landing copy and sent a first-time
    reader to a second screen to understand the first."""
    at = _unlock(_app(monkeypatch).run())
    assert not any("How it works" in lab for lab in _labels(at))


def test_the_form_screen_has_a_way_back(monkeypatch):
    """It had none: a reader who opened it and decided not to spend a
    minute and a dollar was stuck, and the browser's own Back left the
    site entirely."""
    at = _unlock(_app(monkeypatch).run())
    next(b for b in at.button if b.label == "Generate a report").click().run()
    assert any(b.label == "Back" for b in at.button)

    next(b for b in at.button if b.label == "Back").click().run()
    assert any("Generate a report" in lab for lab in _labels(at))


def test_every_screen_can_be_reached_and_left(monkeypatch):
    """A round trip through each view, ending where it started."""
    at = _unlock(_app(monkeypatch).run())
    for label in ("Generate a report",):
        next(b for b in at.button if b.label == label).click().run()
        assert not at.exception, f"{label} raised"
        back = [b for b in at.button if b.label == "Back"]
        assert back, f"no way back from {label}"
        back[0].click().run()
        assert any("Generate a report" in lab for lab in _labels(at)), (
            f"did not return home from {label}"
        )


def test_the_view_is_in_the_url(monkeypatch):
    """So the browser's Back has something to go back to."""
    at = _unlock(_app(monkeypatch).run())
    next(b for b in at.button if b.label == "Generate a report").click().run()
    # AppTest hands back the raw multi-value form.
    got = at.query_params.get("view")
    assert (got[0] if isinstance(got, list) else got) == "tool"


def test_an_unknown_view_in_the_url_falls_back_to_home(monkeypatch):
    at = _app(monkeypatch)
    at.query_params["view"] = "nonsense"
    at.run()
    at = _unlock(at)
    assert any("Generate a report" in lab for lab in _labels(at))


# --------------------------------------------------------- the samples

def test_the_samples_button_is_absent_without_a_key(monkeypatch):
    """Absent rather than broken: a deployment that ships no archive is a
    normal state. The failure that is NOT normal - a key that is set and
    does not open the archive - is reported on screen instead."""
    at = _unlock(_app(monkeypatch).run())
    assert not any("Read a sample" in lab for lab in _labels(at))


def test_a_key_that_does_not_open_the_archive_is_reported(monkeypatch):
    monkeypatch.setenv("DEMO_PASSPHRASE", PHRASE)
    monkeypatch.setenv("SAMPLES_KEY", "not-the-packing-key")
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.text_input(key="gate_input").set_value(PHRASE)
    at.button[0].click().run()
    assert not at.exception
    text = " ".join(m.value for m in at.markdown)
    assert "SAMPLES_KEY" in text


# ------------------------------------------------- reachable-by-URL views

def test_the_samples_view_survives_having_no_samples(monkeypatch):
    """It did not. With no archive the view built a radio over an empty
    option list and `next()` raised StopIteration, which Streamlit shows
    as a red error panel.

    The button that leads here is hidden without an archive, but the view
    is addressable: `go()` writes the view into the query string and the
    URL is adopted on load, so a bookmark, a pasted link, a reload or the
    browser's Back all reach it. A hidden entry point is not a guard.
    """
    at = _app(monkeypatch)
    at.query_params["view"] = "samples"
    at = _unlock(at.run())
    assert not at.exception, "the samples view raised with no archive"

    text = " ".join(m.value for m in at.markdown)
    assert "No sample notes shipped" in text
    # And it offers a way on, rather than being a dead end.
    assert any("Generate a report" in b.label for b in at.button)


def test_every_known_view_renders_without_an_archive(monkeypatch):
    """Each addressable view, entered cold by URL."""
    for view in ("home", "tool", "samples"):
        at = _app(monkeypatch)
        at.query_params["view"] = view
        at = _unlock(at.run())
        assert not at.exception, f"?view={view} raised"


def test_an_unknown_view_still_falls_back(monkeypatch):
    at = _app(monkeypatch)
    at.query_params["view"] = "../../etc/passwd"
    at = _unlock(at.run())
    assert not at.exception
    assert any("Generate a report" in lab for lab in _labels(at))
