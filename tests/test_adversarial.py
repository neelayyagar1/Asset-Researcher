"""Deliberate attempts to break the shell.

Everything a reader can type or put in the address bar, pushed at the
boundaries. The point is not that these inputs are likely - it is that
a stack trace on a page someone is using to judge the builder costs
more than the input was ever worth.

NOTHING HERE MAY START A RUN. A first version of this file clicked
"Generate report" for each hostile ticker, which is not a simulation:
the click queues the run and the next script pass executes the real
pipeline against EDGAR and the model provider. The suite ran for ten
minutes and was spending real money per case before it was killed. The
dangerous act is the click, so the click is gone; a hostile value is
put into the widget and the page is re-rendered around it, which is
what these tests were ever about.

The one exception is an empty ticker, which the form refuses before it
queues anything - that path is asserted directly.
"""

from __future__ import annotations

import pathlib

import pytest
from streamlit.testing.v1 import AppTest

from tests.apptest_helpers import page_text, rendered_markup

APP = str(pathlib.Path(__file__).resolve().parents[1] / "app.py")
PHRASE = "test-only-passphrase"


def _app(monkeypatch, timeout: float = 90):
    monkeypatch.setenv("DEMO_PASSPHRASE", PHRASE)
    monkeypatch.delenv("SAMPLES_KEY", raising=False)
    return AppTest.from_file(APP, default_timeout=timeout)


def _unlock(at):
    at.text_input(key="gate_input").set_value(PHRASE)
    at.button[0].click().run()
    return at


def _form(monkeypatch):
    at = _unlock(_app(monkeypatch).run())
    next(b for b in at.button if b.label == "Generate a report").click().run()
    return at


HOSTILE_TEXT = [
    "",
    "   ",
    "<script>alert(1)</script>",
    "../../etc/passwd",
    "A" * 500,
    "'; DROP TABLE filings; --",
    "\x00\x01\x02",
    "ПРИВЕТ",
    "🙂🙂🙂",
    "AAPL\nMSFT",
    "{{7*7}}",
    "%s%s%s%n",
]


@pytest.mark.parametrize("value", HOSTILE_TEXT)
def test_the_ticker_field_renders_anything_without_raising(
    monkeypatch, value
):
    """Set, then re-render. No click: a click queues a real run."""
    at = _form(monkeypatch)
    at.text_input(key="inline_ticker").set_value(value).run()
    assert not at.exception, f"ticker {value!r} raised"


def test_an_empty_ticker_is_refused_before_anything_is_queued(monkeypatch):
    at = _form(monkeypatch)
    at.text_input(key="inline_ticker").set_value("   ")
    next(b for b in at.button if b.label == "Generate report").click().run()
    assert not at.exception
    assert "Enter a ticker" in page_text(at)
    queued = at.session_state["pending"] if "pending" in at.session_state else None
    assert not queued, f"a blank ticker queued {queued!r}"


@pytest.mark.parametrize("value", HOSTILE_TEXT)
def test_the_gate_never_raises(monkeypatch, value):
    at = _app(monkeypatch).run()
    at.text_input(key="gate_input").set_value(value)
    at.button[0].click().run()
    assert not at.exception, f"passphrase {value!r} raised"
    # And none of them open it.
    assert not "Get started" in page_text(at), (
        f"passphrase {value!r} opened the gate"
    )


@pytest.mark.parametrize("value", [
    "javascript:alert(1)",
    "file:///etc/passwd",
    "http://127.0.0.1:8501/",
    "http://169.254.169.254/latest/meta-data/",
    "not a url at all",
    "https://" + "a" * 300 + ".example",
    "ftp://example.com/x",
    "\n\n\n",
])
def test_a_hostile_source_url_renders_without_raising(monkeypatch, value):
    """Again no click. What a hostile URL does once fetched is covered
    offline by tests/test_web_ssrf.py, which is where that belongs."""
    at = _form(monkeypatch)
    at.text_area(key="inline_urls").set_value(value).run()
    assert not at.exception, f"url {value!r} raised"


@pytest.mark.parametrize("value", [
    "samples", "tool", "home", "", "nonsense", "../../etc/passwd",
    "<script>", "home ", "HOME", "home\x00", "a" * 400,
])
def test_any_view_in_the_url_never_raises(monkeypatch, value):
    at = _app(monkeypatch)
    at.query_params["view"] = value
    at = _unlock(at.run())
    assert not at.exception, f"?view={value!r} raised"


@pytest.mark.parametrize("value", [
    "", "garbage", "0" * 64, "../../", "<script>", "\x00",
])
def test_a_tampered_unlock_token_never_raises_and_never_opens(
    monkeypatch, value
):
    """The token is a digest of the passphrase. A wrong one must refuse
    rather than fail open or fall over."""
    at = _app(monkeypatch)
    at.query_params["k"] = value
    at.run()
    assert not at.exception, f"?k={value!r} raised"
    text = page_text(at)
    assert "Get started" not in text, f"?k={value!r} opened the gate"
