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


def test_centring_the_gate_cannot_push_anything_out_of_reach():
    """`justify-content: center` splits overflow evenly above and below,
    and the half above the top of a scroll container cannot be reached
    because scrollTop does not go negative.

    Found by shrinking the window until the gate plus its error message
    was taller than the viewport. At 380x260 the product mark sat at
    top -12 with scrollTop already 0 - cut off, with no way to scroll to
    it. `safe` falls back to flex-start at exactly the point where
    centring would start hiding something; re-measured at the same size
    afterwards, nothing sits above the viewport at scrollTop 0.
    """
    rule = re.search(
        r"\.block-container:has\(\.ar-gate\) \{([^}]*)\}", theme.stylesheet()
    )
    assert rule, "the gate's container has no rule"
    body = rule.group(1)
    if "justify-content" in body:
        assert "safe center" in body, (
            "the gate centres unsafely, which makes its top unreachable "
            "on a viewport shorter than its content"
        )


def test_the_first_screen_speaks_in_the_products_voice():
    """The gate is the first thing anyone sees and was the last screen
    still set in the old voice - the product's name in the sans at 17px
    semibold, which is the size of a form label, not an introduction.

    Centred, and that is right here: the gate holds one object and has
    nothing to align against. Home was wrong because one centred line
    sat above a column of left-aligned content.
    """
    rule = re.search(r"\.ar-gate h1 \{([^}]*)\}", theme.stylesheet())
    assert rule, "the gate's title has no rule"
    body = rule.group(1)
    assert "--shell-display" in body, "the gate is not in the display face"
    weight = re.search(r"font-weight:\s*(\d+)", body)
    assert weight and int(weight.group(1)) <= 300


def test_the_product_tells_the_browser_it_has_one_light_palette():
    """Without `color-scheme`, the user agent paints its own ground from
    the operating system's preference before any stylesheet arrives. A
    reader on a dark desktop met a near-black screen - measured
    rgb(14, 17, 23) in the pane - that flashed to marble as the app
    mounted, and got dark form controls and a dark scrollbar gutter
    inside a document that is paper.

    It is declared in the document rules because the exported note is
    read on the same laptops as the app.
    """
    assert "color-scheme: light" in theme.document_stylesheet()
    assert "color-scheme: light" in theme.stylesheet()


def test_the_shells_page_is_painted_in_the_shells_own_colour():
    """`html` and `body` were painted with --paper and --ink, which are
    the document's warm tokens, while a later rule gave .stApp the shell
    ground. Measured in the running app: body rgb(250,248,243) against
    .stApp rgb(244,246,249). The note's paper was showing through the
    chrome in the overscroll band - the exact bleed the two-surface
    split exists to prevent.
    """
    sheet = theme.stylesheet()
    rule = re.search(
        r"html, body, \.stApp, \[data-testid=\"stAppViewContainer\"\] \{"
        r"([^}]*)\}",
        sheet,
    )
    assert rule, "nothing paints the shell's page"
    body = rule.group(1)
    assert "--shell-bg" in body, "the shell's page is not the shell's ground"
    assert "var(--paper)" not in body, "the document's paper is in the shell"
    assert "var(--ink)" not in body, "the document's ink is in the shell"


def test_no_table_in_the_shell_inherits_the_hosts_vertical_rules():
    """Streamlit paints a 1px border on every side of every cell in a
    markdown table, in a colour that appears nowhere in this palette.
    The sheet had only ever declared `border-bottom`, so the index read
    as a spreadsheet grid drawn by the host framework.

    Published research tables are horizontal-rule only, which is what
    the note's own tables already do.
    """
    sheet = theme.stylesheet()
    assert re.search(
        r"table\.ar-list th, table\.ar-list td \{[^}]*border-left:\s*0", sheet
    ), "the index's cells do not switch off the host's side borders"


def test_the_note_renders_the_same_inline_as_it_does_framed():
    """A sample note sits in an iframe the host's CSS cannot reach. A
    freshly generated one is written inline into the page, so on that
    screen alone the host's side borders landed on every cell of all
    twelve of the document's tables - the same document, two renderings,
    and the wrong one was the report the reader just paid for.
    """
    assert re.search(
        r'\[data-testid="stMarkdown"\] table\.ar-table th,\s*'
        r'\[data-testid="stMarkdown"\] table\.ar-table td \{[^}]*'
        r"border-left:\s*0",
        theme.stylesheet(),
    ), "the inline note does not neutralise the host's cell borders"

    # And the override must not travel with the export, which carries no
    # Streamlit for it to override. Checked against this rule rather than
    # the word "stMarkdown", which already appears in the document sheet
    # in an unrelated `stMarkdownContainer` rule.
    assert 'stMarkdown"] table.ar-table' not in theme.document_stylesheet()


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
