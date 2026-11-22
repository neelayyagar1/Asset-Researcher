"""Visual tokens and the stylesheet.

The surface is a tearsheet: the one-page company document an analyst pulls,
marks up and forwards. Not a dashboard and not a marketing page. The output
of this product is a document and the application is the machine that makes
it, so the screen and the exported file are the same object.

Four decisions carry it.

**One type scale, ten steps.** An earlier version of this file held 31
distinct font sizes, eighteen of them inside a five-pixel band. Nobody
perceives 0.775rem as a different rank from 0.78rem; they perceive "all the
text is small". Per-component tuning like that is locally defensible and
globally flat, and it is the clearest sign that a stylesheet was assembled
rather than designed. Component rules may only reference the scale, with
one exception: the citation marker is sized relative to the prose it
interrupts (`0.72em`), because a raised marker has to track whatever line
it sits in rather than a fixed step.

**Monospace sets figures and nothing else.** It was doing ten jobs: every
label, every table header, the tab bar, the buttons. Monospace worn as a
costume for "technical" flattens hierarchy and makes a document read as a
terminal. Here it means measurement. Labels are sans, one style, one size.

**A left rail.** The page is a two-column grid: a nine-rem gutter carrying
section labels and provenance, and the content column beside it. A single
centred column with even vertical rhythm is the shape of a template; the
rail gives the layout a second axis and somewhere for quiet information to
live.

**Public Sans for interface, Faustina for display.** Public Sans is the
typeface of the United States federal design system, which is where every
figure in this product originates. No other face carries that argument.
Faustina is a text serif with enough character to set a masthead without
tipping into magazine, and figures are set in Spline Sans Mono, which has
true tabular widths.

Colour is reserved for meaning: slate marks the subject and this analysis,
sienna marks the market and the prevailing view, so a reader learns the pair
without being given a legend.
"""

from __future__ import annotations

# --- tokens -------------------------------------------------------------
#
# Read by the SVG charts as well as the stylesheet, so a chart can never
# drift out of step with the page it sits on.

INK = "#17150f"  # warm near-black, body text
INK_SOFT = "#403c33"  # secondary prose
INK_MUTED = "#6f6a5c"  # labels, captions, axis text
PAPER = "#faf8f3"  # page
SURFACE = "#ffffff"  # tables and panels that sit on the page
RULE = "#ded9cc"  # hairline, structural
RULE_SOFT = "#ece8dd"  # hairline, within a table

ACCENT = "#1d5a86"  # slate: the subject, this analysis
ACCENT_SOFT = "#e9eef3"
ACCENT_2 = "#a8481f"  # sienna: the market, the prevailing view, traded price
# Peers and recessive marks. #b4afa1 measured 2.06:1 against the paper,
# under the 3:1 that WCAG requires of a graphical object carrying meaning:
# a peer bar and the bear-to-bull band are data, not decoration, so they
# have to be distinguishable. This clears it at 3.42:1. Gridlines stay
# lighter on purpose, being genuinely decorative.
NEUTRAL = "#8c8676"

NEGATIVE = "#8a2d1c"  # divergence, bear
POSITIVE = "#2b6349"  # corroboration, bull
CAUTION = "#8a6a1a"  # unverified, thin evidence

FONT_DISPLAY = "'Faustina', Georgia, serif"
FONT_SANS = "'Public Sans', -apple-system, BlinkMacSystemFont, sans-serif"
FONT_MONO = "'Spline Sans Mono', ui-monospace, Menlo, monospace"

# ------------------------------------------------------------- the shell
# The Broadsheet. These are the shell's own, declared apart from the three
# above because `_root()` travels with every exported file: a shell face
# declared there would restyle six sealed notes and every copy a reader has
# already downloaded. The document keeps Faustina; the shell does not.
#
# Newsreader stands in for Denton, the face Public holds at weight 300.
# It is the closest high-contrast serif with true light weights that can be
# served from Google Fonts, and it was drawn for screens rather than for
# print, which matters at a display size on a laptop. The weight is the
# whole point: a serif at 600 is what every competitor already does.
FONT_SHELL_DISPLAY = "'Newsreader', 'Faustina', Georgia, serif"

# A cold ground, so the note's warm paper reads as a different surface the
# moment it opens. The previous shell sat at #fcfcfd, which is neutral to
# the point of being nothing; this commits.
SHELL_BG = "#f4f6f9"  # marble, the page
SHELL_PANEL = "#ffffff"  # a panel lifted off it

# The one accent. It is on the divergence count and on links, and nowhere
# else on the page. An accent used twice is decoration; used once it reads
# as switched on. Measured 9.47:1 on the marble ground and 10.25:1 on a
# white panel, so it clears AA for text at every size it is set at, and
# clears the 3:1 the WCAG 2.2 control rules ask of a boundary.
SHELL_ACCENT = "#1b3a8f"

# Chart type sizes in pixels, pegged to the page scale so a size inside an
# SVG is the same size beside it: --t-label, --t-micro and --t-data at a
# 16px root.
CHART_TICK_PX = 10.0
CHART_LABEL_PX = 11.0
CHART_TITLE_PX = 13.0
# One step below the tick, for a series name beside the figure it names.
CHART_FINE_PX = 9.0

_FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Faustina:wght@400..600&"
    "family=Public+Sans:wght@400;500;600&"
    "family=Spline+Sans+Mono:wght@400;500&display=swap');"
)

# Kept apart from the three above, and served only to the running app. An
# exported note is read offline and forwarded; it should not open a network
# request for a typeface it has no rule for. Two weights only: 300 carries
# every display line, 400 exists for the one place a display line sits at a
# working size and the light weight would go thin.
_SHELL_FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Newsreader:opsz,wght@6..72,300;6..72,400&display=swap');"
)

# Ten type steps and eight spacing stops. A raw rem inside a component rule
# is how the 31-size scale happened, so component rules reference these only.
# d0 exists for exactly one role, the opening headline, and is the only
# fluid step; the rest are flat so a rank is the same rank everywhere.
_SCALE = """
  --t-d0: clamp(2.6rem, 5.4vw, 4.4rem); --t-d0-lh: 0.98; --t-d0-ls: -0.038em;
  --t-d1: 2.6rem; --t-d1-lh: 1.04; --t-d1-ls: -0.034em;
  --t-d2: 1.75rem; --t-d2-lh: 1.08; --t-d2-ls: -0.028em;
  --t-h1: 1.3rem; --t-h1-lh: 1.22; --t-h1-ls: -0.018em;
  --t-h2: 1rem; --t-h2-lh: 1.3;
  --t-body: 0.875rem; --t-body-lh: 1.5;
  --t-read: 1rem; --t-read-lh: 1.68;
  --t-data: 0.8125rem; --t-data-lh: 1.4;
  --t-micro: 0.6875rem; --t-micro-lh: 1.3;
  --t-label: 0.625rem; --t-label-lh: 1.1; --t-label-ls: 0.14em;
  --s1: 4px; --s2: 8px; --s3: 12px; --s4: 16px;
  --s5: 24px; --s6: 32px; --s7: 48px; --s8: 72px;
  --rail: 9rem;
  --nav-h: 41px;
  --ease: cubic-bezier(.2,.6,.2,1);
"""


def _root() -> str:
    """Custom properties, generated from the constants above.

    Generated rather than written twice: the charts read the Python names
    and the stylesheet reads the CSS names, and a palette living in two
    places drifts.
    """
    pairs = {
        "ink": INK,
        "ink-soft": INK_SOFT,
        "ink-muted": INK_MUTED,
        "paper": PAPER,
        "surface": SURFACE,
        "rule": RULE,
        "rule-soft": RULE_SOFT,
        "accent": ACCENT,
        "accent-soft": ACCENT_SOFT,
        "accent-2": ACCENT_2,
        "neutral": NEUTRAL,
        "negative": NEGATIVE,
        "positive": POSITIVE,
        "caution": CAUTION,
        "display": FONT_DISPLAY,
        "sans": FONT_SANS,
        "mono": FONT_MONO,
    }
    declarations = " ".join(f"--{k}: {v};" for k, v in pairs.items())
    return ":root {" + declarations + _SCALE + "}"


# Rules describing the document. These travel with the exported file.
_DOCUMENT_CSS = """
*, *::before, *::after { box-sizing: border-box; }

/* --------------------------------------------------- browser surfaces */

/* The parts nobody draws still carry the design, and they ship with
   defaults belonging to no design system. */
::selection { background: var(--accent); color: #fff; }
/* This product has one palette and it is a light one. Say so to the
   browser, not just to the reader.

   Without this the user agent paints its own default ground from the
   operating system's preference before any stylesheet arrives, so a
   reader whose laptop is set to dark - which on a trading desk is most
   of them - met a near-black screen that flashed to marble as the app
   mounted. Reproduced in the browser pane with prefers-color-scheme
   dark: the page painted rgb(14, 17, 23) and then settled.

   It also fixes the parts no stylesheet reaches: the form controls,
   the scrollbar gutter and the overscroll band are drawn by the user
   agent, and on a dark preference it drew all three dark inside a
   document that is paper. Declared here rather than in the shell
   because the exported note is read on the same laptops. */
html { color-scheme: light; }
html { caret-color: var(--accent); scrollbar-color: var(--rule) transparent;
  scrollbar-width: thin; -webkit-text-size-adjust: 100%; }
::-webkit-scrollbar { width: 11px; height: 11px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--rule);
  border: 3px solid var(--paper); }
::-webkit-scrollbar-thumb:hover { background: var(--ink-muted); }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

/* Every figure here is compared down a column, so lining tabular figures
   are the document default rather than a per-table opt-in. */
body { font-variant-numeric: tabular-nums lining-nums;
  font-feature-settings: "tnum" 1, "lnum" 1; }

/* Visible to a screen reader, never to the eye. Used for the spoken form
   of an accounting negative and for the severity word on a status. */
/* A glossed token. The dotted rule is the only affordance saying there
   is something to hover; without it the tooltip exists and nobody finds
   it, which is the same as not having one. */
.ar-legend strong { font-family: var(--mono); font-weight: 500;
  color: var(--ink); }
abbr.ar-token { text-decoration: underline dotted var(--ink-muted);
  text-underline-offset: 3px; cursor: help; }

.ar-sr { position: absolute; width: 1px; height: 1px; padding: 0;
  margin: -1px; overflow: hidden; clip: rect(0 0 0 0);
  clip-path: inset(50%); white-space: nowrap; border: 0; }

/* A bypass link: offscreen until focused, which is the one pattern that
   serves a keyboard user without showing a control nobody else needs. */
/* `fixed`, not `absolute`, and clipped rather than flung off-screen.

   `position: absolute` resolves against the nearest positioned
   ancestor. This link is written by st.markdown, so it lives several
   Streamlit containers deep, and those containers routinely carry
   `position: relative`, `transform`, `filter`, `contain` or
   `overflow: hidden` - any one of which becomes the containing block.
   The focused link would then land 12px from THAT element's corner
   instead of the page's, or be clipped out of view entirely. This is
   the first control a keyboard user reaches in the whole product, so
   it is the worst possible thing to leave resolving against whatever
   the host framework happens to wrap it in this release.

   `fixed` always resolves against the viewport. And the hidden state
   is a 1px clipped box rather than `left: -9999px`, because an
   off-screen offset is itself defeated by a clipping ancestor, while
   `clip-path` is not - it is the same technique `.ar-sr` already uses
   for screen-reader-only text. */
.ar-skip { position: fixed; z-index: 100;
  left: var(--s3); top: var(--s3);
  width: 1px; height: 1px; overflow: hidden;
  clip-path: inset(50%); white-space: nowrap;
  background: var(--ink); color: var(--paper); padding: var(--s2) var(--s3);
  font-family: var(--sans); font-size: var(--t-label);
  letter-spacing: var(--t-label-ls); text-transform: uppercase;
  text-decoration: none; }
.ar-skip:focus {
  width: auto; height: auto; overflow: visible; clip-path: none; }

/* ---------------------------------------------------------- typography */

h1, h2, h3, h4 { font-family: var(--display); color: var(--ink);
  font-weight: 500; font-optical-sizing: auto; margin: 0; text-wrap: balance; }
h1 { font-size: var(--t-d1); line-height: var(--t-d1-lh);
  letter-spacing: var(--t-d1-ls); }
h2 { font-size: var(--t-h1); line-height: var(--t-h1-lh);
  letter-spacing: var(--t-h1-ls); }
h3 { font-size: var(--t-h2); line-height: var(--t-h2-lh); }

p, li { color: var(--ink-soft); font-size: var(--t-body);
  line-height: var(--t-body-lh); }
a, a:visited { color: var(--accent); text-decoration: underline;
  text-decoration-thickness: 1px; text-underline-offset: 0.18em;
  text-decoration-color: color-mix(in srgb, var(--accent) 38%, transparent);
  transition: text-decoration-color 120ms var(--ease); }
a:hover { text-decoration-color: var(--accent); }

/* The one label style. It was ten. */
.ar-sec-label, .ar-stat-label, .ar-col-label, .ar-pill,
table.ar-table thead th, .ar-status .tag, .ar-finding-grid .lbl,
/* The widget labels were the last text in the product still set in
   Streamlit's own voice: 14px sentence-case regular, directly above a
   button that is 10px uppercase tracked. One label style means this one
   too. */
/* Field labels in the shell's register: small, sentence case, quiet.
   Tracked uppercase belonged to the editorial world this replaced, and
   a label is read far more often than it is admired. */
.stTextInput label, .stTextArea label, .stSelectbox label {
  font-family: var(--sans); font-size: 12px; line-height: 1.4;
  letter-spacing: -.004em; font-weight: 500; text-transform: none;
  color: var(--shell-ink); }

/* ------------------------------------------------------------ masthead */

.ar-masthead { border-top: 2px solid var(--ink); padding-top: var(--s4);
  margin-bottom: var(--s5); display: grid;
  grid-template-columns: var(--rail) minmax(0, 1fr); column-gap: var(--s5); }
.ar-masthead .rail { font-family: var(--mono); font-size: var(--t-micro);
  line-height: var(--t-micro-lh); color: var(--ink-muted); }
.ar-title { font-family: var(--display); font-size: var(--t-d1);
  font-weight: 500; letter-spacing: var(--t-d1-ls);
  line-height: var(--t-d1-lh); color: var(--ink); margin: 0;
  display: flex; align-items: baseline; gap: var(--s3); flex-wrap: wrap; }
.ar-ticker { font-family: var(--mono); font-size: var(--t-micro);
  font-weight: 500; color: var(--surface); background: var(--ink);
  padding: 0.2em 0.5em; position: relative; top: -0.34em;
  letter-spacing: 0.04em; }
.ar-subline { font-size: var(--t-micro); line-height: var(--t-micro-lh);
  color: var(--ink-muted); margin-top: var(--s2); }
.ar-subline .sep { color: var(--rule); padding: 0 var(--s2); }

/* ---------------------------------------------------------- stat strip */

/* The figures are why the page exists, so after the company name they are
   the largest thing on it. `display: contents` drops labels, values and
   notes onto three shared grid rows, so they align across the strip
   without each cell reserving height for the tallest label. */
.ar-stats { display: grid; grid-auto-flow: column; grid-auto-columns: 1fr;
  grid-template-rows: auto auto auto; column-gap: var(--s5);
  border-top: 1px solid var(--ink); border-bottom: 1px solid var(--rule);
  padding: var(--s4) 0 var(--s5); margin: 0 0 var(--s6); align-items: start; }
.ar-stat { display: contents; }
.ar-stat-label { color: var(--ink-muted); }
/* Two ranks, not one. The strip set the traded price, the market multiple
   and the modelled value at identical size, so the only figure this
   product authored tied with four it was handed. */
.ar-stat-value { font-family: var(--sans); font-size: var(--t-h1);
  font-weight: 500; letter-spacing: var(--t-h1-ls);
  line-height: var(--t-h1-lh); color: var(--ink); margin-top: var(--s2);
  font-variant-numeric: tabular-nums lining-nums; }
.ar-stat.lead .ar-stat-value { font-size: var(--t-d2);
  letter-spacing: var(--t-d2-ls); line-height: var(--t-d2-lh); }
.ar-stat-value.pos { color: var(--positive); }
.ar-stat-value.neg { color: var(--negative); }
/* `.ar-stat.lead .ar-stat-value` is (0,3,0) and this was (0,2,0), so the
   lead rule won and a refusal rendered at 28px: on a REIT page the
   largest figure on the screen was the word NM, set bigger than the
   stock's own traded price. The intent was always that a non-figure
   recede. */
.ar-stat.lead .ar-stat-value.nm { font-size: var(--t-h2); letter-spacing: 0; }
.ar-stat-value.nm { color: var(--ink-muted); font-size: var(--t-h2);
  letter-spacing: 0; }
.ar-stat-note { font-size: var(--t-micro); line-height: var(--t-micro-lh);
  color: var(--ink-muted); margin-top: var(--s1); }

/* ------------------------------------------------------ section header */

/* The label sits in the rail; the rule runs the content column and fades
   toward the margin. One of only two gradients in this file, and it is
   structural rather than decorative. */
.ar-sec { display: grid; grid-template-columns: var(--rail) minmax(0, 1fr);
  column-gap: var(--s5); align-items: baseline;
  margin: var(--s8) 0 var(--s5);
  scroll-margin-top: calc(var(--nav-h) + var(--s3)); }
.ar-sec-label { color: var(--ink); }
.ar-sec-body { display: flex; align-items: center; gap: var(--s3); }
.ar-sec-rule { flex: 1; height: 1px;
  background: linear-gradient(90deg, var(--rule), transparent); }
.ar-sec-note { font-size: var(--t-micro); color: var(--ink-muted);
  white-space: nowrap; }

/* Content sits in the right-hand column, aligned under the section rule. */
.ar-block { display: grid; grid-template-columns: var(--rail) minmax(0, 1fr);
  column-gap: var(--s5); }
.ar-block > * { grid-column: 2; }

.ar-row { display: grid; grid-template-columns: 1fr 1fr; gap: var(--s5);
  align-items: start; }

.ar-caption { font-size: var(--t-micro); line-height: 1.5;
  color: var(--ink-muted); margin: 0 0 var(--s4); max-width: 68ch; }
.ar-foot { font-size: var(--t-micro); line-height: 1.5;
  color: var(--ink-muted); margin: var(--s2) 0 var(--s5); max-width: 80ch; }

/* -------------------------------------------------------------- tables */

/* Only a table that actually overflows becomes a scroll container.
   `overflow-x: auto` on every wrap also forces `overflow-y: auto`, which
   made the wrap the scrollport and meant a sticky table header left with
   the table instead of staying put. */
.ar-table-wrap { margin-bottom: var(--s2); }
.ar-table-wrap:has(> .ar-table-scroll) { overflow-x: auto;
  scrollbar-width: thin; }
/* ...and the header inside THAT wrapper cannot be sticky.

   This is the Peers defect, reported three times and never reproduced.

   The scoping above fixed seven tables and left the eighth. Overflow in
   one axis forces the other to `auto`, so the wrapper that scrolls
   horizontally is itself the nearest scrollport - and a wrapper sized to
   its own table has no vertical travel at all. A sticky header in there
   never unsticks and never scrolls. It simply parks at `top: var(--nav-h)`
   measured from the top of the TABLE instead of from the note's section
   bar, which is 41px down, permanently, on top of the first body row.

   On the comparables table the first body row is `tr.subject`: the
   company the whole note is about. Measured on the Realty Income note -
   the header's own row box at viewport y 40, its cells painting at 81,
   over the subject row at 70-101. All a reader ever saw of Realty
   Income's own figures was the few pixels sticking out above its own
   column header. That is the "Peer table is still fucked up".

   The same declaration already existed for the narrow-viewport case,
   where every wrapper becomes a scrollport for the same reason. It
   belongs here too, and for exactly the same reason. */
.ar-table-wrap:has(> .ar-table-scroll) table.ar-table thead th {
  position: static; }
table.ar-table { width: 100%; border-collapse: collapse;
  font-size: var(--t-data); line-height: var(--t-data-lh);
  background: var(--surface); }
table.ar-table thead th { color: var(--ink-muted); text-align: left;
  padding: var(--s2) var(--s3) var(--s1); vertical-align: bottom;
  border-top: 1px solid var(--ink); border-bottom: 1px solid var(--rule);
  white-space: nowrap; background: var(--surface);
  position: sticky; top: var(--nav-h); z-index: 2; }
table.ar-table thead th.num { text-align: right; }
table.ar-table tbody td { padding: 6px var(--s3);
  border-bottom: 1px solid var(--rule-soft); color: var(--ink-soft);
  vertical-align: top; }
table.ar-table tbody td.num { text-align: right; font-family: var(--mono);
  color: var(--ink); white-space: nowrap; }
table.ar-table tbody td.key { color: var(--ink); font-weight: 500;
  min-width: 8.5rem; }
table.ar-table tbody td.nm { color: var(--ink-muted); }
table.ar-table tbody tr:last-child td { border-bottom: 1px solid var(--rule); }
table.ar-table tbody tr:hover td {
  background: color-mix(in srgb, var(--accent) 4%, transparent); }

table.ar-table tbody tr.subject td { background: var(--accent-soft);
  color: var(--ink); font-weight: 500;
  border-bottom: 1px solid color-mix(in srgb, var(--accent) 24%, transparent); }
table.ar-table tbody tr.subject:hover td { background: var(--accent-soft); }
table.ar-table tbody tr.spacer td { height: var(--s2); padding: 0;
  border-bottom: none; background: var(--paper); }
table.ar-table tbody tr.spacer:hover td { background: var(--paper); }
table.ar-table tbody tr.summary td { border-bottom: none;
  color: var(--ink-muted); }
table.ar-table tbody tr.summary.first td { border-top: 1px solid var(--rule); }
table.ar-table tbody tr.summary td.num { color: var(--ink); }
table.ar-table tbody tr.total td { border-top: 1px solid var(--ink);
  border-bottom: none; color: var(--ink); font-weight: 500; }
table.ar-table td.wide { min-width: 17rem; white-space: normal;
  font-size: var(--t-micro); line-height: 1.45; }

table.ar-table.ar-table-scroll { width: auto; min-width: 100%; }
table.ar-table.ar-table-scroll td, table.ar-table.ar-table-scroll th {
  white-space: nowrap; }
table.ar-table.ar-table-scroll td.wide { white-space: normal;
  max-width: 20rem; }

table.ar-table td.heat { font-family: var(--mono); text-align: right;
  color: var(--ink); }
table.ar-table th.rowhead, table.ar-table td.rowhead {
  font-family: var(--mono); font-size: var(--t-micro); color: var(--ink);
  background: var(--surface); font-weight: 400; text-align: left; }

/* The financial summary. Section headings span the table, subtotals are
   ruled above, and derived rows are lighter, because a figure this project
   computed must not look like one the company filed. */
table.ar-statement tbody tr.statement-section td {
  font-family: var(--sans); font-size: var(--t-label);
  letter-spacing: var(--t-label-ls); font-weight: 600;
  text-transform: uppercase; color: var(--ink-muted);
  padding: var(--s5) var(--s3) var(--s1);
  border-bottom: 1px solid var(--rule); }
table.ar-statement tbody tr.statement-section:first-child td {
  padding-top: var(--s1); }
table.ar-statement tbody tr.statement-section:hover td { background: none; }
table.ar-statement tbody tr.statement-section .unit { text-transform: none;
  letter-spacing: 0; color: var(--ink-muted); font-weight: 400;
  font-size: var(--t-micro); float: right; }
table.ar-statement tbody tr.statement-subtotal td {
  border-top: 1px solid var(--rule); color: var(--ink); font-weight: 500; }
table.ar-statement tbody tr.statement-subtotal td.rowhead { font-weight: 600; }
table.ar-statement tbody tr.statement-derived td { color: var(--ink-muted);
  border-bottom: none; }
table.ar-statement tbody tr.statement-derived td.rowhead {
  color: var(--ink-muted); padding-left: var(--s5); }
table.ar-statement tbody tr.statement-line td { border-bottom: none; }
table.ar-statement tbody td.rowhead,
table.ar-statement tbody th.rowhead { white-space: nowrap; }
/* The subject row sets its own colour at (0,2,4) and beat the muting
   rule at (0,2,3), so in the one row about the company being analysed an
   NM rendered identically to a filed figure. */
table.ar-table tbody tr.subject td.nm {
  color: var(--ink-muted); font-weight: 400; }

/* ---------------------------------------------------------- summary */

/* Directly under the headline figures, which is the most valuable space on
   the page. It used to hold three provenance notices: how many citations
   resolved, how far the model sits from the market, how old the filing is.
   All true, none of it analysis. */
.ar-summary { max-width: 72ch; margin: 0 0 var(--s7);
  border-left: 1px solid var(--accent); padding-left: var(--s4); }
.ar-summary p { font-size: var(--t-read); line-height: 1.58;
  color: var(--ink); margin: 0 0 var(--s3); }
.ar-summary p:first-child { font-size: var(--t-h2); line-height: 1.45;
  color: var(--ink); }
.ar-summary p:last-child { margin-bottom: 0; font-size: var(--t-micro);
  line-height: 1.45; color: var(--ink-muted); }

/* The provenance chips beside the company name, each a jump to the note
   at the foot that carries the full wording. */
.ar-chips { display: flex; gap: var(--s2); flex-wrap: wrap;
  margin-top: var(--s3); }
.ar-chips a { font-family: var(--sans); font-size: var(--t-label);
  letter-spacing: var(--t-label-ls); text-transform: uppercase;
  font-weight: 600; text-decoration: none; color: var(--ink-muted);
  border: 1px solid var(--rule); padding: 0.25em 0.5em;
  transition: color 120ms var(--ease), border-color 120ms var(--ease); }
.ar-chips a:hover { color: var(--ink); border-color: var(--ink); }
.ar-chips a.ok { color: var(--positive); border-color: var(--positive); }
.ar-chips a.warn { color: var(--caution); border-color: var(--caution); }
/* Filled, not outlined. A failed-verification chip was the same 10px
   box at the same border weight as the neutral filing-date chip beside
   it, so the one signal worth stopping for read as metadata. */
.ar-chips a.bad { color: var(--paper); background: var(--negative);
  border-color: var(--negative); }
.ar-chips a.bad:hover { color: var(--paper); }

/* ---------------------------------------------------------- status bar */

.ar-status { border-left: 1px solid var(--rule); padding: 0 0 0 var(--s3);
  margin: 0 0 var(--s5); font-size: var(--t-body);
  line-height: var(--t-body-lh); color: var(--ink-soft); max-width: 82ch; }
.ar-status .tag { display: block; margin-bottom: var(--s1); }
.ar-status.ok { border-left-color: var(--positive); }
.ar-status.ok .tag { color: var(--positive); }
.ar-status.warn { border-left-color: var(--caution); }
.ar-status.warn .tag { color: var(--caution); }
/* A divergence is the finding this section exists for; a corroboration
   is context. They carried the same hairline and differed only in the
   colour of a 10px pill. */
.ar-finding.diverge { border-left: 2px solid var(--negative);
  padding-left: var(--s3); }
/* The 3px edge is the status LEVEL, carried without colour: a
   warning and an error keep their meaning in greyscale and under
   forced colours, where the tint does not. The design detector reads
   a thick coloured side border as the standard AI-UI tell, which it
   usually is; here it is the accessibility affordance, so it is
   waived where it lives rather than globally. */
.ar-status.warn { border-left-width: 3px; } /* impeccable-disable-line side-tab */
.ar-status.bad { border-left-color: var(--negative); border-left-width: 3px; } /* impeccable-disable-line side-tab */
.ar-status.bad .tag { color: var(--negative); }
.ar-status.info .tag { color: var(--ink-muted); }

/* ---------------------------------------------------------- two-column */

.ar-split { display: grid; grid-template-columns: 1fr 1fr;
  border-top: 1px solid var(--rule); margin-bottom: var(--s5); }
.ar-split > div { padding: var(--s4) var(--s5) var(--s4) 0; }
.ar-split > div + div { border-left: 1px solid var(--rule);
  padding-left: var(--s5); padding-right: 0; }
.ar-col-label { margin-bottom: var(--s2); color: var(--ink-muted); }
.ar-col-label.bull { color: var(--positive); }
.ar-col-label.bear { color: var(--negative); }
/* Sienna is the market throughout: the prevailing view, the traded price. */
.ar-col-label.street { color: var(--accent-2); }
.ar-col-label.ours { color: var(--accent); }
.ar-split p { margin: 0; }

/* ------------------------------------------------------------ findings */

.ar-finding { border-top: 1px solid var(--rule);
  padding: var(--s4) 0 var(--s2); }
.ar-finding-head { display: flex; align-items: center; gap: var(--s2);
  margin-bottom: var(--s3); }
.ar-pill { padding: 0.25em 0.5em; border: 1px solid; }
.ar-pill.diverge { color: var(--negative); border-color: var(--negative); }
.ar-pill.agree { color: var(--positive); border-color: var(--positive); }
.ar-pill.mat { color: var(--ink-muted); border-color: var(--rule); }
.ar-finding-grid { display: grid; grid-template-columns: 1fr 1fr;
  gap: var(--s5); margin-bottom: var(--s3); }
.ar-finding-grid .lbl { color: var(--ink-muted); margin-bottom: var(--s1); }
.ar-finding-grid p { margin: 0; }
/* The assessment is the finding; the quoted claim and the filed figure
   above it are the evidence. This set the evidence larger than the
   verdict, and put the verdict last. */
.ar-assess { font-size: var(--t-read); line-height: var(--t-read-lh);
  color: var(--ink); border-left: 1px solid var(--accent);
  padding-left: var(--s3); }

/* ---------------------------------------------------------- prose body */

/* The one place the document breathes. The contrast between the dense
   instrument and this single readable column is the design argument. */
.ar-prose { max-width: 66ch; font-size: var(--t-read);
  line-height: var(--t-read-lh); color: var(--ink-soft); }
.ar-prose h2 { font-size: var(--t-h1); margin: var(--s7) 0 var(--s3); }
.ar-prose h3 { font-size: var(--t-h2); margin: var(--s5) 0 var(--s2); }
.ar-prose p, .ar-prose li { font-size: var(--t-read);
  line-height: var(--t-read-lh); margin: 0 0 var(--s4); }
.ar-prose strong { color: var(--ink); font-weight: 600; }
/* Citation markers: raised and small, set in the figure face because that
   is what they point at. */
.ar-prose a { font-family: var(--mono); font-size: 0.72em; font-weight: 500;
  vertical-align: 0.3em; text-decoration: none; padding: 0 0.1em; }
.ar-prose a:hover { background: var(--accent-soft); }

/* ----------------------------------------------------------- section bar */

/* Stuck to the top of the viewport, because the need to jump arises deep in
   the scroll, which is exactly where a list that only exists at the top of
   the page is useless. Scrolls horizontally on a narrow screen rather than
   wrapping to three lines and eating the viewport. */
/* Streamlit wraps every markdown block in two divs whose height is the
   block's own, so a sticky child has zero travel and scrolls away. These
   two are dissolved so the nav's containing block is the scrollport. */
[data-testid="stElementContainer"]:has(nav.ar-nav),
[data-testid="stMarkdownContainer"]:has(> nav.ar-nav) { display: contents; }

.ar-nav { position: sticky; top: 0; z-index: 40; display: flex;
  gap: var(--s4); overflow-x: auto; scrollbar-width: none;
  background: var(--paper); border-top: 1px solid var(--rule);
  border-bottom: 1px solid var(--ink); margin: 0 0 var(--s7);
  padding: var(--s3) var(--s6) var(--s3) 0;
  /* Seventeen sections overflow the measure at any realistic width. The
     mask says so: without it the last label was cut mid-word and 600px of
     navigation was invisible and unsignalled. */
  /* #000 here is an alpha stop, not a palette colour: a mask reads
     luminance, so black means opaque and transparent means cut. */
  /* impeccable-disable-next-line design-system-color -- mask alpha stop, not a palette colour */
  mask-image: linear-gradient(90deg, #000 calc(100% - 44px), transparent);
  -webkit-mask-image: linear-gradient(90deg, #000 calc(100% - 44px), transparent); }
.ar-nav::-webkit-scrollbar { display: none; }
/* 24px minimum target height. These measured 15px and 23px. */
.ar-nav a { min-height: 24px; display: inline-flex; align-items: center; }
.ar-chips a { min-height: 24px; display: inline-flex; align-items: center; }
.ar-nav a { font-family: var(--sans); font-size: var(--t-label);
  line-height: var(--t-label-lh); letter-spacing: var(--t-label-ls);
  font-weight: 600; text-transform: uppercase; color: var(--ink-muted);
  text-decoration: none; white-space: nowrap;
  border-bottom: 2px solid transparent; padding-bottom: 2px;
  transition: color 120ms var(--ease), border-color 120ms var(--ease); }
.ar-nav a:hover { color: var(--ink); border-bottom-color: var(--accent); }
/* The section the reader jumped to stays marked while they read it. */
.ar-sec:target .ar-sec-label { color: var(--accent); }

/* -------------------------------------------------------------- charts */

.ar-figure { margin: 0 0 var(--s4); }
.ar-figure svg { display: block; width: 100%; height: auto; overflow: visible; }
.ar-figure figcaption { font-size: var(--t-micro); line-height: 1.45;
  color: var(--ink-muted); margin-top: var(--s2); max-width: 68ch; }

/* -------------------------------------------------------------- motion */

/* One authored moment: the document settles in once on first paint. Not a
   blanket entrance on every section, which reads as a template playing an
   animation at the reader. */
@media (prefers-reduced-motion: no-preference) {
  .ar-masthead { animation: ar-settle 560ms var(--ease) both; }
  .ar-stats { animation: ar-settle 560ms var(--ease) 120ms both; }
  /* Two phases. The first is the time estimate, and stops short of
     full because the run is not measured. The second creeps for
     another four minutes, so a slow run - a cold EDGAR cache, a
     retried provider call - does not sit at a frozen near-full bar,
     which is the hung-process impression the bar exists to prevent,
     arriving later. It never reaches the end, because it does not
     know where the end is. */
  .ar-progress i {
    animation: ar-fill 300s cubic-bezier(.2,.7,.3,1) both,
      ar-creep 300s linear 300s both; }

  /* A press with no acknowledgement, followed by a rerun most of a second
     later, reads as a button that did not work. These are the product's
     two most consequential clicks. */
  .stButton > button:active, .stDownloadButton > button:active,
  .stFormSubmitButton > button:active {
    transform: translateY(1px); transition-duration: 40ms; }

  /* Reading position across a document that measures over ten thousand
     pixels. Scroll-driven, so it costs no script, and where the timeline
     is unsupported the rule simply does nothing. */
  /* No `position: relative` here. It was added to give the bar below a
     containing block and it silently overrode `position: sticky` at line
     466, because it is later in the sheet at equal specificity. The
     result was a twenty-section document with no navigation at all once
     you were past the first screen. A sticky element is already a
     positioned element, so the containing block was never missing. */
  .ar-nav::after { content: ""; position: absolute; left: 0; bottom: -1px;
    height: 2px; width: 100%; background: var(--accent);
    transform-origin: 0 50%; transform: scaleX(0);
    animation: ar-fill-full linear both;
    animation-timeline: scroll(root block); }

  table.ar-table tbody tr:hover td {
    transition: background-color 90ms var(--ease); }
  /* A 0.72em superscript is a small target; it should answer precisely. */
  .ar-prose a { padding: 0 0.25em;
    transition: background-color 120ms var(--ease); }
}
@keyframes ar-fill { from { transform: scaleX(0) } to { transform: scaleX(.9) } }
@keyframes ar-creep { from { transform: scaleX(.9) } to { transform: scaleX(.99) } }
@keyframes ar-fill-full { from { transform: scaleX(0) } to { transform: scaleX(1) } }
@keyframes ar-settle {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: none; }
}

/* ---------------------------------------------------------- responsive */

@media (max-width: 900px) {
  .ar-masthead, .ar-sec, .ar-block { grid-template-columns: 1fr; }
  .ar-masthead .rail { margin-bottom: var(--s2); }
  .ar-block > * { grid-column: 1; }
  .ar-stats { grid-auto-flow: row; grid-template-rows: none;
    grid-template-columns: 1fr 1fr; row-gap: var(--s4); }
  .ar-stat { display: block; }
  .ar-split, .ar-finding-grid, .ar-row { grid-template-columns: 1fr; }
  .ar-split > div + div { border-left: none; padding-left: 0;
    border-top: 1px solid var(--rule); }
  .ar-title { font-size: var(--t-d2); }
  /* A nowrap section note measured 359px inside a 390px viewport and
     pushed the entire document into horizontal scroll. */
  .ar-sec-note { white-space: normal; }
  /* Reflow. `td.key` at 8.5rem, `td.wide` at 17rem and nowrap figures set
     a min-content floor of roughly 866px, so a 390px viewport required
     scrolling in two directions, and so did 400% zoom. The floors exist
     to stop labels wrapping mid-phrase on a wide screen; at this width a
     wrapped label is the lesser cost. */
  table.ar-table td.key, table.ar-table th.rowhead { min-width: 0; }
  /* The min-widths were relaxed but this was not, and the row labels are
     what set the floor: "Depreciation and amortisation" refusing to wrap
     kept the statement table at 581px inside a 390px viewport, clipping
     the two most recent periods. */
  table.ar-statement tbody td.rowhead,
  table.ar-statement tbody th.rowhead { white-space: normal; }
  table.ar-table td.wide { min-width: 0; white-space: normal; }
  .ar-table-wrap { overflow-x: auto; }
  table.ar-table thead th { position: static; }
}
"""


# Rules that exist only to tame the Streamlit shell. A standalone export has
# no Streamlit in it, so shipping these put dead selectors into the file a
# reader actually forwards.
_APP_CSS = """
/* The shell's page is the shell's colour.

   This painted `html` and `body` with --paper and --ink, which are the
   DOCUMENT's tokens: the note's warm cream and its warm near-black. A
   later rule repainted `.stApp` with the shell ground, so the mismatch
   only showed where .stApp does not reach - the overscroll band at the
   top and bottom of a rubber-band scroll, and any gap around the app
   container. With the old near-white shell the two were a point apart
   and nobody could see it. Against the marble ground it is the note's
   paper appearing in the chrome, which is the one thing the two-surface
   split exists to prevent.

   Measured: body was rgb(250, 248, 243) while .stApp was
   rgb(244, 246, 249), on the same screen. */
html, body, .stApp, [data-testid="stAppViewContainer"] {
  background: var(--shell-bg); color: var(--shell-ink); }
/* The document stylesheet states the heading face as `h1, h2, h3, h4`,
   which is specificity (0,0,1). Streamlit's own emotion rules reach the
   same elements as class-plus-element, (0,1,1), and win: in the running
   app every bare heading rendered in Streamlit's "Source Sans" while the
   exported file, which carries no Streamlit CSS, rendered Faustina
   correctly. The whole typographic argument was shipping only in the
   export. `.ar-title` escaped this by being a class, which is why the
   masthead looked right and the home hero did not.

   Restated here at (0,1,1) so it ties with Streamlit's rule and wins on
   source order, this stylesheet being injected after theirs. This block
   lives in the app stylesheet rather than the document one because it
   exists solely to answer Streamlit; the exported file needs none of it
   and should not carry it. */
[data-testid="stAppViewContainer"] h1, [data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3, [data-testid="stAppViewContainer"] h4,
[data-testid="stAppViewContainer"] .ar-prose h1,
[data-testid="stAppViewContainer"] .ar-prose h2 {
  font-family: var(--display); font-weight: 500; color: var(--ink); }
[data-testid="stAppViewContainer"] p, [data-testid="stAppViewContainer"] li {
  font-family: var(--sans); }
/* A section label is an `h2` so that twenty sections expose twenty
   headings rather than three, but it is set as a label, not as a display
   heading. The restatement above reaches it at (0,1,1), so the label face
   has to be restated here above that. */
[data-testid="stAppViewContainer"] h2.ar-sec-label {
  font-family: var(--sans); font-size: var(--t-label);
  line-height: var(--t-label-lh); letter-spacing: var(--t-label-ls);
  font-weight: 600; text-transform: uppercase; }
/* Figures stay monospaced; the sans restatement above must not reach them. */
[data-testid="stAppViewContainer"] .ar-ticker,
[data-testid="stAppViewContainer"] .ar-masthead .rail,
[data-testid="stAppViewContainer"] table.ar-table td.num,
[data-testid="stAppViewContainer"] table.ar-table td.heat {
  font-family: var(--mono); }

.stApp, [data-testid="stAppViewContainer"] { font-family: var(--sans);
  font-size: var(--t-body); line-height: var(--t-body-lh);
  -webkit-font-smoothing: antialiased; }

/* Streamlit's header is a floating toolbar with a hamburger and a
   running-man icon. It is emptied rather than removed: the button that
   reopens a collapsed sidebar lives inside it, and hiding the toolbar left
   the sidebar unrecoverable once closed. */
header[data-testid="stHeader"] { background: transparent; }
/* The deploy button survived the testid rule on this build, so it is
   hidden by its own wrapper too. It offers a reader a Streamlit action
   that has nothing to do with the product. */
[data-testid="stAppDeployButton"], .stAppDeployButton,
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stToolbarActions"], [data-testid="stAppDeployButton"],
[data-testid="stMainMenu"], [data-testid="stMainMenuButton"],
[data-testid="stStatusWidget"],
/* Streamlit's own "Made with Streamlit" footer, hidden by tag - which
   also hid OURS the moment the shell grew a real one, silently and
   with `!important`, so the closing band rendered into the page and
   computed to display:none. Scoped to everything that is not ours.
   A footer is the right element for a page's ending, so the answer is
   to narrow the rule rather than to downgrade the landmark to a div. */
#MainMenu, footer:not(.ar-close) { display: none !important; }

/* Streamlit appends an anchor to every heading it renders, shown on hover.
   On a heading inside our own markup it points at a fragment that does not
   exist, so a link to nowhere sat beside the title. */
[data-testid="stHeaderActionElements"] { display: none !important; }

button[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"] button {
  background: var(--surface); border: 1px solid var(--rule);
  border-radius: 0; color: var(--ink-muted); box-shadow: none;
  transition: color 120ms var(--ease), background-color 120ms var(--ease),
    border-color 120ms var(--ease); }
button[data-testid="stExpandSidebarButton"]:hover,
[data-testid="stSidebarCollapseButton"] button:hover {
  background: var(--ink); color: var(--paper); border-color: var(--ink); }

/* ===================================================== application shell

   The shell executes the category canon at the Linear/Stripe craft bar,
   recorded as a standing commitment in PRODUCT.md. Near-white ground,
   hairline borders, one spacing scale, monospace figures, and colour
   withheld everywhere except the divergence count.

   It replaces a layout that measured, on one screen, four container
   max-widths and three centre axes - because `text-align: center` was
   applied to blocks carrying a max-width and no auto margin, so each
   block centred inside its own box instead of on the page. The rule
   below is the whole fix: ONE column, declared once, inherited by
   everything. No descendant sets its own width.

   Widths are whole pixels, never `ch`. A `ch` resolves against a
   proportional face and produced 394.017px, 528.62px and 630.59px -
   three edges no two blocks could ever share. */

:root {
  /* The Broadsheet. A cold marble ground rather than the near-white that
     stood here, which was neutral to the point of committing to nothing -
     the exact fault the redesign exists to fix. Cold is also what makes
     the note's warm paper read as a second surface the moment it opens.
     Generated names stay in Python (SHELL_BG, SHELL_ACCENT) so a palette
     does not live in two places. */
  --shell-bg: #f4f6f9;
  --shell-panel: #ffffff;
  /* The shell's display face, declared here and not in `:root`, because
     `:root` travels with every exported note. */
  --shell-display: 'Newsreader', 'Faustina', Georgia, serif;
  --shell-ink: #15161a;
  --shell-soft: #50535c;
  /* 4.91:1 on the ground and 5.04:1 on a panel. The comp's own muted
     tone was #8b8e98, which measures 3.19:1 and fails WCAG 2.2 AA for
     normal text - and this token carries the intro line, every helper
     caption, the table headers and the step numbers. Darkened until it
     passes with margin while staying plainly subordinate to
     --shell-soft at 7.5:1. */
  --shell-mute: #6b6f78;
  --shell-line: #eceef1;      /* inside a panel */
  --shell-line-2: #e2e4e9;    /* panel edge, decorative */
  /* A control's boundary is information, not decoration: WCAG 2.2
     SC 1.4.11 wants 3:1 for the edge that identifies a field. The panel
     hairline measures 1.27:1 on white, which is right for a card and
     wrong for an input. This is 3.27:1. */
  --shell-field-line: #8b8e98;
  /* A control's edge, held to SC 1.4.11's 3:1 like a field's. The
     secondary buttons - Back, Start a report, Download this note -
     were drawn with the panel hairline, which measured 1.47:1 against
     the ground in dark and about 1.1:1 in light, so a button was
     identifiable as a control almost entirely by its text. The
     hairline is right for the edge of a card and wrong for the edge
     of something you press; this is the same tone as the field
     boundary, for the same reason. */
  --shell-btn-line: #8b8e98;
  /* The one focus colour, declared once.

     This was #4f46e5, which is Tailwind's indigo-600 to the digit - the
     most-cited fingerprint of a generated interface, sitting on the focus
     ring of every control in a product whose whole argument is that a
     person made it carefully. That alone was reason to replace it.

     The comment that stood here claimed 8.2:1 on the page and 4.4:1 on
     the bypass link's near-black pill. Measured, it was 5.81:1 and
     2.88:1 - and 2.88:1 FAILS the 3:1 that WCAG 2.2 asks of a focus
     indicator. The figure that justified the colour was never true.

     This one measures 4.77:1 on the marble ground, 5.17:1 on a panel and
     3.50:1 on the ink pill, so the ring is visible everywhere it is
     drawn. It is deliberately a step brighter than --shell-accent: a ring
     is a state and has to carry at a 2px stroke, while the accent is a
     signal set in text. Same hue family, two jobs, neither borrowed from
     the other. */
  --shell-focus: #2563eb;
  /* The one accent, and the whole of the shell's colour. It is on the
     divergence count and on a link, and on nothing else: an accent that
     appears twice is decoration, and appearing once it reads as switched
     on. Measured 9.47:1 on the marble ground and 10.25:1 on a panel. */
  --shell-accent: #1b3a8f;
  --shell-sink: #f7f9fb;      /* table head */
  /* A row under the pointer. The index rows carry no underline and no
     link colour by design, so this is the only pointer-level signal
     that a row opens something - and it was painted --shell-sink,
     which against the table's own fill measures 1.04:1 in dark. The
     affordance did not exist on the scheme where it was the only
     one. */
  --shell-row-hover: #eef0f4;
  /* Three radii, and the mark is one of them. The two product marks
     were drawn at 4px in the bar and 6px on the gate - the same object
     at two shapes, forty pixels apart on the only screen that shows
     both in sequence. */
  --shell-r-sm: 5px;
  --shell-r: 7px;
  --shell-r-lg: 10px;
  --shell-shadow: 0 1px 2px rgba(18, 20, 26, .04);
  /* Four colours used to sit inline in the rules below, where a
     change of scheme could not reach them - the primary button's
     label was literally `#fff`, which on a dark scheme's light fill
     is the one control a reader is meant to press, unreadable. */
  --shell-on-ink: #ffffff;    /* the label on an ink-filled control */
  --shell-ink-hover: #26272d;
  --shell-chip: #f4f5f7;      /* the inline code chip */
  --shell-hover: #f7f8f9;     /* a secondary control, pressed on */
  --shell-hover-line: #d6d9df;
  --shell-col: 1120px;        /* the one column */
  --shell-gut: 28px;
}

.stApp, [data-testid="stAppViewContainer"] { background: var(--shell-bg); }

.block-container {
  max-width: var(--shell-col);
  padding: 26px var(--shell-gut) 64px;
  margin-inline: auto; }

/* The report view needs every pixel a sixteen-column table asks for. */
.block-container:has(.ar-report-view) { max-width: 1280px; }

/* A form gets a narrower column, because a text field stretched to the
   full page is unpleasant to type into and a label sitting a thousand
   pixels from its input is hard to associate with it. This narrows the
   ONE column rather than adding a second width inside it: every element
   on the screen still shares one set of edges. */
.block-container:has(.ar-form-head) { max-width: 760px; }

/* ----------------------------------------------------- shell furniture */

/* A NEAR-BLACK BAND, not a hairline on marble.
   The page was one flat field from the first pixel to the last, so it
   began nowhere and ended nowhere - which is most of what made it read
   as a form rather than as a publication. A dark bookend at the top and
   another at the foot bound the light field between them and give the
   whole page an edge to start from. The rest of the shell keeps its
   marble; the ink is the frame, not a theme. */
.ar-topbar {
  display: flex; align-items: center; gap: 24px;
  height: 56px;
  /* FULL BLEED, past the column's own edges.
     The band is the window's frame, not the column's: a dark strip
     that stops where the text column stops reads as a wide heading
     inside the page rather than as the top of the application. The
     negative inline margin reaches the viewport edge and the padding
     puts the mark back on the column's left edge, so the type still
     aligns with everything below it. Measured for overflow afterwards,
     because `50vw` includes the scrollbar's width and this is the
     usual way a page acquires a horizontal one. */
  margin: -26px calc(50% - 50vw) 32px;
  padding: 0 calc(50vw - 50% + var(--shell-gut));
  background: var(--shell-ink);
  color: var(--shell-on-ink);
  /* The pale 22% rule that a dark field needs: a neutral hairline is
     invisible on ink, and no edge at all lets the band bleed into the
     page under it. */
  border-bottom: .5px solid rgba(255, 255, 255, .22); }
.ar-topbar .brand {
  display: flex; align-items: center; gap: 9px;
  font-size: 13.5px; font-weight: 600; letter-spacing: -.012em;
  color: var(--shell-on-ink); }
.ar-topbar .brand i {
  width: 15px; height: 15px; border-radius: 0;
  background: var(--shell-on-ink); display: block; }


/* The eyebrow. Uppercase, tracked, small, and the only uppercase in
   the shell - which is what makes it read as a label rather than as
   another heading competing with the one under it. */
.ar-brow {
  font-family: var(--sans); font-size: 11px; font-weight: 500;
  letter-spacing: .14em; text-transform: uppercase;
  color: var(--shell-mute); margin-bottom: 9px; }

/* The closing bookend. Full-bleed ink, the same device as the top bar,
   so the light page is held between two dark edges instead of fading
   out into its own bottom padding. */
.ar-close {
  display: flex; align-items: flex-start; gap: 48px;
  margin: 72px calc(50% - 50vw) -64px;
  padding: 40px calc(50vw - 50% + var(--shell-gut)) 44px;
  background: var(--shell-ink); color: rgba(255, 255, 255, .62);
  border-top: .5px solid rgba(255, 255, 255, .22); }
.ar-close .mark {
  display: flex; align-items: center; gap: 9px; flex: 0 0 auto;
  font-family: var(--sans); font-size: 13px; font-weight: 600;
  letter-spacing: -.012em; color: var(--shell-on-ink); }
.ar-close .mark i {
  width: 15px; height: 15px; background: var(--shell-on-ink);
  display: block; }
.ar-close .said { max-width: 620px; }
.ar-close .said p {
  margin: 0 0 7px; font-family: var(--sans); font-size: 12px;
  line-height: 1.6; color: rgba(255, 255, 255, .62); }
.ar-close .said p:last-child { margin-bottom: 0; }

/* The chassis rails: the column's own edges, drawn.
   Every rule on the page ran horizontally, so the content column was
   implied by alignment alone and nothing on screen said where it
   began or ended. Two 0.5px verticals say it, and they are structure
   rather than decoration - the same reason the rows between reports
   are hairlines and not boxes. */
.block-container {
  border-inline: .5px solid var(--shell-line-2); }

/* The line at the head of the download menu. Inside a popover, which
   is the shell, so it reads from the shell's tokens. */
.ar-dl-note {
  margin: 0 0 10px; font-family: var(--sans); font-size: 12px;
  line-height: 1.45; color: var(--shell-mute); max-width: 232px; }

/* Section rhythm, declared once.
   Streamlit puts every `write` in its own element container with its own
   vertical gap, so a margin-bottom here ADDED to that gap and a missing
   margin-top left none at all. The result on the home screen was a
   heading sitting flush on the table above it and a canyon between that
   heading and its own card - the two complaints were one bug.
   The separation now belongs to the TOP of a section head, which is the
   edge that actually divides two sections, and the gap to the head's own
   body is the container's. */
.ar-head { margin: 40px 0 2px; }
/* The screen's opening statement is the first thing on the page and has
   nothing above it to be separated from. */
/* Left, not centred. The line here was the only centred thing on a
   screen where everything else - the steps, the button, the index -
   starts at the column's left edge, which is the two-centre-axes fault
   by another route: a reader's eye is given one start point for one
   sentence and a different one for the rest of the page. It now shares
   the column's edge with everything under it. */
.ar-head.ar-open { margin-top: 0; margin-bottom: 8px; }
/* The single-report screen's title line: the document's name, and the
   marker that says whether it shipped with the tool. Baseline-aligned
   rather than stacked, because they are one statement. */
.ar-head.ar-report-head {
  /* The first thing under the bar on this screen, so it is separated
     from the bar rather than from a section above it - 40px of section
     rhythm here left a band of dead page between the chrome and the
     document's own name. */
  margin-top: 14px;
  display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
/* The screen's title takes the section rank, not a size of its own.

   It was pinned to 17px, which was right when every heading was 15px
   sans - it read as one step up. Against the display serif it reads as
   the serif used small, and the rule this direction rests on is that
   the serif appears at display sizes only: below those it stops being
   chrome and starts impersonating the document sitting underneath it,
   which is the one thing the two surfaces must not do.

   At the section rank it is the same size as "Get started" and
   "Reports", which is correct - it is the same kind of thing, the name
   of what is on the screen. The SAMPLE tag still baseline-aligns
   beside it, because they are one statement. */
.ar-head.ar-report-head h1 { font-size: 26px !important; }
.ar-tag {
  font-family: var(--mono); font-size: 10px; letter-spacing: .08em;
  text-transform: uppercase; color: var(--shell-mute);
  border: 1px solid var(--shell-line); border-radius: 999px;
  padding: 2px 8px; line-height: 1.6; }
/* THE BROADSHEET - the shell's display voice.

   What stood here set every heading on every screen in the sans at 15px
   weight 600. There was no display level at all: a section head and a
   line of body copy were two sizes of the same voice, which is the
   mechanical form of "commits to no idea".

   The serif is the commitment. It is held at 300 - the whisper weight -
   because the inversion is the whole point: every competitor in this
   category shouts in bold sans, and a light serif is the one move that
   reads as composure rather than volume. At 400 it is a magazine; at 600
   it is the thing it is arguing against.

   It appears at display sizes only. A serif at a working size stops
   being chrome and starts being a document, and the note next door is
   the document. Below this, everything is the sans.

   Two display ranks, and nothing between them. A rank that exists once
   is a rank a reader cannot learn. `font-synthesis-weight: none` is
   load-bearing rather than tidy: if Newsreader fails to arrive the
   browser must fall back to a real Faustina or Georgia, not smear a
   synthetic 300 out of a 400, which is how a light serif turns muddy on
   exactly the screen that is meant to carry the idea. */
.ar-head h1, .ar-head h2 {
  font-family: var(--shell-display) !important; font-size: 26px !important;
  font-weight: 300 !important; letter-spacing: -.012em !important;
  line-height: 1.22 !important; color: var(--shell-ink); margin: 0;
  font-optical-sizing: auto; font-synthesis-weight: none; }

/* The screen's opening line. The one display moment in the product, and
   the only place the serif is allowed to be large. */
.ar-head.ar-open h1, .ar-head.ar-open h2 {
  font-size: clamp(34px, 4.6vw, 46px) !important;
  line-height: 1.08 !important; letter-spacing: -.02em !important; }
.ar-head p {
  font-size: 12.5px; color: var(--shell-mute); margin: 3px 0 0;
  line-height: 1.5; }
/* The screen's opening statement, which carries no heading above it
   because the bar already names the project. It is the first thing read,
   so it is set at reading size in the primary tone rather than as a
   caption. */
.ar-head p.lead {
  /* 560px, not 62ch. A `ch` resolves against a proportional face and
     lands on a fraction - this one measured 531.067px - which is the
     exact defect the one-column rule exists to prevent, reintroduced
     by the person who wrote the rule. Widths in the shell are whole
     pixels on the grid. */
  font-size: 14px; color: var(--shell-soft); max-width: 560px;
  margin-top: 0; }

/* THE ONE DISPLAY MOMENT.

   The screen's opening statement. It was a 14px caption floating in the
   middle of an otherwise empty band, so the first thing a reader met
   was a line of helper text - and the product's display rank existed in
   the stylesheet with nothing in the markup using it, because home's
   only h1 is screen-reader-only by design (the topbar already carries
   the name, and drawing it twice is what made the old screen look
   unedited).

   So the lead itself takes the display rank. It is not a slogan and
   must never become one: it is the plain instruction for what this
   screen is for, set at the size of a statement instead of the size of
   an apology. That is the whole move - the same honest words, given the
   typographic weight the page was refusing them. */
.ar-head.ar-open p.lead {
  font-family: var(--shell-display);
  font-weight: 300;
  font-size: clamp(30px, 3.9vw, 42px);
  line-height: 1.1;
  letter-spacing: -.02em;
  color: var(--shell-ink);
  /* Wide enough that the sentence does not break, narrow enough that a
     longer one would wrap before the column edge rather than running
     the full 1120px, which no display line should. */
  max-width: 720px;
  margin: 2px 0 0;
  font-optical-sizing: auto;
  font-synthesis-weight: none;
  /* A display line that drops one word onto its own row looks like an
     accident at exactly the moment the page is making its case. */
  text-wrap: balance; }

.ar-card {
  background: var(--shell-panel); border: 1px solid var(--shell-line-2);
  border-radius: var(--shell-r-lg); box-shadow: var(--shell-shadow);
  overflow: hidden; }
.ar-card + .ar-card { margin-top: 16px; }
.ar-card .pad { padding: 14px; }

.ar-lbl {
  font-size: 11px; letter-spacing: .04em; text-transform: uppercase;
  color: var(--shell-mute); margin-bottom: 9px; }

/* The reports table. Figures are monospace and right-aligned so a
   column of them reads as a column. */
/* The index is an index, not a panel.

   This sat inside a card - hairline border, white fill, radius - which
   is the shape a generated interface reaches for by default. Every
   research index worth copying (OpenAI, Anthropic, Runway, Cartesia)
   does the same thing instead: rows on the page itself, separated by
   one hairline, with the metadata muted beside the name. The rules
   between the rows already group them; a box around the group is a
   second grouping of the same thing.

   Taking the fill away also does something the box was hiding. On the
   marble ground the figures are the only white-adjacent thing left on
   the lower half of the screen, so the eye lands on the data rather
   than on the container holding it. The column head keeps a fill, but
   it is not what distinguishes it: --shell-sink is #f7f9fb against a
   #f4f6f9 ground, which is 1.026:1 and not a perceptible surface. What
   actually marks that row as a different KIND of row is its 11px
   tracked mute type and the rule under it. The fill is kept as the
   faintest possible settling rather than as the distinction, and an
   earlier version of this comment claimed otherwise - it is a
   candidate for deletion on the owner's call, not on mine.

   The rows stay interactive - a row is still one link - so this does
   not cost the affordance. Hover and the focus ring both paint the
   whole row, and both are tested. */
table.ar-list { width: 100%; border-collapse: collapse;
  border-top: 1px solid var(--shell-line-2); }
/* Horizontal rules only, which is the convention every published
   research table follows and the one the note's own tables already use.

   These were not ours. Streamlit paints a 1px border on every side of
   every cell in a markdown table - rgba(21, 22, 26, .1), a colour that
   appears nowhere in this palette - and the sheet had only ever set
   `border-bottom`, so the vertical rules survived untouched. The index
   read as a spreadsheet grid, and the lines doing it belonged to the
   host framework rather than to the design. Declared explicitly in both
   directions, because a default you did not write is still a default
   you are shipping. */
table.ar-list th, table.ar-list td {
  border-left: 0; border-right: 0; }

/* The same leak, on a screen where it matters more.

   A sample note renders inside its own iframe, which Streamlit's CSS
   cannot reach. A note you have just generated is written INLINE into
   the page instead - so on that screen, and only on that screen, every
   cell of all twelve of the document's tables picked up the host's side
   borders. The identical document rendered two different ways depending
   on which door the reader came through, and the one that looked wrong
   was the one they had just paid five minutes and a dollar for.

   The override lives here rather than in the document rules on purpose:
   the exported file carries no Streamlit, so a document-side rule would
   be dead weight travelling with every download. */
[data-testid="stMarkdown"] table.ar-table th,
[data-testid="stMarkdown"] table.ar-table td {
  border-left: 0; border-right: 0; }
table.ar-list th {
  text-align: left; font-size: 11px; font-weight: 500;
  color: var(--shell-mute); letter-spacing: .03em;
  padding: 9px 16px; background: var(--shell-sink);
  border-bottom: 1px solid var(--shell-line); }
table.ar-list td {
  padding: 11px 16px; border-bottom: 1px solid var(--shell-line);
  font-size: 13px; color: var(--shell-ink); }

/* A row is a link made of four cell-filling links. Each anchor fills
   its own cell's padding box, so the whole row is a hit target with no
   dead strip between cells, and the padding moves from the cell to the
   anchor to make that true. Colour and underline are inherited from
   the cell so the table looks like a table rather than like four
   columns of blue. The hover and focus states are on the row, because
   that is the object the reader is pointing at - and the focus ring is
   drawn with an outline offset inward, since an outline on a table
   cell is otherwise clipped by the card's own edge. */
/* The row link is an overlay: it fills its cell and carries no text,
   so the figures stay in the cell where a screen reader can read
   them. An earlier version wrapped the text and hid six anchors from
   the accessibility tree to get the row to one tab stop, which hid
   the figures with them.

   Filling the cell is what makes the row a target with no dead
   strip - a table stretches its cells to the row's height, and a
   block inside one takes only its own content, which left 21px of a
   62px row dead at the width where a company name wraps. `inset: 0`
   on an absolutely positioned child of a positioned cell needs no
   percentage height to resolve. */
table.ar-list td { position: relative; padding: 11px 16px; }
/* `color: inherit`, because this anchor never declared one and so wore
   Streamlit's: #0054a3, on all forty-two of them. It does not show
   today - the anchors are overlays with the row's text outside them, so
   there is no glyph to paint - but an undeclared colour is a host
   default we are shipping, and it becomes visible the moment one of
   these carries text, or in a forced-colours mode that honours it. The
   same host blue is already documented two hundred lines below as what
   broke the bypass link's contrast. */
a.ar-row-link { position: absolute; inset: 0; color: inherit; }
table.ar-list tr:hover td { background: var(--shell-row-hover); }
/* The focus ring spans the ROW, which is what the row is.

   It did not. Only the first anchor in each row is focusable - the
   other six carry tabindex="-1" - and `inset: 0` resolves against that
   anchor's own cell, so the ring was a box around the Ticker cell.
   Measured in the running page: 81px of outline on a 968px row, eight
   per cent of the thing it was meant to indicate. The comment here
   claimed "hover and the focus ring both paint the whole row, and both
   are tested"; the tint did, the ring never had.

   On a row that is one link, a ring around one of its seven cells does
   not say "this row is focused", it says "this cell is selected" -
   which is a different and wrong statement about what Enter will do.

   Drawn as inset shadows on the cells instead of an outline on the
   anchor: top and bottom on every cell, and the two end caps on the
   first and last, so the four edges close into one rectangle around the
   whole row. */
table.ar-list tr:has(a.ar-row-link:focus-visible) td {
  background: var(--shell-row-hover);
  box-shadow: inset 0 2px 0 0 var(--shell-focus),
              inset 0 -2px 0 0 var(--shell-focus); }
table.ar-list tr:has(a.ar-row-link:focus-visible) td:first-child {
  box-shadow: inset 0 2px 0 0 var(--shell-focus),
              inset 0 -2px 0 0 var(--shell-focus),
              inset 2px 0 0 0 var(--shell-focus); }
table.ar-list tr:has(a.ar-row-link:focus-visible) td:last-child {
  box-shadow: inset 0 2px 0 0 var(--shell-focus),
              inset 0 -2px 0 0 var(--shell-focus),
              inset -2px 0 0 0 var(--shell-focus); }
a.ar-row-link:focus-visible { outline: none; }
/* Except under forced colours, where the row-wide ring does not exist.
   Both channels carrying it are ones the user agent takes away: it
   forces `box-shadow` to none and overrides `background-color`, while
   `outline` survives. So switching the outline off above left a
   keyboard user in Windows High Contrast Mode with no focus indicator
   on the index at all - SC 2.4.7 and SC 1.4.11 failing outright, where
   before this change a forced-colour outline was at least drawn around
   the focused cell. The ring is one cell wide here rather than one row,
   because `inset: 0` resolves against the anchor's own cell and inset
   shadows are exactly what this mode removes; a visible indicator on
   the right row beats a correct one that is not painted.
   `Highlight` is the system colour, so it is whatever the reader's own
   scheme uses for selection rather than anything of ours. */
@media (forced-colors: active) {
  a.ar-row-link:focus-visible {
    outline: 3px solid Highlight; outline-offset: -3px; }
}
/* The headline finding: a figure and the question it answers, in one
   cell. The figure leads because it is what gets scanned; the label
   under it is what makes the figure mean anything, and it is set small
   and back so a column of them does not compete with the figures in
   the mono columns beside it. */
table.ar-list td.find b {
  display: block; font-family: var(--mono); font-size: 13px;
  font-weight: 500; font-feature-settings: "tnum" 1, "lnum" 1;
  color: var(--shell-ink); letter-spacing: -.01em; }
table.ar-list td.find span {
  display: block; margin-top: 1px; font-size: 11.5px; line-height: 1.3;
  color: var(--shell-mute); }

table.ar-list td.co { color: var(--shell-soft); }
table.ar-list td.tk { font-weight: 600; letter-spacing: -.01em; }
/* Filed and Cited are context rather than the figure a reader came
   for, so they are set a step back. They are still figures, so they
   keep the mono face and the right edge. */
table.ar-list td.dim { color: var(--shell-mute); }
/* A figure does not wrap. At tablet width the Filed column broke
   "2026-08-05" across two lines, which makes a date look like two
   numbers and adds a line's height to every row in the table. */
table.ar-list th.num, table.ar-list td.num { white-space: nowrap; }
table.ar-list th.num, table.ar-list td.num {
  text-align: right; font-family: var(--mono); font-size: 12.5px;
  font-feature-settings: "tnum" 1, "lnum" 1; }

/* The divergence pill (`.ar-count`) was removed with it. It was the
   shell's one coloured device, and it lost its only caller when the
   home table dropped the Divergences column - the count does not exist
   outside a rendered note, so the column was a header promising data
   the product could not supply. A device with no use is not a device,
   and leaving its rules behind would let a later surface pick up a
   colour convention nothing documents. Colour in the shell is now the
   focus ring alone; the note keeps its own semantic palette. */

.ar-kv {
  display: flex; justify-content: space-between; gap: 16px;
  padding: 7px 0; font-size: 12.5px; color: var(--shell-soft); }
.ar-kv + .ar-kv { border-top: 1px solid var(--shell-line); }
.ar-kv b {
  color: var(--shell-ink); font-weight: 500; font-family: var(--mono);
  font-size: 12px; font-feature-settings: "tnum" 1; }

/* Numbered steps. Get Started is instructions, so it is a list of
   actions and not a row of marketing claims. */
/* Four steps across, not four stacked. They lived in a rail beside
   the table; the table now takes the full measure and the
   instructions sit under it, where a stacked list would be a thin
   column of text under a wide one. Across, each step is a short
   paragraph in its own band and the whole thing is four lines deep
   instead of sixteen. */
/* No card around this. It had one - a hairline border, a white fill and
   a radius - and the card failed its own test: take the border, fill
   and radius away and nothing about the four steps becomes harder to
   read or to act on, because the rules BETWEEN the columns already do
   the grouping. A container that groups things the content already
   groups is the most common decoration in generated interfaces, and on
   this page it was also what made the steps read as a widget sitting on
   the page rather than as part of it.

   What replaces it is one hairline along the top, which is the
   structural move the reference material uses for exactly this: a
   column group announced by a rule, not boxed by a border. */
.ar-steps {
  counter-reset: step; display: grid; gap: 0;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border-top: 1px solid var(--shell-line-2);
  padding-top: 18px; margin-top: 14px;
  list-style: none; }
/* The host out-specifies the line above.
   Streamlit ships `.st-emotion-cache-… > ul, … > ol { display: block;
   width: fit-content }` - a child combinator on a class, (0,2,0),
   against `.ar-steps` at (0,1,0). So the moment these steps became a
   real `ol` for screen readers, the host collapsed the four columns
   into a stacked, indented list. The semantics fix broke the layout,
   which is the whole reason this is verified in the browser and not in
   the stylesheet.
   Declared with `!important` rather than by escalating the selector,
   because the emotion class is a build hash and any selector written
   against it is wrong at the next Streamlit release. */
ol.ar-steps {
  display: grid !important; width: auto !important;
  list-style: none !important; }
/* ...and the same fight one level down, which the first pass missed.
   The host styles the ITEMS too - `margin-left: 1.15rem`,
   `padding-left: .3rem`, `margin-block: .2rem` - and out-specifies
   `.ar-step` at (0,1,0). Measured after the ol was fixed: the ol's box
   started at x 28 with the lead, both section heads and the index, and
   all four steps sat at 46.4 inside it, so the first step's prose began
   at 51.2 - 23px right of every other left edge on the page, which is
   the one commitment this direction rests on. `.ar-step`'s own
   `padding: 2px 20px 2px 0` was discarded wholesale with it: computed
   padding-top and padding-right were both 0.
   No `!important` here. `ol.ar-steps > li.ar-step` is (0,2,2), which
   clears the host on specificity alone - verified by injecting exactly
   this rule into the running page and re-measuring, and it is the form
   the phone rules below have to take for the same reason. */
ol.ar-steps > li.ar-step {
  margin: 0; padding: 2px 20px 2px 0; }
ol.ar-steps > li.ar-step + li.ar-step { padding-left: 20px; }
.ar-step {
  display: grid; grid-template-rows: auto 1fr; gap: 7px;
  align-content: start; padding: 2px 20px 2px 0; }
.ar-step + .ar-step {
  border-top: 0; border-left: 1px solid var(--shell-line);
  padding-left: 20px; }
.ar-step:before {
  counter-increment: step; content: counter(step, decimal-leading-zero);
  font-family: var(--mono); font-size: 11px; color: var(--shell-mute); }
.ar-step .t { font-size: 13px; color: var(--shell-ink); line-height: 1.5; }
.ar-step .t span { color: var(--shell-soft); }
/* The chip ends its line. Padding on an inline element puts visible
   space between it and whatever follows, so a comma or a full stop
   after one reads as a typo - "AAPL , say". Keep punctuation off its
   right-hand side rather than fighting the box model. */
.ar-step code {
  font-family: var(--mono); font-size: 12px;
  background: var(--shell-chip);
  border-radius: var(--shell-r-sm); padding: 1px 5px;
  color: var(--shell-ink); }

.ar-empty {
  padding: 28px 16px; text-align: center; color: var(--shell-mute);
  font-size: 12.5px; line-height: 1.6; }

/* The run's current stage, inside the live region that announces it. */
.ar-stage {
  font-size: 13px; color: var(--shell-ink); margin: 0 0 8px; }

/* ------------------------------------------------------------- the gate

   One screen with one field. Everything on it - the mark, the title,
   the line, the field and the button - is a child of one 320px column
   that is itself centred, so there is a single centre line and nothing
   can drift off it. The previous gate centred each block inside its own
   max-width box and produced three. */
/* The gate is the first thing anyone sees, and it was the last screen
   still speaking in the old voice: the product's name set in the sans at
   17px semibold, which is the size of a form label rather than of an
   introduction.

   Centred here, and that is not the fault the home screen had. Home was
   one centred sentence above a column of left-aligned content, so the
   eye was given two different places to start. The gate holds exactly
   one object and nothing to align against, which is the case where a
   centre axis is the only sensible one.

   The 128px top pad put the whole object in the upper third and left a
   dead band under it taller than the object itself. It sits on a true
   vertical centre now, so the space above and below is the same space
   and reads as composition rather than as content that ran out. */
.block-container:has(.ar-gate) {
  max-width: 320px;
  padding-top: 0;
  min-height: 100svh;
  display: flex; flex-direction: column;
  /* `safe`, and it is load-bearing.
     Plain `center` splits any overflow evenly above and below, and the
     half above the top of a scroll container cannot be reached, because
     scrollTop does not go negative. Found by shrinking the window until
     the gate plus its error message was taller than the viewport: at
     380x260 the product mark sat at top -12 with scrollTop already 0,
     cut off with no way to scroll to it. `safe` falls back to
     flex-start at exactly the point where centring would start hiding
     something. */
  justify-content: safe center;
  /* Above dead centre by a little. An object centred exactly looks low,
     because the eye reads the optical centre as higher than the
     geometric one. */
  padding-bottom: 9vh; }
/* Streamlit's vertical block grows to fill its parent, so centring the
   container alone moved nothing: the child filled the height and its
   own content stayed at the top of it. Measured - container flex,
   justify-content centre, height 982, and the gate still painting at
   the top. The child has to stop growing before the centring means
   anything. */
.block-container:has(.ar-gate) > div,
.block-container:has(.ar-gate) [data-testid="stVerticalBlock"] {
  flex: 0 0 auto; }
.ar-gate { text-align: center; margin-bottom: 20px; }
.ar-gate .brand i {
  width: 22px; height: 22px; border-radius: var(--shell-r-sm);
  display: inline-block;
  background: var(--shell-ink); margin-bottom: 18px; }
/* The name, in the voice the rest of the product now speaks in. */
.ar-gate h1 {
  font-family: var(--shell-display) !important; font-size: 32px !important;
  font-weight: 300 !important; letter-spacing: -.02em !important;
  line-height: 1.12 !important;
  color: var(--shell-ink); margin: 0 !important;
  font-optical-sizing: auto; font-synthesis-weight: none; }
.ar-gate p {
  font-size: 12.5px; color: var(--shell-mute); margin: 7px 0 0; }
.block-container:has(.ar-gate) [data-testid="stForm"] {
  border: 0; padding: 0; }
/* Streamlit's own `label_visibility="collapsed"` hides this, and it
   sets `aria-label` on the input from the same text - verified in the
   accessibility tree of the running app, which reads
   `textbox "Passphrase"`. So the field is named, and this rule only
   has to not fight the hiding.

   An audit reported the field as having no accessible name but the
   placeholder, and a visually-hidden replacement was written for it.
   That replacement was inert: it set position and clip and never set
   `display`, so Streamlit's `display: none` still won, and it left a
   rule in the sheet that did nothing. Checked rather than assumed,
   and reverted. */
.block-container:has(.ar-gate) .stTextInput label { display: none; }

/* ------------------------------------------------------------- sidebar */

[data-testid="stSidebar"] { background: var(--surface);
  border-right: 1px solid var(--rule); }
[data-testid="stSidebar"] > div:first-child { padding-top: var(--s5); }
[data-testid="stSidebarContent"] { padding: 0 var(--s5); }
[data-testid="stSidebar"] label {
  font-family: var(--sans) !important; font-size: var(--t-label) !important;
  line-height: var(--t-label-lh) !important;
  letter-spacing: var(--t-label-ls) !important; text-transform: uppercase;
  color: var(--ink-muted) !important; font-weight: 600 !important; }
[data-testid="stSidebar"] p, [data-testid="stCaptionContainer"] p {
  font-size: var(--t-micro); line-height: 1.45; color: var(--ink-muted); }

/* ------------------------------------------------------------ controls */

/* Addressed by test id, because the `[data-baseweb="select"]` rule that
   stood here styled nothing: this build emits no such attribute. It was
   the only place the control's face and size were declared, so the
   Strategy field was the one input on the form still set in Streamlit's
   own type - on the screen where a reader decides whether this is
   built. */
[data-testid="stSelectbox"] div[role="combobox"] {
  font-family: var(--sans); font-size: 13px; background: var(--shell-panel);
  border: 1px solid var(--shell-field-line); border-radius: var(--shell-r);
  color: var(--shell-ink); box-shadow: none;
  transition: border-color 120ms var(--ease); }
/* The select and the radio get the same ring as every other control.
   Without a rule naming them, the ring falls through to the global
   focus style, which Streamlit's own `outline: none` out-specifies for
   widget internals - the mechanism this file documents twice already. */
[data-testid="stSelectbox"] div[role="combobox"]:focus-visible,
[data-testid="stSelectbox"] div[role="combobox"]:focus-within,
[data-testid="stRadio"] input:focus-visible + div,
[data-testid="stRadio"] label:focus-within {
  outline: 2px solid var(--shell-focus) !important; outline-offset: 2px;
  border-radius: var(--shell-r-sm); }
.stTextInput input, .stTextArea textarea {
  font-family: var(--sans); font-size: 13px; color: var(--shell-ink);
  box-shadow: none; }
.stTextInput input { font-family: var(--mono); font-size: 12.5px; }
/* The ring is on the wrapper, because that is where the visible border
   is; `outline: none` on the inner input beat the global focus-visible
   rule and left keyboard users with no indication at all. */
/* The Baseweb focus rule that stood here addressed nothing in this
   build; the live one is on the root element further down. */
.stTextInput input::placeholder, .stTextArea textarea::placeholder {
  color: var(--ink-muted); opacity: 1; }

/* Streamlit wraps a button's label in its own <p>, and the document's
   global paragraph colour then won against the button's: the primary
   action rendered #403c33 on #17150f, about 1.8:1, which is invisible.
   Every control's descendants inherit the control's colour instead. */
.stButton > button *, .stDownloadButton > button *,
.stFormSubmitButton > button *,
[data-testid="stExpander"] summary *, .stTabs [data-baseweb="tab"] * {
  color: inherit; }

/* Sentence case, not uppercase tracked: a tracked-caps button is the
   editorial world this shell replaced, and at 11px it is measurably
   slower to read than the label it encodes. Full width within its own
   column, so two buttons in a row are the same size - they measured
   166px and 155px with a 167px gap between them, because each was
   centring inside its own host column rather than sharing a row. */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  font-family: var(--sans); font-size: 13px; letter-spacing: -.005em;
  /* SQUARE. A rounded rectangle is the default shape of every
     framework's button and reads as one; an unrounded action reads as
     something that was set rather than dropped in, and it is the same
     corner the rules, the table and the two dark bands already use.
     The radius is the single most recognisable fingerprint of a
     generated interface, and this shell was wearing it on its one
     most-looked-at control. */
  text-transform: none; font-weight: 500; border-radius: 0;
  border: 1px solid var(--shell-ink); background: var(--shell-ink);
  color: var(--shell-on-ink); width: 100%; min-height: 40px;
  padding: 0 20px;
  /* No lift either. A shadow under a flat-field button is depth the
     page does not otherwise have. */
  box-shadow: none;
  transition: background-color 120ms var(--ease),
    border-color 120ms var(--ease), color 120ms var(--ease); }
.stButton > button:hover, .stFormSubmitButton > button:hover {
  background: var(--shell-ink-hover);
  border-color: var(--shell-ink-hover); }
.stDownloadButton > button, .stButton > button[kind="secondary"] {
  background: var(--shell-panel); color: var(--shell-ink);
  border-color: var(--shell-btn-line); box-shadow: none; }
.stDownloadButton > button:hover,
.stButton > button[kind="secondary"]:hover {
  background: var(--shell-hover);
  border-color: var(--shell-hover-line);
  color: var(--shell-ink); }
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible,
.stFormSubmitButton > button:focus-visible {
  outline: 2px solid var(--shell-focus); outline-offset: 2px; }

/* A field's label, in our colours rather than Streamlit's.

   This was never claimed, so it was never wrong in the light scheme -
   Streamlit's static theme paints a dark warm grey, which passes on
   white. On a dark ground the same colour measured 1.76:1, which is
   every field label on the form screen. A static config has one scheme
   and cannot follow the system, so the label has to be ours. */
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label {
  color: var(--shell-soft); font-size: 13px; font-weight: 500; }
/* The options beside a radio, which are labels by another name. */
.stRadio [data-testid="stWidgetLabel"] p,
.stRadio label p { color: var(--shell-ink); }

/* A row of buttons shares one row and splits it evenly. */
[data-testid="stHorizontalBlock"] { gap: 10px; }
[data-testid="stColumn"] { min-width: 0; }

/* `st.status` renders as an expander, not as its own element: there is no
   `stStatus` test id in this Streamlit build, and the rules that targeted
   one styled nothing. The progress surface a reader watches for the whole
   ninety seconds of a run was therefore the only unthemed surface in the
   product, carrying Streamlit's 8px radius and default sans while every
   other edge here is square. Confirmed against the shipped assets, which
   expose stExpander, stExpanderDetails and stExpanderIcon{,Check,Error,
   Spinner} and no stStatus. */
/* Streamlit puts the form container in the tab order and then removes
   its outline, so a keyboard user landed on an invisible stop. If it is
   focusable it has to show focus. */
[data-testid="stVerticalBlock"]:focus-visible,
section:focus-visible, div[class*="block-container"]:focus-visible {
  outline: 2px solid var(--shell-focus); outline-offset: 2px; }

/* Streamlit's own anchor rules out-specify `.ar-skip`, so in the app the
   bypass link rendered #0054a3 on its near-black pill, 2.43:1, with its
   focus ring suppressed: the first control a keyboard user meets was
   invisible and close to unreadable. The export, whose shell we write, is
   unaffected. */
/* The status block, when it renders in the SHELL rather than the note.

   `.ar-status` is a document component - it carries the note's own
   warnings - so it is declared in the document rules, in document
   tokens. But the shell renders it too: the gate's "Refused" and "Slow
   down" messages and the workspace's failure panel are all this
   component, sitting on the cold marble ground wearing the note's warm
   cream-world neutrals.

   Only the NEUTRALS are remapped. The severity hues stay exactly as
   they are: negative, caution and positive are semantic, they mean the
   same thing on both surfaces, and they were measured for contrast on
   both (the error tone computes about 7.9:1 on marble). Remapping those
   would be inventing a second vocabulary for one meaning.

   The `:not()` chain matters: the severity classes set the border
   colour themselves, and a blanket override here would win on source
   order and erase the one thing the border is for. */
/* Keyed on `.ar-status-shell`, which only `ui.shell_status` emits.
   It was `[data-testid="stMarkdown"] .ar-status`, and that was wrong:
   the note rendered inline on the live report screen goes through the
   same `st.markdown` call, so the rule repainted all five of the
   DOCUMENT's own status blocks in shell tokens - measured rgb(80, 83,
   92) inline against rgb(64, 60, 51) in the iframe and the export. The
   same document, two renderings, which is what the host's table
   borders were fixed for one commit earlier. No container distinguishes
   the two, so the surface is named at the call site instead. */
.ar-status-shell { color: var(--shell-soft); }
.ar-status-shell:not(.ok):not(.warn):not(.bad) {
  border-left-color: var(--shell-line-2); }

/* Shell tokens, not document ones. The contrast was never the problem
   here - cream on near-black is fine - but this is the shell, and it
   was painting a control in --paper and --ink, which are the note's
   warm cream and warm near-black. Found by listing every colour the
   rendered shell actually paints: #faf8f3 came back as a TEXT colour,
   and this link was the only thing using it. Same leak as the one that
   had html and body wearing the document's ground, and the same fix.

   A palette is only declared in one place if everything reads from it. */
.ar-skip, .ar-skip:visited, .ar-skip:hover, .ar-skip:active {
  background: var(--shell-ink) !important;
  color: var(--shell-on-ink) !important; text-decoration: none !important; }
/* The ring draws OUTSIDE the link's dark pill, on the page, so the page
   is what it has to be seen against. It was `var(--paper)` - #faf8f3,
   the ground of the editorial world this shell replaced - which
   measures 1.04:1 on the new #fcfcfd page: invisible, on the first
   control a keyboard user reaches in the whole product. The focus
   colour every other control uses is visible against both the near-
   black pill and the near-white page. */
.ar-skip:focus-visible {
  outline: 2px solid var(--shell-focus) !important; outline-offset: 2px; }

/* The earlier rule here was `section:focus-visible`, (0,1,1), which loses
   to Streamlit's emotion rule setting `outline: none`. Only the
   outline-offset landed, which is the tell. The main container is a
   full-viewport tab stop, so without this a keyboard user lands on a
   silent invisible stop covering the whole page. Negative offset keeps
   the ring inside the viewport. */
section.stMain:focus-visible, [data-testid="stMain"]:focus-visible {
  /* --shell-focus, not --accent. This was the one control in the shell
     painting its ring in the DOCUMENT's slate (#1d5a86) while every
     other control - buttons, fields, selects, row links, the shell nav,
     the bypass link - used #2563eb. Not a contrast failure: the slate
     measures 6.87:1 on the marble ground, well past the 3:1 SC 1.4.11
     asks. It is a consistency failure, and a second focus hue that
     appears exactly once is a hue a reader cannot learn. */
  outline: 2px solid var(--shell-focus) !important; outline-offset: -2px; }

[data-testid="stExpander"] { background: var(--surface);
  border: 1px solid var(--rule); border-radius: 0; box-shadow: none; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] p,
[data-testid="stExpanderDetails"] p {
  font-family: var(--mono); font-size: var(--t-micro); color: var(--ink-soft);
  letter-spacing: 0; text-transform: none; }

/* The run blocks the script for about ninety seconds, and the stage lines
   all land in the first five of them: a working system read as a hung one.
   A determinate bar is honest here only because the status block mounts
   once per run and is replaced on completion, so the animation cannot
   replay. It stops short of the end because the duration is an estimate,
   and a bar that reaches 100% while the work continues is a lie. */
.ar-progress { height: 2px; background: var(--rule); margin-top: var(--s2); }
.ar-progress i { display: block; height: 100%; background: var(--accent);
  transform-origin: 0 50%; transform: scaleX(0); }

/* The fill animates only under `prefers-reduced-motion: no-preference`,
   so a reader who asks for reduced motion kept `scaleX(0)` for the whole
   ninety-second run: the one surface saying the system is working was a
   flat line. They get a static partial fill instead - no movement, but
   the bar is visibly a bar in progress rather than an empty track. */
@media (prefers-reduced-motion: reduce) {
  .ar-progress i { transform: scaleX(0.35); }
}

/* `st.divider` renders a plain `hr`, which the element selector already
   reaches. The test-id companions that used to sit beside these two rules
   (stDecoration, stDivider, stVerticalBlockBorderWrapper) are not emitted
   by this Streamlit build at all and styled nothing; tests/
   test_theme_selectors.py now fails on any such rule rather than letting
   it rot here. */
hr { border-color: var(--rule); margin: var(--s5) 0; }
[data-testid="stAlert"] { border-radius: 0; }


/* --------------------------------------------------------------- home */

/* The proposition, set at the one deliberate extreme in the type scale and
   given the viewport to itself. No pillar grid, no hero image, no badge:
   the sentence is the argument. */
/* The `1fr` row here used to hold nothing: the button is a Streamlit
   element rendered outside this container, so the row was pure filler and
   left a 214px hole between the lede and the only control on the screen,
   which reads as a bug rather than as breathing room. */
/* The form sits at a measure, not at the window's width. A ticker field
   stretched across 1200px of a wide screen is the look of a layout with
   nothing in it, which is what the empty second column used to be. */
/* Streamlit's input wrapper, at rest. The inner `input` was themed and
   the wrapper was not, so a white 8px-rounded box sat around a square
   cream field on cream paper, with the reveal toggle in a second rounded
   chip beside it. On the gate screen that is the one element saying
   "Streamlit app", forty pixels from the headline. */
/* Controls, addressed by the hooks this Streamlit build actually emits.

   Every `[data-baseweb="..."]` rule that stood here was dead: this
   build renders react-aria widgets and the page contains zero elements
   carrying a `data-baseweb` attribute. They were inherited from a
   Streamlit that did use Baseweb, and they had been "styling" the form
   for some time while the browser applied none of them.

   The consequence was not cosmetic. Streamlit's own default gives the
   field root a 1px WHITE border on a white fill, so a text input had no
   visible boundary at all, and the focus ring written for
   `[data-baseweb="input"]:focus-within` never applied to anything - a
   keyboard reader had no indication of which field held focus.

   A control's boundary is information rather than decoration, so it is
   held to WCAG 2.2 SC 1.4.11 at 3:1 rather than to the hairline used
   for a card edge, which is 1.27:1 and right for a card. */
[data-testid="stTextInputRootElement"],
[data-testid="stTextAreaRootElement"],
[data-testid="stSelectbox"] div[role="combobox"],
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
  background: var(--shell-panel) !important;
  border: 1px solid var(--shell-field-line) !important;
  border-radius: var(--shell-r) !important;
  box-shadow: none !important; }

[data-testid="stTextInputRootElement"] input,
[data-testid="stTextAreaRootElement"] textarea {
  background: transparent; border: 0; color: var(--shell-ink); }

/* The ring goes on the root, which is where the visible border is. */
[data-testid="stTextInputRootElement"]:focus-within,
[data-testid="stTextAreaRootElement"]:focus-within {
  border-color: var(--shell-focus) !important;
  outline: 2px solid var(--shell-focus); outline-offset: 1px; }

/* The reveal toggle is a second tab stop inside the field's own box, so
   the field's :focus-within ring sits in the same place and does not
   move when focus does. It gets a ring of its own. */
[data-testid="stTextInputRootElement"] button {
  background: transparent; border: 0; color: var(--shell-mute); }
[data-testid="stTextInputRootElement"] button:focus-visible {
  outline: 2px solid var(--shell-focus); outline-offset: -2px;
  border-radius: var(--shell-r-sm); }

/* A pull quote in the written guide, set as print sets one. */
.ar-prose blockquote { margin: var(--s4) 0; padding-left: var(--s4);
  border-left: 2px solid var(--rule); }
.ar-prose blockquote p { font-family: var(--display); font-size: var(--t-read);
  line-height: var(--t-read-lh); color: var(--ink); margin: 0; }
.ar-prose code { font-family: var(--mono); font-size: 0.88em;
  background: var(--surface); padding: 0.1em 0.3em; }

/* Streamlit's "Press Enter to apply" hint. It renders half inside the
   field and half under the reveal toggle, and it explains a convention
   nobody needs explaining. */
[data-testid="InputInstructions"] { display: none !important; }

/* Also removed with it: `.ar-about`, `.ar-doors`, `.ar-claims` and
   `.ar-workspace` rules. No Python module emits any of those classes,
   so they styled nothing - and a dead rule in a stylesheet is worse
   than no rule, because the next surface inherits it by accident.

/* The editorial shell that stood here is gone: `.ar-about` (its page
   is deleted), `.ar-home`, `.ar-gate` and `.ar-workspace-intro` display
   rules, the three-column `.ar-claims` row, and a block of `max-width`
   declarations on controls.

   Those max-widths are the measured defect. `34rem` on a button, on
   every input and on every caption, plus `15ch` on a heading and `54ch`
   on a lede, is five independent widths inside one column - and `ch`
   resolves against a proportional face, which is where 394.017px,
   528.62px and 630.59px came from. Nothing in the shell sets its own
   width now; everything inherits the one column. */

/* Streamlit sizes an element container to its content, so a button
   inside it measured 148px in a 362px column however wide the button
   asked to be. The container is what has to fill the column. */
[data-testid="stElementContainer"]:has(.stButton),
[data-testid="stElementContainer"]:has(.stFormSubmitButton),
[data-testid="stElementContainer"]:has(.stDownloadButton) { width: 100%; }

/* Every shell element names its own face. Streamlit's default
   (Source Sans) reaches anything inside a markdown container that does
   not, which put a third family on a page whose system has two plus a
   monospace - and a third family is a Layer 2 fluency defect a reader
   registers without being able to name it. */
.ar-topbar, .ar-topbar *, .ar-head, .ar-head *, .ar-card, .ar-card *,
.ar-step, .ar-step *, .ar-empty, .ar-kv, .ar-kv span, .ar-lbl,
table.ar-list, table.ar-list th, table.ar-list td, .ar-gate, .ar-gate * {
  font-family: var(--sans); }
/* Figures are monospace; the headings above them are not. A column
   header set in mono AND tracked reads as "V a l u e". */
.ar-step code, .ar-kv b, table.ar-list td.num { font-family: var(--mono); }
table.ar-list th.num { font-family: var(--sans); letter-spacing: .03em; }

/* The current screen, named. Not a pill and not a tab: it is a label,
   so it is shaped like one. */
.ar-topbar .where {
  font-size: 13px; color: rgba(255, 255, 255, .62); font-weight: 500;
  padding-left: 14px;
  border-left: .5px solid rgba(255, 255, 255, .22); }

/* On a phone the bar still has to hold the product name and the screen
   it is on without wrapping; the source line used to wrap to three and
   overlap what was under it. */
/* Between a phone and a laptop, four columns of prose measure about
   170px each and read as four narrow gutters. Two and two keeps the
   same object and gives each step a line it can finish. */
@media (max-width: 980px) and (min-width: 701px) {
  .ar-steps { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .ar-step:nth-child(odd) { border-left: 0; padding-left: 0; }
  .ar-step:nth-child(n + 3) {
    border-top: 1px solid var(--shell-line); padding-top: 13px;
    margin-top: 11px; }
}

@media (max-width: 700px) {
  .ar-topbar { gap: 14px; height: auto; padding-block: 10px;
    margin-bottom: 18px; }
  .ar-topbar .brand { white-space: nowrap; }

  /* The closing band is a row of two: the mark, then the text. At
     375px that row gives the text about 120px and sets it one or two
     words to the line, which is worse than no ending at all. It
     stacks, and the mark goes above the text it belongs to. */
  .ar-close { flex-direction: column; gap: 18px;
    padding-block: 30px 34px; margin-top: 48px; }
  .ar-close .said { max-width: none; }
  .ar-topbar .where { padding-left: 10px; }

  /* Streamlit keeps its columns side by side at every width, so on a
     phone the right rail was about 100px wide and Get started set one
     word per line. The row stacks instead, in source order, which puts
     the notes above the instructions and the primary action last. */
  [data-testid="stHorizontalBlock"] { flex-direction: column; gap: 22px; }
  [data-testid="stColumn"] { width: 100% !important; flex: 1 1 100%; }

  /* Seven columns do not fit 375px, and four did not either: on the
     deployed site the header wrapped to "Headlin e metric", the Value
     column was clipped and the right edge was cut off. A table a
     reader cannot read is worse than four columns fewer.

     Ticker, Company and the headline finding survive - and the
     finding is now one cell carrying both its figure and its label,
     so the phone keeps the whole statement rather than half of it.
     Price, the two filed ratios, Filed and Cited go: they are context
     the note itself carries, and five numeric columns on a 375px
     screen is a horizontal scrollbar.

     Pinned by NAME in the suite rather than by index. This rule has
     been wrong twice from counting children - once when the metric
     label moved, once when the table widened - and it is wrong
     silently, on the one screen nobody opens while working. */
  table.ar-list th:nth-child(3), table.ar-list td:nth-child(3),
  table.ar-list th:nth-child(4), table.ar-list td:nth-child(4),
  table.ar-list th:nth-child(5), table.ar-list td:nth-child(5),
  table.ar-list th:nth-child(7), table.ar-list td:nth-child(7),
  table.ar-list th:nth-child(8), table.ar-list td:nth-child(8) {
    display: none; }

  /* And the four steps go back to a stack: four columns of prose on a
     375px screen is one word per line. */
  /* Written as `ol.ar-steps > li.ar-step` rather than `.ar-step`,
     because the rule that takes the host's list box off the steps is
     (0,2,2) and a bare `.ar-step` at (0,1,0) would now lose to it - so
     the stack would keep the desktop gutters. The selector follows the
     base rule up rather than reaching for `!important`. */
  .ar-steps { grid-template-columns: minmax(0, 1fr); }
  ol.ar-steps > li.ar-step { padding-right: 0; }
  ol.ar-steps > li.ar-step + li.ar-step {
    border-left: 0; padding-left: 0;
    border-top: 1px solid var(--shell-line); padding-top: 13px;
    margin-top: 2px; }
  /* The padding moved onto the row link, so the phone rule has to
     follow it there or the rows keep their desktop height. */
  table.ar-list th { padding: 9px 10px; }
  table.ar-list td { padding: 9px 10px; }
}

/* The note's section index, lifted into the shell so it has a
   scrollport to stick to. Styled to match the one inside the note
   rather than the shell's own chrome, because it is the document's
   navigation and the reader should not notice it moved. */
.ar-shell-nav {
  position: sticky; top: 0; z-index: 5;
  /* ONE LINE, scrolled, not wrapped.
     This said `flex-wrap: wrap`, so twenty-two uppercase section names
     stacked into three ragged rows above the document - the owner's
     word for it was a blob, and he was right. The index inside the
     note has always been a single rail that scrolls sideways under a
     fade; lifting it into the shell was supposed to be invisible to
     the reader, and the one property that gave it away was this.
     A rail stays one line deep whatever the section count, which is
     the only version that reads as chrome rather than as content. */
  display: flex; flex-wrap: nowrap; gap: 0 20px;
  overflow-x: auto; scrollbar-width: none;
  padding: 11px 0; margin-bottom: 6px;
  background: var(--shell-bg);
  border-bottom: 1px solid var(--shell-line);
  /* The fade says there is more to the right. Without it the last
     label is cut mid-word, which reads as a rendering fault rather
     than as an affordance. #000 is an alpha stop, not a colour: a
     mask reads luminance, so black is opaque and transparent cuts. */
  /* impeccable-disable-next-line design-system-color -- mask alpha stop, not a palette colour */
  mask-image: linear-gradient(90deg, #000 calc(100% - 48px), transparent);
  -webkit-mask-image: linear-gradient(90deg, #000 calc(100% - 48px), transparent); }
.ar-shell-nav::-webkit-scrollbar { display: none; }
.ar-shell-nav a {
  font-size: 11px; letter-spacing: .04em; text-transform: uppercase;
  color: var(--shell-mute); text-decoration: none; white-space: nowrap;
  padding: 3px 0; min-height: 24px; display: inline-flex;
  align-items: center; }
.ar-shell-nav a:hover { color: var(--shell-ink); }
.ar-shell-nav a:focus-visible {
  outline: 2px solid var(--shell-focus); outline-offset: 2px; }

/* The dialog that carries the form once a report is on screen. */
/* One rule, both schemes. The dark block used to set this selector
   too, and the same selector at the same specificity appeared again
   here - a media query adds no specificity, so this one won in both
   and the New report dialog stayed cream while its labels were
   painted from dark tokens. It needs no dark twin: --paper and --ink
   are answered in the dark scheme, so this follows. */
[data-testid="stDialog"] div[role="dialog"] { border-radius: 0;
  border: 1px solid var(--ink); background: var(--paper); }

/* ---------------------------------------------------------- open state */

/* No cover page. The application opens on the instrument itself: one rule,
   the name, the input on the same baseline, and one line saying what comes
   out. A hero with three numbered pillars is a landing page for a product
   with one user, and it is the first thing a reader would have seen. */
/* Composed to the viewport rather than stacked at the top of it. The
   headline takes the top, the lede sits under it, and the hint is pinned to
   the bottom edge, so the empty space between them reads as deliberate
   rather than as a block that ran out of content. */
"""


def document_stylesheet() -> str:
    """Everything the rendered note needs, and nothing about the shell.

    This is what the standalone export carries. It used to carry the whole
    sheet, so a file with no Streamlit in it shipped 41 lines of rules for
    Streamlit's toolbar, sidebar and tab bar.
    """
    return f"<style>{_FONT_IMPORT}{_root()}{_DOCUMENT_CSS}</style>"


def stylesheet() -> str:
    """The document rules plus the shell overrides, for the running app.

    The shell's own font import rides here and not in `_FONT_IMPORT`, so
    the standalone export stays free of it. Both `@import` rules have to
    precede every other statement in the sheet, which is why they are
    concatenated first rather than written beside the rules that use them.
    """
    # NO <link> ELEMENTS HERE. This cost the whole stylesheet once.
    #
    # An audit noted, correctly, that the `@import` is a serial round
    # trip and that until the font lands the opening line paints in
    # Faustina - which this product loads at 400..600, so there is no
    # 300 in it and `font-synthesis-weight: none` rightly refuses to
    # fake one. The display line therefore first paints at weight 400
    # and reflows to 300.
    #
    # The obvious mitigation is a pair of preconnects ahead of the
    # sheet. It was tried, and Streamlit's markdown sanitiser rejects
    # `<link>` - and takes the entire `<style>` with it. Measured in the
    # browser: every style element on the page empty, 74KB of
    # stylesheet gone, the app rendering unstyled. The suite stayed
    # green throughout, because every test reads `stylesheet()` and the
    # string it returns was perfectly correct; what broke was what the
    # host did with it.
    #
    # So the swap stands, and is recorded rather than hidden. Removing
    # it needs the font served from our own origin, or a Streamlit
    # version that lets a `<link>` into the head.
    return (
        f"<style>{_FONT_IMPORT}{_SHELL_FONT_IMPORT}"
        f"{_root()}{_DOCUMENT_CSS}{_APP_CSS}</style>"
    )
