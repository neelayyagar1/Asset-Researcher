---
name: Asset Researcher
description: A tearsheet - the one-page company document an analyst pulls, marks up and forwards.
colors:
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
  neutral: "#b4afa1"
  negative: "#8a2d1c"
  positive: "#2b6349"
  caution: "#8a6a1a"
typography:
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
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "12px 16px"
  button-primary-hover:
    backgroundColor: "{colors.accent}"
    textColor: "#ffffff"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "12px 16px"
  button-secondary-hover:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
  input-text:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
  nav-link:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.label}"
    padding: "0 0 2px"
  nav-link-hover:
    textColor: "{colors.ink}"
  chip-provenance:
    backgroundColor: "transparent"
    textColor: "{colors.ink-muted}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "0.25em 0.5em"
  chip-provenance-hover:
    textColor: "{colors.ink}"
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
  ticker-badge:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.surface}"
    typography: "{typography.micro}"
    rounded: "{rounded.none}"
    padding: "0.2em 0.5em"
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

**Creative North Star: "The Tearsheet"**

The artifact is the one-page company document an analyst pulls, marks up and
forwards. Not a dashboard and not a marketing page. The product's output is a
document and the application is the machine that makes it, so the running screen
and the exported HTML file are the same object: `document_stylesheet()` ships the
document rules alone, and `stylesheet()` adds the Streamlit shell overrides for
the app. Anything that would be a dead selector in a forwarded file stays out of
the export.

The page is dense on purpose and breathes in exactly one place. Tables, stat
strips and charts are packed to instrument density; the narrative column
(`.ar-prose`, 66ch, 1rem/1.68) is the single wide-measure, generously leaded
surface, and the contrast between the two is the argument. Depth is drawn with
hairlines and tonal fields on warm paper; nothing floats. Colour is an index, not
decoration: slate marks the subject and this analysis, sienna marks the market
and the prevailing view, and the reader learns the pair without a legend.

Everything structural is square. There is no radius token other than zero, no
shadow anywhere in the document stylesheet, and no filled alert panels - state is
carried by a 1px left rule and a label in the relevant colour.

**Key Characteristics:**
- Warm paper (#faf8f3) and warm near-black (#17150f); white is reserved for
  tables and panels sitting on the paper.
- One type scale of ten steps; no raw font-size value in any component rule.
- Monospace sets figures and nothing else.
- A 9rem left rail gives the page a second axis.
- Hairlines and tonal fields instead of shadows; zero radius throughout.
- Two gradients in the whole stylesheet, both informational.
- One authored motion moment, on first paint.

## Colors

A warm paper-and-ink ground with two indexing hues (slate, sienna) and three
semantic signals (corroboration, divergence, caution). Thirteen tokens plus a
tint, generated once in Python and emitted as `:root` custom properties, so the
SVG charts and the stylesheet read the same palette and cannot drift.

### Primary
- **Slate** (`{colors.accent}`): the subject and this analysis. Links, the
  `:focus-visible` ring, `::selection`, `caret-color`, the subject bar in a peer
  chart, the left rule on the summary and on a finding's assessment, the active
  nav underline, and the section label of whatever section the reader jumped to.
- **Slate Wash** (`{colors.accent-soft}`): the subject's row in a comparables
  table and the hover field behind a citation marker. The only non-white fill
  used to mark identity.

### Secondary
- **Sienna** (`{colors.accent-2}`): the market - the prevailing view and the
  traded price. The "street" column label, and the dashed traded-price reference
  line in the valuation and cash-flow charts. Never used for the subject.

### Tertiary
- **Stone** (`{colors.neutral}`): peers and other recessive marks in charts;
  the thing the subject is being measured against.

### Neutral
- **Warm Ink** (`{colors.ink}`): body-weight emphasis, headings, figures in a
  numeric cell, the 2px rule that opens the masthead and the open state, and the
  rule above a total row.
- **Soft Ink** (`{colors.ink-soft}`): running prose and ordinary table cells.
- **Muted Ink** (`{colors.ink-muted}`): labels, captions, notes, axis text,
  "NM" values, and derived (computed-not-filed) statement rows.
- **Paper** (`{colors.paper}`): the page, the sticky nav background, table
  spacer rows, and input fills.
- **Surface** (`{colors.surface}`): tables, status panels, the sidebar, and the
  sticky table header that must occlude rows scrolling under it.
- **Rule** (`{colors.rule}`): structural hairlines, chip borders, scrollbar
  thumb.
- **Rule Soft** (`{colors.rule-soft}`): hairlines *inside* a table, one step
  quieter than structural rules.

### Semantic
- **Corroboration** (`{colors.positive}`): agreement between narrative and
  figures; the bull column label; the sensitivity-grid tint.
- **Divergence** (`{colors.negative}`): a narrative that the filed figures do
  not support; the bear column label.
- **Caution** (`{colors.caution}`): unverified or thin evidence.

### Named Rules
**The Two-Hue Rule.** Slate is the subject and this analysis; sienna is the
market and the prevailing view. A mark that means neither is grey. No third hue
is introduced for emphasis.

**The Colour-Follows-Entity Rule.** In any comparison, colour attaches to the
entity, not to its rank or to its value's sign, so filtering or reordering a peer
set never repaints the survivors.

**The One-Direction Tint Rule.** A conditional fill answers one question and
shades one side of the answer. The sensitivity grid tints only cells that clear
the traded price (`color-mix` of corroboration at 5-19% by distance); an empty
grid is a finding, not a bug.

## Typography

**Display Font:** Faustina (with Georgia, serif)
**Body Font:** Public Sans (with -apple-system, BlinkMacSystemFont, sans-serif)
**Figure Font:** Spline Sans Mono (with ui-monospace, Menlo, monospace)

**Character:** Public Sans is the typeface of the United States federal design
system, which is where every figure in this product originates; Faustina is a
text serif with enough character to set a masthead without tipping into magazine;
Spline Sans Mono has true tabular widths. All three load from one Google Fonts
import at weights 400-600.

Tabular lining figures are a document default, set on `body` with both
`font-variant-numeric` and `font-feature-settings`, because every figure here is
compared down a column.

### Hierarchy
Ten steps, declared once as custom properties (`--t-*`) with their line-height
and letter-spacing. The frontmatter carries the values.

- **d0** - open state headline only, capped at 16ch. The one fluid step.
- **d1** - the company name in the masthead, and `h1`.
- **d2** - the lead figure in the stat strip; the masthead title below 900px.
- **h1** - `h2`, and ordinary stat-strip values.
- **h2** - `h3`, the summary's opening paragraph, and an "NM" stat value.
- **body** - `p` and `li`, status lines, a finding's assessment, form controls.
- **read** - the narrative column, the summary body, the open-state lede. The
  only generously leaded step (1.68).
- **data** - table bodies. Numeric cells switch to the figure face.
- **micro** - captions, footnotes, the masthead subline, the ticker badge,
  table row heads, statement units.
- **label** - the single label style (0.625rem/0.14em/600/uppercase), applied in
  one rule to section labels, stat labels, column labels, pills, chips, table
  headers, status tags, finding labels, nav links, buttons and sidebar labels.

### Named Rules
**The One Scale Rule.** Component rules reference `--t-*` only. There is exactly
one literal font-size in the document stylesheet - the citation marker at
`0.72em`, relative to the prose it sits in - and no raw `rem` or `px` font-size
anywhere else. An earlier stylesheet held 31 distinct sizes, eighteen inside a
five-pixel band; per-component tuning is how that happens.

**The Figures-Only Monospace Rule.** The figure face sets numbers and
number-adjacent identifiers: numeric table cells, heat cells, row heads, the
ticker badge, the masthead rail, citation markers, and chart text. Labels, table
headers, buttons and tabs are sans. Monospace worn as a costume for "technical"
flattens hierarchy and makes a document read as a terminal.

**The One Label Rule.** There is one label style, defined in one selector list.
A new surface that needs a label joins that list rather than declaring a size.

**The Two Ranks Rule.** The stat strip sets exactly two ranks: the figure this
product authored carries `lead` (d2); the figures it was handed sit at h1. A
value of "NM", "Unsolvable" or "n/a" drops to h2 in muted ink, because it is a
statement about the data rather than a figure.

## Layout

Two columns, everywhere it matters: a `9rem` rail (`--rail`) and
`minmax(0, 1fr)` of content, with a `24px` column gap. The masthead, every
section header and every content block share that grid, so a label in the rail
and a rule in the content column line up down the whole page. `.ar-block > *`
is forced to column 2, which is what keeps charts and tables aligned under the
section rule while the rail stays quiet.

Spacing is eight stops on a 4/8/12/16/24/32/48/72 ramp. Section headers are
separated by `72px` above and `24px` below; that single large stop is what
carries the document's rhythm. The app container is capped at `1240px` with
`32px 24px 72px` padding. Measures are explicit and per-surface: narrative 66ch,
summary 72ch, status 82ch, captions and figure captions 68ch, footnotes 80ch,
open-state lede 54ch, open-state headline 16ch.

The section bar is sticky at `top: 0` with `--nav-h: 41px`; sticky table headers
offset to `top: var(--nav-h)` and sections carry
`scroll-margin-top: calc(var(--nav-h) + var(--s3))` so a jump target is not
hidden under the bar. Two Streamlit wrappers around the nav are dissolved with
`display: contents` so the nav's containing block is the scrollport.

Only a table that actually overflows becomes a scroll container:
`.ar-table-wrap:has(> .ar-table-scroll)` gets `overflow-x: auto`. Applying it
unconditionally also forces `overflow-y: auto`, which turns the wrap into the
scrollport and breaks the sticky header.

### Responsive behaviour
One breakpoint, `max-width: 900px`. The rail collapses: masthead, section header
and block all become single-column and the rail's content becomes a line above
the title. The stat strip flows to a two-column, row-based grid and `.ar-stat`
leaves `display: contents` for `display: block`. Split columns, finding grids and
side-by-side rows stack, with the dividing left border becoming a top border.
The masthead title steps from d1 to d2. Section notes lose `white-space: nowrap`
(a nowrap note measured 359px in a 390px viewport and pushed the whole document
into horizontal scroll). Sticky table headers go `static`.

The nav does not wrap at any width: it scrolls horizontally with its native
scrollbar hidden, and a mask-image fades its last `44px` so the overflow is
signalled rather than cut mid-word.

### Named Rules
**The Second Axis Rule.** Section labels live in the rail, never above their
content. A single centred column with even vertical rhythm is the shape of a
template.

**The Same Object Rule.** Layout is built in our own markup, not with host
framework columns. A Streamlit column is a full-width block outside this grid,
and anything placed in one escapes the content column - and breaks the promise
that the screen and the exported file are the same document.

## Elevation & Depth

No shadows. `box-shadow` appears in the stylesheet only as `box-shadow: none`,
stripping host-framework defaults from buttons, inputs and status panels. Depth
is drawn two ways: hairline rules at two weights (structural `rule`, in-table
`rule-soft`) plus a 2px ink rule that opens a document, and tonal fields (white
`surface` panels and slate-wash rows on warm `paper`). The sticky table header
occludes by being opaque `surface`, not by lifting.

### Named Rules
**The Hairline Rule.** Structure is a 1px line. A 2px line opens a document
(masthead, open state) and a 1px ink line closes a total or opens a header; a
1px left rule marks a quoted, assessed or status-bearing passage. No borders
heavier than 2px, no shadows, no filled alert panels.

## Shapes

Zero radius, everywhere, asserted against the host framework
(`border-radius: 0` on buttons, inputs, status containers, alerts and the
sidebar toggle). The recurring silhouettes are the rule and the box outline: a
pill or chip is a 1px outline in the colour that carries its meaning with
`0.25em 0.5em` padding and no fill; the ticker badge is the single inverted
shape on the page, ink field with surface text, nudged `-0.34em` to sit on the
title's baseline.

## Components

Every component is a Python function returning a single line of HTML with an
`ar-` class; the stylesheet is the only place style lives.

### Masthead
Company name (d1, display face) with the ticker badge on the baseline, the
report's provenance line in the rail set in the figure face at micro, and a
slash-separated subline beneath. No eyebrow: a tracked "EQUITY RESEARCH NOTE"
above a heading that already says what it is adds a rank and carries no
information.

### Stat strip
The headline figures as one hairline-divided row: ink rule above, rule hairline
below, `24px` column gaps. `.ar-stat` is `display: contents` so labels, values
and notes land on three shared grid rows and align across the strip; the note
cell is always emitted (an empty one would staircase the strip). Two ranks, per
the Two Ranks Rule. Tone classes colour a value with corroboration or divergence.

### Section header
Label in the rail (label style, ink), then a 1px rule across the content column
fading to transparent, then an optional note. `#id` from a slugged label;
`:target` tints the label slate so the section the reader jumped to stays marked.

### Section bar (nav)
Sticky, full-width, paper-backed, ink rule beneath, label-style uppercase links
with a transparent 2px bottom border that turns slate on hover. Horizontally
scrollable with a fade mask. The report is one continuous document, not a tab
set; this is the jump-back.

### Tables
Ruled header (label style, muted, ink rule above, `rule` hairline below,
sticky), no gridlines, `rule-soft` hairlines between rows, white surface. Numeric
cells are right-aligned and set in the figure face in ink; `key` cells are
ink/500 with an `8.5rem` minimum; `wide` cells drop to micro and wrap. Row hover
is a 4% slate wash. Row variants: `subject` (slate wash, held on hover),
`spacer` (8px of paper), `summary` and `total` (ruled above in ink).

**Statement table.** The financial summary adds section-heading rows (label
style spanning the table, with a right-floated unit note), subtotal rows ruled
above, and `derived` rows in muted ink and indented - because a figure this
project computed must not look like one the company filed.

**Sensitivity table.** Discount rate against terminal growth, cells in the
figure face, tinted one direction only per the One-Direction Tint Rule.

### Summary
Directly under the headline figures, in the page's most valuable space: 72ch,
a 1px slate left rule, `16px` of left padding. First paragraph h2, body
paragraphs read, closing paragraph micro and muted.

### Provenance chips
Label-style outlined links beside the company name, each jumping to the
provenance note that carries the full wording. Tone classes `ok` / `warn` /
`bad` colour text and border together; hover goes to ink.

### Status line
A ruled line in place of a filled panel: 1px left border, `12px` padding, a
block label tag above the message, both tinted by level
(`ok` / `warn` / `bad` / `info`). A section with nothing to show emits an `info`
status reading "Not available" plus a sentence saying why.

### Finding
One narrative-versus-figures comparison. A head row of outlined pills
(Corroborated or Divergence, plus materiality in muted), then management
position and reported figures side by side in a 1fr 1fr grid - the comparison
*is* the finding, and stacking it makes the reader hold the first in memory -
then the assessment in a slate-ruled passage.

### Split
Two opposed positions in ruled columns, divided by a 1px vertical rule: bull
against bear, street against ours. Column labels take the semantic or indexing
colour that names the side.

### Narrative column
66ch at read size, headings at h1/h2 with `48px`/`24px` of space above.
Citation markers are set in the figure face at `0.72em`, raised `0.3em`, no
underline, with a slate-wash hover - set in the figure face because that is
what they point at.

### Open state
What the application shows before a report exists. Not a cover page: a 2px ink
rule, the headline at d0 capped to 16ch, a lede, and a label-style hint pinned
to the bottom edge by a four-row grid (`auto auto 1fr auto`) over
`calc(100vh - 11rem)`, so the empty space reads as composed rather than as a
block that ran out of content.

### Controls (app shell only)
Buttons are label-style uppercase, square, ink-on-ink primary going slate on
hover; secondary and download buttons are transparent with ink text, inverting
on hover. Inputs are paper-filled, square, `rule`-bordered; the focus ring is a
2px slate outline on the *wrapper*, because that is where the visible border is.
These rules ship only in `stylesheet()`, never in the exported document.

### Browser surfaces
The parts nobody draws still carry the design: `::selection` is slate on white,
`caret-color` slate, the scrollbar is an 11px `rule` thumb inset 3px with paper
as its border going muted-ink on hover, and `:focus-visible` is a 2px slate
outline at 2px offset.

### Charts

Six inline-SVG figures (`metric_bars`, `margin_lines`, `peer_bars`,
`valuation_range`, `dcf_bridge`, `free_cash_flow_history`), each wrapped in a
`figure` with a micro, muted, 68ch caption. SVG rather than rasterised plots so
the chart inherits the page's typefaces, stays sharp, carries no background
tile, and needs no plotting dependency.

- **One axis per chart.** Revenue and margin are two charts, never two scales on
  one; a dual-axis chart lets the author choose where the lines cross.
- **The subject is the only coloured mark** in a peer chart (slate); peers are
  stone. Sienna is the traded price or the market view, always dashed
  (`stroke-dasharray` 4 3 / 3 3 / 2 2 for reference and projection lines).
- **Horizontal gridlines only**, recessive, behind the marks. No frame, no axis
  box.
- **Direct labels, selectively.** A number on every point is noise.
- **Type is pegged to the page scale, in pixels, at a 16px root:** title 13px
  (display face, 500), label 11px, tick 10px, and a 9px fine step for a series
  name beside the figure it names. Chart text defaults to the figure face with
  `font-variant-numeric: tabular-nums`; a subtitle is sans and muted.
- **Each chart is drawn at the pixel width it will occupy** and capped with
  `style="max-width: Npx"`, so a user unit is a pixel and a 13px title in a
  chart is 13px beside it. Without the cap the type scales with the container.
- Colour comes from the Python token constants, the same values the stylesheet
  emits.

**The One Axis Rule.** One quantity, one scale, one chart.

**The Same Size Rule.** A type size inside an SVG equals the same type size
beside it. Charts never scale beyond their layout width.

### Motion

One authored moment and nothing else. Under
`@media (prefers-reduced-motion: no-preference)`, the masthead and then the stat
strip settle in once on first paint (`ar-settle`: 5px rise and fade, 420ms,
`cubic-bezier(.2,.6,.2,1)`, the strip delayed 80ms). Everything else that moves
is a 120ms state transition on the same easing, applied to colour, border-colour
and text-decoration-colour only - never to size, position or opacity. There is
no scroll-triggered animation, and no entrance on sections: a blanket entrance
reads as a template playing an animation at the reader.

**The One Moment Rule.** The document settles in once. Any further motion is a
120ms colour transition responding to the pointer or the keyboard.

## Do's and Don'ts

### Do:
- **Do** reference `--t-*` for every font-size and `--s1`-`--s8` for every
  spacing value in a new rule.
- **Do** put a new label on the single label-style selector list instead of
  declaring a size.
- **Do** keep the figure face for figures: numeric cells, heat cells, row heads,
  citation markers, chart text.
- **Do** index with the two hues - slate for the subject and this analysis,
  sienna for the market and the prevailing view - and leave everything else grey.
- **Do** draw structure with 1px hairlines (`rule` structural, `rule-soft`
  in-table) and mark passages with a 1px left rule.
- **Do** place section labels in the 9rem rail and content in column 2.
- **Do** build layout in our own markup so the screen and the exported file stay
  the same object, and keep host-framework overrides out of
  `document_stylesheet()`.
- **Do** set two ranks in a stat strip, and drop a non-figure ("NM",
  "Unsolvable") to a smaller, muted rank.
- **Do** peg chart type to the page scale in pixels and cap each SVG at its
  design width.
- **Do** state why a section is empty, in a sentence, in an `info` status line.

### Don't:
- **Don't** open with a cover page. The application opens on the instrument: a
  rule, the name, what comes out, where to start.
- **Don't** build a pillar grid. Numbered 01/02/03 heading-plus-paragraph
  three-ups are the most recognisable generated-page pattern there is.
- **Don't** put an eyebrow or kicker above a heading. A tracked label announcing
  what the heading already says adds a rank and carries no information.
- **Don't** wear monospace as a costume. It is not for labels, table headers,
  buttons or tabs.
- **Don't** add a decorative gradient. The stylesheet contains exactly two, both
  informational: the section rule fading toward the margin, and the nav's
  44px overflow mask.
- **Don't** add a shadow or a radius. Depth is hairlines and tonal fields;
  corners are square.
- **Don't** write a raw `rem` or `px` font-size into a component rule. That is
  how a 31-size scale happens.
- **Don't** colour a mark by its rank or the sign of its value in a comparison;
  colour follows the entity.
- **Don't** put two scales on one chart, or draw an axis frame.
- **Don't** animate on scroll or give sections entrance animations.
- **Don't** use a filled alert panel, or a third accent hue for emphasis.
