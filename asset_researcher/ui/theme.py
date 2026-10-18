"""Visual tokens and the stylesheet, in one place.

The look is taken from printed sell-side research rather than from web
dashboards, because that is the document this tool is competing with. The
specific decisions, and why:

**Warm paper, not white.** A neutral `#ffffff` page with a blue primary is the
default of every component library, so it reads as a template on sight. The
surface here is `#fbfaf7`, the colour of coated stock, and every rule is a
warm grey drawn from it. The difference is small per pixel and total in
impression.

**Three typefaces with three jobs.** Newsreader, a text serif, sets company
names and section titles, the way a research masthead does. IBM Plex Sans
carries interface text and prose. IBM Plex Mono carries every figure, with
tabular figures enabled, so digits align in a column and a reader can compare
down a table without reading each number. Mixing a serif display face with a
grotesque and a mono is a deliberate editorial pairing; a single sans across
all three roles is what a framework default looks like.

**No cards, shadows or rounded corners.** Structure comes from hairline rules
and whitespace. A drop shadow implies a floating surface, which is a
skeuomorphism from software; research is laid out on a flat page in columns
separated by rules.

**Colour is reserved for meaning.** Slate blue marks the subject company,
sienna marks a second series or a divergence. Nothing is coloured for
decoration, so a coloured mark always means something.
"""

from __future__ import annotations

# --- tokens -------------------------------------------------------------
#
# Referenced by both the stylesheet and the SVG charts, so a chart can never
# drift out of step with the page it sits on.

INK = "#14130f"  # warm near-black, body text
INK_SOFT = "#46433b"  # secondary prose
INK_MUTED = "#767163"  # labels, captions, axis text
PAPER = "#fbfaf7"  # page
SURFACE = "#ffffff"  # tables and panels that sit on the page
RULE = "#e2ded4"  # hairline, structural
RULE_SOFT = "#efede6"  # hairline, within a table

ACCENT = "#1f5f8b"  # slate blue: the subject, the primary series
ACCENT_SOFT = "#e8eef3"
ACCENT_2 = "#b4542a"  # sienna: a second series, the traded price
NEUTRAL = "#b8b4a8"  # peers, recessive marks

NEGATIVE = "#8c2f1f"  # divergence, bear
POSITIVE = "#2f6b4f"  # corroboration, bull
CAUTION = "#8a6d1f"  # unverified, thin evidence

FONT_DISPLAY = "'Newsreader', Georgia, serif"
FONT_SANS = "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif"
FONT_MONO = "'IBM Plex Mono', 'SF Mono', Menlo, monospace"


_FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;"
    "1,6..72,400&"
    "family=IBM+Plex+Sans:wght@400;500;600&"
    "family=IBM+Plex+Mono:wght@400;500;600&display=swap');"
)


# The stylesheet is one string rather than many injections: Streamlit reruns
# the script top to bottom on every interaction, and a single <style> block
# applied once is both cheaper and easier to reason about than styles
# scattered through the view code.
_CSS = """
:root {
  --ink: %(ink)s;
  --ink-soft: %(ink_soft)s;
  --ink-muted: %(ink_muted)s;
  --paper: %(paper)s;
  --surface: %(surface)s;
  --rule: %(rule)s;
  --rule-soft: %(rule_soft)s;
  --accent: %(accent)s;
  --accent-soft: %(accent_soft)s;
  --accent-2: %(accent_2)s;
  --negative: %(negative)s;
  --positive: %(positive)s;
  --caution: %(caution)s;
  --sans: %(sans)s;
  --mono: %(mono)s;
  --display: %(display)s;
}

/* ---------------------------------------------------- page and chrome */

/* Streamlit's own header is a floating toolbar with a hamburger and a
   running-man icon. It is the single clearest sign of the framework, and
   nothing in it is needed once the sidebar carries the controls. */
header[data-testid="stHeader"] { display: none; }
[data-testid="stToolbar"] { display: none; }
#MainMenu, footer { display: none; }
[data-testid="stDecoration"] { display: none; }

html, body, .stApp, [data-testid="stAppViewContainer"] {
  background: var(--paper);
  color: var(--ink);
}

.stApp, [data-testid="stAppViewContainer"] {
  font-family: var(--sans);
  font-size: 14.5px;
  line-height: 1.62;
  -webkit-font-smoothing: antialiased;
}

/* 1180px is about 95 characters of body prose at this size, which is the
   upper bound for comfortable reading. Streamlit's "wide" layout runs edge
   to edge and turns a paragraph into a single long line. */
.block-container {
  max-width: 1180px;
  padding: 2.1rem 2.4rem 5rem;
}

/* ------------------------------------------------------------ typography */

h1, h2, h3, h4 {
  font-family: var(--display);
  color: var(--ink);
  font-weight: 500;
  letter-spacing: -0.012em;
  line-height: 1.22;
}
h1 { font-size: 2.05rem; }
h2 { font-size: 1.42rem; }
h3 { font-size: 1.14rem; }

p, li { color: var(--ink-soft); }
a, a:visited { color: var(--accent); text-decoration: none;
  border-bottom: 1px solid color-mix(in srgb, var(--accent) 32%%, transparent); }
a:hover { border-bottom-color: var(--accent); }

code, kbd { font-family: var(--mono); font-size: 0.88em;
  background: var(--accent-soft); padding: 0.08em 0.3em; }

/* -------------------------------------------------------------- masthead */

.ar-masthead { border-top: 2px solid var(--ink); padding-top: 0.95rem;
  margin-bottom: 0.2rem; }
.ar-eyebrow { font-family: var(--mono); font-size: 0.645rem;
  letter-spacing: 0.17em; text-transform: uppercase; color: var(--ink-muted); }
.ar-title { font-family: var(--display); font-size: 2.32rem; font-weight: 500;
  letter-spacing: -0.018em; line-height: 1.12; color: var(--ink);
  margin: 0.34rem 0 0.1rem; display: flex; align-items: baseline; gap: 0.7rem;
  flex-wrap: wrap; }
.ar-ticker { font-family: var(--mono); font-size: 0.82rem; font-weight: 500;
  letter-spacing: 0.06em; color: var(--ink); border: 1px solid var(--ink);
  padding: 0.14rem 0.46rem; position: relative; top: -0.26rem; }
.ar-subline { font-family: var(--mono); font-size: 0.705rem; color: var(--ink-muted);
  letter-spacing: 0.035em; padding-bottom: 0.85rem; }
.ar-subline .sep { color: var(--rule); padding: 0 0.42rem; }

/* ------------------------------------------------------------ stat strip */

/* Figures are the reason the page exists, so they get the widest treatment
   on it: a single row divided by hairlines, labels small and recessive
   above values set large in tabular mono. No boxes, because a box around a
   number adds nothing a rule does not already do. */
.ar-stats { display: flex; border-top: 1px solid var(--ink);
  border-bottom: 1px solid var(--rule); margin: 0 0 1.5rem; }
.ar-stat { flex: 1 1 0; padding: 0.82rem 0 0.9rem 0.92rem;
  border-left: 1px solid var(--rule-soft); min-width: 0; }
.ar-stat:first-child { border-left: none; padding-left: 0; }
/* Two lines, reserved whether or not the label needs them, so the values
   below stay on one baseline across the strip. Truncating instead turned
   "Market cap / free cash flow" into "Market cap / free cash f...". */
.ar-stat-label { font-family: var(--mono); font-size: 0.6rem;
  letter-spacing: 0.145em; text-transform: uppercase; color: var(--ink-muted);
  line-height: 1.3; min-height: 2.6em; padding-right: 0.6rem; }
.ar-stat-value { font-family: var(--mono); font-size: 1.56rem; font-weight: 400;
  font-variant-numeric: tabular-nums; color: var(--ink); line-height: 1.32;
  letter-spacing: -0.018em; margin-top: 0.22rem; }
.ar-stat-value.pos { color: var(--positive); }
.ar-stat-value.neg { color: var(--negative); }
.ar-stat-value.nm { color: var(--ink-muted); font-size: 1.18rem; }
.ar-stat-note { font-family: var(--sans); font-size: 0.665rem;
  color: var(--ink-muted); line-height: 1.35; margin-top: 0.1rem; }

/* -------------------------------------------------------- section header */

/* Label, then a rule running to the right margin. A standard editorial
   device, and it separates sections without spending a heading level or
   vertical space on each one. */
.ar-sec { display: flex; align-items: center; gap: 0.78rem;
  margin: 2.15rem 0 0.95rem; }
.ar-sec:first-child { margin-top: 0.4rem; }
.ar-sec-label { font-family: var(--mono); font-size: 0.655rem; font-weight: 500;
  letter-spacing: 0.165em; text-transform: uppercase; color: var(--ink);
  white-space: nowrap; }
.ar-sec-rule { flex: 1; height: 1px; background: var(--rule); }
.ar-sec-note { font-family: var(--sans); font-size: 0.705rem;
  color: var(--ink-muted); white-space: nowrap; letter-spacing: 0.01em; }
.ar-caption { font-size: 0.775rem; color: var(--ink-muted); line-height: 1.52;
  margin: -0.45rem 0 0.95rem; max-width: 72ch; }

/* ---------------------------------------------------------------- tables */

/* Published financial tables have no vertical rules, no zebra striping and
   no sort affordances. They have a ruled header, right-aligned tabular
   figures, and generous row height. Streamlit's dataframe is a spreadsheet
   grid, which is the wrong object: it invites the reader to sort and filter
   a table whose row order is itself part of the analysis. */
.ar-table-wrap { overflow-x: auto; margin-bottom: 0.5rem; }
table.ar-table { width: 100%%; border-collapse: collapse;
  font-size: 0.805rem; background: var(--surface); }
table.ar-table thead th {
  font-family: var(--mono); font-size: 0.59rem; font-weight: 500;
  letter-spacing: 0.115em; text-transform: uppercase; color: var(--ink-muted);
  text-align: left; padding: 0.46rem 0.72rem 0.42rem; vertical-align: bottom;
  border-top: 1px solid var(--ink); border-bottom: 1px solid var(--rule);
  white-space: nowrap; background: var(--surface); }
table.ar-table thead th.num { text-align: right; }
table.ar-table tbody td {
  padding: 0.44rem 0.72rem; border-bottom: 1px solid var(--rule-soft);
  color: var(--ink-soft); vertical-align: top; }
table.ar-table tbody td.num {
  text-align: right; font-family: var(--mono); font-variant-numeric: tabular-nums;
  color: var(--ink); white-space: nowrap; letter-spacing: -0.01em; }
table.ar-table tbody td.key { color: var(--ink); font-weight: 500;
  min-width: 8.5rem; }
table.ar-table.ar-table-scroll { width: auto; min-width: 100%%; }
table.ar-table.ar-table-scroll td, table.ar-table.ar-table-scroll th {
  white-space: nowrap; }
table.ar-table.ar-table-scroll td.wide { white-space: normal;
  max-width: 20rem; }
table.ar-table tbody td.nm { color: var(--ink-muted); }
table.ar-table tbody tr:last-child td { border-bottom: 1px solid var(--rule); }

/* The subject of a comparable-company table is separated from its peer set,
   never sorted into it. */
table.ar-table tbody tr.subject td { background: var(--accent-soft);
  color: var(--ink); font-weight: 500;
  border-bottom: 1px solid color-mix(in srgb, var(--accent) 24%%, transparent); }
table.ar-table tbody tr.spacer td { height: 0.5rem; padding: 0;
  border-bottom: none; background: var(--paper); }
table.ar-table tbody tr.summary td { border-bottom: none;
  color: var(--ink-muted); font-size: 0.775rem; }
table.ar-table tbody tr.summary.first td { border-top: 1px solid var(--rule); }
table.ar-table tbody tr.summary td.num { color: var(--ink); }
table.ar-table tbody tr.total td { border-top: 1px solid var(--ink);
  border-bottom: none; color: var(--ink); font-weight: 500; }
table.ar-table td.wide { min-width: 17rem; white-space: normal;
  font-size: 0.775rem; line-height: 1.48; }

/* Sensitivity grid: the one table that earns a fill, because the reader is
   looking for a boundary rather than a value. */
table.ar-table td.heat { font-family: var(--mono); text-align: right;
  font-variant-numeric: tabular-nums; color: var(--ink); }
table.ar-table th.rowhead, table.ar-table td.rowhead {
  font-family: var(--mono); font-size: 0.665rem; color: var(--ink);
  background: var(--surface); font-weight: 500; text-align: left; }

/* The financial summary. Section headings span the table; subtotals are
   ruled above; derived rows are lighter, because a figure this project
   computed must not look like one the company filed. */
table.ar-statement tbody tr.statement-section td {
  font-family: var(--mono); font-size: 0.585rem; letter-spacing: 0.145em;
  text-transform: uppercase; color: var(--ink-muted); padding: 1.05rem 0.72rem 0.3rem;
  border-bottom: 1px solid var(--rule); }
table.ar-statement tbody tr.statement-section:first-child td { padding-top: 0.3rem; }
table.ar-statement tbody tr.statement-subtotal td {
  border-top: 1px solid var(--rule); color: var(--ink); font-weight: 500; }
table.ar-statement tbody tr.statement-subtotal td.rowhead { font-weight: 600; }
table.ar-statement tbody tr.statement-derived td {
  color: var(--ink-muted); font-size: 0.755rem; border-bottom: none; }
table.ar-statement tbody tr.statement-derived td.rowhead {
  color: var(--ink-muted); font-weight: 400; padding-left: 1.35rem; }
table.ar-statement tbody tr.statement-line td { border-bottom: none; }
table.ar-statement tbody td.rowhead { white-space: nowrap; }

.ar-foot { font-size: 0.705rem; color: var(--ink-muted); line-height: 1.5;
  margin: 0.45rem 0 1.1rem; max-width: 86ch; }

/* ------------------------------------------------------------ status bar */

/* A left rule and a line of text. Streamlit's st.success and st.warning are
   filled, rounded, icon-bearing panels; three of them stacked on a page is
   the look of a form that has just been submitted incorrectly. */
.ar-status { border-left: 2px solid var(--rule); padding: 0.1rem 0 0.1rem 0.82rem;
  margin: 0 0 1.4rem; font-size: 0.805rem; color: var(--ink-soft);
  line-height: 1.5; }
.ar-status .tag { font-family: var(--mono); font-size: 0.6rem;
  letter-spacing: 0.145em; text-transform: uppercase; display: block;
  margin-bottom: 0.14rem; }
.ar-status.ok { border-left-color: var(--positive); }
.ar-status.ok .tag { color: var(--positive); }
.ar-status.warn { border-left-color: var(--caution); }
.ar-status.warn .tag { color: var(--caution); }
.ar-status.bad { border-left-color: var(--negative); }
.ar-status.bad .tag { color: var(--negative); }
.ar-status.info .tag { color: var(--ink-muted); }

/* ------------------------------------------------------------ two-column */

.ar-split { display: grid; grid-template-columns: 1fr 1fr; gap: 0;
  border-top: 1px solid var(--rule); }
.ar-split > div { padding: 0.95rem 1.3rem 1.1rem 0; }
.ar-split > div + div { border-left: 1px solid var(--rule);
  padding-left: 1.3rem; padding-right: 0; }
.ar-col-label { font-family: var(--mono); font-size: 0.6rem;
  letter-spacing: 0.145em; text-transform: uppercase; margin-bottom: 0.42rem; }
.ar-col-label.bull { color: var(--positive); }
.ar-col-label.bear { color: var(--negative); }
.ar-col-label.street { color: var(--ink-muted); }
.ar-col-label.ours { color: var(--accent); }
.ar-split p { margin: 0; font-size: 0.835rem; line-height: 1.58; }

/* ------------------------------------------------------------- findings */

/* One divergence between what management says and what the filings show.
   The claim and the figures sit side by side because the comparison is the
   finding; stacking them makes the reader hold one in memory. */
.ar-finding { border-top: 1px solid var(--rule); padding: 0.92rem 0 0.3rem; }
.ar-finding-head { display: flex; align-items: center; gap: 0.6rem;
  margin-bottom: 0.6rem; }
.ar-pill { font-family: var(--mono); font-size: 0.585rem; letter-spacing: 0.13em;
  text-transform: uppercase; padding: 0.15rem 0.42rem; border: 1px solid; }
.ar-pill.diverge { color: var(--negative); border-color: var(--negative); }
.ar-pill.agree { color: var(--positive); border-color: var(--positive); }
.ar-pill.mat { color: var(--ink-muted); border-color: var(--rule); }
.ar-finding-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;
  margin-bottom: 0.62rem; }
.ar-finding-grid .lbl { font-family: var(--mono); font-size: 0.585rem;
  letter-spacing: 0.13em; text-transform: uppercase; color: var(--ink-muted);
  margin-bottom: 0.18rem; }
.ar-finding-grid p { margin: 0; font-size: 0.825rem; line-height: 1.55; }
.ar-assess { font-size: 0.825rem; line-height: 1.55; color: var(--ink);
  border-left: 2px solid var(--accent); padding-left: 0.75rem;
  margin-bottom: 0.3rem; }

/* ------------------------------------------------------------ prose body */

/* The finished note. Measure capped near 74 characters, first-line indents
   after the opening paragraph, and citation markers set small and raised so
   they do not interrupt the line. */
.ar-prose { max-width: 74ch; font-size: 0.925rem; line-height: 1.72;
  color: var(--ink-soft); }
.ar-prose h2 { font-size: 1.28rem; margin: 2.2rem 0 0.7rem;
  padding-bottom: 0.32rem; border-bottom: 1px solid var(--rule); }
.ar-prose h3 { font-size: 1.04rem; margin: 1.5rem 0 0.5rem; }
.ar-prose p { margin: 0 0 0.92rem; }
.ar-prose a { font-family: var(--mono); font-size: 0.72em; font-weight: 500;
  vertical-align: 0.28em; border: none; padding: 0 0.05em;
  color: var(--accent); }
.ar-prose a:hover { background: var(--accent-soft); }
.ar-prose strong { color: var(--ink); font-weight: 600; }

/* --------------------------------------------------------------- charts */

.ar-figure { margin: 0 0 1.1rem; }
.ar-figure svg { display: block; width: 100%%; height: auto;
  overflow: visible; }
.ar-figure figcaption { font-size: 0.7rem; color: var(--ink-muted);
  line-height: 1.45; margin-top: 0.22rem; }

/* ------------------------------------------------------------------ nav */

/* Streamlit's tab bar is a pill row with a sliding red underline. Reset to
   a letterspaced rule, which is how a document's sections are indexed. */
.stTabs [data-baseweb="tab-list"] { gap: 0; border-bottom: 1px solid var(--rule);
  background: transparent; margin-bottom: 1.5rem; }
.stTabs [data-baseweb="tab"] {
  font-family: var(--mono); font-size: 0.645rem; letter-spacing: 0.145em;
  text-transform: uppercase; color: var(--ink-muted); background: transparent;
  padding: 0.52rem 0.95rem; height: auto; border-radius: 0;
  border-bottom: 2px solid transparent; }
.stTabs [data-baseweb="tab"]:first-child { padding-left: 0; }
.stTabs [data-baseweb="tab"]:hover { color: var(--ink); background: transparent; }
.stTabs [aria-selected="true"] { color: var(--ink); font-weight: 500;
  border-bottom: 2px solid var(--ink); }
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 0; }

/* -------------------------------------------------------------- sidebar */

[data-testid="stSidebar"] { background: var(--surface);
  border-right: 1px solid var(--rule); }
[data-testid="stSidebar"] > div:first-child { padding-top: 1.7rem; }
[data-testid="stSidebarContent"] { padding: 0 1.25rem; }
[data-testid="stSidebar"] label, [data-testid="stSidebar"] .ar-field {
  font-family: var(--mono) !important; font-size: 0.6rem !important;
  letter-spacing: 0.145em !important; text-transform: uppercase;
  color: var(--ink-muted) !important; font-weight: 500 !important; }
[data-testid="stSidebar"] p { font-size: 0.74rem; color: var(--ink-muted);
  line-height: 1.5; }
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarCollapsedControl"] button { color: var(--ink-muted); }

/* ------------------------------------------------------------- controls */

.stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] > div {
  font-family: var(--mono); font-size: 0.82rem; background: var(--paper);
  border: 1px solid var(--rule); border-radius: 0; color: var(--ink);
  box-shadow: none; }
.stTextArea textarea { font-family: var(--sans); font-size: 0.8rem;
  line-height: 1.55; }
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--accent); box-shadow: none; outline: none; }
.stTextInput input::placeholder, .stTextArea textarea::placeholder {
  color: var(--neutral, #b8b4a8); }

.stButton > button, .stDownloadButton > button {
  font-family: var(--mono); font-size: 0.665rem; letter-spacing: 0.145em;
  text-transform: uppercase; font-weight: 500; border-radius: 0;
  border: 1px solid var(--ink); background: var(--ink); color: var(--paper);
  padding: 0.56rem 1rem; box-shadow: none; transition: none; }
.stButton > button:hover, .stDownloadButton > button:hover {
  background: var(--accent); border-color: var(--accent); color: #fff; }
.stButton > button[kind="secondary"], .stDownloadButton > button {
  background: transparent; color: var(--ink); }
.stButton > button[kind="secondary"]:hover { background: var(--ink);
  color: var(--paper); }
.stButton > button:focus { box-shadow: none !important; }

/* Streamlit's progress log. Kept, because a reader waiting on a two-minute
   pipeline should see which stage it is in, but reset to a plain ruled
   panel rather than a rounded card with a spinner badge. */
[data-testid="stStatusWidget"], [data-testid="stStatus"] {
  background: var(--surface); border: 1px solid var(--rule);
  border-radius: 0; box-shadow: none; }
[data-testid="stStatus"] p, [data-testid="stStatus"] div {
  font-family: var(--mono); font-size: 0.72rem; color: var(--ink-soft); }

[data-testid="stExpander"] { border: none; border-top: 1px solid var(--rule);
  border-radius: 0; background: transparent; }
[data-testid="stExpander"] summary { font-family: var(--mono);
  font-size: 0.72rem; color: var(--ink); padding: 0.6rem 0; }
[data-testid="stExpander"] summary:hover { color: var(--accent); }

hr, [data-testid="stDivider"] { border-color: var(--rule); margin: 1.6rem 0; }
[data-testid="stAlert"] { border-radius: 0; }
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 0; }

/* ------------------------------------------------------------ cover page */

.ar-cover { border-top: 2px solid var(--ink); padding-top: 1.4rem;
  max-width: 62ch; }
.ar-cover h1 { font-size: 2.7rem; line-height: 1.1; margin: 0.5rem 0 0.9rem; }
.ar-cover .lede { font-size: 1rem; line-height: 1.66; color: var(--ink-soft); }
.ar-guarantee { border-top: 1px solid var(--rule); margin-top: 1.9rem;
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 0; }
.ar-guarantee > div { padding: 1rem 1.2rem 0.4rem 0; }
.ar-guarantee > div + div { border-left: 1px solid var(--rule);
  padding-left: 1.2rem; }
.ar-guarantee .n { font-family: var(--mono); font-size: 0.6rem;
  letter-spacing: 0.145em; color: var(--accent); margin-bottom: 0.3rem; }
.ar-guarantee .h { font-family: var(--display); font-size: 1.02rem;
  color: var(--ink); margin-bottom: 0.26rem; }
.ar-guarantee p { font-size: 0.78rem; line-height: 1.52; margin: 0; }

/* ----------------------------------------------------------- responsive */

@media (max-width: 900px) {
  .block-container { padding: 1.4rem 1rem 3rem; }
  .ar-stats { flex-wrap: wrap; }
  .ar-stat { flex: 1 1 42%%; border-left: none;
    border-top: 1px solid var(--rule-soft); padding-left: 0; }
  .ar-split, .ar-finding-grid, .ar-guarantee { grid-template-columns: 1fr; }
  .ar-split > div + div { border-left: none; padding-left: 0;
    border-top: 1px solid var(--rule); }
  .ar-guarantee > div + div { border-left: none; padding-left: 0;
    border-top: 1px solid var(--rule); }
  .ar-title { font-size: 1.72rem; }
}
"""


def stylesheet() -> str:
    """The full `<style>` block, tokens substituted."""
    body = _CSS % {
        "ink": INK,
        "ink_soft": INK_SOFT,
        "ink_muted": INK_MUTED,
        "paper": PAPER,
        "surface": SURFACE,
        "rule": RULE,
        "rule_soft": RULE_SOFT,
        "accent": ACCENT,
        "accent_soft": ACCENT_SOFT,
        "accent_2": ACCENT_2,
        "negative": NEGATIVE,
        "positive": POSITIVE,
        "caution": CAUTION,
        "sans": FONT_SANS,
        "mono": FONT_MONO,
        "display": FONT_DISPLAY,
    }
    return f"<style>{_FONT_IMPORT}{body}</style>"
