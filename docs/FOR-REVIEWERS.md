# Asset Researcher

A ticker goes in. About a minute later a sourced equity research note comes
out: the filed financial record, the narrative management wrapped around
it, and the places where the two do not agree.

## The problem

A PM at a fundamental fund spends three to four hours assembling a pitch
from the same sources every time: the 10-K, recent 10-Qs, the proxy, any
8-Ks, a peer screen, and whatever news moved the name. The sources are
fixed and the assembly is mechanical. The judgment is not.

Quant shops automated the assembly years ago. Smaller fundamental shops
have not, because the tooling assumes a data budget they do not have. This
is the assembly, built on sources that are free and authoritative.

It does not form a view. There is no buy, sell or hold anywhere in it.

## What makes it different from a chatbot over filings

A chatbot answers, and the reader cannot tell a quotation from a
recollection. Three constraints make that distinction checkable.

**The model may not write a number.** Every financial figure is read from
the company's XBRL submissions to the SEC and inserted by the renderer.
Both writing prompts forbid a figure in prose, and a verifier flags any
that appear. So the model writes "operating margin contracted, and the
decline outpaced the revenue slowdown" where it could have written "fell
240bps to 29.1%". Less satisfying, and the only version you can trust
without checking.

**Citations are resolved, not asserted.** Claims carry character offsets
checked against the exact stored source text. The interface says
*located*, not *verified*, because locating a quote is not establishing
that it supports the claim. The system checks provenance, not inference,
and says so.

**The counter-case is mandatory.** Every report states the evidence against
its own thesis and what would falsify it. A report that returns an empty
one gets a visible warning instead.

## What it actually found on Apple

The note opens with a sentence composed from filed data:

> At 51 times free cash flow the price requires 15.8% annual growth. The
> filed record compounded at 6.1% over five years.

Then the part a screen will not give you. Cash conversion has fallen from
126% of net income to 99%, days sales outstanding have risen from 26 to 35,
and the accrual ratio has crossed from −6.7% to +0.1%. Management describes
cost discipline; the receivables are building. That reconciliation is the
product.

It also declines to lead with its own price target. A single-stage DCF on a
company like Apple lands far from the market, and the report says the gap
describes the model rather than a mispricing, then puts the reverse solve
first instead. What the price *requires* is arguable. "The model says $210"
is not.

## How it is built

Python. SEC EDGAR and XBRL for everything financial, Finnhub for quotes and
a peer list, optional user-supplied URLs classified as secondary. A
deterministic quantitative layer does concept resolution, series building,
validation, comparables and valuation. Two model calls sit on top: one
produces cited descriptive sections, one reasons over that plus the filed
series. They are separate because the API rejects citations and structured
output in the same request.

The view layer is hand-built: a stylesheet, HTML components and inline SVG
charts, no component library. The screen and the exported file render from
one ordered section list, so they cannot drift.

361 tests, no network, about five seconds.

## What it does not do

Stated here rather than buried.

- **No segment revenue.** The SEC's `companyfacts` API is undimensioned, so
  segment detail needs the dimensional XBRL instance.
- **Multiples are trailing, on the last reported fiscal year**, not twelve
  months. The most recent results announcement is read, so the narrative is
  current; the comparables table is not.
- **The discount rate is a convention**, not derived from the filer's
  capital structure. Every assumption carries its basis, and the ones that
  are conventions say so.
- **The peer set is a vendor list**, pinnable by hand. It is a starting
  point and the note labels it as one.
- **Semantic citation support is unchecked.** Provenance is verified;
  inference is not.

## Links

- Sample notes, pre-rendered: *(deploy link)*
- Live tool: *(deploy link)*
- Source, with the architecture and design notes: *(repository link)*

Research assistance, not investment advice. It issues no recommendation.
