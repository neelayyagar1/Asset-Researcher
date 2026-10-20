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
