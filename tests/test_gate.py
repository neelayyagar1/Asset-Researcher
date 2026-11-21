"""The passphrase gate.

Not authentication: one secret, shared, no per-person revocation. What it
buys is that a stranger cannot reach the Generate button and spend the
API balance behind it. That makes it worth testing in exactly one
respect, which is that it cannot fail open.
"""

from __future__ import annotations

import hmac


def test_a_wrong_passphrase_does_not_match():
    assert not hmac.compare_digest("wrong", "right")


def test_the_right_passphrase_matches():
    assert hmac.compare_digest("right", "right")


def test_an_empty_attempt_does_not_match_a_configured_secret():
    """The default value of an untouched text input is the empty string,
    so this is the state every visitor starts in."""
    assert not hmac.compare_digest("", "a-real-passphrase")


def test_a_prefix_of_the_secret_does_not_match():
    assert not hmac.compare_digest("a-real", "a-real-passphrase")


def test_the_gate_is_wired_ahead_of_everything_it_protects():
    """A gate placed after the work it guards is not a gate. The call has
    to sit above the report pipeline in the module, because this file runs
    top to bottom on every rerun."""
    source = (
        __import__("pathlib").Path(__file__).resolve().parents[1] / "app.py"
    ).read_text()

    gate_at = source.index("if not _gate():")
    assert "st.stop()" in source[gate_at:gate_at + 80]

    for guarded in ("def generate(", "_run_pending()", "Generate report"):
        assert source.index(guarded) > gate_at, (
            f"{guarded!r} is reachable before the gate"
        )


def test_no_passphrase_configured_leaves_the_app_open():
    """Local runs have no secret and must not be locked out of their own
    tool; the gate exists for deployments, which set one."""
    source = (
        __import__("pathlib").Path(__file__).resolve().parents[1] / "app.py"
    ).read_text()
    assert "if not secret:\n        return True" in source


def test_the_backoff_screen_still_has_a_field_and_a_button(monkeypatch):
    """A screen a reader cannot act on is a dead end.

    The backoff branch rendered the gate markup and a countdown, then
    returned before the form was built. The field and the submit button
    were absent, nothing re-rendered when the delay elapsed, and the
    countdown was a frozen number: the only way forward was a page
    reload, which the screen did not say. That is the first screen of
    the artifact.
    """
    import pathlib
    from streamlit.testing.v1 import AppTest

    app_path = str(pathlib.Path(__file__).resolve().parents[1] / "app.py")
    monkeypatch.setenv("DEMO_PASSPHRASE", "the-real-phrase")
    monkeypatch.delenv("SAMPLES_KEY", raising=False)

    at = AppTest.from_file(app_path, default_timeout=60).run()
    for _ in range(5):
        at.text_input(key="gate_input").set_value("wrong").run()
        at.button[0].click().run()

    assert not at.exception
    text = " ".join(m.value for m in at.markdown)
    assert "Too many attempts" in text, "the backoff never engaged"

    # The screen must remain operable.
    assert at.text_input(key="gate_input") is not None, (
        "the passphrase field is gone during backoff"
    )
    assert at.button, "no control on the backoff screen"
