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

## What it found on Realty Income

This one is in the samples, so the claim can be checked against the note
rather than taken on trust.

Realty Income is a net-lease REIT that has grown its asset base steadily
and says so. The note agrees on the arithmetic and disagrees on who the
growth went to. Five of eight management claims diverge from the filed
figures, and the one that matters reads:

> The cost-of-capital claim is supported at the enterprise level and
> contradicted at the per-share level for three consecutive years.
> External growth was funded at a cost that did not leave a spread for
> existing holders once dilution is counted.

Per-share funds from operations, per-share operating cash flow and
per-share net income all fell across FY2022 to FY2024 while the asset
base compounded. Both statements are true at once, which is the whole
point: a screen shows the enterprise growing, and the per-share series
shows the existing holder standing still. Ninety of ninety citations
resolve to the filings.

The same note also declines to produce a valuation. A discounted cash
flow discounts unlevered cash flow to an enterprise value and bridges to
equity across net debt, which does not describe a company valued on funds
from operations against asset value. So the headline reads Price / FFO
14.7x and the target cell reads **Declined**, with the reason in place
rather than a blank. Truist is refused for the opposite reason: deposits
are the funding of a bank, not a claim to subtract.

Declining to answer is a feature here, not a gap. A tool that always
produces a number produces one for the companies where it should not.

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

424 tests, no network, about five seconds.

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
- **An acquisition sets the growth record.** The projection takes a capped
  revenue CAGR from filed statements, and filed revenue does not separate
  organic growth from a deal. A company growing 5% organically that closed
  an acquisition in the final year reports a three-year CAGR well above
  that, and the summary's first sentence then says the price asks less
  than the record delivered. The magnitude guard is a unit-error check and
  a 2.4x revenue step does not trip it. Beneish does move on the sales
  growth index, which is the right flag for the wrong reason.
- **Fiscal labels follow the first-week rule, not the filer's cover.** A
  year ending 2021-01-30 is labelled FY2021. Walmart agrees; Target, Gap
  and Kohl's call it fiscal 2020, so for those filers the columns sit a
  year off their own 10-K. A 53-week year passes the duration check
  correctly but is not flagged, so the extra week prints as growth.
- **Non-USD filers get an incomplete note, deliberately.** Monetary facts
  in another currency are refused rather than converted, because the
  market capitalisation they would be priced against is a USD quote. The
  note says so and the figures are absent rather than wrong.
- **Banks and REITs get no discounted cash flow.** The model discounts
  unlevered cash flow and bridges across net debt, which does not describe
  a deposit-funded balance sheet or a company valued on funds from
  operations against asset value. Comparables, the statement table and the
  health screens still run, sector-gated.
- **No active-section indicator while scrolling.** Twenty sections down a
  long document and the index marks your place only after a click.
  Mapping scroll position to a nav item needs script, and faking it in CSS
  would mark the wrong section.
- **Focus does not return to the trigger when a dialog closes.**
  Streamlit owns the dialog. Focus enters it, the trap holds, Escape
  closes it and the background is inert; on close focus lands on the body,
  which is not reachable without script.

## Links

- Sample notes, pre-rendered: *(deploy link)*
- Live tool: *(deploy link)*
- Source, with the architecture and design notes: *(repository link)*

Research assistance, not investment advice. It issues no recommendation.
