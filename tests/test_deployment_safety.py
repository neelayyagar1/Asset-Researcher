"""The properties a public deployment depends on.

Each of these was a real defect found in review, and each is the kind
that passes a code read and fails in front of a reviewer or an attacker.
"""

from __future__ import annotations

import pathlib
import threading

import pytest

from asset_researcher.hosting import samples
from asset_researcher.hosting.spend import SpendLimitExceeded, SpendTracker
from asset_researcher.ui import components as ui

ROOT = pathlib.Path(__file__).resolve().parents[1]


# --------------------------------------------- the two secrets differ

def test_the_sample_key_is_not_the_gate_passphrase():
    """The blob ships in a public repository. Sealing it with the phrase
    that guards the API key would publish an offline oracle for that
    phrase: unlimited guesses, no logs, no detection."""
    app = (ROOT / "app.py").read_text()
    assert 'os.environ.get("SAMPLES_KEY"' in app
    assert "samples.load(_passphrase())" not in app


def test_a_wrong_key_cannot_open_the_archive():
    blob = samples.pack({"a": "<p>x</p>"}, {"a": "A"}, "the-real-key")
    with pytest.raises(ValueError):
        samples.unpack(blob, "not-the-key")
    assert samples.unpack(blob, "the-real-key")[0].slug == "a"


def test_the_archive_does_not_leak_its_contents():
    blob = samples.pack(
        {"cost": "<html>COSTCO WHOLESALE</html>"}, {"cost": "Costco"}, "k" * 20
    )
    for probe in (b"COSTCO", b"<html", b"Costco"):
        assert probe not in blob


def test_a_tampered_archive_fails_closed():
    blob = bytearray(samples.pack({"a": "<p>x</p>"}, {"a": "A"}, "key-key-key"))
    blob[-1] ^= 0x01
    with pytest.raises(ValueError):
        samples.unpack(bytes(blob), "key-key-key")


# ------------------------------------------------- the spend cap binds

def test_concurrent_starts_cannot_all_pass_one_budget(tmp_path):
    """Checking and then spending let every request inside the window see
    the same pre-spend total. Forty concurrent starts against a $10 cap
    all passed, committing about $52."""
    tracker = SpendTracker(
        path=tmp_path / "spend.json", daily_cap_usd=10.0, session_cap_usd=100.0
    )
    start = threading.Barrier(40)
    allowed: list[int] = []
    lock = threading.Lock()

    def attempt() -> None:
        start.wait()
        try:
            tracker.reserve(0.0, 2.00)
        except SpendLimitExceeded:
            return
        with lock:
            allowed.append(1)

    threads = [threading.Thread(target=attempt) for _ in range(40)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(allowed) == 5, f"{len(allowed)} runs passed a 5-run budget"
    assert tracker.spent_today() == pytest.approx(10.0)


def test_a_reservation_is_charged_before_the_run(tmp_path):
    tracker = SpendTracker(
        path=tmp_path / "spend.json", daily_cap_usd=10.0, session_cap_usd=100.0
    )
    tracker.reserve(0.0, 2.00)
    assert tracker.spent_today() == pytest.approx(2.00)


def test_settling_replaces_the_estimate_with_the_real_cost(tmp_path):
    tracker = SpendTracker(
        path=tmp_path / "spend.json", daily_cap_usd=10.0, session_cap_usd=100.0
    )
    tracker.reserve(0.0, 2.00)
    tracker.settle(2.00, 1.20)
    assert tracker.spent_today() == pytest.approx(1.20)


def test_an_unsettled_run_leaves_its_estimate_charged(tmp_path):
    """A crash should cost the budget, not the operator."""
    tracker = SpendTracker(
        path=tmp_path / "spend.json", daily_cap_usd=10.0, session_cap_usd=100.0
    )
    tracker.reserve(0.0, 2.00)
    assert tracker.remaining_today() == pytest.approx(8.00)


# ------------------------------------------------ the gate cannot brick

def test_a_non_ascii_attempt_does_not_raise():
    """compare_digest raises TypeError on non-ASCII str. A mail client
    turns a hyphen into an en dash, so a reviewer pasting the passphrase
    out of an email hit it - and a passphrase containing one would have
    made the gate raise for everyone, unlockable by nobody."""
    import hmac

    assert not hmac.compare_digest("pässwörd".encode(), b"secret")


def test_tracebacks_are_suppressed_not_merely_redacted():
    """`false` is a legacy alias Streamlit maps to "stacktrace": it
    redacts the message and still ships the traceback."""
    config = (ROOT / ".streamlit" / "config.toml").read_text()
    assert 'showErrorDetails = "none"' in config


# ------------------------------------------------------- display names

@pytest.mark.parametrize(
    "conformed,shown",
    [
        ("COSTCO WHOLESALE CORP /NEW", "Costco Wholesale Corp."),
        ("NNN REIT INC", "NNN REIT Inc."),
        ("FORD MOTOR CO", "Ford Motor Co."),
        ("Lumen Technologies, Inc.", "Lumen Technologies, Inc."),
    ],
)
def test_edgar_conformed_names_are_made_fit_to_show(conformed, shown):
    """"/NEW" is a filing-system artifact, not part of a company's name.
    A reader who sees it concludes nothing was normalised on the way
    out."""
    assert ui.display_name(conformed) == shown
