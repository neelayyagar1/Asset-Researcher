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
.ar-sec-label, .ar-stat-label, .ar-col-label, .ar-pill, .ar-field,
table.ar-table thead th, .ar-status .tag, .ar-finding-grid .lbl,
/* The widget labels were the last text in the product still set in
   Streamlit's own voice: 14px sentence-case regular, directly above a
   button that is 10px uppercase tracked. One label style means this one
   too. */
.stTextInput label, .stTextArea label, .stSelectbox label {
  font-family: var(--sans); font-size: var(--t-label);
  line-height: var(--t-label-lh); letter-spacing: var(--t-label-ls);
  font-weight: 600; text-transform: uppercase; }

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
  /* The workspace has neither a masthead nor a stat strip, so home to
     workspace was the one transition in the product that hard-cut. */
  .ar-workspace { animation: ar-settle 560ms var(--ease) both; }
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
[data-testid="stAppViewContainer"] h2.ar-sec-label,
[data-testid="stAppViewContainer"] h3.ar-block-label {
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

.block-container { max-width: 1240px; padding: var(--s6) var(--s5) var(--s8); }

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

.stTextInput input, .stTextArea textarea,
.stSelectbox [data-baseweb="select"] > div {
  font-family: var(--sans); font-size: var(--t-body); background: var(--paper);
  border: 1px solid var(--rule); border-radius: 0; color: var(--ink);
  box-shadow: none; transition: border-color 120ms var(--ease); }
/* The ring is on the wrapper, because that is where the visible border
   is; `outline: none` on the inner input beat the global focus-visible
   rule and left keyboard users with no indication at all. */
.stTextInput [data-baseweb="input"]:focus-within,
.stTextArea [data-baseweb="textarea"]:focus-within {
  border-color: var(--accent); outline: 2px solid var(--accent);
  outline-offset: 1px; }
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

.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  font-family: var(--sans); font-size: var(--t-label);
  letter-spacing: var(--t-label-ls); text-transform: uppercase;
  font-weight: 600; border-radius: 0; border: 1px solid var(--ink);
  background: var(--ink); color: var(--paper);
  padding: var(--s3) var(--s4); box-shadow: none;
  transition: color 120ms var(--ease), background-color 120ms var(--ease),
    border-color 120ms var(--ease); }
.stButton > button:hover, .stDownloadButton > button:hover {
  background: var(--accent); border-color: var(--accent); color: #fff; }
.stDownloadButton > button, .stButton > button[kind="secondary"] {
  background: transparent; color: var(--ink); }
.stButton > button[kind="secondary"]:hover { background: var(--ink);
  color: var(--paper); }
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible,
.stFormSubmitButton > button:focus-visible {
  outline: 2px solid var(--accent); outline-offset: 2px; }

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
  outline: 2px solid var(--accent); outline-offset: 2px; }

/* Streamlit's own anchor rules out-specify `.ar-skip`, so in the app the
   bypass link rendered #0054a3 on its near-black pill, 2.43:1, with its
   focus ring suppressed: the first control a keyboard user meets was
   invisible and close to unreadable. The export, whose shell we write, is
   unaffected. */
.ar-skip, .ar-skip:visited, .ar-skip:hover, .ar-skip:active {
  color: var(--paper) !important; text-decoration: none !important; }
.ar-skip:focus-visible {
  outline: 2px solid var(--paper) !important; outline-offset: 2px; }

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
.stTextInput [data-baseweb="input"], .stTextArea [data-baseweb="textarea"] {
  background: var(--paper); border-radius: 0; border: 1px solid var(--rule);
  box-shadow: none; }
.stTextInput [data-baseweb="input"] input { background: transparent; }
.stTextInput [data-baseweb="input"] button,
.stTextInput [data-baseweb="input"] [role="button"] {
  background: transparent; border: 0; border-radius: 0; color: var(--ink-muted); }

/* A pull quote in the written guide, set as print sets one. */
.ar-prose blockquote { margin: var(--s4) 0; padding-left: var(--s4);
  border-left: 2px solid var(--rule); }
.ar-prose blockquote p { font-family: var(--display); font-size: var(--t-read);
  line-height: var(--t-read-lh); color: var(--ink); margin: 0; }
.ar-prose code { font-family: var(--mono); font-size: 0.88em;
  background: var(--surface); padding: 0.1em 0.3em; }

/* The guide's own headings, which were falling through to browser
   defaults and rendering the page title smaller than its sections. */
.ar-about h2 { font-size: var(--t-d2); letter-spacing: var(--t-d2-ls);
  margin: 0 0 var(--s4); }
.ar-about h3 { font-size: var(--t-h1); margin: var(--s6) 0 var(--s3); }
.ar-about h4 { font-size: var(--t-h2); margin: var(--s5) 0 var(--s2); }
.ar-about { border-top: 2px solid var(--ink); padding-top: var(--s5); }

.ar-doors { display: flex; gap: var(--s5); flex-wrap: wrap;
  margin-top: var(--s3); }
.ar-about { max-width: 42rem; }
.ar-about h1 { font-size: var(--t-d2); letter-spacing: var(--t-d2-ls);
  margin: 0 0 var(--s4); }
.ar-about h3 { margin-top: var(--s5); }
.ar-about h4 { margin-top: var(--s4); }
.ar-gate { max-width: 34rem; }
.ar-gate h1 { max-width: none; }
.ar-workspace-intro, .ar-workspace { max-width: 34rem; }
.stTextInput, .stTextArea, .stSelectbox,
[data-testid="stCaptionContainer"] { max-width: 34rem; }
.stButton > button, .stFormSubmitButton > button { max-width: 34rem; }
.ar-home { border-top: 2px solid var(--ink); padding-top: var(--s5);
  padding-bottom: var(--s5); }
.ar-home h1 { font-size: var(--t-d0); line-height: var(--t-d0-lh);
  letter-spacing: var(--t-d0-ls); margin: 0 0 var(--s5);
  /* Wraps on its own measure rather than on four hard `<br>`s, which
     could not respond to width. */
  max-width: 15ch; }
.ar-home .lede { font-size: var(--t-read); line-height: var(--t-read-lh);
  color: var(--ink-soft); margin: 0; max-width: 54ch; }

/* The three guarantees, ruled rather than boxed. Cards would make them
   look like features; rules make them look like terms. */
.ar-claims { display: grid; grid-template-columns: repeat(3, 1fr);
  border-top: 1px solid var(--rule); margin-top: var(--s7); }
.ar-claims > div { padding: var(--s5) var(--s5) var(--s6) 0; }
.ar-claims > div + div { border-left: 1px solid var(--rule);
  padding-left: var(--s5); }
.ar-claims h2 { font-size: var(--t-h2); margin: 0 0 var(--s2); }
.ar-claims p { font-size: var(--t-micro); line-height: 1.55; margin: 0; }

/* ------------------------------------------------------- the workspace */

.ar-workspace-intro { border-top: 2px solid var(--ink);
  padding-top: var(--s4); margin-bottom: var(--s5); }
/* An h1, because this screen's only heading was an h2 and a hierarchy
   that starts at level two tells a screen-reader user the page title is
   missing. Set at the same size it always was. */
.ar-workspace-intro h1 { font-size: var(--t-d2);
  letter-spacing: var(--t-d2-ls);
  margin: 0 0 var(--s2); }
.ar-workspace-intro p { font-size: var(--t-body); color: var(--ink-muted);
  margin: 0; max-width: 46ch; }

/* The dialog that carries the form once a report is on screen. */
[data-testid="stDialog"] div[role="dialog"] { border-radius: 0;
  border: 1px solid var(--ink); background: var(--paper); }

@media (max-width: 900px) {
  .ar-claims { grid-template-columns: 1fr; }
  .ar-claims > div + div { border-left: none; padding-left: 0;
    border-top: 1px solid var(--rule); }
}

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
