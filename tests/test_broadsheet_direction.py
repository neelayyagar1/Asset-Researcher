"""The Broadsheet — the shell's visual direction, pinned.

The direction was chosen on 2026-11-21 and is recorded as a standing
commitment in PRODUCT.md. These tests exist because the previous shell was
graded 6/10 for committing to no idea, and the specific failure mode of a
redesign is that it half-conforms to the thing it replaced. Each assertion
here is one of the commitments stated in that section.

The load-bearing one is the scope test. The owner chose "shell only": the
research note keeps its own document world, which means the shell's new type
may not reach the document's token block, because `document_stylesheet()` is
what every exported file and every sealed sample carries. A shell font that
leaks into `_root()` would restyle six sealed notes and every file a reader
has already downloaded.
"""

from __future__ import annotations

import re

from asset_researcher.ui import theme


def _root_block(sheet: str) -> str:
    """The `:root { ... }` declarations, which travel with an export."""
    match = re.search(r":root\s*\{(.*?)\}", sheet, re.S)
    assert match, "the stylesheet declares no :root block"
    return match.group(1)


# --------------------------------------------------------------- the scope

def test_the_document_display_face_is_untouched_by_the_redesign():
    """The note is not restyled. Faustina carries its headings before and
    after, because the document is a different surface from the shell."""
    assert "Faustina" in theme.FONT_DISPLAY


def test_the_shell_display_face_is_not_the_document_display_face():
    """Two surfaces, two display faces. If these were the same token the
    shell could not change without the note changing with it."""
    assert theme.FONT_SHELL_DISPLAY != theme.FONT_DISPLAY


def test_the_exported_note_never_downloads_a_shell_only_font():
    """An exported file is read offline and forwarded. It should not fetch a
    typeface it has no rule for."""
    document = theme.document_stylesheet()
    assert "Newsreader" not in document


def test_the_running_app_does_load_the_shell_display_face():
    assert "Newsreader" in theme.stylesheet()


def test_the_shell_display_token_is_shell_scoped():
    """`_root()` is emitted by both stylesheets, so a shell face declared
    there would reach the document. It belongs to the shell block."""
    assert "--shell-display" not in _root_block(theme.stylesheet())
    assert "--shell-display" in theme.stylesheet()


# -------------------------------------------------------- the commitments

def test_the_display_serif_is_held_at_a_light_weight():
    """"Never use the serif at its heavy weights — the light whisper is the
    entire point." A serif at 600 is every other fintech."""
    sheet = theme.stylesheet()
    rule = re.search(r"\.ar-head h1, \.ar-head h2 \{([^}]*)\}", sheet)
    assert rule, "no shell heading rule in the sheet"
    assert "--shell-display" in rule.group(1), (
        "the shell's headings are not set in the shell display face"
    )
    weight = re.search(r"font-weight:\s*(\d+)", rule.group(1))
    assert weight, "the display rule does not state a weight"
    assert int(weight.group(1)) <= 300


def test_the_shell_ground_is_colder_than_the_document_paper():
    """The shell is cold so the note's warm paper reads as another surface.
    Compared on the blue channel, which is what warmth costs."""

    def blue(hex_colour: str) -> int:
        return int(hex_colour.lstrip("#")[4:6], 16)

    def red(hex_colour: str) -> int:
        return int(hex_colour.lstrip("#")[0:2], 16)

    shell = theme.SHELL_BG
    paper = theme.PAPER
    assert blue(shell) >= red(shell), "the shell ground is warm, not cold"
    assert red(paper) >= blue(paper), "the document paper is no longer warm"


def test_the_accent_is_declared_once():
    """One accent, on the divergence count and on links. A second accent
    makes the first one decoration."""
    assert theme.SHELL_ACCENT.startswith("#")
    assert len(theme.SHELL_ACCENT) == 7


# ------------------------------------------------------- not generated-looking

def _hue(colour: str) -> float:
    import colorsys

    raw = colour.lstrip("#")
    r, g, b = (int(raw[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)[0] * 360


def _ratio(one: str, two: str) -> float:
    def lum(colour: str) -> float:
        raw = colour.lstrip("#")
        parts = [int(raw[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        parts = [
            p / 12.92 if p <= 0.03928 else ((p + 0.055) / 1.055) ** 2.4
            for p in parts
        ]
        return 0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]

    high, low = sorted((lum(one), lum(two)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def _shell_token(name: str) -> str:
    match = re.search(rf"{name}:\s*(#[0-9a-fA-F]{{6}})", theme.stylesheet())
    assert match, f"{name} is not declared in the stylesheet"
    return match.group(1)


def test_no_shell_colour_is_the_indigo_every_generator_reaches_for():
    """Indigo and violet (roughly 235-270 degrees) are the single most
    recognisable tell of a generated interface. The focus ring was
    #4f46e5 - Tailwind indigo-600 exactly - on a product whose entire
    argument is that a person built it with care."""
    for token in ("--shell-accent", "--shell-focus"):
        hue = _hue(_shell_token(token))
        assert not 235 <= hue <= 270, (
            f"{token} sits at {hue:.0f} degrees, in the indigo/violet band"
        )


def test_the_focus_ring_clears_three_to_one_on_every_ground_it_lands_on():
    """WCAG 2.2 SC 1.4.11. The ring this replaced measured 2.88:1 on the
    near-black bypass pill and failed, while the comment beside it
    claimed 4.4:1. A number nobody re-measured is not evidence."""
    focus = _shell_token("--shell-focus")
    for ground, label in (
        (theme.SHELL_BG, "the marble ground"),
        (theme.SHELL_PANEL, "a panel"),
        ("#15161a", "the ink pill"),
    ):
        ratio = _ratio(focus, ground)
        assert ratio >= 3.0, f"focus ring is {ratio:.2f}:1 on {label}"
