# Using Asset Researcher

Written for the person reading the output rather than the person maintaining
the code. No programming knowledge assumed.

---

## What it does

You give it a ticker. It reads the company's most recent annual report, proxy
statement and recent 8-K filings directly from the SEC, pulls every financial
figure from the company's own structured submissions, screens a peer set,
builds a valuation, and writes a research note.

The whole thing takes about a minute.

## What it is for

It does the assembly. The 10-K, the proxy, the 8-Ks, the peer screen, the
comps table, the financial summary, the first-pass model: the part of a pitch
that is the same work every time.

It does not form a view. There is no buy, sell or hold anywhere in the output
and no price target presented as a conclusion. What you get is a structured
account of the evidence and an explicit statement of what the current price
requires an investor to believe. The judgment stays with you.

---

## Running a report

1. Enter a ticker in the left panel.
2. Pick a mandate template, or describe your own mandate in your own words.
3. Optionally paste public URLs you want considered, one per line.
4. Press **Generate report**.

### About the mandate

The mandate determines what gets surfaced first, which horizon matters for
catalysts, and how risk is framed. An event-driven reader and a long-only
compounder reader get the same facts ordered differently.

**It never changes the facts.** Same filings, same figures, same citations,
same disclosed divergences, whoever is reading. A finding that is
inconvenient for your mandate is reported exactly as plainly as a convenient
one. If the tool quietly told each reader what they wanted to hear it would
be worse than useless.

Anything the system inferred about your mandate rather than read from your
description is listed under **Sources**, so you can correct it.

### About additional sources

Anything you paste is classified as secondary and attributed as opinion in
the note, never stated as fact. A sell-side note you add will appear as "a
report from X characterises...", not as a finding.

---

## Reading the output

### The header

Five figures, always in the same place.

| | |
| --- | --- |
| **Traded price** | The current quote, with market capitalisation beneath it. |
| **Probability-weighted target** | The three valuation cases weighted 25 / 50 / 25, with the bear-to-bull range beneath. |
| **Implied upside** | The target against the traded price. |
| **Price implies FCF growth** | The free cash flow growth rate the *current price* requires, solved backwards. |
| **Market cap / free cash flow** | What the market pays for a dollar of free cash flow, with the filed growth rate beneath. |

Beneath them sits a verification line stating how many citations were checked
and what share of the note is sourced, and, where relevant, a warning that
the model diverges sharply from the market.

### The tabs

- **Summary** is the one-screen read: where the analysis departs from
  consensus, the valuation picture, the principal divergences, what would
  have to be true, the catalysts, and the questions to ask management.
- **Thesis** carries the argument: trajectory, bull and bear, valuation
  context, and the disconfirming case.
- **Reconciliation** sets every management claim against the filed figures,
  divergences first.
- **Valuation** holds the model: what the market is paying, implied
  expectations, the three cases, the bridge, the sensitivity grid, the
  projection and every assumption with its basis.
- **Financials** is the filed record in statement order, plus trends and
  health measures.
- **Peers** is the comparable company analysis.
- **Management** covers the officers, what their pay rewards, and ownership.
- **Note** is the full descriptive narrative with every claim linked to its
  source.
- **Sources** lists every document used, every gap in the material, and every
  citation with its status.

---

## How to check it

This matters more than anything else here, so it is worth doing once
properly on a name you know.

**Check a number.** Open the Financials tab. Every figure there is read from
the company's own structured submissions to the SEC. Lines set in a lighter
weight (growth rates, margins, free cash flow) are computed from the filed
lines directly above them; everything else is exactly as submitted. Open the
company's 10-K and compare. They will match, because no figure in the report
was written by the model.

**Check a claim.** Open the Note tab. Every claim carries a small bracketed
number that links to the source document. Click one and you land on the
filing it came from.

**Check what it missed.** Open Sources. Gaps in the source material are
listed with a reason. If the proxy could not be found, or a section was
truncated, it says so. A report resting on material it could not read says so
rather than filling the hole.

### What "verified" means, exactly

A verified citation means the quoted text genuinely appears in the stated
document at the stated place. It does **not** mean the claim built on that
quote is a fair reading of it.

The system checks provenance. It does not check inference. That is why the
citations are linked at the point of each claim: so the judgment it cannot
make is cheap for you to make.

The coverage percentage is the share of the note sitting inside a cited span.
It measures how much of the prose is attributed, not how well.

---

## What to be careful about

**The modelled target is the weakest number in the report.** A single-stage
discounted cash flow on a highly rated company routinely lands far from the
market. On Apple it lands roughly 63% low. That is usually a statement about
generic assumptions, not about a mispricing, and the report says so where it
happens.

Read the **implied expectations** instead. "The price requires 17% annual
free cash flow growth against a filed record of 1.5%" is a claim you can
argue with. "The model says $119" is not.

**The assumptions are conventions until you replace them.** The discount rate
is a starting point, not a derivation from this company's capital structure.
Every input is listed with its basis in the Valuation tab, and the ones that
are conventions say so.

**The peer set is Finnhub's, not a considered comparable universe.** Each row
states why it is there (same or adjacent SIC code, relative size) so you can
reject the ones that do not belong. Companies with collapsed earnings produce
extreme multiples; those are shown but marked, and excluded from the summary
statistics.

**The primary filing may be months old.** The report states its age in the
header. Anything after it comes only from 8-K filings and news.

**It is not investment advice** and does not make a recommendation. It
assembles evidence for you to evaluate.

---

## Taking it with you

The left panel offers two exports once a report exists.

**Standalone HTML** is one self-contained file. The charts, the tables and the
styling travel inside it, so it opens on any machine with no access to this
application and prints to PDF with the layout intact. This is the one to
forward.

**Markdown** is plain text, for pasting into a memo, a wiki or an email.

Both carry the same caveats the screen carries: the verification state, the
model divergence warning, the gaps in the source material, and the
disclaimer. A note read six weeks later, detached from the tool that produced
it, is exactly where those matter most.

---

## When something is missing

Sections disappear rather than render empty, and the report says why.

- **No management analysis.** The company filed no proxy statement, or it
  could not be retrieved. Check Sources.
- **No discounted cash flow.** The filings do not support a cash flow model.
  For some filers that is the correct answer rather than a failure.
- **No peer comparison.** No peer had usable multiples.
- **Health measures reported as "not meaningful".** Altman Z, Piotroski F and
  Beneish M were fitted on industrial balance sheets. For a bank or a REIT
  the arithmetic still runs, but the answer means nothing, so a number is not
  shown.
- **A citation marked "unverified".** The quoted text could not be matched
  against the stored source. Treat that claim as unsupported.
