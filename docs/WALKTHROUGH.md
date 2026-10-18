# Walkthrough

The product end to end, with the reasoning behind each choice. Written to be
read beside a running copy.

---

## 1. The opening screen

An empty application is the first thing anyone sees, and "enter a ticker" in a
grey box says nothing about what the tool guarantees. The cover states the
three claims the engine is built to make good on: every figure is filed, every
claim is cited, the counter-case is mandatory.

Each of those is a promise the rest of the product has to keep, and each one
cost something to keep. They are on the first screen so a reader can hold the
rest of the output against them.

**Why a sidebar rather than a search bar.** Three inputs matter and two of
them are not a ticker. The mandate shapes what surfaces first; additional URLs
bring a reader's own sources in. A single search bar would hide both behind a
settings icon and almost nobody would open it.

**Why the mandate is free text.** Real mandates are idiosyncratic. A dropdown
of five fund types would flatten "long-only, 20 to 30 names, three to five
years, durable pricing power, management that allocates capital well" into
"Value". The presets exist only because a stranger opening a hosted demo will
not write a thoughtful mandate before seeing any output, so they pre-fill an
editable box rather than replacing it.

**The boundary that matters.** The mandate changes emphasis and ordering. It
never changes the facts, the figures, the citations, or which divergences get
disclosed. A tool that quietly tells each reader what they want to hear is
worse than no tool, so the caption says so and the prompt enforces it.

---

## 2. Generating

The progress log names the stage rather than showing a spinner, because the
pipeline is about a minute and a reader waiting on it should be able to tell a
slow retrieval from a hung one.

Behind it, in order:

1. **Resolve the ticker to a CIK**, then pull the filing index and the SIC
   code from one submissions payload. Sector classification comes from the
   filer's own SEC code, so it is a fact about the company rather than a
   judgment the tool made.
2. **Pull `companyfacts`**, every XBRL fact the company has ever tagged.
3. **Resolve concepts.** XBRL has no universal name for "revenue". The model
   maps this filer's concept *names* onto a canonical taxonomy and never sees
   a value, so the worst case is a mislabelled series rather than a wrong
   number. Cached per company, and corrected by a pinned override rather than
   by patching output.
4. **Build the series, validate, score, and fetch peers.** Peers run in
   parallel at low fidelity; any peer that fails is dropped rather than
   blocking the report.
5. **Select document sections**, then make the two model calls.

**Why peers are fetched cheaply.** A full concept resolution per peer meant a
model call and a 4MB download for each of eight companies. Removing that path
took cold assembly from roughly two minutes to 35 seconds. The cost is that a
peer's figures come from a fixed tag list rather than per-company resolution,
so peer debt can omit components the subject's includes. That asymmetry is
disclosed in the comparables footnote rather than left for a reader to find.

**Why section selection is content density, not structure.** Parsing Item
headings is the obvious approach and it failed in two ways that testing on one
company would not have caught. JPMorgan repeats page headers more than a
hundred times, and a proxy's compensation tables contain short heading-shaped
lines; both returned the table of contents, which looked populated. Selection
now scores windows by content density, rejects the contents listing by its
characteristically wide span, and rejects inline XBRL markup by density.

Two cases needed specific handling. JPMorgan's Item 7 is a 398-character
pointer to a section elsewhere, which is followed and recovered. And the first
750 characters of an 8-K are inline XBRL cover data, with the actual
disclosure sometimes beginning 3,000 characters in: without stripping it, an
8-K announcing a CEO succession contributed nothing but boilerplate. That one
was caught by the report's own disconfirming-evidence section, which is a
point in favour of making that section mandatory.

---

## 3. The masthead and the five figures

Company name in a text serif, ticker in a bordered monospace chip, then a
provenance line: industry, report date, and the mandate the note was prepared
for.

Beneath it, five figures divided by hairlines. No cards, no shadows, no
rounded corners. A box around a number adds nothing a rule does not already
do, and structure from rules and whitespace is what printed research looks
like.

**The strip changes depending on whether the model is load-bearing.** A
single-stage discounted cash flow on a highly rated company routinely lands
far from the market. On Apple it lands about 63% below. Where the valuation
layer detects a divergence that large, it says so, and setting the modelled
target at the largest type size on the page with a caveat beneath it
disowning that same number is not a presentation anyone can act on.

So when the caveat fires, the strip leads with the traded price, the
market-cap-to-free-cash-flow multiple, the growth the price implies and the
discount rate it implies, and the modelled value moves to the end labelled
"illustrative". It is not removed. The target is what a reader came for, and
hiding it would be its own kind of dishonesty.

That logic lives in one module that both the screen and the exported file
read. They used to build the strip separately, which is how the page came to
demote the disowned target while the file a reader forwards still led with it.

**Then the status lines.** Verification state, model divergence where
relevant, and how old the primary filing is. Ruled left borders rather than
filled rounded panels: three alert boxes stacked on a page is the look of a
form that has just been submitted incorrectly.

The verification line is careful about what it claims. It says citations were
**located**, covering a stated share of the note's prose, and that locating a
quote is not establishing that it supports the claim. It also says explicitly
that the checks cover the descriptive note and that the analysis is synthesis
over it carrying no citations. An earlier version printed "100% of the
narrative is cited. Every figure comes from filed XBRL data" above a header
block in which the price, the market capitalisation and every modelled output
are not filed figures at all.

---

## 4. Summary

The one-screen read, for a reader deciding whether to spend ten minutes.

**Where this analysis departs from consensus** comes first, as the street view
against this analysis in ruled columns. A note that agrees with consensus
throughout has said nothing a price does not already reflect, and where no
variant view was found the report says that rather than manufacturing one.

**Valuation in brief** pairs the case range with the filed free cash flow
history. Those two charts together are the argument: here is what the model
says, and here is the cash record the market is pricing.

**Principal divergences** is the table a PM reads first. Management claim
against reported figures, most material first.

Then **what would have to be true**, the **catalysts** with timeframes and
confirming evidence, and the **questions for management** that the disclosure
does not answer.

---

## 5. Valuation

**What the market is paying** opens the tab, before any modelled output: the
free cash flow multiple, the yield, and the filed compound growth rate. On
Apple that is 51 times, a 2.0% yield, and 1.5% growth. Those three numbers
need no model and cannot be argued with, and they frame the valuation question
better than the model output does.

**Implied expectations** is the primary output. Holding the model fixed, what
growth rate does the current price require? That is a statement about the
market's expectations rather than an assertion about value, and it is the
number a PM can argue with. "The price requires 16% annual free cash flow
growth against a filed record of 1.5%" is a claim. "The model says $133" is
not.

**The cases** are each a full model run at their own assumptions, not a
multiple applied to one forecast, shown next to the bridge from forecast cash
flows through terminal value to equity value. The bridge answers in one glance
the question the single output cannot: how much of this is the forecast and
how much is the perpetuity assumption behind it.

**The sensitivity grid** runs discount rate against terminal growth, the two
assumptions a reviewer pushes on first. Cells are shaded by whether they clear
the traded price, because the reader's question is which assumptions would
justify the price rather than what the midpoint is. It appears in the exported
file as well as on screen; it previously existed only on screen, and the file
is the thing that gets circulated.

**The assumptions table** lists every input the model reads with the basis a
reviewer needs to challenge it, including the three that set the answer most
directly: base free cash flow, net debt and the share count. An earlier
version omitted all three and listed a "free cash flow margin" that `run_dcf`
never read, so a reviewer who disagreed with it and changed it changed
nothing. The growth driver is now named for what it grows: it is applied to
free cash flow, which holds the cash margin flat by construction, and calling
it "revenue growth" hid that assumption.

### What changed in the model, and why

The first version used the latest year's free cash flow, a five-year horizon
and a 9% discount rate, producing $103 against a $313 price with 74% of the
value in the terminal assumption. Sensitivity analysis showed no single
assumption explained the gap: four simultaneously generous changes reached
$213.

Three defaults changed, each for a reason rather than to close the gap. A
three-year mean base, because Apple's FY2025 free cash flow sits below FY2022
on a receivables build the filing itself flags. A ten-year horizon, which cut
terminal dependence from 74% to 58%. And 8.5% rather than 9%, still a
convention and still labelled as one.

Three arithmetic errors were also fixed. Free cash flow is now unlevered by
adding back after-tax interest before discounting at a weighted average cost
of capital, because operating cash flow is reported after interest and
subtracting net debt from a levered figure charges the debt claim twice. The
share count is current shares outstanding rather than last year's
weighted-average diluted count, which mixed a fiscal-year average with an
equity value as at today. And net debt now nets marketable securities.

That last one mattered most. Net debt was computed as total debt less cash and
equivalents, which reported Apple, a company with roughly $163B of liquid
assets against $99B of borrowings, as carrying $63B of net debt, printed that
in a valuation bridge and deducted it from equity value. It is wrong by about
$8 a share, and it is wrong in the direction a reader checks first.

---

## 6. Financials

Four charts, then the statement.

**The table is in statement order**: revenue, cost, gross profit, operating
income, net income, then cash flow, then the balance sheet. An earlier version
sorted canonical metrics alphabetically, which put capital expenditure above
cash and revenue below operating income. No financial statement is ordered
alphabetically, and an analyst finds a line by its position, so that table cost
the reader time on every lookup even though every figure in it was correct.

Statement order is sector-aware. A bank's summary carries net interest income,
deposits and return on equity, and omits gross profit, which does not exist
for it.

**Derived rows are set apart.** Growth rates, margins and free cash flow are
computed from the filed lines above them and are shown in a lighter weight.
The guarantee is that no figure is model-generated, not that none is computed,
and the difference has to be visible.

**Three tokens, not one.** `n.d.` where the company did not tag the line, `NM`
where a ratio's denominator makes it meaningless, and blank where there is no
prior period to compute a change against. One token for all three told a
reader "Interest expense: not meaningful" about a line Apple reports, which is
a claim about the company rather than about the filing.

Capital expenditure prints in parentheses as the outflow it is, so the cash
flow block foots when read down the column. Free cash flow is absent, not
zero, for a year where capex was not tagged: defaulting it printed operating
cash flow under the label "free cash flow".

Rounding is half away from zero rather than Python's default half-to-even, so
a filed $12,500,000 renders as 13 and ties to the filing a reader is checking.

---

## 7. Peers

The comparable-company table follows the standard layout: identifiers, market
data, operating metrics, then multiples, with the subject separated from the
peer set and mean, median, high and low ruled off beneath. An analyst reads
dozens of these a week and finds a number by its position.

**The peer set is Finnhub's, not ours.** Choosing a peer set is an analytical
judgment, arguably the judgment in relative valuation, and inventing one would
be exactly the kind of unsourced opinion the quantitative layer exists to keep
out. Every row states its own basis for inclusion, so a PM can reject the ones
that do not belong.

**One median.** The table and the chart beneath it used to disagree: the table
excluded collapsed-earnings outliers and the chart did not, so one said 15.3x
and the other drew a dashed line at 23.9x under a subtitle reading "extreme
multiples excluded". There is now one function with one default, used by the
table, the chart and the prompt.

**Exclusion is per value, not per row.** A peer flagged for a 1,218x P/E still
has a perfectly good EV/Revenue, and dropping the whole row removed it from
columns where nothing was wrong.

The footnote says what was excluded and from which column, flags any peer
reporting a net margin above its EBITDA margin (arithmetically impossible
without a one-off or a period mismatch), and discloses the subject-versus-peer
resolver asymmetry.

The table scrolls rather than compressing. Fifteen columns squeezed into the
content measure wrapped half the company names onto two lines.

---

## 8. The note, and the sources

The descriptive note renders with citation markers inline and hyperlinked at
the point of each claim, rather than as a footnote list below the prose. A
list makes the reader break stride and scroll; a link at the claim does not. A
citation that could not be located is labelled "unverified" in words rather
than marked with a symbol.

**Sources** carries every document used with its form, filing date, character
count and a link; every gap in the material with a reason; everything the
mandate parser inferred rather than read; and every citation with its status.
A report built on a filing whose MD&A could not be found should say so.

---

## 9. Taking it away

A research note that exists only inside a running web application is not a
deliverable. The work product is a document a PM forwards, attaches to a
committee pack, or opens six weeks later to check what the thesis said.

**Standalone HTML** is one self-contained file: charts inline as SVG,
stylesheet inline in the head, no network dependency for anything structural.
It prints to PDF with the layout intact and carries print rules so a
divergence is not broken across a page break. **Markdown** is the plain-text
version for pasting into a memo.

Both come out of the same renderers the page uses. An export built from a
second set of formatters drifts from the screen within a week, and the first
time it matters is when somebody circulates the drifted version. Both carry
the verification state, the divergence warning, the gaps and the disclaimer,
which is read from configuration rather than written twice.

---

## 10. Why it looks the way it does

The brief was that it must not look generated. Generic clean is the generated
look, so the page commits to a specific identity rather than avoiding one.

**Warm paper, not white.** A neutral `#ffffff` page with a blue primary is the
default of every component library and reads as a template on sight. The
surface is `#fbfaf7`, the colour of coated stock, and every rule is a warm
grey drawn from it. Small per pixel, total in impression.

**Three typefaces with three jobs.** Newsreader, a text serif, sets company
names and section titles the way a research masthead does. IBM Plex Sans
carries interface text and prose. IBM Plex Mono carries every figure with
tabular figures enabled, so digits align down a column and a reader can
compare without reading each number. A single sans across all three roles is
what a framework default looks like.

**Colour means something.** Slate blue marks the subject, sienna a second
series or the traded price, and nothing is coloured for decoration, so a
coloured mark always carries information.

**Structure from rules.** Section headings are a letterspaced label with a
hairline running to the right margin, which is a standard editorial device and
separates sections without spending a heading level on each. Figures sit in a
hairline-divided strip. Tables have a ruled header, no vertical gridlines, no
zebra striping and no sort affordances, because the row order of a
comparables table is itself part of the analysis.

**Charts are inline SVG.** They were rasterised figures. SVG means they
inherit the page's typefaces (a plotting library uses whatever font it finds
on the host, so the same report rendered on a laptop and in a container showed
two different faces), they stay sharp when a reader zooms to check a figure,
and they carry no grey background tile. It also removed the project's heaviest
dependency and its only display-server workaround.

Every chart convention is about reading rather than drawing. One axis per
chart, never two scales on one, because a dual-axis chart lets the author
choose where the lines cross. The subject is the only coloured mark in a peer
chart, and colour follows the entity rather than its rank, so filtering peers
never repaints the survivors. Direct labels selectively; a number on every
point is noise. The axis stops at the first gridline above the data rather
than always adding a whole step, which had Apple's revenue axis running to
$600B against a $416B maximum.

---

## 11. What a review found

Five reviewer profiles went through the product and the code: a fundamental
PM, a quantitative PM auditing the data, an equity research associate, a
compliance officer, and a staff engineer. Most of what is described above as
"an earlier version did X" came out of that pass. The ones worth naming:

- Net debt ignored marketable securities, reporting a net-cash company as
  levered.
- Three different peer medians appeared in one document.
- Fiscal-year labels were derived from the calendar year of the period end, so
  a 52/53-week filer whose year-end crossed 31 December had two fiscal years
  collapse into one column and a whole year vanish with no warning.
- The three-year mean base free cash flow dropped negative years before
  averaging, which is not an average, and was the only thing standing between
  a cash-burning filer and a confident valuation.
- A missing capex year defaulted to zero, turning free cash flow into
  operating cash flow silently.
- A compound growth rate divided by the number of observations rather than
  elapsed time, reading a gapped series as 21% growth where the true rate was
  10%.
- The Markdown export passed model and filing text through as raw HTML, and
  the test that claimed to guard it could not fail.
- A failed report spent real money and recorded nothing, so neither spend cap
  bound.
- The assumptions table omitted the three inputs that set the answer and
  listed one the model never read.

Each is fixed, and most carry a regression test naming the case that produced
them.

## 12. What is still open

- Segment revenue, which needs the dimensional XBRL instance.
- Trailing-twelve-month figures: quarterly data is retrieved and unused, so
  multiples are on the last reported fiscal year.
- A discount rate derived from the filer's own capital structure.
- Semantic citation checking. Provenance is verified; inference is not.
- Persisting a run for reconstruction: model, prompt versions and source
  hashes are not recorded against a finished report.
- Session spend accounting resets on reload, so only the daily cap truly
  binds on a public deployment.
