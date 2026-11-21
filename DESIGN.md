---
name: Asset Researcher
description: A quiet application shell that frames one object - the research note it produces.
colors:
  shell-bg: "#fcfcfd"
  shell-panel: "#ffffff"
  shell-ink: "#15161a"
  shell-soft: "#50535c"
  shell-mute: "#6b6f78"
  shell-line: "#eceef1"
  shell-line-2: "#e2e4e9"
  shell-sink: "#fbfbfc"
  shell-field-line: "#8b8e98"
  shell-ink-hover: "#26272d"
  shell-secondary-hover: "#f7f8f9"
  shell-secondary-hover-line: "#d6d9df"
  # Declared in the stylesheet as --shell-focus and used by every
  # focus ring in the shell, including the bypass link, whose ring was
  # the replaced world's paper colour at 1.04:1 until it was measured.
  shell-focus: "#4f46e5"
  count-fill: "#f3f4f6"
  count-hot-ink: "#b4231a"
  count-hot-fill: "#fdf2f1"
  count-cool-ink: "#16794f"
  count-cool-fill: "#f0f8f4"
  code-fill: "#f4f5f7"
  ink: "#17150f"
  ink-soft: "#403c33"
  ink-muted: "#6f6a5c"
  paper: "#faf8f3"
  surface: "#ffffff"
  rule: "#ded9cc"
  rule-soft: "#ece8dd"
  accent: "#1d5a86"
  accent-soft: "#e9eef3"
  accent-2: "#a8481f"
  neutral: "#8c8676"
  negative: "#8a2d1c"
  positive: "#2b6349"
  caution: "#8a6a1a"
typography:
  shell-title:
    fontFamily: "'Public Sans', -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "17px"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.02em"
  shell-head:
    fontFamily: "'Public Sans', -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "15px"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.015em"
  shell-brand:
    fontFamily: "'Public Sans', -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "13.5px"
    fontWeight: 600
    letterSpacing: "-0.012em"
  shell-body:
    fontFamily: "'Public Sans', -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.5
  shell-note:
    fontFamily: "'Public Sans', -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "12.5px"
    fontWeight: 400
    lineHeight: 1.5
  shell-field-label:
    fontFamily: "'Public Sans', -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "12px"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "-0.004em"
  shell-micro:
    fontFamily: "'Public Sans', -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "11px"
    fontWeight: 500
    letterSpacing: "0.03em"
  shell-figure:
    fontFamily: "'Spline Sans Mono', ui-monospace, Menlo, monospace"
    fontSize: "12.5px"
    fontWeight: 400
    fontFeature: "\"tnum\" 1, \"lnum\" 1"
  shell-figure-sm:
    fontFamily: "'Spline Sans Mono', ui-monospace, Menlo, monospace"
    fontSize: "12px"
    fontWeight: 500
    fontFeature: "\"tnum\" 1"
  shell-figure-micro:
    fontFamily: "'Spline Sans Mono', ui-monospace, Menlo, monospace"
    fontSize: "11px"
    fontWeight: 400
    letterSpacing: "0.02em"
  d0:
    fontFamily: "'Faustina', Georgia, serif"
    fontSize: "clamp(2.6rem, 5.4vw, 4.4rem)"
    fontWeight: 500
    lineHeight: 0.98
    letterSpacing: "-0.038em"
  d1:
    fontFamily: "'Faustina', Georgia, serif"
    fontSize: "2.6rem"
    fontWeight: 500
    lineHeight: 1.04
    letterSpacing: "-0.034em"
  d2:
    fontFamily: "'Faustina', Georgia, serif"
    fontSize: "1.75rem"
    fontWeight: 500
    lineHeight: 1.08
    letterSpacing: "-0.028em"
  h1:
    fontFamily: "'Faustina', Georgia, serif"
    fontSize: "1.3rem"
    fontWeight: 500
    lineHeight: 1.22
    letterSpacing: "-0.018em"
  h2:
    fontFamily: "'Faustina', Georgia, serif"
    fontSize: "1rem"
    fontWeight: 500
    lineHeight: 1.3
  body:
    fontFamily: "'Public Sans', -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
  read:
    fontFamily: "'Public Sans', -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.68
  data:
    fontFamily: "'Spline Sans Mono', ui-monospace, Menlo, monospace"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.4
    fontFeature: "\"tnum\" 1, \"lnum\" 1"
  micro:
    fontFamily: "'Public Sans', -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "0.6875rem"
    fontWeight: 400
    lineHeight: 1.3
  label:
    fontFamily: "'Public Sans', -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "0.625rem"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "0.14em"
rounded:
  none: "0"
  xs: "4px"
  sm: "5px"
  md: "7px"
  lg: "10px"
spacing:
  s1: "4px"
  s2: "8px"
  s3: "12px"
  s4: "16px"
  s5: "24px"
  s6: "32px"
  s7: "48px"
  s8: "72px"
  rail: "9rem"
  nav-h: "41px"
  shell-gut: "28px"
  shell-pad: "14px"
  shell-gap: "16px"
  shell-row: "11px"
  shell-topbar-h: "52px"
components:
  button-primary:
    backgroundColor: "{colors.shell-ink}"
    textColor: "#ffffff"
    typography: "{typography.shell-body}"
    rounded: "{rounded.md}"
    padding: "0 16px"
    height: "36px"
    width: "100%"
  button-primary-hover:
    backgroundColor: "{colors.shell-ink-hover}"
    textColor: "#ffffff"
  button-secondary:
    backgroundColor: "{colors.shell-panel}"
    textColor: "{colors.shell-ink}"
    typography: "{typography.shell-body}"
    rounded: "{rounded.md}"
    padding: "0 16px"
    height: "36px"
    width: "100%"
  button-secondary-hover:
    backgroundColor: "{colors.shell-secondary-hover}"
    textColor: "{colors.shell-ink}"
  input-text:
    backgroundColor: "{colors.shell-panel}"
    textColor: "{colors.shell-ink}"
    typography: "{typography.shell-figure}"
    rounded: "{rounded.md}"
  input-select:
    backgroundColor: "{colors.shell-panel}"
    textColor: "{colors.shell-ink}"
    typography: "{typography.shell-body}"
    rounded: "{rounded.md}"
  field-label:
    backgroundColor: "transparent"
    textColor: "{colors.shell-ink}"
    typography: "{typography.shell-field-label}"
  card:
    backgroundColor: "{colors.shell-panel}"
    textColor: "{colors.shell-ink}"
    rounded: "{rounded.lg}"
    padding: "14px"
  card-flush:
    backgroundColor: "{colors.shell-panel}"
    textColor: "{colors.shell-ink}"
    rounded: "{rounded.lg}"
    padding: "0"
  card-label:
    backgroundColor: "transparent"
    textColor: "{colors.shell-mute}"
    typography: "{typography.shell-micro}"
  topbar:
    backgroundColor: "{colors.shell-bg}"
    textColor: "{colors.shell-ink}"
    typography: "{typography.shell-brand}"
    padding: "0 28px"
    height: "52px"
  topbar-where:
    backgroundColor: "transparent"
    textColor: "{colors.shell-soft}"
    typography: "{typography.shell-body}"
    padding: "0 0 0 14px"
  topbar-meta:
    backgroundColor: "transparent"
    textColor: "{colors.shell-mute}"
    typography: "{typography.shell-figure-micro}"
  list-header:
    backgroundColor: "{colors.shell-sink}"
    textColor: "{colors.shell-mute}"
    typography: "{typography.shell-micro}"
    padding: "9px 16px"
  list-cell:
    backgroundColor: "{colors.shell-panel}"
    textColor: "{colors.shell-ink}"
    typography: "{typography.shell-body}"
    padding: "11px 16px"
  list-cell-num:
    backgroundColor: "{colors.shell-panel}"
    textColor: "{colors.shell-ink}"
    typography: "{typography.shell-figure}"
    padding: "11px 16px"
  count:
    backgroundColor: "{colors.count-fill}"
    textColor: "{colors.shell-soft}"
    typography: "{typography.shell-figure-micro}"
    rounded: "{rounded.sm}"
    padding: "2px 7px"
  count-hot:
    backgroundColor: "{colors.count-hot-fill}"
    textColor: "{colors.count-hot-ink}"
  count-cool:
    backgroundColor: "{colors.count-cool-fill}"
    textColor: "{colors.count-cool-ink}"
  kv-row:
    backgroundColor: "transparent"
    textColor: "{colors.shell-soft}"
    typography: "{typography.shell-note}"
    padding: "7px 0"
  kv-value:
    backgroundColor: "transparent"
    textColor: "{colors.shell-ink}"
    typography: "{typography.shell-figure-sm}"
  step:
    backgroundColor: "transparent"
    textColor: "{colors.shell-ink}"
    typography: "{typography.shell-body}"
    padding: "11px 0"
  step-number:
    backgroundColor: "transparent"
    textColor: "{colors.shell-mute}"
    typography: "{typography.shell-figure-micro}"
  step-code:
    backgroundColor: "{colors.code-fill}"
    textColor: "{colors.shell-ink}"
    typography: "{typography.shell-figure-sm}"
    rounded: "{rounded.xs}"
    padding: "1px 5px"
  empty-state:
    backgroundColor: "{colors.shell-panel}"
    textColor: "{colors.shell-mute}"
    typography: "{typography.shell-note}"
    padding: "28px 16px"
  brand-mark:
    backgroundColor: "{colors.shell-ink}"
    rounded: "{rounded.xs}"
    size: "16px"
  ticker-badge:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.surface}"
    typography: "{typography.micro}"
    rounded: "{rounded.none}"
    padding: "0.2em 0.5em"
  chip-provenance:
    backgroundColor: "transparent"
    textColor: "{colors.ink-muted}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "0.25em 0.5em"
  chip-provenance-bad:
    backgroundColor: "{colors.negative}"
    textColor: "{colors.paper}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "0.25em 0.5em"
  pill-divergence:
    backgroundColor: "transparent"
    textColor: "{colors.negative}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "0.25em 0.5em"
  pill-agree:
    backgroundColor: "transparent"
    textColor: "{colors.positive}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "0.25em 0.5em"
  table-header:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.label}"
    padding: "8px 12px 4px"
  table-row-subject:
    backgroundColor: "{colors.accent-soft}"
    textColor: "{colors.ink}"
    typography: "{typography.data}"
    padding: "6px 12px"
  stat-value:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.h1}"
  stat-value-lead:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.d2}"
---

# Design System: Asset Researcher

## Overview

**Creative North Star: "The Quiet Instrument Around the Document"**

This product ships two surfaces, and the whole system is the relationship
between them. The **research note** is the object the product makes: warm paper
(`paper`), a Faustina masthead, a 9rem left rail, square corners, hairlines, and
colour used only as an index. The **application shell** is the frame that makes
and lists those notes: near-white ground (`shell-bg`), Public Sans throughout,
hairline-bordered panels on a 7px/10px radius pair, monospace figures, and
colour withheld from everything except one count. Both live in one stylesheet,
`asset_researcher/ui/theme.py`: `_DOCUMENT_CSS` is the note and travels with the
exported HTML file, the block marked `application shell` is the chrome and never
leaves the app. `document_stylesheet()` emits the first; `stylesheet()` emits
both.

The shell executes the category canon at the Linear/Stripe restraint bar. This
is a **standing brand commitment**, not a preference: PRODUCT.md records it as
chosen on 2026-11-20 from four rendered comps (against an
accountant's-worksheet, an engineering-drawing and a giant-type direction), with
the instruction to execute it straight, at full fidelity, with no smuggled
quirk. The same commitment says the note keeps its own document world and is not
restyled - which is why this file documents two worlds instead of reconciling
them into one.

The shell's restraint is load-bearing rather than decorative. A reader comes here
to get a note, so the chrome's job is to be legible, say where they are, and get
out of the way: a 52px topbar, one heading, panels with real content in them, and
the primary action always the highest-contrast thing on the screen - the darkest
in the light scheme and the lightest in the dark one. Contrast is measured, not
eyeballed: `tests/test_contrast.py` reads the shipped stylesheet and fails the
build if any text tone drops below 4.5:1 on any ground it renders on, in EITHER
scheme, and if a control boundary or the focus ring drops below 3:1.

**Dark is the same design, not a second one.** It follows
`prefers-color-scheme` and offers no switch: a toggle is a control, a preference
to persist and a state to get wrong. Nothing moves and nothing changes shape -
it is entirely a redefinition of the token block, which is the reason the
palette is declared in one place. The suite fails if the light scheme declares a
colour the dark one does not answer, because the failure mode of a half-written
dark mode is not ugliness but a light token surviving on a dark ground.

The dark scheme answers the DOCUMENT tokens as well as the shell ones, and does
so in the shell stylesheet only. The report screen writes the note's markup
straight into the page, so those tokens have to follow the shell there; the
exported file and the iframe'd note carry `document_stylesheet()`, which does
not include that block, so a downloaded note stays on paper in both schemes.

**Key Characteristics:**
- Two documented surfaces: the note (warm, serif, square, ruled) and the shell
  (near-white, sans, rounded, panelled). They share one stylesheet and one
  type/figure pairing, nothing else.
- ONE column in the shell, declared once on `.block-container`. No descendant
  sets its own width, and no width is expressed in `ch`.
- Colour is withheld across the entire shell except the divergence count and the
  focus ring.
- Every shell text tone measures at or above 4.5:1 on every ground; the control
  boundary measures 3.27:1 to meet WCAG 2.2 SC 1.4.11.
- Two families plus a monospace: Faustina (note display), Public Sans (all UI
  and prose), Spline Sans Mono (every figure).
- Shell depth is one 1px-blur ambient shadow; the note has no shadow at all.

## Colors

Two palettes with one shared discipline: colour means something or it is absent.
The shell is a grey ramp on near-white with exactly two coloured states; the note
is warm paper and ink with two indexing hues and three semantic signals.

### Primary
The shell has no accent. Its primary is its ink.

- **Shell Ink** (`{colors.shell-ink}`): the shell's only strong value. Headings,
  table cells, key-value answers, the brand mark, and the fill of the primary
  button (white text on it). 15.6:1 on the ground.
- **Note Slate** (`{colors.accent}`): in the note only - the subject and this
  analysis. Links, `::selection`, `caret-color`, the subject bar in a peer chart,
  the left rule on the summary and on a finding's assessment, the nav hover
  underline, the progress fill, and the section label of the section the reader
  jumped to.
- **Note Slate Wash** (`{colors.accent-soft}`): the subject's row in a
  comparables table and the hover field behind a citation marker.

### Secondary
- **Note Sienna** (`{colors.accent-2}`): the market - the prevailing view and
  the traded price. The "street" column label and the dashed traded-price
  reference line. Never used for the subject, and never used in the shell.

### Tertiary
- **Note Stone** (`{colors.neutral}`): peers and other recessive marks in
  charts - the thing the subject is measured against. Measured at 3.42:1 against
  the paper, because a peer bar is a graphical object carrying meaning and WCAG
  asks 3:1 of one.

### Neutral
Shell ramp, in order of weight:

- **Shell Ground** (`{colors.shell-bg}`): the page. Near-white rather than
  white, so a white panel reads as a panel.
- **Shell Panel** (`{colors.shell-panel}`): cards, the reports table, every
  control's fill.
- **Shell Secondary Text** (`{colors.shell-soft}`): the company column, the
  key-value label, the step's continuation phrase, the current-screen name in the
  topbar, and the neutral count. 7.5:1 on the ground.
- **Shell Muted Text** (`{colors.shell-mute}`): the lowest tone that still
  carries text - the head's one-line note, every helper caption, the card label,
  the table header, the step number, the empty state, and the topbar's
  provenance line. 4.91:1 on the ground and 5.04:1 on a panel.
- **Shell Hairline** (`{colors.shell-line}`): lines *inside* a panel - row
  dividers in the reports table, between key-value rows and between steps, and
  under the topbar.
- **Shell Panel Edge** (`{colors.shell-line-2}`): the card's own border and the
  secondary button's border. Decorative by role: it separates a panel from the
  ground and is never the only thing identifying a control.
- **Shell Field Boundary** (`{colors.shell-field-line}`): the resting border of
  every text input, textarea and select. 3.27:1 on white, because a control's
  boundary is information and WCAG 2.2 SC 1.4.11 asks 3:1 of it. The panel
  hairline measures 1.27:1, which is right for a card and wrong for a field.
- **Shell Sink** (`{colors.shell-sink}`): the reports table's header band, one
  step down from the panel it sits in.
- **Shell Ink Hover** (`{colors.shell-ink-hover}`), **Shell Secondary Hover**
  (`{colors.shell-secondary-hover}`), **Shell Secondary Hover Line**
  (`{colors.shell-secondary-hover-line}`): button hover states, one step from
  rest in each direction.
- **Count Fill** (`{colors.count-fill}`) and **Code Fill**
  (`{colors.code-fill}`): the two grey chips - a count with no judgement, and an
  inline literal inside a step.

Note ramp:

- **Warm Ink** (`{colors.ink}`): body-weight emphasis, headings, numeric cells,
  the 2px rule that opens the document, the rule above a total.
- **Soft Ink** (`{colors.ink-soft}`): running prose and ordinary table cells.
- **Muted Ink** (`{colors.ink-muted}`): labels, captions, notes, axis text, "NM"
  values, and derived (computed-not-filed) statement rows.
- **Paper** (`{colors.paper}`): the note's page, its sticky nav, table spacer
  rows.
- **Surface** (`{colors.surface}`): the note's tables and panels, and the sticky
  table header that must occlude rows scrolling under it.
- **Rule** (`{colors.rule}`) / **Rule Soft** (`{colors.rule-soft}`): structural
  hairlines, and hairlines one step quieter inside a table.

### Semantic
- **Divergence Count** (`{colors.count-hot-ink}` on
  `{colors.count-hot-fill}`): the shell's one piece of colour. A divergence count
  is the only figure in the chrome that carries a judgement, so it is the only
  one allowed to catch the eye.
- **Agreement Count** (`{colors.count-cool-ink}` on
  `{colors.count-cool-fill}`): the same chip when the count is benign.
- **Focus Ring** (`{colors.focus-ring}`): indigo, on every shell button, text
  input root, textarea root and reveal toggle. The one hue in the shell that is
  not a state of the content.
- Note semantics, unchanged: **Corroboration** (`{colors.positive}`),
  **Divergence** (`{colors.negative}`), **Caution** (`{colors.caution}`).

### Named Rules
**The Withheld-Colour Rule.** The shell is greyscale. The only coloured things
on it are the divergence/agreement count and the focus ring. A new shell surface
that wants emphasis gets weight, size or a hairline - not a hue.

**The Measured-Contrast Rule.** No shell text tone ships without a measurement.
`shell-ink`, `shell-soft` and `shell-mute` each measure at or above 4.5:1 on
`shell-bg`, `shell-panel` and `shell-sink`, and `tests/test_contrast.py` reads
those values out of the shipped stylesheet and asserts it. The comp's own muted
tone was `#8b8e98` (3.19:1); it was darkened to `shell-mute` until it passed
with margin while staying plainly subordinate to `shell-soft`.

**The Boundary-Is-Information Rule.** A card edge may be a 1.27:1 hairline. A
control edge may not: every field boundary uses `shell-field-line` at 3.27:1.

**The Two-Hue Rule (note only).** Slate is the subject and this analysis; sienna
is the market and the prevailing view. A mark that means neither is grey, and no
third hue is introduced for emphasis.

**The Colour-Follows-Entity Rule (note only).** In any comparison, colour
attaches to the entity, not to its rank or its value's sign, so filtering or
reordering a peer set never repaints the survivors.

## Typography

**Display Font:** Faustina (with Georgia, serif) - the note only.
**Body/UI Font:** Public Sans (with -apple-system, BlinkMacSystemFont,
sans-serif) - the whole shell, and the note's prose.
**Figure Font:** Spline Sans Mono (with ui-monospace, Menlo, monospace) - every
figure, both surfaces.

**Character:** Public Sans is the typeface of the United States federal design
system, which is where every figure in this product originates. Faustina is a
text serif with enough character to set a masthead without tipping into
magazine, and it appears on exactly one surface. Spline Sans Mono has true
tabular widths. All three load from one Google Fonts import at weights 400-600,
and the shell names its family on every one of its own elements so Streamlit's
default (Source Sans) cannot become a fourth.

Tabular lining figures are a document default, set on `body` with both
`font-variant-numeric` and `font-feature-settings`, and re-asserted on the
shell's numeric cells and key-value answers, because every figure here is
compared down a column.

### Hierarchy

**Shell.** Small, flat, and set in literal pixels, because this surface is
chrome and its ranks are a half-step apart by design.

- **shell-title** (600, 17px, -0.02em): the gate's name. The largest type in the
  shell, and it appears on one screen.
- **shell-head** (600, 15px, -0.015em): every screen and section heading
  (`.ar-head h1`, `.ar-head h2` - styled identically so the document outline can
  be correct without anything moving).
- **shell-brand** (600, 13.5px, -0.012em): the product name in the topbar.
- **shell-body** (400, 13px/1.5): table cells, step text, button labels, select
  values.
- **shell-note** (400, 12.5px/1.5): the one line under a heading, key-value
  labels, the empty state.
- **shell-field-label** (500, 12px, sentence case): widget labels. Small,
  sentence case, quiet - the tracked uppercase label belongs to the note's world,
  and a label is read far more often than it is admired.
- **shell-micro** (500, 11px, 0.03-0.04em): the card label (uppercase) and the
  reports table header (sentence case).
- **shell-figure** (12.5px mono), **shell-figure-sm** (12px mono),
  **shell-figure-micro** (11px mono): the value column, the key-value answer and
  the ticker input; step numbers, inline code and the topbar's source line.

**Note.** Ten steps, declared once as `--t-*` custom properties with their
line-height and letter-spacing: `d0` (opening headline, the one fluid step),
`d1` (company name, `h1`), `d2` (lead stat; the masthead title below 900px),
`h1` (`h2`, ordinary stat values), `h2` (`h3`, the summary's opening paragraph,
an "NM" value), `body` (`p`, `li`, status lines), `read` (the narrative column
and the summary, the only generously leaded step at 1.68), `data` (table
bodies), `micro` (captions, footnotes, the ticker badge, row heads), `label`
(the single tracked uppercase label style).

### Named Rules
**The One Scale Rule (note).** Component rules in `_DOCUMENT_CSS` reference
`--t-*` only. There is exactly one literal font-size in the note stylesheet -
the citation marker at `0.72em`, relative to the prose it interrupts. An earlier
stylesheet held 31 distinct sizes, eighteen inside a five-pixel band; that is
what per-component tuning produces.

**The Pixel-Ladder Rule (shell).** The shell does not reuse the note's `rem`
ladder; it sets literal pixels from a short list - 17, 15, 13.5, 13, 12.5, 12,
11. A new shell element takes a size off that list. Inventing a step between two
of them is how a 31-size scale starts.

**The Figures-Only Monospace Rule.** The figure face sets numbers and
number-adjacent identifiers, on both surfaces: numeric cells, key-value answers,
step numbers, the ticker input, inline code, citation markers, chart text, the
topbar's source line. The headers above them are not monospace -
`table.ar-list th.num` is explicitly returned to sans, because a column header
set in mono and tracked reads as "V a l u e".

**The One Label Rule (note).** The note has one tracked label style, defined in
one selector list. A new note surface that needs a label joins that list rather
than declaring a size. The shell's labels are a separate, sentence-case register
and never borrow it.

**The Two Ranks Rule (note).** The stat strip sets exactly two ranks: the figure
this product authored carries `lead` (d2); figures it was handed sit at h1. A
value of "NM" or "Unsolvable" drops to h2 in muted ink, because it is a
statement about the data rather than a figure.

## Layout

**The shell has one column.** `--shell-col` (1120px) is declared once, on
`.block-container`, with `28px` side gutters (`--shell-gut`) and `26px/64px`
vertical padding, centred with `margin-inline: auto`. Nothing inside it sets a
width. Two screens narrow that same column instead of introducing a second axis:
`:has(.ar-form-head)` takes it to 760px so a text field is pleasant to type into
and a label sits near its input, `:has(.ar-gate)` takes it to 320px with 128px
of top padding, and `:has(.ar-report-view)` widens it to 1280px because a
sixteen-column table asks for every pixel. In all four cases every element on
the screen shares one set of edges.

This replaced a shell that measured, on one screen, four container max-widths
and three competing centre axes - `text-align: center` applied to blocks that
carried a max-width and no auto margin, so each block centred inside its own box
rather than on the page. Widths are whole pixels, never `ch`: `ch` resolves
against a proportional face and produced 394.017px, 528.62px and 630.59px, three
edges no two blocks could ever share.

Horizontal structure inside the column is host columns used for what they are:
a `1.9 / 1` split on the reports screen (the note listing, then a rail carrying
Get started and the primary action), with `10px` between button columns and
`min-width: 0` on every column so nothing refuses to shrink. A button's element
container is forced to `width: 100%`, because Streamlit sizes a container to its
content and a full-width button inside one measured 148px in a 362px column.

Shell rhythm is not a strict ramp; it is a short set of reused stops - `28px`
gutter and topbar gap, `24px` under the topbar, `16px` between cards and inside
table cells, `14px` card padding and head margin, `11px` on a table row and a
step, `9px` on a table header, `7px` on a key-value row. The topbar is `52px`
tall, full-bleed by negative margins against the gutter, with a hairline under
it.

**The note has two columns** wherever it matters: a `9rem` rail (`--rail`) and
`minmax(0, 1fr)` of content, `24px` apart. Masthead, section header and content
block share that grid, so a label in the rail and a rule in the content column
line up down the page; `.ar-block > *` is forced to column 2. Note spacing is
eight stops (4/8/12/16/24/32/48/72) and section headers are separated by `72px`
above and `24px` below. Measures are explicit and per-surface: narrative 66ch,
summary 72ch, status 82ch, captions 68ch, footnotes 80ch. The note's section bar
is sticky at `top: 0` with `--nav-h: 41px`, sticky table headers offset to it,
and sections carry `scroll-margin-top: calc(var(--nav-h) + var(--s3))`.

### Responsive behaviour
The shell breaks once, at `max-width: 700px`: the topbar loses its fixed height
and its provenance line (a reader can find that in the note itself, and the bar
was wrapping to three lines and overlapping), and host columns stack in source
order with `flex-direction: column` - which puts the notes above the
instructions and the primary action last.

The note breaks once, at `max-width: 900px`: the rail collapses and the masthead
rail becomes a line above the title, the stat strip flows to a two-column
row-based grid, splits and finding grids stack with the dividing left border
becoming a top border, the masthead title steps from d1 to d2, section notes lose
`nowrap` (a nowrap note measured 359px in a 390px viewport and pushed the whole
document into horizontal scroll), table and statement row-head minimum widths
relax to let labels wrap, and sticky table headers go static.

### Named Rules
**The One Column Rule.** The shell's width is declared once, on
`.block-container`, and inherited by everything. A screen that needs a different
measure narrows or widens that one column with a `:has()` selector. No
descendant declares a width, and no width is expressed in `ch`.

One exception, and only one: a paragraph of running prose may carry a
reading measure, because line length is a property of text rather than
of layout. The home screen's opening sentence is capped at 560px for
that reason. It does not reopen the defect the rule exists to close,
because a measure does not create a competing axis: the paragraph keeps
the column's own left edge, so every block on the screen still starts
at the same x. What is forbidden is a BOX that sets its own width and
then centres inside itself, which is what produced three centre lines.

The measure is stated in pixels on the grid, not in `ch`. The rule was
broken once that way after it was written - `62ch` resolved to
531.067px - and tests/test_theme_selectors.py now fails on any `ch`
width in the shell.

**The Second Axis Rule (note).** Section labels live in the rail, never above
their content. A single centred column with even vertical rhythm is the shape of
a template.

**The Same Object Rule (note).** The note's layout is built in our own markup,
not with host framework columns, because the screen and the exported file are
the same object. Host columns are legitimate in the shell, where there is no
export - and that is the only place they appear.

## Elevation & Depth

Two answers, one per surface. The **note has no shadows at all**: `box-shadow`
appears in `_DOCUMENT_CSS` only as `none`, stripping host defaults. Depth there
is hairlines at two weights plus a 2px ink rule that opens a document, and tonal
fields (white panels and slate-wash rows on warm paper). The sticky table header
occludes by being opaque, not by lifting.

The **shell is almost flat**: one ambient shadow, used on the card and the
secondary button, and a marginally stronger one on the primary button so the
page's single most important control sits a hair above everything else. Both are
1px of blur with no spread. A panel is identified by its edge and its fill; the
shadow only keeps the edge from reading as a drawn box.

### Shadow Vocabulary
- **Ambient panel** (`box-shadow: 0 1px 2px rgba(18, 20, 26, .04)`): the card,
  the secondary and download buttons. Barely visible by intent.
- **Primary control** (`box-shadow: 0 1px 2px rgba(18, 20, 26, .16)`): the
  primary and form-submit buttons only.

### Named Rules
**The Hairline Rule.** Structure is a 1px line on both surfaces. In the note a
2px line opens a document and a 1px left rule marks a quoted, assessed or
status-bearing passage; nothing is heavier than 2px, and there are no filled
alert panels. In the shell the only lines are the panel edge, the in-panel
hairline and the field boundary.

**The One Shadow Pair Rule.** The shell has exactly two shadows, both
`0 1px 2px` and differing only in alpha. There is no elevation ladder, no hover
lift, and no shadow on the note.

## Shapes

**The shell is softly rounded on a two-step pair.** `--shell-r` (7px) is the
control radius - every button, text input, textarea and select. `--shell-r-lg`
(10px) is the panel radius, used on the card and nothing else. Below those sit
one small radius for small objects, `--shell-r-sm` (5px): the product mark in
the bar (16px square) and on the gate (22px square), inline code, and the reveal
toggle's focus ring. The mark was drawn at 4px in the bar and 6px on the gate -
the same object at two shapes, forty pixels apart on the only screen that shows
both in sequence - and that is now one declared token. The recurring
shell silhouettes are the hairline-bordered rounded panel, the rounded figure
chip, and the small solid ink square that stands in for a logo.

**The note is square, everywhere**, asserted against the host framework
(`border-radius: 0` on expanders, alerts, the dialog, the sidebar toggle). Its
recurring silhouettes are the rule and the unfilled box outline: a pill or chip
is a 1px outline in the colour that carries its meaning with `0.25em 0.5em`
padding and no fill - except the failed-verification chip, which is filled,
because outlined it was indistinguishable from the neutral filing-date chip
beside it. The ticker badge is the single inverted shape in the note, ink field
with surface text, nudged `-0.34em` onto the title's baseline.

### Named Rules
**The Two Radii Rule (shell).** 7px for anything a user operates, 10px for a
panel. A third STRUCTURAL radius is a new rank nobody asked for; `--shell-r-sm`
(5px) is not one, because it dresses objects smaller than a control rather than
introducing a rank between them.

**Mask stops are not palette colours.** The nav's overflow fade uses `#000` and
`transparent` inside a `mask-image`, where a mask reads luminance: black means
opaque and transparent means cut. It is an alpha value wearing a colour's
notation, and it is the only `#000` in the stylesheet.

**The Square Note Rule.** Nothing in the exported note has a corner radius. A
rounded element inside the note is a host-framework default that escaped.

## Components

Every component is a Python function in `asset_researcher/ui/components.py`
returning one line of HTML with an `ar-` class; the stylesheet is the only place
style lives. Shell components and note components share the prefix and nothing
else - `.ar-count` is deliberately not named `.ar-pill`, because the note
stylesheet already owns `.ar-pill` and two meanings on one class name is how a
shell change silently restyles a report.

### Buttons (shell)
- **Shape:** 7px radius (`{rounded.md}`), `36px` minimum height, `0 16px`
  padding, full width within its own column - so two buttons in a row are the
  same size. They measured 166px and 155px with a 167px gap when each was
  centring inside its own host column.
- **Primary:** ink fill, ink border, white label, `13px/500` sentence case.
  Sentence case, not uppercase tracked: a tracked-caps button belongs to the
  editorial world this shell replaced, and at 11px it is measurably slower to
  read than the label it encodes.
- **Secondary / download:** panel fill, ink label, panel-edge border, ambient
  shadow.
- **Hover:** primary to `shell-ink-hover`; secondary to
  `shell-secondary-hover` with `shell-secondary-hover-line`. 120ms on colour,
  border-colour and text-colour only.
- **Focus:** a 2px indigo ring at 2px offset.
- **Active:** `translateY(1px)` over 40ms, under
  `prefers-reduced-motion: no-preference`. A press with no acknowledgement,
  followed by a rerun most of a second later, reads as a button that did not
  work.
- Every descendant of a control inherits the control's colour, because Streamlit
  wraps a button label in its own `<p>` and the note's paragraph colour was
  winning - the primary action rendered at about 1.8:1.

### Inputs / Fields (shell)
- **Style:** panel fill, `shell-field-line` boundary at 3.27:1, 7px radius; the
  inner `input`/`textarea` is transparent and border-free so the root carries the
  whole visible edge. Text inputs are set in the figure face (12.5px mono);
  textareas and selects in sans at 13px.
- **Label:** `shell-field-label` - 12px, 500, sentence case, above the field.
  Hidden entirely on the gate, where there is one field and a sentence already
  naming it.
- **Focus:** the border turns indigo and a 2px indigo outline sits at 1px
  offset, on the **root**, because that is where the visible border is. The
  reveal toggle is a second tab stop inside the field's box and gets its own
  inset ring.
- **Placeholder:** muted, `opacity: 1`.
- Streamlit's "Press Enter to apply" hint is hidden: it renders half inside the
  field and half under the reveal toggle, and explains a convention nobody needs
  explained.

### Cards / Containers (shell)
- **Corner:** 10px. **Background:** panel on ground. **Border:** 1px
  `shell-line-2`. **Shadow:** ambient panel (see Elevation). **Padding:** `14px`
  via an inner `.pad`, or zero in the flush variant so a table runs to the
  panel's own edge. `overflow: hidden` clips the table's corners to the card's.
- **Card label:** optional 11px uppercase muted line above the content, `9px`
  beneath it.
- Stacked cards are `16px` apart.

### Navigation (shell topbar)
The shell's one piece of persistent chrome, and it is not a tab set. `52px`
tall, full-bleed, hairline under it: brand mark and product name on the left,
the current screen named in words with a hairline before it
(`aria-current="page"`), and the data provenance in mono on the right. It
carried two rounded pills with the active one tinted; in this register that
shape means "tab", neither was clickable (Streamlit owns navigation, so they
were spans), and the tint measured 1.09:1. Real navigation lives in the page, in
real buttons.

### Reports table (shell signature)
The product's own output on the first screen, in a flush card: a `shell-sink`
header band at 11px muted, `11px/16px` cells on hairlines, no last-row border.
The ticker column is 600-weight and tightened; company and metric take
`shell-soft`; the value column is right-aligned mono with `tnum`. Columns are the
ones the data actually supports - an earlier version carried "Divergences" and
"Built" because the comp did, and filled the first with the metric's *name* and
the second with nothing. A missing value is an em dash, never a non-breaking
space under a column headed "Value".

### Count chip (shell signature)
`.ar-count`: inline-flex, mono 11px, `2px 7px`, 5px radius. Grey by default,
`hot` on a divergence, `cool` on agreement. The single place colour is permitted
in the shell, and both tinted pairs are asserted at 4.5:1 against their own
fills by `tests/test_contrast.py`.

### Steps (shell)
Get started is instructions, so it is a numbered list of actions and not a row
of marketing claims. A `26px / 1fr` grid per row with CSS
`counter(step, decimal-leading-zero)` in mono muted, rows `11px` apart on
hairlines, continuation phrases in `shell-soft`, literals in a 4px grey code
chip. The screen this replaced carried three guarantees about the product and no
instructions for using it.

### Key-value rows (shell)
A label-left/answer-right flex row, `7px` vertical, hairline between rows. The
answer is mono 12px with `tnum` and ink; the label is `shell-note` in
`shell-soft`.

### Empty states (shell)
`28px/16px`, centred, muted 12.5px inside a card. The reports list and the
samples list each have one, and each says what to do rather than only that there
is nothing.

### Gate (shell)
One screen, one field. The 320px column holds every element - mark, title, line,
field, button - as a child of one centred box, so there is a single centre line
and nothing can drift off it. The form's own border and padding are removed and
the field's label is hidden. It explained, before asking, what the product was;
everyone reaching this screen was sent the link and the passphrase, so the
explanation answered a question nobody was asking.

### Note components
The note's own vocabulary is unchanged by this build and documented here as what
ships:

- **Masthead:** company name at d1 with the ticker badge on its baseline,
  provenance in the rail in mono micro, slash-separated subline beneath, over a
  2px ink rule. No eyebrow.
- **Stat strip:** one hairline-divided row, ink rule above, `24px` column gaps.
  `.ar-stat` is `display: contents` so labels, values and notes land on three
  shared grid rows and align across the strip; the note cell is always emitted,
  because an empty one would staircase the strip. Two ranks, per the Two Ranks
  Rule.
- **Section header:** label in the rail, a 1px rule across the content column
  fading toward the margin, an optional note; `:target` tints the label slate so
  the section the reader jumped to stays marked.
- **Section bar:** sticky, paper-backed, label-style uppercase links with a
  transparent 2px bottom border that turns slate on hover; horizontally
  scrollable with a 44px fade mask, because seventeen sections overflow at any
  realistic width.
- **Tables:** ruled header (sticky, label style, muted), no gridlines,
  `rule-soft` between rows, white surface, numeric cells right-aligned in mono.
  Row variants: `subject` (slate wash, held on hover), `spacer`, `summary`,
  `total` (ruled above in ink). The statement table adds spanning section rows,
  ruled subtotals, and `derived` rows in muted ink and indented - because a
  figure this project computed must not look like one the company filed.
- **Summary, findings, splits, provenance chips, status lines, narrative column,
  charts:** as recorded in the Colors and Typography rules above. Six inline-SVG
  figures read their colour from the same Python constants the stylesheet emits,
  and their type is pegged to the page scale in pixels (title 13, label 11, tick
  10, fine 9) with each SVG capped at its design width, so a 13px title inside a
  chart is 13px beside it.
- **Status, severe state:** the note's `warn` and `bad` status lines carry a
  **3px** left rule rather than the 1px hairline everything else uses. This is a
  conscious semantic deviation, scoped to one state on one surface: it encodes
  severity, and the note was deliberately left unrestyled by this build. The
  Impeccable detector flags it as a side-tab accent; it is recorded here as a
  carried deviation, not as a pattern a new surface may copy.

### Motion
Shell: button press (`translateY(1px)`, 40ms), 120ms colour transitions on
controls, and the run's determinate progress bar. The bar animates to
`scaleX(.97)` over 75s and stops short of the end because the duration is an
estimate and a bar that reaches 100% while work continues is a lie; under
`prefers-reduced-motion: reduce` it holds a static `scaleX(0.35)`, because a flat
line was the one surface saying the system is working.

Note: one authored moment. Masthead, stat strip (80-120ms later) and workspace
settle in once on first paint (`ar-settle`: 5px rise and fade, 560ms, `--ease`).
Everything else that moves is a 120ms transition on colour, border-colour or
text-decoration-colour - never size, position or opacity. The reading-position
bar under the section nav is scroll-driven, so it costs no script and simply
does nothing where the timeline is unsupported.

**The One Moment Rule.** A surface settles in once. Any further motion is a
120ms colour transition responding to the pointer or the keyboard, or an honest
progress indicator. No scroll-triggered entrances.

### Host-framework addressing (both surfaces)
Not a visual rule, but a durable constraint on how any new rule must be written.
**This Streamlit build renders react-aria widgets and the page contains zero
elements carrying a `data-baseweb` attribute.** Every `[data-baseweb]` rule that
once styled the form was dead, and the consequence was not cosmetic: Streamlit's
default gives a field root a 1px *white* border on a white fill, so a text input
had no visible boundary, and the focus ring written for
`[data-baseweb="input"]:focus-within` never applied to anything. Controls are
therefore addressed through the test ids this build actually emits -
`stTextInputRootElement`, `stTextAreaRootElement`, `stSelectbox` - and
`tests/test_theme_selectors.py` fails on any rule naming a hook absent from the
shipped bundle. The same check already removed `stStatus`, `stDecoration`,
`stDivider` and `stVerticalBlockBorderWrapper`.

## Do's and Don'ts

### Do:
- **Do** declare a shell width once, on `.block-container`, and narrow or widen
  that one column with a `:has()` selector when a screen needs a different
  measure.
- **Do** write shell widths in whole pixels.
- **Do** take a shell font size off the shipped ladder (17, 15, 13.5, 13, 12.5,
  12, 11) and a note font size off `--t-*`.
- **Do** use 7px for anything a user operates and 10px for a panel.
- **Do** give a control's boundary `shell-field-line` (3.27:1) and keep the
  1.27:1 hairline for card edges.
- **Do** measure a new shell text tone against `shell-bg`, `shell-panel` and
  `shell-sink` before shipping it, and add it to `tests/test_contrast.py`.
- **Do** set figures in the monospace face and the headers above them in sans.
- **Do** put the focus ring where the visible border is - on the field root, not
  the inner input.
- **Do** address a Streamlit control with a `data-testid` hook that the shipped
  bundle actually contains.
- **Do** keep host-framework overrides out of `document_stylesheet()`, so the
  exported note carries no dead selectors.
- **Do** index with the note's two hues on the note, and leave everything else
  grey.
- **Do** place note section labels in the 9rem rail and note content in
  column 2.

### Don't:
- **Don't** introduce a colour into the shell. The divergence count and the
  focus ring are the complete list.
- **Don't** express a width in `ch`. It resolves against a proportional face and
  produced 394.017px, 528.62px and 630.59px - three edges no two blocks could
  share.
- **Don't** set a `max-width` on a shell button, input, caption or heading. Five
  independent widths inside one column is the defect this shell replaced.
- **Don't** centre a block with `text-align: center` on a box that carries its
  own max-width and no auto margin. That is how one screen got three centre
  axes.
- **Don't** set a shell button in tracked uppercase. Sentence case, 13px, 500.
- **Don't** reuse a note class name for a shell component, or the reverse.
  `.ar-count` exists because `.ar-pill` was taken.
- **Don't** add a third structural radius to the shell, an elevation ladder, a
  hover lift, or any shadow to the note.
- **Don't** add a shell navigation element shaped like a tab unless it is a real
  control. A dead tab bar is the first thing a reader tries and the first thing
  that fails.
- **Don't** put an eyebrow or kicker above a heading on either surface. A tracked
  label announcing what the heading already says adds a rank and carries no
  information.
- **Don't** wear monospace as a costume. It is not for labels, table headers,
  buttons or tabs.
- **Don't** copy the note's 3px severity rule onto a new surface. It is a scoped
  deviation on one state of an unrestyled surface, not a house device.
- **Don't** write a `[data-baseweb]` selector. Nothing in this build carries that
  attribute.
- **Don't** restyle the research note to match the shell. The two worlds are the
  system, and PRODUCT.md commits to both.
- **Don't** open the application on a marketing page. A reader sees real notes
  before any claim about them.
- **Don't** build a pillar grid or a numbered three-up of claims. Get started is
  instructions, not guarantees.
- **Don't** animate on scroll or give sections entrance animations.
- **Don't** put two scales on one chart, draw an axis frame, or colour a mark by
  its rank or the sign of its value.
