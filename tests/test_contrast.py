"""Text contrast, measured rather than eyeballed.

The chosen register is deliberately restrained, and restraint is one
shade away from illegible. The muted token shipped at #8b8e98, which
measures 3.19:1 on this ground - below WCAG 2.2 AA for normal text -
and that token carries the home screen's one-line proposition, every
helper caption under a field, the table headers and the step numbers.

The reader is a portfolio manager reading on a laptop in daylight, so
this is not a theoretical failure.
"""

from __future__ import annotations

import re

from asset_researcher.ui import theme

AA_NORMAL = 4.5


def _luminance(value: str) -> float:
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    channels = []
    for index in (0, 2, 4):
        raw = int(value[index : index + 2], 16) / 255
        channels.append(
            raw / 12.92 if raw <= 0.03928 else ((raw + 0.055) / 1.055) ** 2.4
        )
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast(foreground: str, background: str) -> float:
    high, low = sorted(
        (_luminance(foreground), _luminance(background)), reverse=True
    )
    return (high + 0.05) / (low + 0.05)


def _token(name: str) -> str:
    """Read a --shell-* custom property out of the shipped stylesheet."""
    css = theme.stylesheet()
    match = re.search(rf"--{name}:\s*(#[0-9a-fA-F]{{3,6}})\s*;", css)
    assert match, f"--{name} is not declared in the stylesheet"
    return match.group(1)


def test_the_contrast_helper_agrees_with_known_values():
    """Checks the checker: black on white is 21:1, white on white is 1:1."""
    assert round(contrast("#000000", "#ffffff"), 1) == 21.0
    assert round(contrast("#ffffff", "#ffffff"), 1) == 1.0


def test_every_shell_text_tone_passes_aa_on_every_ground():
    grounds = {
        "page": _token("shell-bg"),
        "panel": _token("shell-panel"),
        "table head": _token("shell-sink"),
    }
    tones = {
        "ink": _token("shell-ink"),
        "secondary": _token("shell-soft"),
        "muted": _token("shell-mute"),
    }
    for tone_name, tone in tones.items():
        for ground_name, ground in grounds.items():
            measured = contrast(tone, ground)
            assert measured >= AA_NORMAL, (
                f"{tone_name} {tone} on {ground_name} {ground} measures "
                f"{measured:.2f}:1, below the {AA_NORMAL}:1 WCAG 2.2 AA "
                f"floor for normal text"
            )


def test_the_divergence_colours_pass_on_their_own_fills():
    """The one place colour is used, so it has to be readable."""
    for fore, back, label in (
        ("#b4231a", "#fdf2f1", "divergence red"),
        ("#16794f", "#f0f8f4", "corroboration green"),
    ):
        measured = contrast(fore, back)
        assert measured >= AA_NORMAL, (
            f"{label} measures {measured:.2f}:1 on its own fill"
        )


def _resolve(value: str) -> str:
    """Turn `var(--token)` into the hex the stylesheet declares for it."""
    value = value.strip()
    if not value.startswith("var("):
        return value
    name = value[4:].split(")")[0].strip().lstrip("-")
    return _token(name)


def test_the_bypass_link_focus_ring_is_visible_against_the_page():
    """It was not. The ring was `var(--paper)` - #faf8f3, the ground of
    the editorial world this shell replaced - which measures about
    1.01:1 against the new #fcfcfd page. The ring draws OUTSIDE the
    link's dark pill, on the page, so the page is what it has to be seen
    against, and this is the first control a keyboard user reaches in
    the entire product.

    SC 1.4.11 wants 3:1 for a focus indicator.
    """
    css = theme.stylesheet()
    rule = re.search(
        r"\.ar-skip:focus-visible\s*\{[^}]*outline:\s*[\d.]+px\s+solid\s+"
        r"([^;!}]+)",
        css,
    )
    assert rule, "the bypass link has no focus-visible outline rule"

    ring = _resolve(rule.group(1))
    page = _token("shell-bg")
    measured = contrast(ring, page)
    assert measured >= 3.0, (
        f"the bypass link's focus ring is {ring} on {page}, which "
        f"measures {measured:.2f}:1 - below the 3:1 floor for a focus "
        f"indicator, and it is the first thing a keyboard user lands on"
    )
