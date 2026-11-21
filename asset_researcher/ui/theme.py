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
.ar-skip { position: absolute; left: -9999px; top: 0; z-index: 100;
  background: var(--ink); color: var(--paper); padding: var(--s2) var(--s3);
  font-family: var(--sans); font-size: var(--t-label);
  letter-spacing: var(--t-label-ls); text-transform: uppercase;
  text-decoration: none; }
.ar-skip:focus { left: var(--s3); top: var(--s3); }

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
.ar-status.warn { border-left-width: 3px; }
.ar-status.bad { border-left-color: var(--negative); border-left-width: 3px; }
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
  .ar-progress i { animation: ar-fill 75s cubic-bezier(.2,.7,.3,1) both; }

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
@keyframes ar-fill { from { transform: scaleX(0) } to { transform: scaleX(.97) } }
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
html, body, .stApp, [data-testid="stAppViewContainer"] {
  background: var(--paper); color: var(--ink); }
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
#MainMenu, footer { display: none !important; }

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
  --shell-bg: #fcfcfd;
  --shell-panel: #ffffff;
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
  /* The one focus colour, declared once. 8.2:1 on the page and 4.4:1
     on the bypass link's near-black pill, so it is visible wherever a
     ring is drawn. */
  --shell-focus: #4f46e5;
  --shell-sink: #fbfbfc;      /* table head */
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

/* ------------------------------------------------------------- dark

   The same shell, on the other ground. Nothing moves and nothing
   changes shape: the register is restraint, and a dark mode that
   reorganises the page is a second design rather than the same one
   after dark.

   Every colour is a token redefinition, which is the whole reason the
   palette is declared in one block. Four colours used to sit inline in
   the rules - among them the primary button's label, hard-coded white,
   which on this scheme's near-white fill would have made the one
   control a reader is meant to press unreadable. The suite now fails
   if the light scheme declares a colour this one does not answer.

   Following the system rather than offering a switch. A toggle is a
   control, a preference to persist and a state to get wrong, and the
   reader this is built for has already told their laptop which they
   want. The measured ratios are in the suite, not in a comment: every
   tone is checked against every ground it lands on, at the same 4.5:1
   floor the light scheme is held to, and the field boundary and focus
   ring at the 3:1 the WCAG 2.2 control rules ask for. */
@media (prefers-color-scheme: dark) {
  :root {
    --shell-bg: #0d0e12;
    --shell-panel: #161820;
    --shell-ink: #e8eaef;
    --shell-soft: #b9bdc8;
    --shell-mute: #9499a5;
    /* Lines read louder on a dark ground than on a light one at the
       same distance from it, so these sit closer to the panel than
       their light counterparts do to white. */
    --shell-line: #242732;
    --shell-line-2: #2c3040;
    --shell-field-line: #767c8a;
    --shell-btn-line: #6a6f7e;
    --shell-focus: #a5a0ff;
    --shell-sink: #121419;
    --shell-shadow: 0 1px 2px rgba(0, 0, 0, .4);
    --shell-on-ink: #11131a;
    --shell-ink-hover: #ffffff;
    --shell-chip: #1d212b;
    --shell-hover: #1d212b;
    --shell-hover-line: #3a3f52;

    /* The DOCUMENT tokens, answered here and only here.
    
       The reading screen puts a note in an iframe, where it keeps its
       own paper world and nothing out here reaches it. The REPORT
       screen does not: it writes `ui.masthead`, `ui.stat_strip` and
       every section's HTML straight into the Streamlit page. So on
       the longest screen in the product, `.ar-title { color:
       var(--ink) }` was painting #17150f on a near-black ground -
       1.06:1 - with the prose at --ink-soft around 1.4:1, and only
       the tables legible, because `table.ar-table` paints its own
       white. A page of readable tables with invisible headings
       between them.
    
       Also reached by this: `[data-testid="stExpander"]`, which is
       what `st.status` renders as, was left at --surface #ffffff
       while `.ar-stage` inside it is painted --shell-ink, near-white.
       For the whole ninety seconds of a run, the one line telling a
       dark-mode reader what the system was doing was white on white.
       And `.ar-progress` drew its track in --rule, the light
       hairline, so the empty track was brighter than the fill and the
       bar read as running backwards.
    
       These live in _APP_CSS rather than in `_root()` deliberately.
       `document_stylesheet()` - what the exported file and the
       iframe'd note carry - is the font import plus `_root()` plus
       _DOCUMENT_CSS, and does NOT include this block. So a downloaded
       note stays on paper, which is what a document should be, while
       the same markup inside the shell follows the shell. */
    --ink: #e9ebf0;
    --ink-soft: #c2c6d0;
    --ink-muted: #9aa0ac;
    --paper: #14161c;
    --surface: #171a21;
    --rule: #2a2e38;
    --rule-soft: #21242c;
    --accent: #8fb6d8;
    --accent-soft: #1b2a36;
    --accent-2: #c9a227;
  }

  /* Streamlit paints a few surfaces from its own static config, which
     has one scheme and cannot follow the system. These are the ones a
     reader meets. */
  .stApp, [data-testid="stAppViewContainer"],
  [data-testid="stHeader"] { background: var(--shell-bg); }

  /* The note renders in its own document, which carries its own paper
     world and is not restyled here - a research note is a document,
     and a document on a dark screen is still on paper. The frame it
     sits in gets an edge so the white does not run into the page. */
  iframe { border-radius: var(--shell-r); }
}



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

.ar-topbar {
  display: flex; align-items: center; gap: 28px;
  height: 52px; margin: -26px calc(-1 * var(--shell-gut)) 24px;
  padding: 0 var(--shell-gut);
  border-bottom: 1px solid var(--shell-line); }
.ar-topbar .brand {
  display: flex; align-items: center; gap: 9px;
  font-size: 13.5px; font-weight: 600; letter-spacing: -.012em;
  color: var(--shell-ink); }
.ar-topbar .brand i {
  width: 16px; height: 16px; border-radius: var(--shell-r-sm);
  background: var(--shell-ink); display: block; }
.ar-topbar .meta {
  margin-left: auto; font-family: var(--mono); font-size: 11px;
  color: var(--shell-mute); letter-spacing: .02em; }

.ar-head { margin-bottom: 14px; }
.ar-head h1, .ar-head h2 {
  font-family: var(--sans) !important; font-size: 15px !important;
  font-weight: 600 !important; letter-spacing: -.015em !important;
  line-height: 1.3 !important; color: var(--shell-ink); margin: 0; }
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
table.ar-list { width: 100%; border-collapse: collapse; }
table.ar-list th {
  text-align: left; font-size: 11px; font-weight: 500;
  color: var(--shell-mute); letter-spacing: .03em;
  padding: 9px 16px; background: var(--shell-sink);
  border-bottom: 1px solid var(--shell-line); }
table.ar-list td {
  padding: 11px 16px; border-bottom: 1px solid var(--shell-line);
  font-size: 13px; color: var(--shell-ink); }
table.ar-list tr:last-child td { border-bottom: 0; }

/* A row is a link made of four cell-filling links. Each anchor fills
   its own cell's padding box, so the whole row is a hit target with no
   dead strip between cells, and the padding moves from the cell to the
   anchor to make that true. Colour and underline are inherited from
   the cell so the table looks like a table rather than like four
   columns of blue. The hover and focus states are on the row, because
   that is the object the reader is pointing at - and the focus ring is
   drawn with an outline offset inward, since an outline on a table
   cell is otherwise clipped by the card's own edge. */
table.ar-list td { padding: 0; }
a.ar-row-link {
  display: block; padding: 11px 16px; color: inherit;
  text-decoration: none; font: inherit; letter-spacing: inherit; }
table.ar-list td.num a.ar-row-link { text-align: right; }
table.ar-list tr:hover td { background: var(--shell-sink); }
table.ar-list tr:has(a.ar-row-link:focus-visible) td {
  background: var(--shell-sink); }
a.ar-row-link:focus-visible {
  outline: 2px solid var(--shell-focus); outline-offset: -2px; }
table.ar-list td.co { color: var(--shell-soft); }
table.ar-list td.tk { font-weight: 600; letter-spacing: -.01em; }
/* Filed and Cited are context rather than the figure a reader came
   for, so they are set a step back. They are still figures, so they
   keep the mono face and the right edge. */
table.ar-list td.dim a.ar-row-link { color: var(--shell-mute); }
/* A figure does not wrap. At tablet width the Filed column broke
   "2026-08-05" across two lines, which makes a date look like two
   numbers and adds a line's height to every row in the table. */
table.ar-list th.num, table.ar-list td.num a.ar-row-link {
  white-space: nowrap; }
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
.ar-steps {
  counter-reset: step; display: grid; gap: 0;
  grid-template-columns: repeat(4, minmax(0, 1fr)); }
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
.block-container:has(.ar-gate) { max-width: 320px; padding-top: 128px; }
.ar-gate { text-align: center; margin-bottom: 20px; }
.ar-gate .brand i {
  width: 22px; height: 22px; border-radius: var(--shell-r-sm);
  display: inline-block;
  background: var(--shell-ink); margin-bottom: 18px; }
.ar-gate h1 {
  font-family: var(--sans) !important; font-size: 17px !important;
  font-weight: 600 !important; letter-spacing: -.02em !important;
  color: var(--shell-ink); margin: 0 !important; }
.ar-gate p {
  font-size: 12.5px; color: var(--shell-mute); margin: 5px 0 0; }
.block-container:has(.ar-gate) [data-testid="stForm"] {
  border: 0; padding: 0; }
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
  text-transform: none; font-weight: 500; border-radius: var(--shell-r);
  border: 1px solid var(--shell-ink); background: var(--shell-ink);
  color: var(--shell-on-ink); width: 100%; min-height: 36px;
  padding: 0 16px;
  box-shadow: 0 1px 2px rgba(18, 20, 26, .16);
  transition: background-color 120ms var(--ease),
    border-color 120ms var(--ease), color 120ms var(--ease); }
.stButton > button:hover, .stFormSubmitButton > button:hover {
  background: var(--shell-ink-hover);
  border-color: var(--shell-ink-hover); }
.stDownloadButton > button, .stButton > button[kind="secondary"] {
  background: var(--shell-panel); color: var(--shell-ink);
  border-color: var(--shell-btn-line); box-shadow: var(--shell-shadow); }
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
.ar-skip, .ar-skip:visited, .ar-skip:hover, .ar-skip:active {
  color: var(--paper) !important; text-decoration: none !important; }
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
  outline: 2px solid var(--accent) !important; outline-offset: -2px; }

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
.ar-step code, .ar-kv b, table.ar-list td.num,
.ar-topbar .meta { font-family: var(--mono); }
table.ar-list th.num { font-family: var(--sans); letter-spacing: .03em; }

/* The current screen, named. Not a pill and not a tab: it is a label,
   so it is shaped like one. */
.ar-topbar .where {
  font-size: 13px; color: var(--shell-soft); font-weight: 500;
  padding-left: 14px; border-left: 1px solid var(--shell-line-2); }

/* On a phone the bar's three parts do not fit. The source line wrapped
   to three lines and overlapped the tabs, and the product name broke
   across two. The meta is the first thing to go: it is provenance a
   reader can find in the note itself, and a wrapped, overlapping bar is
   the first thing seen on the screen. */
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
  .ar-topbar .meta { display: none; }
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

     Ticker, Company and Value survive. Price, the metric LABEL, Filed
     and Cited go: the label explains the figure while the figure is
     the reason the row is there, and the rest is context the note
     itself carries. Pinned by NAME in the suite rather than by index,
     because the rule this replaces hid child 3 - the metric label
     when it was written, and Price from the day the table widened. */
  table.ar-list th:nth-child(3), table.ar-list td:nth-child(3),
  table.ar-list th:nth-child(4), table.ar-list td:nth-child(4),
  table.ar-list th:nth-child(6), table.ar-list td:nth-child(6),
  table.ar-list th:nth-child(7), table.ar-list td:nth-child(7) {
    display: none; }

  /* And the four steps go back to a stack: four columns of prose on a
     375px screen is one word per line. */
  .ar-steps { grid-template-columns: minmax(0, 1fr); }
  .ar-step { padding-right: 0; }
  .ar-step + .ar-step {
    border-left: 0; padding-left: 0;
    border-top: 1px solid var(--shell-line); padding-top: 13px;
    margin-top: 2px; }
  /* The padding moved onto the row link, so the phone rule has to
     follow it there or the rows keep their desktop height. */
  table.ar-list th { padding: 9px 10px; }
  table.ar-list td { padding: 0; }
  a.ar-row-link { padding: 9px 10px; }
}

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
    """The document rules plus the shell overrides, for the running app."""
    return f"<style>{_FONT_IMPORT}{_root()}{_DOCUMENT_CSS}{_APP_CSS}</style>"
