# Asset Researcher — everything, in one place

This is the only document written for you. It carries every choice made
and why, the vocabulary you will need to defend in a room, and the
evidence behind each claim the project makes.

It replaces thirteen separate files. If something here needs more
explaining than it gets, that is a signal the thing itself needs
rebuilding, not that this page needs another appendix.

---

# 1. What it is, in one paragraph

A ticker goes in. About seven minutes later a sourced research note
comes out: the filed financial record, the narrative management wrapped
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

## How long a report actually takes

**About five minutes, not one.** Measured tonight against the real
APIs: eighteen sample notes across three full rebuilds at five to
seven minutes each, and two reports driven through the interface
itself at about seven, timed from the click to the file landing on
disk.

The interface said "about a minute" until that was measured, and the
progress bar filled in seventy-five seconds. A reader who presses the
button on a one-minute promise and is still waiting six minutes later
concludes it has hung — which is the exact impression the bar exists
to prevent. Both now say five, and the bar creeps for a further five
rather than freezing near-full.

The cost is about $1.20 a report, which was roughly right already.

## "Report" in the app, "research note" in the document

Deliberate, and worth having the answer ready because it is the kind
of thing a reader notices.

The interface says **report** everywhere a reader acts — Start a
report, Generate report, Reports. It is the plain word for the thing
the button produces, and the screen that asked someone to "build a
note" was asking them to do something they had no name for.

The artifact says **research note**, which is the industry term for a
single-issuer piece of sell-side or buy-side writing, and it is what
the downloaded file is called. Calling the document a report would
make it sound like a filing or a compliance output, which is the
opposite of what it is.

So: the app produces reports; what you get is a research note. If
someone asks, that is the answer.

## The design words, and what they actually mean

You are not a designer any more than you are a finance person, and
these five come up every time the shell is discussed. Each one is a
real decision in the current build, so each is defensible in a room.

**Display rank.** The size a page reserves for its single most
important line, far enough above body text that no one has to be told
which it is. The old shell had none: every heading was 15px semibold
sans, so a section head and a paragraph were the same voice at two
sizes. Having a display rank is the difference between a page that is
composed and one that is merely tidy.

**Processing fluency.** The finding that information which is easier
to process is judged more *true*, not just more pleasant, and that the
effect works below conscious awareness. It is why a stray typeface or
a colour that is nearly-but-not-quite a system colour costs more than
it looks like it should: the reader cannot name what is off, and
attributes the unease to the content. On a document arguing from
filings, that is expensive.

**Token role.** A colour is not just a value, it is a job. `#1b3a8f`
is "the divergence count and links", not "blue". The moment the same
blue also fills a button or tints a panel, it stops being a signal and
becomes decoration, and the signal is gone. Most design systems rot
this way rather than by picking bad colours.

**Optical centre.** An object centred by arithmetic looks slightly low,
because the eye reads the centre as higher than it is. The gate sits a
little above true centre for this reason. It is the kind of thing
nobody notices when it is right and everybody feels when it is wrong.

**Safe centring.** A CSS detail worth knowing because it bit this
build. Centring content vertically splits any overflow evenly above
and below — and the half above the top of a scrolling box cannot be
reached, because scroll position does not go negative. On a short
window the gate's own product mark was cut off with no way to scroll
to it. `safe` centring falls back to top-aligned at exactly the point
where centring would start hiding something.

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

## Why the shell looks like this — The Broadsheet

The shell before this one executed the category standard at a high
craft bar: the restraint register of Linear and Stripe. You graded it
**6/10** and named the fault exactly — "still feels lacking instead of
tastefully minimal."

That was the right read, and the diagnosis is worth keeping because it
is not obvious. The old shell was not badly made. It was *neutral*. It
committed to no idea at all, and the mechanical proof of that is that
every heading on every screen was set in the same sans at 15px weight
600. There was no display rank anywhere in the product. A section head
and a line of body copy were two sizes of one voice, so nothing on the
page could be the most important thing on it.

**The idea it commits to now.** Every competitor in this category
shouts in bold sans. The shell whispers: a high-contrast serif held at
weight **300** carries every display line, a functional sans carries
every working surface, and colour is withheld from the entire page
except the one figure that encodes a judgement. The register is a
financial broadsheet, which is also the register of the thing the
product makes.

If someone asks why a serif: because the product is a *publication*.
It produces a research note, which is a document in a publishing
tradition, and a serif at display size is what that tradition looks
like. If they ask why so light: because weight is volume, and the one
thing a credibility artifact cannot afford is to sound like it is
selling. Restraint is the argument.

**Where it came from.** Nine Refero style references were read in
full, and the two closest were Public (monochrome editorial, the serif
held light, one accent reserved for links) and Wealthsimple (editorial
display serif over a functional sans, hairline rules instead of card
chrome). Neither palette nor typeface was reused. What was carried is
the convention inversion and the hairline-over-chrome discipline. The
result must not be mistakable for either site, and is not.

**Why the shell is COLD and the note stays warm.** This is the one
decision the whole thing hangs on. The ground is a cold marble
`#f4f6f9`; the note keeps its warm paper `#faf8f3`. They are
deliberately different surfaces, so the moment a note opens, a reader
can feel they have moved from the chrome into the document. The shell
is the frame; the note is the object. Two centred axes on one screen
was the old fault, and two *surfaces* with one axis each is the fix.

**One accent, `#1b3a8f`, and almost nowhere.** It is on the divergence
count and on links, and on nothing else. An accent that appears twice
is decoration; appearing once, it reads as switched on. On the home
screen it does not appear at all — there is no divergence count there
— so that screen is entirely monochrome, which is correct rather than
a miss.

**The thing that was in the code and should not have been.** The focus
ring on every control in the product was `#4f46e5`. That is Tailwind
indigo-600 to the digit, and indigo is the single most recognisable
fingerprint of a machine-generated interface. It sat on a product
whose whole argument is that a person built it carefully. It was also
measurably broken: the comment beside it claimed 4.4:1 on the bypass
link's near-black pill, and the real figure was **2.88:1**, which
fails the 3:1 that WCAG 2.2 requires of a focus indicator. The number
that justified the colour had never been true. It is `#2563eb` now, at
4.77:1, 5.17:1 and 3.50:1 on the three grounds it lands on.

**Cards came off two things.** The Get started steps and the Reports
index were both boxed. Both failed the same test: take away the
border, the fill and the radius, and nothing becomes harder to read or
to act on, because the hairlines between the columns and between the
rows already do the grouping. A container that groups what the content
already groups is decoration. It also made instructions read as a
widget dropped onto the page rather than part of it. Every research
index worth copying — OpenAI, Anthropic, Runway, Cartesia — renders
rows on the page with one hairline between them, and that is what this
does now.

**The rule everything rests on:** one column, declared once, inherited
by everything. No descendant sets its own width, and no width is
expressed in `ch`, because a `ch` resolves against a proportional face
and lands on a fraction. The shell this replaced carried 394.017px,
528.62px and 630.59px — three container edges no two blocks could ever
share, which is what produced three competing centre axes.

One exception, stated: a paragraph of running prose may carry a reading
measure, because line length is a property of text rather than layout,
and it keeps the column's left edge so it creates no competing axis.

## Why there is one palette and no dark mode

There was a dark mode. It is gone, and the honest version of why is
worth more than the design argument that used to sit here.

It shipped half-done. The dark scheme answered every shell token and no
document token, on the assumption that a note always renders in its own
frame and keeps its paper world. That is true of the reading screen and
false of the report screen, which writes the document straight into the
page — so on the longest screen in the product the title was near-black
on near-black at 1.06:1 and the prose about 1.4:1. A page of readable
tables with invisible headings between them.

Asked which way to commit, you said to delete it: it was the last thing
you cared about and the design work mattered more. So it was deleted
rather than half-kept — thirteen tests retired with it, and
`_scheme_block("dark")` now raises deliberately with the message "no
dark scheme: this product has one palette", so nobody half-reintroduces
it by accident.

What this buys: one committed light palette, measured once, on one set
of grounds. A half-written second scheme does not fail by being ugly.
It fails by letting a light token survive on a dark ground, which is
invisible to whoever wrote it and the only thing the reader sees.

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

834 tests, no network, about a minute. Every fix below was
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

**One reviewer's reports were on every other reviewer's first
screen.** Reports a visitor generates are written to disk, so that
clicking a row on the index cannot destroy one. The store was a single
directory in a single container, and every visitor to the deployment
shares that container — so a reviewer who generated a report on a name
they were considering put that ticker at the top of the index for
everyone else holding the link, with the document one click away. On a
tool shown to portfolio managers the ticker someone chose to research
is itself the sensitive thing, and this demo goes to more than one
person. Each visitor now has a scope of their own, carried in the URL
beside the unlock token.

*Found by* reading the diff. Nothing about the running app looks
wrong, and the module's own docstring asserted the opposite.

**Dark mode stopped at the shell, and the report screen is not the
shell.** The dark scheme answered every shell token and no document
token, on the stated assumption that a note renders in its own iframe
and keeps its paper world. True of the reading screen; false of the
report screen, which writes the document's markup straight into the
page. So on the longest screen in the product the title was near-black
on near-black at 1.06:1, the prose about 1.4:1, and only the tables
survived because they paint their own white — a page of readable
tables with invisible headings between them. The run-status panel and
the progress bar went the same way.

**A chart whose caption described a different series from its bars.**
ADP's Financials row reads FY2026 5,245; the chart above it said
$5.4B. The bars were right — the `describe=` beside them read raw
operating cash flow, so the caption and the spoken description printed
operating cash flow under a label saying capital expenditure had been
taken off. $5,444m is exactly that note's operating cash flow,
recovered from its own ratios. The chart was also computing its own
free cash flow with an untagged year defaulting to zero capex, which
is verbatim the defect the valuation module documents having fixed —
surviving in a second copy because the fix was applied to one. There
is one implementation now.

**Summary statistics that contradicted their own caption.** "Excluding
the subject and extreme multiples" sat under a table whose screen
covered two of its six ratios. Realty Income shipped with a peer at a
3,473% net margin — a revenue denominator filed two orders of
magnitude out — and the printed peer mean margin read 462.8%. It now
reads 32.8%. The outlier's own row still shows its real figures:
suppressing them would be editing the data.

**A sentence that drew a conclusion it had not checked.** "The price
therefore rests on expectations not present in the filed cash flow
history" printed on every note. It follows only when the price implies
more growth than the record delivered, and on two of four it was
backwards — telling a reader to interrogate optimism in a price that
embeds caution. It compares now, and says so when there is no model to
compare against.

**The lead figure described a deduction it does not make.** Realty
Income's masthead read "Price / FFO — funds from operations, before
gains on disposal". Gains on disposal are in net income, which is the
first term of the formula. The note's own body said so four sections
down. It reads "Price / FFO proxy" now, and says it keeps those gains
in.

**A 35,000px document with no navigation past the first screen.** The
note's frame is sized to its own content so the page scrolls once
instead of through a nested scrollbar. The cost, unnoticed until it
was measured, is that the note's document never scrolls — so its
sticky section index sat at viewport-top 773 at the top and −19,227
twenty thousand pixels down. The index now lives in the shell, which
is the thing that scrolls.

**Prose outside a comment, which CSS fails silently on.** An edit left
two sentences and a dangling `*/` in the stylesheet. The browser
discarded everything to the next closing brace, the phone table rule
stopped applying, and the home table went back to overflowing a 375px
screen — the exact defect that rule exists to prevent. The suite was
green throughout, because every test about it asked whether the text
was in the stylesheet, and it was, inside the wreckage.

### Examined and deliberately not changed

Three findings from reviews did not survive checking, and saying so is
part of the record:

- **Cintas reporting identical total debt in two years** was called a
  stale tag. Short-term debt rises from nil over the same period with
  total debt flat, which is what a maturing tranche reclassifying looks
  like, and the note's question to management about the intended
  permanent capital structure is the right question to ask about it.
- **The terminal-share figure taken from the baseline run** was called
  a defect. It sits beside the model value at default assumptions and
  both describe the same run; taking it from the solved run would make
  two halves of one sentence describe two different runs. What was
  wrong is that it did not say which run it meant, and now it does.
- **The gate's password field having no accessible name** was
  reported because its label is hidden with `display: none`. The
  running app's accessibility tree reads `textbox "Passphrase"`:
  Streamlit's collapsed-label mode sets `aria-label` on the input from
  the same text, so the name never depended on the label element. The
  visually-hidden replacement written for it was worse than nothing —
  it never set `display`, so it could not take effect and left a rule
  in the sheet that did nothing. Reverted.
- **Pointing the document's focus ring at the shell's focus token**
  was recommended for consistency. That rule travels with the exported
  file, which carries no shell tokens, and an undefined custom property
  invalidates the declaration — the change would have removed the focus
  outline from every downloaded note, in the name of accessibility.

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
the one the note can carry: on a net-income-plus-depreciation proxy per
diluted share, the metric fell from FY2022 to FY2024 and recovered only
partially in FY2025, still short of FY2022, while the share count more
than doubled and interest expense outgrew revenue.

**Do not say "the spread narrowed" in a room.** A reviewer checked that
sentence against the note and it does not hold: the note states the
spread is not quantifiable from the disclosure, and revenue measured
against the gross real estate balance improved in every year. The
corrected claim above is what the filings support.

Two of their findings did not hold — they were reading notes that had
already been rebuilt. Both were checked before anything changed.

---

# 6. What it does not do

Stated here rather than discovered.

- **One discount rate, 8.5%, for every filer.** A company with no net
  debt and one with negative book equity get the same number. Calling
  it a convention is honest and is not the same as having a view.
  Everything downstream inherits it, the implied figures included.

  **The implied growth is solved AT 8.5%.** The solver varies growth
  while holding everything else fixed, so the headline figure moves
  when the rate moves. An earlier draft of this page said the opposite,
  and a reviewer checked it against the code. The note leads with the
  implied requirement because it frames the price as a question rather
  than asserting a value, not because it escapes the assumption. The
  implied discount rate printed beside it is the same solve run the
  other way: each is the other's complement, each holding the other at
  a convention, and the page does not yet say so.
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
- **A report you generate outlives your reloads and not the
  container.** The rendered document is written to disk the moment it
  exists, so it joins the index on the first screen and clicking a row
  cannot destroy it. The deployment's filesystem is ephemeral, which is
  the right lifetime for a demo and the wrong one for anything you want
  to keep — download it. Each visitor sees only their own, through a
  scope carried in the URL; anyone you send that URL to sees them too.
  The browser's Back is silent unless the save actually failed, which
  is the one case where leaving loses something.
- **The samples carry the figures they were built with.** They are
  artifacts: real runs against real filings on the date shown on each
  note.
- **No active-section indicator while scrolling.**
- **A note still wants a route of its own** rather than a frame. The
  frame is sized to the note's full height so the page scrolls once,
  and the consequence is that nothing inside the note can be sticky —
  its section index is rebuilt in the shell to work around exactly
  that, and the table headers inside it cannot be recovered the same
  way. A per-note route would end both.

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
