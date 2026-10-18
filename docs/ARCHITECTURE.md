# Architecture

This document is the reference the source comments point at. It explains why
the system is shaped the way it is, and records the decisions that are not
obvious from reading the code.

---

## 1. What this is

Asset Researcher takes a ticker and produces a sourced equity research note:
the filed financial record, the narrative management wrapped around it, and
the places where the two do not agree.

The problem it addresses is specific. A portfolio manager at a fundamental
fund spends three to four hours assembling a pitch from a known set of
sources: the 10-K, the latest 10-Qs, the proxy, recent 8-Ks, a peer screen,
and whatever news moved the name. The sources are the same every time and
the assembly is mechanical. The judgment is not, which is why this produces
an input to a decision rather than a decision.

What it is not: a chatbot over filings. A chatbot answers a question and the
reader has no way to tell a quotation from a recollection. The design
constraint throughout is that the reader must be able to check any figure or
claim without trusting the system.

---

## 2. The guarantee, and what it costs

Three claims are made, and each one costs something.

**Every figure comes from a filing.** Financial values are read from the
company's own XBRL submissions to the SEC, which are structured, machine
readable and legally attested. The model is never permitted to write a
number: both writing prompts forbid it in prose, and the renderer inserts
filed values into the finished report. A number the model typed would be
unverifiable by construction, and a report that is 99% grounded is a report
a reader has to check line by line, which is the work the tool was meant to
remove.

The cost is that the model writes "operating margin contracted, and the
decline outpaced the revenue slowdown" where it could have written "operating
margin fell 240bps to 29.1%". The prose is less satisfying to read on its
own. It is the only version that can be trusted without checking.

**Every narrative claim carries a citation.** Call A runs with the Messages
API's citations feature, which returns character offsets into the documents
supplied. Those offsets are resolved against the exact stored text the model
was given, so a citation is checked rather than merely present.

The cost is that citations and structured output cannot be requested in one
call; the API rejects the combination. That is why the pipeline is two calls
rather than one (§6).

**The counter-case is mandatory.** Every report states the strongest evidence
against its own thesis, what would falsify it, and what the source material
could not see. This is enforced in the schema, not just requested in the
prompt: a report that returns an empty disconfirming section has that
section replaced with a visible warning rather than rendered blank.

The cost is tokens and a less confident-sounding note. A research tool that
only produces conviction is a tool that produces conviction regardless of the
evidence.

### What the guarantee does not cover

Worth stating plainly, because the limits are where trust is actually lost.

A verified citation means the quoted text appears at the stated offsets in
the stated document. It does not mean the claim built on the quote is a fair
reading of it. The verifier checks provenance, not inference. Semantic
support remains a human judgment, and the citations are rendered inline and
linked specifically so that judgment is cheap to exercise.

Coverage is reported as the percentage of narrative characters sitting inside
a cited span. It is a measure of how much of the prose is attributed, not of
how well.

---

## 3. Sources and the provider boundary

### EDGAR

SEC EDGAR is the primary source and the only one that is authoritative.
Three endpoints carry the work:

| Endpoint | Purpose |
| --- | --- |
| `company_tickers.json` | ticker to CIK |
| `data.sec.gov/submissions/CIK##########.json` | the filing index, and the SIC code |
| `data.sec.gov/api/xbrl/companyfacts/CIK##########.json` | every XBRL fact the filer has ever tagged |

Two operational facts govern the client. EDGAR rejects any request without a
`User-Agent` identifying a real contact, with HTTP 403 and no explanatory
body, so the header is required configuration rather than an option. And the
documented rate ceiling is ten requests a second; the client is set to eight
to leave headroom, because exceeding it earns a block rather than a 429.

Filings are immutable once accepted, which is the property the cache is built
on. A document is stored under its accession number, and a document already
in the store is never re-fetched and its text never re-derived. That is what
keeps citation offsets valid for the life of a report.

### Finnhub

The only non-EDGAR dependency, and it is confined to the two things EDGAR
does not publish: the current quote, and a peer list. Market capitalisation
is not a filed figure, so it is computed from a quoted price and a filed
share count, and labelled accordingly.

The peer list is Finnhub's, not ours. Choosing a peer set is an analytical
judgment, arguably *the* judgment in relative valuation, and inventing one
would be precisely the kind of unsourced opinion the quantitative layer
exists to keep out. Finnhub's list is attributable, the report says where it
came from, and each row states its own basis for inclusion so a PM can
disagree with it on the evidence.

### User-supplied URLs

A PM wants their own sources in the report. Accepting an arbitrary URL and
fetching it server-side is a server-side request forgery primitive, so
`sources/web.py` applies a scheme allowlist, resolves DNS and validates every
returned address rather than the hostname, revalidates on each redirect hop,
and rejects ambiguous numeric hostnames.

That last defence exists because the obvious implementation is bypassable.
`0177.0.0.1`, `2130706433`, `0x7f.0.0.1` and `127.1` all resolve to loopback,
and whether a given form resolves is platform-dependent, so a check that
passes on a developer's machine can fail open in a container.

Fetched pages are Tier C (below), are never treated as instructions, and are
attributed as opinion in the report.

### Trust tiers

Every passage carries a tier, and the writing prompts bind the tier to how a
claim may be stated.

- **Tier A, authoritative.** SEC filings and XBRL. May be stated as fact.
  Figures come only from here.
- **Tier B, primary.** Company investor relations material and press
  releases. Attributed to the company: "the company states...".
- **Tier C, secondary.** News, commentary, user-supplied links. Attributed as
  opinion with the outlet named. Never presented as established fact.

Management's own characterisations are claims regardless of tier. The prompt
requires "management attributes the decline to...", never "the decline was
caused by...".

### The provider boundary

`llm/provider.py` defines the interface; `llm/claude.py` implements it
against the Anthropic SDK. Nothing outside that module imports the SDK.

This is not abstraction for its own sake. The intended buyer is a fund, and
funds have views about where their research material is processed. The
boundary is what makes "self-hosting is a swap, not a rewrite" true rather
than aspirational: a provider that supports citations and structured outputs
drops in behind the same interface. Model choice, effort tiers and token
budgets are configuration (`config/settings.yaml`), not code.

---

## 4. The mandate and the objectivity boundary

A report is written for a reader, and readers differ. A long-only compounder
fund and an event-driven fund reading the same 10-K want different things
surfaced first.

The mandate is free text, parsed into a structured profile
(`analysis/mandate.py`). Free text is the primary input because real mandates
are idiosyncratic and a taxonomy would flatten them; the presets in
`config/mandates/presets.yaml` exist only because a stranger opening a hosted
demo will not write a thoughtful mandate description before seeing any
output. They pre-fill an editable box.

**The boundary is the important part.** The mandate changes emphasis,
ordering, which horizon matters for catalysts, and how risk is framed. It
never changes the facts: the same filings, the same filed figures, the same
citations, and the same disclosed divergences regardless of who is reading.
A finding inconvenient for a reader's mandate is reported exactly as plainly
as a convenient one. This is stated in the prompt and repeated in the
interface, because a tool that quietly tells each reader what they want to
hear is worse than no tool.

Anything the parser inferred rather than read is recorded in `assumptions`
and shown in the report, so the reader can correct it. An empty list is a
truthful answer; a plausible-sounding invented thesis-killer is one the user
may not notice and will then be reported against.

---

## 5. The quantitative spine

Everything in this layer is deterministic. The model participates in exactly
one step, and only by naming things.

### Concept resolution

XBRL has no universal name for "revenue". Apple tags
`RevenueFromContractWithCustomerExcludingAssessedTax`; others use
`Revenues`, `SalesRevenueNet`, or a custom extension. A hand-maintained
mapping would be permanently out of date.

So resolution is model-assisted, and tightly fenced: the model sees a filer's
concept *names* and maps them onto the canonical taxonomy in
`config/metrics/canonical.yaml`. **It never sees or touches a value.** The
worst case is a mislabelled series, which validation catches, rather than a
wrong number, which nothing would.

Resolution is cached per company and not re-run per report. A mapping that
turns out wrong is pinned in `config/overrides/{cik}.yaml`, which always wins
and is never re-resolved. Fixing a mapping at the source beats patching
output after the fact.

### Series construction

`quant/series.py` turns raw facts into annual series, and two decisions there
were learned the hard way.

**Do not filter on XBRL's `frame` field.** It looks like the right filter and
works for income-statement facts. Verified against Apple's `Assets` concept:
the most recent fiscal year's balance-sheet facts report with `frame=None` in
their own 10-K and only gain a populated frame a year later, when they
reappear as the prior-year comparative in the next one. Filtering on
`frame is not None` silently drops the most recent balance sheet from every
report. Facts are grouped by their `end` date instead, which is always
present, and deduplicated by taking the most recently filed value for a given
period, since later filings carry restatements.

**`form="10-K"` and `fp="FY"` do not mean the fact spans a year.** Verified
against Realty Income: quarterly interest-expense facts with 90 and 91 day
durations are tagged `form=10-K, fp=FY` and sit directly alongside the real
annual value. Without a duration check, one series mixes a $78M quarter with
a $309M year, which is a plausible-looking number that is simply wrong and
that no reader would catch by eye. Duration facts must therefore span 330 to
400 days; instant facts are exempt.

### Composite metrics

Some canonical metrics have no single tag. Total debt is the sum of several
disjoint concepts, which is summed rather than guessed at. Verified on Apple:
`LongTermDebtNoncurrent` plus `CommercialPaper` plus the current portion
reconciles to $98.7B exactly against the filed balance sheet.

### Validation and health scores

`quant/validate.py` checks internal consistency: that the accounting identity
holds, that subtotals sum, that a series has no impossible jumps. A failure
is surfaced in the report rather than swallowed.

Altman Z, Piotroski F and Beneish M are computed from filed statements using
the published methodologies. They are **reported as not meaningful**, never
as a number, for filers whose balance sheet structure the models do not fit.
Altman Z was fitted on manufacturers and says nothing about a bank; printing
3.2 for JPMorgan would be arithmetic masquerading as analysis. Sector gating
(`quant/sectors.py`) is driven by the filer's own SEC SIC code, read from the
same submissions payload that gives the filing index, so it costs no extra
request and is a fact about the filer rather than a classification we chose.

### The financial summary

`analysis/statements.py` renders the summary in statement order: revenue,
cost, gross profit, operating income, net income, then cash flow, then the
balance sheet. An earlier version sorted canonical metrics alphabetically,
which put capital expenditure above cash and revenue below operating income.
No financial statement is ordered alphabetically, and an analyst finds a line
by its position, so that table cost the reader time on every lookup even
though every figure in it was correct.

Statement order is sector-aware. A bank's summary carries net interest
income, deposits and return on equity, and omits gross profit, which does not
exist for it.

Three kinds of row appear and the distinction is load-bearing: filed lines,
subtotals the statement itself presents as sums, and derived lines (growth
rates, margins, free cash flow) that this module computes. Derived rows are
set in a lighter weight. The guarantee is that no figure is model-generated,
not that none is computed, and the difference has to be visible.

Rounding is half away from zero, not Python's default half-to-even, so a
filed $12,500,000 renders as 13 and matches the filing a reader is checking
against.

---

## 6. The two model calls

### Why two

The Messages API rejects a request that enables both citations and structured
output. Call A needs citations; Call B needs a schema. So:

**Call A, narrative** (`analysis/narrative.py`). Citations on, no schema.
Produces the descriptive sections from the source passages: business
overview, industry position, recent developments, management and governance,
risk. Everything descriptive, nothing synthetic. The response comes back as
prose split into spans, each carrying the offsets of whatever it cites.

**Call B, reconciliation** (`analysis/reconcile.py`). Schema on, no
citations. Reasons over Call A's output plus the filed series, and produces
the analytical half: the reconciliation of narrative against figures, variant
views, management assessment, what would have to be true, catalysts, bull and
bear, and the disconfirming case.

Running Call B without citations is an acceptable trade rather than a
compromise: it reasons over material that is already grounded. The
descriptive note carries verified citations and every figure comes from filed
XBRL, so its job is analysis over vetted inputs rather than assertion about
new ones. It is held to the same rule about never writing a figure.

### The schema trap

Every property in a structured-output schema must appear in `required`.
pydantic omits any field carrying a default, and a property absent from
`required` is one the model may silently skip. The symptom was a report where
`variant_views`, `management` and `what_would_have_to_be_true` came back
empty on every run while `financial_trajectory` was always populated: the
first three had defaults and the fourth did not. `llm/schema.py` now forces
every property into `required` and sets `additionalProperties: false`
recursively.

### Grounding and verification

`grounding/verify.py` resolves each returned citation against the stored
source text. A citation whose offsets do not contain the quoted text is a
failure, is counted, and is rendered inline as "unverified" rather than
dropped. The verification banner states the result either way; a reader who
can see that two claims failed is better served than one shown a clean report
with a quiet hole in it.

Two refinements came from false positives. The verifier flags unsupported
figures in prose by matching digit strings against filed values, which
initially flagged numbers from our own preamble (gap messages carry counts
like "truncated to 40,000 of 68,169 characters") and SEC item codes such as
`2.02` and `5.02`. Both are now excluded, because blaming the model for
quoting us trains a reader to ignore the warnings.

Coverage is measured in characters, not spans. Measured by spans it read 50%
where the character figure was 76%, because the API splits a response at
citation boundaries and produces single-character spans like `';'`.

### Document selection

A 10-K runs to hundreds of thousands of characters and only parts of it are
worth sending. Section extraction (`documents/sections.py`) was originally
structural, parsing Item headings, and it failed in two ways that a test on
one company would not have caught: JPMorgan repeats page headers more than a
hundred times, and a proxy's compensation tables contain short
heading-shaped lines. The table of contents was returned instead of the
document, and it looked populated.

Selection is now content-density scoring (`documents/density.py`), with the
table of contents rejected by its characteristically wide span and inline
XBRL markup rejected by a markup-density test. Two more cases needed specific
handling:

- **Cross-referenced sections.** JPMorgan's Item 7 is a 398-character pointer
  to a section elsewhere in the document. `recover_cross_referenced_section`
  follows it. The first implementation returned 1,085,000 characters by
  spanning from the first region's start to the last region's end.
- **8-K cover pages.** The first 750 characters of an 8-K are inline XBRL
  cover data (`true`, `NASDAQ`, a CIK) and the actual disclosure can begin
  3,000 characters in. Without stripping it, an 8-K announcing a CEO
  succession contributed nothing but boilerplate. This was caught by Call B's
  own disconfirming-evidence section, which is a point in favour of making
  that section mandatory.

Every source that fails to load is recorded in the bundle's `gaps` with a
reason and surfaced in the report. A report built on a filing whose MD&A
could not be found should say so; the alternative is a confident-looking
thesis with a hole in it.

### Caching

Three caches, each keyed on something immutable or explicitly time-bounded:

- **Documents**, by accession number. Permanent, because a filing never
  changes once accepted.
- **Concept resolution**, per company. Permanent; corrected by override.
- **Bundles**, per ticker per day. The quote moves, so this expires.

Prompt caching is used across the two calls, and effort is tiered by task:
low for concept resolution and mandate parsing, medium for the narrative,
high for the reconciliation. There is no reason to pay for deep reasoning to
map a tag name.

---

## 7. Valuation

The valuation layer (`quant/valuation.py`) is deterministic arithmetic over
assumptions with a stated basis. Every input appears in an assumptions table
with where it came from, and inputs that are conventions rather than filings
say so and invite replacement.

### Why implied expectations lead

A single-stage discounted cash flow on a highly rated company routinely lands
far from the market price. On Apple it lands roughly 63% below. The honest
reading is not that Apple is 63% overvalued; it is that a generic model with
generic assumptions is the wrong instrument for that question.

So the primary output is the reverse solve: holding the model fixed, what
growth rate or discount rate does the *current price* require? That is a
statement about the market's expectations rather than an assertion about
value, and it is the number a PM can actually argue with. On Apple the price
implies free cash flow growth of about 17% a year, against a filed five-year
compound rate of 1.5%, and an implied discount rate near the risk-free rate.
That gap is the finding.

The modelled target is still shown, because hiding it would be its own kind
of dishonesty, but where the divergence exceeds a threshold the report says
in the header that the gap more likely describes the model than a
mispricing, and treats the implied expectations as primary. `ImpliedExpectations.caveat`
fires above 75% terminal dependence or 40% divergence.

### The cash flow context

Alongside the model, the report states what the market is paying in terms
that need no model at all: market capitalisation over free cash flow, the
free cash flow yield, and the compound growth of free cash flow as filed. On
Apple: 51 times, a 2.0% yield, and 1.5% compound growth over five years.
Those three numbers frame the valuation question better than the model
output does, and they cannot be argued with.

### Defaults, and why they changed

The first version used the latest year's free cash flow as the base, a
five-year horizon and a 9% discount rate. That produced $103 against a $313
price with 74% of the value in the terminal assumption. Sensitivity analysis
showed no single assumption explained the gap: four simultaneously generous
changes reached $213.

Three defaults changed as a result, each for a reason rather than to close
the gap:

- **A three-year average base**, not the latest year. Apple's FY2025 free
  cash flow sits below FY2022, largely on a receivables build the filing
  itself flags. One distorted year should not set the base.
- **A ten-year horizon**, not five. This cut terminal dependence from 74% to
  58%. Above roughly 75% a DCF is a statement about perpetuity growth rather
  than about the forecast, and should be labelled as one.
- **8.5% rather than 9%** as the starting discount rate, which is still a
  convention and still labelled as one. A real analyst derives it from the
  company's own capital structure, and the assumptions table says so.

The result moved to $119. The gap to market is largely real and remains the
point of the section.

### Cases and sensitivity

Bear, base and bull are each a full model run at their own assumptions, not a
multiple applied to one forecast, with probabilities of 0.25 / 0.50 / 0.25
and a probability-weighted target.

The sensitivity grid runs discount rate against terminal growth, the two
assumptions a reviewer pushes on first, and reports `NM` where the rate is at
or below the growth rate, which has no finite solution. Cells are shaded by
whether they clear the traded price, because the reader's question is which
assumptions would justify the price rather than what the midpoint is.

---

## 8. Degradation, hosting and cost

### Partial failure is the normal case

Some filers have never filed a proxy. Some have no usable peer. Some tag
nothing under a concept the taxonomy expects. The system reports what is
missing and continues; it does not fail the report, and it does not fill the
gap.

Every gap carries a severity and a reason and appears in the report. A peer
fetched at low fidelity that fails is dropped from the comps table rather
than blocking anything, which is why peers are deliberately fetched without
per-peer concept resolution: a full resolution per peer meant an LLM call and
a 4MB download for each of eight companies.

Removing that path took cold assembly from roughly two minutes to 35 seconds.

### Cost control

A hosted demo is an open invitation to spend someone else's money.
`hosting/spend.py` enforces a per-session and a per-day cap, checked before a
run starts rather than after it has spent.

The estimate must sit below the session cap or no run can start at all. An
earlier configuration had a $3.50 estimate against a $3.00 session cap, which
rejected every run with a message about budget. A measured report costs
about $1.30; the estimator assumes $2.00 against a $6.00 session cap and a
$25 daily cap.

### Secrets

Keys come from the environment via `.env`, which is gitignored, with
`.env.example` documenting the shape. `scripts/install-hooks.sh` installs a
pre-commit hook that blocks a commit containing any value from `.env` and
fails closed if it cannot run. There is a test asserting no key material
reaches logs or rendered output.

---

## 9. The view layer

`asset_researcher/ui/` holds the markup, the stylesheet and the charts. None
of it imports Streamlit, and every renderer is a pure function from data to a
string. Two things follow.

First, it is testable without a server, so the conventions the project claims
to follow are assertions rather than screenshots: that negatives are
parenthesised, that the subject of a peer table is separated from its peers,
that an absent value reads as absent.

Second, the standalone HTML export comes out of the same renderers the page
uses. An export built from a second set of formatters drifts from the screen
within a week, and the first time it matters is when somebody circulates the
drifted version.

Charts are inline SVG rather than rasterised figures. They inherit the page's
typefaces (a plotting library uses whatever font it finds on the host, so the
same report rendered on a laptop and in a container showed two different
faces), they stay sharp when a reader zooms to check a figure, and they carry
no background tile. Dropping the plotting library also removed the project's
heaviest dependency and its only display-server workaround.

Presentation follows published research rather than a web dashboard: fixed
column order, dollars in millions, negatives in parentheses, multiples to one
decimal with a trailing `x`, `NM` where a ratio is not meaningful, the
subject separated from its peer set, and summary statistics ruled off
beneath. These are conventions to be matched, not a design to be invented.
An analyst reads dozens of these a week and finds a number by its position.

All model and filing text is escaped at this boundary. `ui/markdown.py`
converts the finished note from the small Markdown subset Call A emits,
rather than taking a general Markdown dependency, because the risk worth
guarding against is not an unsupported construct but unescaped model output
reaching the page as markup.

---

## 10. Extending it

The seams, in the order a fund would use them.

**A different model provider.** Implement `llm/provider.py`. Nothing else
imports the SDK. The provider must support citations with character offsets
and structured output; if it does not support both, the two-call split in §6
still holds.

**A different metric taxonomy.** `config/metrics/canonical.yaml` defines what
a metric means independently of any filer's tag names. Everything downstream
reads canonical names only and never touches a raw XBRL tag, so adding a
sector or a line item is a configuration change.

**A different sector classification.** `config/settings.yaml` maps SIC
ranges to sector classes. First match wins, so narrower ranges precede
broader ones they overlap.

**Additional sources.** Implement the `sources/base.py` document interface
and assign a tier. The prompts already bind tier to attribution, so a new
Tier C source is attributed as opinion without a prompt change.

**Different house conventions.** The renderers in `ui/components.py` are pure
functions, so a fund that formats comps differently changes one module and
the tests tell them what they broke.

### Known limits

Stated because a roadmap that omits them is marketing.

- **Segment revenue is not broken out.** `companyfacts` is undimensioned, so
  segment detail requires parsing the dimensional XBRL instance. The revenue
  build in the financial summary is therefore consolidated.
- **Quarterly data is retrieved but not used.** Series construction filters
  to annual periods. Relaxing the filter is a change to one predicate, not a
  new fetch.
- **Semantic citation support is unverified.** See §2.
- **The discount rate is a convention, not a derivation.** Deriving it from
  the filer's own capital structure is the obvious next step and is labelled
  as missing in every assumptions table.
