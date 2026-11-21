# Asset Researcher — everything, in one place

This is the only document written for you. It carries every choice made
and why, the vocabulary you will need to defend in a room, and the
evidence behind each claim the project makes.

It replaces thirteen separate files. If something here needs more
explaining than it gets, that is a signal the thing itself needs
rebuilding, not that this page needs another appendix.

---

# 1. What it is, in one paragraph

A ticker goes in. About a minute later a sourced research note comes
out: the filed financial record, the narrative management wrapped
around it, and the places where the two do not agree. Every figure is
read from the company's XBRL submissions to the SEC. Every narrative
claim carries a citation resolved against stored source text. It issues
no buy, sell or hold.

The decisive audience is not the daily user. It is the person reading
it to decide whether you are worth hiring.

---

# 2. Running it

**The live site.** One link, one passphrase, both set in Streamlit Cloud
under Settings → Secrets: `DEMO_PASSPHRASE` and `SAMPLES_KEY`. The
samples key is a different value from the passphrase on purpose: the
sealed archive is committed to a public repository, so sharing one
secret between them would turn that blob into an offline guessing
oracle for the secret guarding the API keys.

**Locally.**

    .venv/bin/python -m pytest -q              # the whole suite, no network
    .venv/bin/python scripts/check-credentials.py
    .venv/bin/streamlit run app.py

**Rebuilding the sample notes.** Each costs a real API call.

    .venv/bin/python scripts/publish-sample.py --ticker ADP
    SAMPLES_KEY='<from .env>' .venv/bin/python scripts/pack-samples.py

---

# 3. Vocabulary you need to defend

Every reader-facing term was checked against documents a buy-side
professional would accept: SEC filings, CFA Institute standards, FDIC
and World Bank definitions, Nareit, and named practitioner frameworks.
A term that was only *plausible* was replaced.

Learn the first group. They are the ones someone will ask about.

## The five that matter most

**Price-implied expectations.** The tool's best idea, and the number
the note now leads with. Instead of forecasting a value and comparing
it to the price, it starts from the price and solves backwards for the
growth the price requires. Mauboussin & Rappaport, *Expectations
Investing* (Columbia, rev. 2021): the method "starts with what we know,
the stock price, and asks whether the expectations for the company's
financial performance implied by the stock price are justified."

If asked why you lead with it: because it does not depend on a discount
rate you chose. A target does.

**Variant perception.** Where this analysis departs from consensus.
Traceable to Michael Steinhardt; CFA Institute's *Enterprising
Investor* (Rimkus, 2015) uses it verbatim — "our ability to distinguish
our perceptions from the market's." The earlier label, "variant view",
returned no professional usage at all.

**Located, not verified.** The single most important sentence in the
product. Locating a quote establishes that the quoted text sits where
the citation says it does. It establishes nothing about whether it
supports the claim built on it. Those fail independently, and almost
every tool built on filings conflates them.

If asked whether this is hedging: it is the opposite. Hedging reduces
your exposure. This increases it, by naming the surface you did not
check.

**Mandate, strategy, style.** CFA Standard III(C) puts the three words
in sequence — "managing a portfolio to a specific mandate, strategy, or
style" — so the tool is free to use the loosest. A mandate is a
document agreed between an asset owner and a manager. It is not
something typed into a textarea in ninety seconds. The form therefore
says **Strategy** and **How you invest**; "mandate" survives only where
the structured profile genuinely carries horizon, constraints and
concentration.

**Reconciliation — the word is already taken.** Under Reg G and Item
10(e) of Reg S-K, "reconciliation" means non-GAAP to GAAP. A PM opening
a section called *Reconciliation* expects an adjustments bridge. The
section is therefore **Management vs. filed figures**.

## Renamed, and what each replaced

| Now reads | Was | Why |
|---|---|---|
| Bear case | Counter-case | No usage in any filing, CFA document or published note. CFA's own heading is "Investment Risks" |
| Price-implied expectations | Implied expectations | The canonical form buys a named framework for one adjective |
| Current valuation | Market pricing | CFA puts multiples under "Valuation" |
| Management vs. filed figures | Reconciliation | See above |
| Distress and manipulation screens | Health | The contents are Altman, Piotroski and Beneish — named screens are the credibility; "Health" hid it |
| Questions for management | Questions | One word, and it becomes something a PM recognises |
| Business description | Note | The whole document is the note |
| Investment summary | Summary | CFA's heading, and it says which kind of summary |
| Nonperforming loans / total assets | Nonperforming Loan Ratio | **A factual mislabel.** The World Bank series (FB.AST.NPER.ZS) divides by gross loans. Ours divides by total assets, giving a number roughly half what a bank analyst expects |

## Terms kept, and the defence for each

- **Net debt, net cash, Net debt / EBITDA** — formula matches filings
  exactly (Vulcan Materials 10-K FY2025 non-GAAP reconciliation).
- **Efficiency ratio** — matches the FDIC *Quarterly Banking Profile*
  definition exactly.
- **FFO before gains on disposal** — Nareit's 1991 white paper, restated
  2018. The label deliberately does not claim Nareit FFO when the
  gain-on-sale deduction is unavailable.
- **Net interest income / total assets** — *not* called NIM, because NIM
  uses average earning assets and we cannot build that denominator.
  This restraint is worth pointing at in a demo: it is what a PM checks
  for.
- **Proved reserves** — "proved", not "proven", is the SEC's spelling in
  Reg S-K Subpart 1200.
- **Catalysts** — CFA requires the question: "what will prompt the market
  to re-price the security?"

---

# 4. The choices, and why

## Why the shell looks like this

The application shell executes the category standard at a high craft
bar — the restraint register of Linear and Stripe. Near-white ground,
hairline borders, one spacing scale, monospace for every figure, and
colour withheld from the whole surface except the divergence count and
the focus ring.

This was chosen from four rendered comps: an accountant's worksheet, an
engineering drawing, giant type, and the category standard. You picked
the standard deliberately, for a specific professional audience, and
asked for minimalism rather than invention. It is recorded in
`PRODUCT.md` as a standing commitment so it is not relitigated.

**The rule everything rests on:** one column, declared once, inherited
by everything. No descendant sets its own width, and no width is
expressed in `ch`, because a `ch` resolves against a proportional face
and lands on a fraction. The shell this replaced carried 394.017px,
528.62px and 630.59px — three container edges no two blocks could ever
share, which is what produced three competing centre axes.

One exception, stated: a paragraph of running prose may carry a reading
measure, because line length is a property of text rather than layout,
and it keeps the column's left edge so it creates no competing axis.

## Why the note keeps its own look

The research note was left unrestyled: warm paper, a serif display
face, a 9rem left rail, square corners. It is a document, and a
document wants a second axis to scan down. The shell is chrome around
it. The two are stated as different surfaces in `DESIGN.md` rather than
smoothed into one.

## Why it refuses things

- **No discounted cash flow for a bank or a REIT.** The model discounts
  unlevered cash flow to an enterprise value and bridges to equity
  across net debt. For a deposit-funded balance sheet that bridge is
  meaningless; for a REIT valued on FFO against asset value it
  describes nothing. Realty Income's target cell reads **Declined**,
  with the reason in place.
- **No model on a stale input.** If a load-bearing line stops more than
  one filed period behind the filer's newest, the model refuses rather
  than building on a figure the company no longer reports.
- **No negative value per share.** Equity is an option with a zero
  floor. A negative residual describes leverage, not mispricing, so it
  prints NM.
- **The model may not write a number.** Every figure in prose is
  inserted by the code from filed data, and a verifier flags any that
  are not.

Declining to answer is a feature. A tool that always produces a number
produces one for the companies where it should not.

## Why these six companies

Realty Income, Costco, Lumen, ADP, Cintas, Fastenal.

Ford and Truist were dropped. Ford paired good reasoning with a +564%
headline, a blank FY2025 revenue, and a variant perception its own
table contradicted. Truist was a null note that missed a thesis sitting
in a three-day-old filing.

Cintas and Fastenal replaced them, chosen because every load-bearing
line resolves current — verified for nothing, before any money was
spent, by assembling their data and checking the tags.

**Know this before you present:** Cintas has a pending UniFirst merger
with an FTC timing agreement. Its standalone valuation therefore reads
as overvalued, because the price embeds deal completion. The note says
so and names the binary. That is correct behaviour, and someone will
ask.

---

# 5. Validation — the evidence for each claim

## The suite

582 tests, no network, about forty-five seconds. Every fix below was
written as a failing test first, and the failure was watched before the
fix was written.

## What the design scores, measured in the live DOM

| Layer | Before | After |
|---|---|---|
| First impression (50ms) | 41 | 74 |
| Processing fluency | 34 | 86 |
| Perception bias | 55 | 80 |

| Measure | Before | After |
|---|---|---|
| Container widths on home | 4 | 1 |
| Competing centre axes | 3 | 0 |
| Muted text contrast | 3.19:1, fails AA | 4.91:1 |
| Field boundary contrast | 1.27:1, fails | 3.27:1 |
| Type families rendering | 3 | 2 plus a monospace |

The mechanical design detector went from 22 findings to 2: one is a
mask stop that is an alpha value wearing a colour's notation, the other
a deliberate 3px severity rule in the note.

## The defects that mattered, and how each was found

**A valuation input pointing at a dead tag.** Four of six filers had a
debt or capital-expenditure mapping resolving to an XBRL concept the
company had abandoned — ADP's total debt last filed FY2011 at $37m
against real debt near $5bn. The series looked complete, so nothing
objected, and the note bridged enterprise value to equity across $4.4bn
of net cash the company does not have.

*Cause:* the resolver received about 500 bare tag names with no way to
tell a live tag from a dead one. Each concept now carries the last year
the filer reported it.

*Effect, in the output:* ADP's equity value fell from $134.2B to
$129.2B and its target from $357.68 to $345.10. Lumen stopped declining
and now leads with a real implied growth rate, because its capital
expenditure resolves to FY2025 instead of FY2013.

*Found by* checking candidate filers before paying to build notes on
them.

**Browser Back did nothing.** The listener was a JavaScript
SyntaxError: `\n` escapes were consumed by a non-raw Python string, so
the browser received a string literal split across two lines and the
script never parsed. The in-app Back buttons kept working because they
are server-side widgets — which is why the fault presented as "only
your buttons work."

*Found by* reading what the browser was actually served, not the code.

**Three tests were matching the stylesheet.** `at.markdown` returns
every markdown block, and the first is 60KB of CSS carrying every
selector and comment as text. Two tests "proved" a component rendered
while the line emitting it was deleted. A third reported that eleven
hostile passphrases **opened the gate**. They did not — "Get started"
appears in a CSS comment about phone layout.

A false positive on an authentication property is the dangerous
direction. Fixed once in a shared helper that reads the page the way a
reader sees it.

**The honest sentence was dead code.** The function carrying "locating
a quote is not establishing that it supports the claim" had no callers,
while the screen said "every claim is traced back to the document it
came from." The qualification now renders and the dead block is gone.

**Implementation vocabulary reached the reader.** Two notes carried
"the renderer will populate" inside cited sentences. Our own prompts
taught the model that word. The prompts now forbid it and a test fails
on any note that shows it.

**The first keyboard stop had an invisible focus ring** — `#faf8f3` on
`#fcfcfd`, 1.04:1, a leftover from the replaced design.

**The gate's backoff was a dead end** — field and button both removed,
frozen countdown, no instruction to reload, on the first screen.

**A note rendered through a letterbox** — 40,000px of document in a
2,000px frame. The frame is same-origin, so the note now sizes it to
its own content and the page scrolls once.

## What the review panels said

A portfolio manager read four notes cold and said yes to a second
meeting. What earned it, in their words: the ADP note argues that for
that issuer the quality screen and the valuation input are the same
contaminated number — because gross profit and operating income do not
map, so the only margin series available is net margin, which carries
the client-funds spread through the largest rate move in decades — and
then refuses to resolve it from data it does not have.

They also broke the project's flagship claim. An earlier version of the
written guide said Realty Income's per-share FFO, operating cash flow
and net income "all fell across FY2022 to FY2024". The window ended at
the trough, FY2025 was higher in the same table, and the note's own
Limitations section said the finding might be wrong. The claim is now
the one the evidence supports: the spread narrowed until growth was
scale-additive rather than per-share accretive, while the share count
doubled.

Two of their findings did not hold — they were reading notes that had
already been rebuilt. Both were checked before anything changed.

---

# 6. What it does not do

Stated here rather than discovered.

- **One discount rate, 8.5%, for every filer.** A company with no net
  debt and one with negative book equity get the same number. Calling
  it a convention is honest and is not the same as having a view.
  Everything downstream inherits it. This is why the note leads with
  the implied growth requirement, which is solved from the price and
  does not depend on the rate.
- **Consensus is a recommendation count, not an estimate.** The note
  publishes how many analysts rate the name a buy, a hold or a sell. It
  does not say what they expect it to earn; that data is behind a paid
  tier.
- **No segment revenue.** The SEC's `companyfacts` API is undimensioned.
- **Multiples are trailing, on the last reported fiscal year**, not
  twelve months.
- **The peer set is a vendor list**, pinnable by hand, labelled as a
  starting point.
- **Semantic citation support is unchecked.** Provenance is verified;
  inference is not.
- **An acquisition sets the growth record.** Filed revenue does not
  separate organic growth from a deal.
- **Fiscal labels follow the first-week rule**, so for some retailers
  the columns sit a year off their own 10-K cover.
- **Non-USD filers get an incomplete note, deliberately.** Monetary
  facts in another currency are refused rather than converted.
- **A report lives only in the session.** Download it to keep it; the
  browser's Back asks before discarding one.
- **The samples carry the figures they were built with.** They are
  artifacts: real runs against real filings on the date shown on each
  note.
- **No active-section indicator while scrolling.**
- **A note still wants a route of its own** rather than a frame.

---

# 7. Operations

**Spend.** Each note costs about $1.10 to build. The six samples cost
roughly $13 across the rebuilds, including two that were thrown away
and rebuilt after defects were found in the output.

**Secrets.** `.env` locally, Streamlit Secrets in production. Never in
a commit — a commit guard refused two drafts of this project's own
documentation for carrying the passphrase, which is the guard working.

**The archive.** Six notes, sealed, committed as a blob. Without the
key it is bytes.
