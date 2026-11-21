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


# --------------------------------------------------------------- dark mode

def _scheme_block(scheme: str) -> str:
    """The token declarations for one colour scheme.

    `_token` above reads the first match in the whole stylesheet, which
    is the light value, so a dark palette checked with it would measure
    the light one and pass by accident.
    """
    css = theme.stylesheet()
    if scheme == "light":
        # Not the first `:root` in the file: the document world
        # declares its own tokens before the shell does, and that block
        # carries no --shell-* at all. Found by its contents.
        start = css.rindex(":root", 0, css.index("--shell-bg:"))
        return css[start : css.index("}", start)]
    start = css.index("@media (prefers-color-scheme: dark)")
    opened = css.index("{", css.index(":root", start))
    return css[opened : css.index("}", opened)]


def _tokens(scheme: str) -> dict[str, str]:
    return {
        name: value
        for name, value in re.findall(
            r"--shell-([a-z0-9-]+):\s*(#[0-9a-fA-F]{3,6})\s*;",
            _scheme_block(scheme),
        )
    }


def test_a_dark_scheme_redeclares_every_colour_it_inherits():
    """The failure mode of a half-written dark mode is not ugliness, it
    is a light token surviving on a dark ground - black text on black,
    or a hairline that disappears. Every colour the light scheme
    declares has to be answered."""
    light, dark = _tokens("light"), _tokens("dark")
    assert light, "no light tokens found"
    missing = sorted(set(light) - set(dark))
    assert not missing, f"dark mode does not redeclare: {missing}"


def test_every_shell_text_tone_passes_aa_on_every_ground_in_dark():
    dark = _tokens("dark")
    grounds = {k: dark[k] for k in ("bg", "panel", "sink")}
    tones = {k: dark[k] for k in ("ink", "soft", "mute")}
    for tone_name, tone in tones.items():
        for ground_name, ground in grounds.items():
            measured = contrast(tone, ground)
            assert measured >= AA_NORMAL, (
                f"dark {tone_name} {tone} on {ground_name} {ground} "
                f"measures {measured:.2f}:1"
            )


def test_the_dark_field_boundary_meets_the_control_floor():
    """SC 1.4.11: 3:1 for the edge that identifies a control. The light
    scheme was shipped with a boundary measuring 1.27:1 - a white
    border on a white fill - and a keyboard reader had no idea which
    field held focus."""
    dark = _tokens("dark")
    for ground in ("bg", "panel"):
        measured = contrast(dark["field-line"], dark[ground])
        assert measured >= 3.0, (
            f"the dark field boundary measures {measured:.2f}:1 on "
            f"{ground}"
        )


def test_the_focus_ring_is_offset_so_its_neighbour_is_the_ground():
    """This is the premise the next test rests on, so it is checked
    rather than assumed.

    A ring drawn ON a control sits against that control's fill, and the
    primary button's fill is --shell-ink, which inverts between
    schemes: no single ring colour can clear 3:1 against both a
    near-black and a near-white fill. Offsetting the ring puts the page
    between the two, so the colour it has to answer is the ground. The
    row links offset INWARD, onto a panel or a table head, which is why
    those two are grounds as well.
    """
    css = theme.stylesheet()
    rings = re.findall(
        r"outline:\s*2px solid var\(--shell-focus\);\s*"
        r"outline-offset:\s*(-?\d+)px",
        css,
    )
    assert rings, "no focus ring declares an offset"
    assert all(int(px) != 0 for px in rings), (
        "a focus ring sits flush against the control it surrounds"
    )


def test_the_dark_focus_ring_is_visible_on_every_ground_it_lands_on():
    dark = _tokens("dark")
    for ground in ("bg", "panel", "sink"):
        measured = contrast(dark["focus"], dark[ground])
        assert measured >= 3.0, (
            f"the dark focus ring measures {measured:.2f}:1 on {ground}"
        )


def test_the_primary_button_label_passes_on_its_own_fill():
    """The label was hard-coded white. In a dark scheme the fill
    becomes light, and white on light is unreadable - the one control
    on the screen a reader is meant to press."""
    for scheme in ("light", "dark"):
        tokens = _tokens(scheme)
        measured = contrast(tokens["on-ink"], tokens["ink"])
        assert measured >= AA_NORMAL, (
            f"{scheme}: the primary button's label measures "
            f"{measured:.2f}:1 on its fill"
        )


def test_the_widget_labels_take_their_colour_from_a_token():
    """Found by measuring the live page, not by reading the CSS.

    Streamlit paints its own widget labels from a static config that
    has one scheme and cannot follow the system, so on the dark ground
    "Ticker", "Strategy" and "How you invest" measured 1.76:1 - the
    labels of every field on the form screen, well under the 4.5:1
    floor. Nothing in this stylesheet had ever claimed that colour, so
    there was no rule to get wrong; it was simply never ours.

    Checked as a chain: this test says the label is painted from a
    shell token, and the contrast tests above say every shell text
    token clears 4.5:1 on every ground in both schemes.
    """
    css = theme.stylesheet()
    rule = re.search(
        r'\[data-testid="stWidgetLabel"\][^{}]*\{[^}]*\}', css
    )
    assert rule, "widget labels are left to Streamlit's static theme"
    assert "var(--shell-" in rule.group(0), (
        f"widget labels are coloured outside the token system: "
        f"{rule.group(0)}"
    )


def test_a_secondary_button_has_a_boundary_a_reader_can_see():
    """Measured on the live page, in dark: the secondary button's
    border came out at 1.47:1 against the ground and its fill at about
    1.3:1, so Back, Start a report and Download this note were
    identifiable as controls almost entirely by their text.

    SC 1.4.11 asks 3:1 for the visual information that identifies a
    control. This project already applied that to input boundaries,
    with --shell-field-line at 3.27:1, and left buttons on the panel
    hairline - which is the right weight for the edge of a card and
    the wrong one for the edge of a control. The hairline stays where
    it belongs; buttons get the boundary token.
    """
    for scheme in ("light", "dark"):
        tokens = _tokens(scheme)
        measured = contrast(tokens["btn-line"], tokens["bg"])
        assert measured >= 3.0, (
            f"{scheme}: a secondary button's boundary measures "
            f"{measured:.2f}:1 against the page"
        )


def test_the_card_hairline_stays_a_hairline():
    """The fix must not be applied by darkening the shared line token:
    a card edge at 3:1 is a box drawn round everything, which is the
    register this shell was rebuilt to get away from."""
    for scheme in ("light", "dark"):
        tokens = _tokens(scheme)
        assert contrast(tokens["line-2"], tokens["bg"]) < 2.0, (
            f"{scheme}: the panel hairline has become a border"
        )
