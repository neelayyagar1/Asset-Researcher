"""Visual tokens and the stylesheet.

The surface is a tearsheet: the one-page company document an analyst pulls,
marks up and forwards. Not a dashboard and not a marketing page. The output
of this product is a document and the application is the machine that makes
it, so the screen and the exported file are the same object.

Four decisions carry it.

**One type scale, nine steps.** An earlier version of this file held 31
distinct font sizes, eighteen of them inside a five-pixel band. Nobody
perceives 0.775rem as a different rank from 0.78rem; they perceive "all the
text is small". Per-component tuning like that is locally defensible and
globally flat, and it is the clearest sign that a stylesheet was assembled
rather than designed. Component rules may only reference the scale.

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
NEUTRAL = "#b4afa1"  # peers, recessive marks

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

_FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Faustina:wght@400..600&"
    "family=Public+Sans:wght@400;500;600&"
    "family=Spline+Sans+Mono:wght@400;500&display=swap');"
)

# Nine type steps and eight spacing stops. A raw rem inside a component rule
# is how the 31-size scale happened, so component rules reference these only.
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
table.ar-table thead th, .ar-status .tag, .ar-finding-grid .lbl {
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
.ar-stat-value { font-family: var(--sans); font-size: var(--t-d2);
  font-weight: 500; letter-spacing: var(--t-d2-ls);
  line-height: var(--t-d2-lh); color: var(--ink); margin-top: var(--s2);
  font-variant-numeric: tabular-nums lining-nums; }
.ar-stat-value.pos { color: var(--positive); }
.ar-stat-value.neg { color: var(--negative); }
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
  margin: var(--s7) 0 var(--s4); scroll-margin-top: var(--s5); }
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

.ar-table-wrap { overflow-x: auto; margin-bottom: var(--s2);
  scrollbar-width: thin; }
table.ar-table { width: 100%; border-collapse: collapse;
  font-size: var(--t-data); line-height: var(--t-data-lh);
  background: var(--surface); }
table.ar-table thead th { color: var(--ink-muted); text-align: left;
  padding: var(--s2) var(--s3) var(--s1); vertical-align: bottom;
  border-top: 1px solid var(--ink); border-bottom: 1px solid var(--rule);
  white-space: nowrap; background: var(--surface);
  position: sticky; top: 0; z-index: 2; }
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
table.ar-statement tbody td.rowhead { white-space: nowrap; }

/* ---------------------------------------------------------- status bar */

.ar-status { border-left: 1px solid var(--rule); padding: 0 0 0 var(--s3);
  margin: 0 0 var(--s5); font-size: var(--t-body);
  line-height: var(--t-body-lh); color: var(--ink-soft); max-width: 82ch; }
.ar-status .tag { display: block; margin-bottom: var(--s1); }
.ar-status.ok { border-left-color: var(--positive); }
.ar-status.ok .tag { color: var(--positive); }
.ar-status.warn { border-left-color: var(--caution); }
.ar-status.warn .tag { color: var(--caution); }
.ar-status.bad { border-left-color: var(--negative); }
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
.ar-assess { font-size: var(--t-body); line-height: var(--t-body-lh);
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
.ar-nav { position: sticky; top: 0; z-index: 40; display: flex;
  gap: var(--s4); overflow-x: auto; scrollbar-width: none;
  background: var(--paper); border-top: 1px solid var(--rule);
  border-bottom: 1px solid var(--ink); margin: 0 0 var(--s6);
  padding: var(--s3) 0; }
.ar-nav::-webkit-scrollbar { display: none; }
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
  .ar-masthead { animation: ar-settle 420ms var(--ease) both; }
  .ar-stats { animation: ar-settle 420ms var(--ease) 80ms both; }
}
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
}
"""


# Rules that exist only to tame the Streamlit shell. A standalone export has
# no Streamlit in it, so shipping these put dead selectors into the file a
# reader actually forwards.
_APP_CSS = """
html, body, .stApp, [data-testid="stAppViewContainer"] {
  background: var(--paper); color: var(--ink); }
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
[data-testid="stStatusWidget"], [data-testid="stDecoration"],
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
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--accent); box-shadow: none; outline: none; }
.stTextInput input::placeholder, .stTextArea textarea::placeholder {
  color: var(--neutral); }

.stButton > button, .stDownloadButton > button {
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
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible {
  outline: 2px solid var(--accent); outline-offset: 2px; }

[data-testid="stStatus"] { background: var(--surface);
  border: 1px solid var(--rule); border-radius: 0; box-shadow: none; }
[data-testid="stStatus"] p, [data-testid="stStatus"] div {
  font-family: var(--mono); font-size: var(--t-micro); color: var(--ink-soft); }

hr, [data-testid="stDivider"] { border-color: var(--rule);
  margin: var(--s5) 0; }
[data-testid="stAlert"], [data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: 0; }


/* ---------------------------------------------------------- open state */

/* No cover page. The application opens on the instrument itself: one rule,
   the name, the input on the same baseline, and one line saying what comes
   out. A hero with three numbered pillars is a landing page for a product
   with one user, and it is the first thing a reader would have seen. */
/* Composed to the viewport rather than stacked at the top of it. The
   headline takes the top, the lede sits under it, and the hint is pinned to
   the bottom edge, so the empty space between them reads as deliberate
   rather than as a block that ran out of content. */
.ar-open { border-top: 2px solid var(--ink); padding-top: var(--s5);
  min-height: calc(100vh - 11rem); display: grid;
  grid-template-rows: auto auto 1fr auto; }
.ar-open h1 { font-size: var(--t-d0); line-height: var(--t-d0-lh);
  letter-spacing: var(--t-d0-ls); max-width: 16ch; margin-bottom: var(--s5); }
.ar-open .lede { font-size: var(--t-read); line-height: var(--t-read-lh);
  color: var(--ink-soft); margin: 0; max-width: 54ch; }
.ar-open .hint { font-family: var(--sans); font-size: var(--t-label);
  letter-spacing: var(--t-label-ls); text-transform: uppercase;
  font-weight: 600; color: var(--ink-muted); margin: 0;
  border-top: 1px solid var(--rule); padding-top: var(--s3);
  align-self: end; }
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
