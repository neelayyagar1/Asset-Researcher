# Architect review

A simulated review session. The reviewer is a senior software architect who
builds applications and data pipelines for large enterprise clients. He has
delivered systems *for* finance teams and is not a finance person. He judges
whether a thing is usable, trustworthy, buildable-on and explicable **without**
domain knowledge, and he is hostile to vocabulary that covers for unfinished
thinking.

He reviewed an earlier build and got stuck on a form field labelled *Mandate*.
He remembers.

Session length: about forty-five minutes. Local instance, `localhost:8950`.
He did not press **Generate report**; he was told it spends real money, and he
said that was the most interesting sentence anyone had said to him all day.

---

## Transcript

### 0:00 — The gate

**ARCHITECT:** Don't say anything. I want the first ten seconds cold.

*[He opens the URL. A cream page. A serif wordmark reading "Asset Researcher".
A password box. A black "ENTER" button. Nothing else.]*

**ARCHITECT:** Right. Ten seconds. What I know is: there is a thing called
Asset Researcher, it wants a password I don't have, and it has good
typography. That's it. I don't know what it does, who runs it, whether I'm
supposed to have an account, or what to do if I don't have the password.

**DEV:** The passphrase goes out by email with the link.

**ARCHITECT:** Then the page should say that. One line: "A private demo.
The passphrase came with your link — reply to that email if you've lost it."
Right now the failure mode for a reviewer who mislays it is a dead end with
no exit. There's no support address, no "what is this", nothing. I've shipped
auth gates to enterprises; the thing procurement always flags first is a login
screen that doesn't identify the system.

*[He types `nope123`, presses Return.]*

**ARCHITECT:** Good — "REFUSED. That passphrase is not right." Clean, red
rule, no stack trace. It's an `alert` role, I checked, so a screen reader
announces it. Focus doesn't return to the box though, so a keyboard user has
to find their way back. Small.

*[He opens dev tools. Element inspector.]*

**ARCHITECT:** Interesting. There's a "Deploy" button and a "Main menu" in the
DOM *before* I've authenticated. That's Streamlit's own chrome sitting above
your gate. On a client demo, a stray "Deploy" button in the corner is the
single fastest way to make a reviewer think they're looking at a prototype
rather than a product. Hide it.

*[Types the real passphrase. He's in.]*

**ARCHITECT:** Hold on — look at the address bar. `?k=` and a hex string. What
is that?

**DEV:** A digest of the passphrase. It's so browser Back doesn't log you out.

**ARCHITECT:** So the URL is now a bearer token. Anyone I paste this link to is
in, forever, without the passphrase. You've documented that in the code — I'll
check — but nothing on *screen* tells me. I'm about to copy this URL into a
Slack message to a colleague because that's what people do. Put a line in the
footer: "This link grants access. Don't forward it."

---

### 0:06 — First ten seconds, properly

*[Home screen.]*

> **Asset Researcher**
> Enter a US-listed ticker. The tool reads that company's filings to the SEC,
> pulls the financial record out of them, and writes a research note that
> cites every figure back to the filing it came from.
>
> `BUILD A REPORT`  `HOW IT WORKS`  `READ A SAMPLE`
>
> Samples are already built: instant, and free.
> A new report takes about a minute and spends one live API call.

**ARCHITECT:** *That* is a good ten seconds. Genuinely. I know what goes in
(a ticker), what comes out (a research note), where the data comes from (SEC),
and what the differentiator is (citations). Three doors, each labelled with
what it costs me. I know which one to press. That's better than most
enterprise products I'm paid to fix.

One correction, and it's not cosmetic. "Spends one live API call" — is that
true?

**DEV:** It's... roughly.

**ARCHITECT:** I read the code. It parses the strategy text with a model call,
drafts the narrative with a second, reconciles with a third. That's three,
minimum, and `ESTIMATED_REPORT_COST_USD = 2.00`. Your own deploy doc says
"$1.30 each". So I have three numbers — "one API call", "$2.00", "$1.30" —
and they disagree. Say "about a minute and roughly two dollars of model
time." Nobody minds the cost. Everybody minds being told a number that turns
out to be decorative.

*[He reads the three pillar cards.]*

**ARCHITECT:** "Every figure is filed." Understood. "Every claim is located" —
and then the card explains that locating a quote is not establishing that it
supports the claim. That's an unusually honest sentence and I'd put money on
it being the best thing in the product.

"The counter-case is mandatory." What's a counter-case?

**DEV:** The evidence against the thesis.

**ARCHITECT:** Then say that. Hold that thought, I want to come back to it.

---

### 0:11 — How it works

*[Clicks `HOW IT WORKS`. A long document loads.]*

**ARCHITECT:** Wall of text, no headings visible above the fold, no estimated
read time. But the content... let me read.

*[Two minutes of silence.]*

**ARCHITECT:** OK. The "What it does not do" section is the strongest piece of
writing in this entire project and I want to say that plainly before I start
breaking things. "No segment revenue." "The discount rate is a convention, not
derived from the filer's capital structure." "Fiscal labels follow the
first-week rule, not the filer's cover... Walmart agrees; Target, Gap and
Kohl's call it fiscal 2020." "Non-USD filers get an incomplete note,
deliberately."

I have never seen a product ship a list of its own defects, in public, with
examples. Vendors spend six weeks hiding that list from me during procurement.
If you are using this thing as a credential, that section *is* the credential.
Lead with it.

**DEV:** It's in the How it works page.

**ARCHITECT:** Which is door number two of three, below the fold, after 900
words. Nobody gets there.

Now the problems. Count the terms in that page that I, an experienced
engineer, cannot define: XBRL. 10-Q. Proxy. 8-K. CAGR. Beneish. Unlevered cash
flow. Funds from operations. Net debt. 53-week year. Dimensional XBRL
instance. Deposit-funded balance sheet. Sector-gated.

I can *guess* at maybe four. The rest are opaque. That's fine in the note
itself — a PM is the reader there. It is not fine on the page whose single job
is to explain the system to someone who doesn't know it.

**DEV:** That page is sourced from `docs/FOR-REVIEWERS.md`, so it can't drift
from the repo.

**ARCHITECT:** Clever, and I like the mechanism. But it means one document is
doing two jobs with two audiences — the engineer reading the repo and the
stranger pressing a button — and it's optimised for the first. Split it, or
put a four-line plain-English summary at the top of the page that the
repository doesn't need.

Also: it says "424 tests, no network, about five seconds."

*[He runs the suite.]*

```
438 passed in 15.00s
```

**ARCHITECT:** 438 in fifteen. The number is user-facing and it's stale, which
means nothing regenerates it. That's a tiny thing that tells me something
large: you have a claim in your interface that no test asserts. Make the About
page read the count, or make a test fail when the sentence is wrong. Don't
hand-maintain a number in prose.

---

### 0:19 — The samples, and the thing nobody looked at

*[Back → `READ A SAMPLE`. Six notes: ADP, Costco, Ford, Lumen, Realty Income,
Truist. He picks ADP. A note renders in a frame below.]*

**ARCHITECT:** First: the frame. There's a scrollbar inside a scrollbar, and
the note's own navigation index is trapped in the inner one. The code comment
admits this and says the honest fix is a page of its own. Agreed — and if you
know the fix, the comment is a to-do, not a design note.

Second: the two buttons at the top, "Back" and "Build one instead", are 130
pixels apart with nothing between them. That's `st.columns([1, 1, 3])` doing
the spacing for you. It reads as two unrelated controls.

Now the content. Let me read the section headings down the side.

> Summary · Variant view · Market pricing · Implied expectations · Valuation ·
> Trajectory · Bull and bear · What must be true · Counter-case · Limitations ·
> Reconciliation · Catalysts · Questions · Financials · Health · Peers ·
> Management · Note · Sources · Provenance

**ARCHITECT:** Stop. "Variant view." "Market pricing." "Trajectory." "What must
be true." "Counter-case." "Health." A section called "Note" inside a document
that is itself a note. I cannot define a single one of those from the words
alone.

**DEV:** Those are renamed. I did a vocabulary audit — `docs/VOCABULARY.md`,
every term checked against CFA Institute, SEC, FDIC, Nareit. The ones that
couldn't be sourced got renamed.

**ARCHITECT:** Show me.

*[Dev opens `asset_researcher/ui/document.py`. Headings read: Investment
summary, Variant perception, Current valuation, Bear case, Distress and
manipulation screens, Questions for management, Business description.]*

**ARCHITECT:** So the *application* was fixed.

*[He opens the dev-tools console and reads the headings out of the live sample
frame.]*

```
["Summary","Variant view","Market pricing","Implied expectations","Valuation",
 "Trajectory","Bull and bear","What must be true","Counter-case","Limitations",
 "Reconciliation","Catalysts","Questions","Financials","Health","Peers",
 "Management","Note","Sources","Provenance"]
```

**ARCHITECT:** The samples weren't. They're pre-built artefacts sealed in an
encrypted blob, and they were built before the rename. So the six documents
that your *own home page* makes the primary action — "Samples are already
built: instant, and free", the cheap door, the one you deliberately styled to
catch a reviewer with four minutes — are the pre-fix version. Every term your
audit classified as "could not source — cut or rename" is sitting in them,
intact.

You fixed the code and shipped the old output. That is the single most common
failure I see in data products and it is why I always ask to see the artefact,
not the pipeline. The pipeline is right. The artefact is what the client reads.

**DEV:** I'll regenerate them.

**ARCHITECT:** You'll regenerate them *and* you'll add a test that fails when
the packed samples contain a heading the renderer no longer emits. Otherwise
it happens again in six weeks, by which point it's in somebody's inbox.

---

### 0:26 — The word he came back for

**ARCHITECT:** Let me search this note for "mandate".

*[Five hits: "Over the mandate's horizon" as a section caption; "what the
mandate cares about"; "inferred rather than read from the mandate
description"; twice more in prose.]*

**ARCHITECT:** So. Last time I laughed at a form field called *Mandate*,
because nothing on screen told me whether it was a real word. You renamed the
field — I'll get to that, it's much better — and the word is still here. Five
times. In the document. With no field, no caption and no glossary attached to
it any more.

You removed the word from the one place where it had an explanation next to
it, and left it in the five places where it doesn't.

**DEV:** It's a real term, it's cited in the audit —

**ARCHITECT:** I believe you. That was never the complaint. The complaint is
that the interface assumes I already know, and your fix moved the assumption
rather than removing it. Either the note says what a mandate is, once, or it
uses the words you chose for the form — "strategy", "how you invest" —
consistently. Pick one vocabulary and use it in all three renderers.

---

### 0:30 — The claim that contradicts itself ninety times

**ARCHITECT:** Your How it works page says, and I'm quoting:

> The interface says *located*, not *verified*, because locating a quote is not
> establishing that it supports the claim.

That's the most sophisticated thing in this product. It's an epistemics claim
and it's correct.

*[He scrolls to the Sources section of the note. A citations table, column
headed "Status".]*

**ARCHITECT:** Every row says **Verified**.

*[He counts in the console.]*

```
"Located"  → 1
"Verified" → 90
```

**ARCHITECT:** One "Located", in the banner. Ninety "Verified", in the table
immediately underneath it. The banner even reads "Citations located" and then
the evidence under it says the opposite word, ninety times, in the same scroll.

**DEV:** `"Verified" if c.verified else c.status` —

**ARCHITECT:** I know what the line says. The field is named `verified`, so the
label became "Verified". That's the variable name leaking into the interface,
which is the same disease as "Debt, long and short combined" and "FFO (as
reported by the company, when tagged)" that your own audit already caught
elsewhere.

Here is why this one is different from the others. The other leaks make you
look like an engineer. This one makes you look like you are claiming something
you explicitly promised not to claim. If a portfolio manager reads your About
page, agrees that the distinction is important, scrolls down, and sees
"Verified" ninety times — he doesn't conclude you have a labelling bug. He
concludes the careful sentence on the About page was marketing. You lose the
best argument you have, with a one-word diff.

Change the cell to "Located". Add a test that asserts the string "Verified"
appears nowhere in a rendered report.

---

### 0:34 — Three renderers, three vocabularies

**ARCHITECT:** One more on this. Your `app.py` says, in a comment:

> The sections come from `asset_researcher/ui/document.py`, which the export
> also renders. They used to be built here and again there, which is how the
> screen came to show one set of section labels and the file another.

And the About page says the screen and the exported file "render from one
ordered section list, so they cannot drift."

*[He opens `ui/export.py` beside `ui/document.py`.]*

| Screen (`document.py`) | HTML export (`export.py`) | Markdown export |
|---|---|---|
| Investment summary | — | Summary |
| Variant perception | Where this analysis departs from consensus | Where this analysis departs from consensus |
| Current valuation | What the market is paying | — |
| — | Implied expectations | — |
| Trajectory | Financial trajectory | Financial trajectory |
| Bear case | Disconfirming evidence | Disconfirming evidence |
| Distress and manipulation screens | Financial health | — |
| Business description | Descriptive note | Descriptive note |
| Sources | Documents used | Sources |

**ARCHITECT:** They have drifted. Three renderers, three vocabularies, and
"Implied expectations" is a heading that exists only in the HTML export and
nowhere on screen at all. The invariant is stated in two places and held in
neither.

**DEV:** The *order* comes from one list.

**ARCHITECT:** Then say "the order cannot drift", because that's what's true.
A stated invariant that doesn't hold is worse than no invariant, because I
stop checking. I found this in ninety seconds with two files open. That tells
me nobody has diffed the three outputs since the export was written — and the
export is the artefact you email to people.

The fix is structural and it's small: the label belongs on the section
definition, and all three renderers read it from there. You already have a
`Section` dataclass with a `label`. Use it in `export.py`. Then add a test
that renders one report three ways and asserts the heading sets match.

---

### 0:38 — The form

*[`BUILD ONE INSTEAD`.]*

**ARCHITECT:** Right. This is the screen I complained about and it's
substantially better.

> **TICKER** — *A US-listed company symbol. The tool looks it up in the SEC's
> own ticker list, so anything that files with the SEC works and anything else
> is refused by name.*
>
> **STRATEGY** — a dropdown, pre-filled with "Long-only, quality compounders"
>
> **HOW YOU INVEST** — a textarea, pre-filled
>
> **OTHER DOCUMENTS TO READ (URLs, optional)**

**ARCHITECT:** "Mandate" is gone, the field says "How you invest", every field
has a caption saying what it does *and* what it does not do — "It does not
change a single reported figure, a citation, or which disagreements with
management get disclosed." That last clause is excellent. It pre-empts exactly
the question a sceptical reader would ask, which is whether telling the tool
what I want changes what it tells me.

Three problems.

**One.** The captions are 11-pixel text in a mid-grey. I measured the
contrast: about 5.1 to 1, so it technically passes AA. But 11px is below what
any enterprise accessibility reviewer will sign off, and the captions are
carrying the entire explanation of the product. The most important prose on
the screen is set in the smallest type on the screen. Invert that.

**Two.** Watch this.

*[He resizes to 375px. The "How you invest" textarea renders five lines of the
preset and then slices the sixth horizontally through the middle of the
letters: "...about free cash flow conversion, incremental" cut at the
x-height.]*

**ARCHITECT:** There's a comment in your code that says this was fixed —
height went from 110 to 150 because "the default content was cut through the
middle of a line of type, so the first thing a reader saw of the field they
most need to read was the app failing to hold its own text." Your words. It is
still doing it. You fixed it at one width and shipped it broken at another.
A fixed pixel height can't hold variable-length text at variable widths; the
field needs to size to its content, or the presets need to be short enough
that the shortest supported width holds them.

**Three.** The Streamlit "Deploy" button is still in the corner.

*[He clicks the dropdown, then clicks away, then tabs backwards into it, then
reloads mid-interaction.]*

**ARCHITECT:** Form state survives the rerun. Good. Tab order is sane. The
skip link at the top actually goes somewhere, which is more than most.

---

### 0:41 — Navigation, and the thing that will cost somebody a report

**ARCHITECT:** Now the browser Back button, which is where I expect to find
blood.

*[He navigates Home → Samples → Back.]*

**ARCHITECT:** It went back. But look — full page reload. White flash, then the
whole app boots again.

**DEV:** Streamlit keeps query params server-side, so a history change never
reaches the server. The only way to follow Back is to reload. The unlock token
in the URL is what makes the reload survivable.

**ARCHITECT:** I understand why. I want you to look at the consequence.

A reload ends the Streamlit session. The generated report lives in
`st.session_state["report"]`. Therefore: **a user who generates a report and
then presses Back — or swipes back on a trackpad, which is the same gesture
and people do it by accident constantly — destroys a two-dollar, one-minute
report with no undo and no warning.**

Your code comments worry at length about Back re-locking the gate. Nobody
worried about Back deleting the artefact. The gate is an inconvenience. The
report is the product.

**DEV:** The downloads are right there in the masthead.

**ARCHITECT:** Only if they've already pressed them. Three options, in order of
how much I'd argue for them. Best: persist the finished report to disk keyed
by a run id and put the run id in the URL, so Back and refresh and a second
tab all resurrect it — that's an afternoon and it also gives you shareable
report links, which you want anyway. Next best: don't let Back off the report
screen without an `onbeforeunload` confirmation. Worst but non-zero: auto-save
the HTML export as a download the moment the report completes.

*[He pastes the URL into a second tab.]*

**ARCHITECT:** Second tab with the token — in. Second tab without it — locked,
no explanation. And here —

*[He edits the token in the URL to garbage and reloads.]*

**ARCHITECT:** Straight to the passphrase box, no message. The right behaviour
is a line saying "this link's access key is not valid — enter the passphrase."
Otherwise a reviewer with a mangled link from an email client concludes the
site is broken, not that their link is.

*[He tries `?view=build`, an invented view name.]*

**ARCHITECT:** Falls back to home. No crash, no error. Good — someone thought
about that one.

---

### 0:43 — Under the hood

**ARCHITECT:** Give me the two-minute architecture.

**DEV:** `sources/` fetches — EDGAR, Finnhub, user URLs. `quant/` is
deterministic: concept resolution, series, validation, comparables, valuation.
`analysis/` assembles the bundle and runs two model calls. `grounding/`
verifies citations. `ui/` renders. `app.py` is a view layer that computes
nothing.

**ARCHITECT:** That took forty seconds and the directory names match the
sentences, which is rarer than it should be. I could find my way around this.
21,000 lines, 438 tests passing in 15 seconds with no network — that's a real
test suite, not decoration. The `fakes.py` at 404 lines tells me somebody
cared about making the tests fast on purpose.

The code comments are unusual. Most of them explain *why* a thing is the way
it is, and several of them document a bug that was fixed and what it looked
like. That's expensive to write and very valuable to the next maintainer. I'd
keep that habit.

Now. Three things.

**One: there is no logging. At all.**

*[He greps.]*

```
grep -rn 'import logging|logger\.' asset_researcher/ | wc -l
0
```

**ARCHITECT:** Zero. In twenty-one thousand lines. So: it's 3am, a report
fails, the user sees "The report could not be generated: <something>", and
there is no record anywhere of which ticker, which source, which stage, which
status code. Your `.streamlit/config.toml` sets `showErrorDetails = "none"`,
which is the correct security posture — and there's a good comment explaining
why `"none"` and not `false`. But the combination means the user sees nothing
useful and *the operator sees nothing at all*.

And note the inconsistency: you suppress tracebacks at the platform level and
then `app.py` prints `f"...{exc}"` straight into the browser. So the exception
string reaches the user anyway, through your own code, bypassing the setting
you deliberately hardened. An exception from a requests call can contain a URL;
a URL can contain a key. You have a test that stops secrets reaching *files*.
You have nothing stopping one reaching the *screen*.

Structured logging at stage boundaries — ticker, stage, duration, outcome — is
maybe sixty lines and it is the difference between a demo and a system.

**Two: who gets paged?**

**DEV:** Nobody. It's a demo.

**ARCHITECT:** Then say so in the deploy doc, in those words, because right now
the doc reads like an operations runbook — Cloudflare Access policies, secrets,
Python version pinning — and an operations runbook with no on-call section
implies there is one. Write the honest line: "Unmonitored. If it breaks, it
breaks until the author notices."

**Three: the spend cap is a JSON file on an ephemeral disk.**

`data/spend.json`, daily cap $10, session cap $3, ~$2 reserved per run.
The reserve-then-settle pattern is genuinely good — you charge the estimate
*before* the run and reconcile after, so two simultaneous visitors can't both
pass a check neither has paid for. The docstring even says that if it ever runs
multi-process this needs real shared storage. Correct.

But `data/` is gitignored and you're deploying to Streamlit Community Cloud.
Container restarts wipe the file. A restart resets the day's spend to zero.
Your docstring says "persisted across restarts" — persisted across *process*
restarts on a durable disk, yes; across *container* restarts on a free PaaS,
no. So your $10/day ceiling is really $10 per container lifetime, and you do
not control how many of those there are in a day.

The backstop that actually holds is the spend limit on the Anthropic account
itself. Set it, and say in the deploy doc that it — not the JSON file — is the
real cap.

**Four, since I'm here: no retries.**

Timeouts exist, 30 seconds on EDGAR and 20 on Finnhub, good. Retries: none.
A single transient 503 from EDGAR, forty seconds into a ninety-second run,
kills the report. The money is already spent — you reserved it before the run
and the model calls that completed are billed. The user gets an error and an
invitation to spend it again. Three retries with backoff on the read path is
the cheapest reliability you will ever buy.

---

### 0:45 — Closing

**ARCHITECT:** Last thing. Console.

```
An iframe which has both allow-scripts and allow-same-origin for its
sandbox attribute can escape its sandboxing.  (×4)
```

**ARCHITECT:** That's Streamlit's `components.html`, used for your Back bridge
and for rendering the sample notes. It's the framework's choice, not yours, but
an enterprise security review will raise it and you should have the answer
ready rather than discovering it in a questionnaire: the content in those
frames is your own generated HTML, not third-party, and the sample notes are
authenticated-and-decrypted before rendering.

That's my forty-five minutes.

---

## Ten-second test

What he understood before anyone spoke, in order:

**At the gate (0:00–0:10):** nothing. A name, a password box, and good
typography. He could not tell what the system was, who ran it, whether he was
meant to have an account, or what to do without the passphrase. **The gate is
currently a ten-second window that communicates zero.**

**At home (0:06–0:16), unaided:**

- Input is a US stock ticker. ✅
- Output is a written research note. ✅
- The data comes from SEC filings. ✅
- The differentiator is that figures and claims trace back to a source. ✅
- There are three things he can do, and he knew which to press first. ✅
- Two of the three doors told him what they cost him. ✅

He described this as "better than most enterprise products I'm paid to fix."

**What he got wrong from the home screen**, and only found out later: that a
report is "one live API call" (it is at least three, and about two dollars),
and that the sample notes represent the current product (they do not).

The home screen passes the ten-second test. The gate in front of it fails it,
and the sample notes behind it undo part of it.

---

## Every word he could not define

Exact on-screen strings, in the places he met them. He is a senior engineer
with no finance background; where he could not infer a meaning from the screen
alone, that is listed as a failure of the screen, not of him.

### Section headings in the shipped sample notes — could not infer any of these

| On screen | His reading |
|---|---|
| **Variant view** | "Variant of what? A/B test? A different version of the note?" |
| **Prevailing view** | "Prevailing where? Whose view?" |
| **Market pricing** | "Is this prices, or the act of pricing something?" |
| **Trajectory** | "Of the share price? The company? A projection?" |
| **What must be true** | "Must be true for what? This is a sentence fragment." |
| **Counter-case** | "A legal counter-suit? A counter-argument? A test case?" |
| **Reconciliation** | "In my world this is a data-integrity job. Comparing two systems." |
| **Health** | "Of the company, the data, or the report?" |
| **Note** | "There is a section called Note inside a document called a note." |
| **Questions** | "Whose questions? Asked of whom? Answered where?" |
| **Implied expectations** | "Implied by whom, expecting what?" |
| **Provenance** | Recognised — "but that's a data-lineage word, not a reading word." |

Every one of these is listed in the project's own `docs/VOCABULARY.md` under
"Could not source — cut or rename". The renderer was fixed. The samples he read
were not.

### Figures and labels

| On screen | His reading |
|---|---|
| **Traded price** | "Why not just 'share price'?" |
| **Price implies FCF growth** | "FCF?" |
| **Price implies discount rate** | "Discount on what? A sale price?" |
| **Terminal share of value** | "Terminal as in final, or terminal as in a Bloomberg terminal?" |
| **Accrual ratio** | "No idea. Ratio of accrual to what?" |
| **Net debt** | Guessed correctly. |
| **Efficiency ratio** | "Efficiency of what? Higher is better, presumably?" (It is not.) |
| **Modelled value, illustrative** | "Illustrative meaning 'made up'? I genuinely can't tell." |
| **NM** | "N/M? Not meaningful? Nautical miles? It's unexplained at point of use." |
| **82/82 CITED** | Understood immediately. Called it "the best chip on the page." |

### Prose and captions

| On screen | His reading |
|---|---|
| **mandate** — "Over the mandate's horizon", ×5 in the note | The word he objected to last time. The form that explained it no longer uses it; the note that never explained it still does. |
| **Prepared for three to five years · quality/compounder · long** | "Three facts jammed into a subtitle with no labels. 'long' is a word I know and a word I don't, simultaneously." |
| **Divergence, high materiality** / **Corroborated, high materiality** | "Materiality is a word I know from audit. Here it's a severity level with no key." |
| **XBRL** | Used on the home screen and the About page, defined nowhere. |
| **10-Q, 8-K, proxy, DEF 14A** | "Form numbers. I'd need to look up every one." |
| **CAGR, Beneish, Altman, Piotroski, unlevered cash flow, FFO, ROIC, EBITDA, TSR** | All on the About page or in the note. None defined at point of use. |
| **"sector-gated"**, **"dimensional XBRL instance"**, **"deposit-funded balance sheet"** | Implementation vocabulary on the page whose job is explaining the system to a stranger. |

### What he could define, and praised

"Every figure is filed", "Every claim is located", "Basis for inclusion",
"Gaps in the source material", "Filed 2026-08-05", "Solved back from the traded
price", "Peer set from …", and the entire *What it does not do* list. His
comment: "when this product writes plainly it is better than anything it writes
in jargon, and it knows how to write plainly, which means every jargon term in
it is a choice."

---

## What he would tell a client about shipping this

> "Don't ship it as a product. Do ship it as evidence.
>
> I've reviewed a lot of internal tools and most of them fail on judgement —
> somebody didn't think about what happens at the edges. This one doesn't have
> that problem. Whoever built it thought about concurrency on the spend
> counter, constant-time comparison on the passphrase, en-dashes from mail
> clients mangling a pasted secret, what a corrupt counter file should assume,
> why `showErrorDetails = "none"` and not `false`. The test suite is real: 438
> tests, no network, fifteen seconds. The code comments explain *why*, and
> several of them document the bug that produced the current shape. That is the
> work of somebody who will be good to have on a team.
>
> What it fails on is **the gap between what it says about itself and what it
> actually renders**, and that gap is the one thing I cannot let past me.
>
> Three examples, all found in under forty-five minutes. It says the interface
> deliberately avoids the word 'verified' — and then prints 'Verified' ninety
> times in the citations table. It says the screen and the export render from
> one list so they cannot drift — and they have drifted, into three different
> vocabularies across three renderers. It carries a careful, well-sourced
> vocabulary audit, acts on it in the code, and then ships six sample notes,
> as the primary call to action, containing every term the audit said to cut.
>
> Individually those are small bugs. Together they're a pattern, and the
> pattern is: **the claims are maintained by hand and nothing tests them.**
> For a product whose entire proposition is trustworthiness, that is the
> proposition failing on itself. A sceptical reader who finds the 'Verified'
> table doesn't log a labelling bug — he concludes the careful paragraph about
> epistemics was marketing. That's the whole asset, lost to a one-word diff.
>
> Operationally it is a demo, and that's fine, but it should say so. No
> logging anywhere in 21,000 lines. No retries on the fetch path, so one
> transient 503 burns two dollars and produces nothing. A spend cap enforced by
> a JSON file on a free PaaS with an ephemeral disk. Nobody on call. None of
> that is wrong for a demo; all of it is wrong for a thing whose deploy doc
> reads like a runbook.
>
> Fix the self-contradictions first — they're hours, not days, and they are
> the ones that cost you the reader. Then add logging and retries. Then
> decide whether the gate is meant to be security or a speed bump, and label
> it accordingly.
>
> If you're asking me whether the person who built this can build: yes,
> clearly, and the honesty in 'What it does not do' is a professional
> instinct you can't teach. If you're asking me whether I'd put it in front
> of a client on Monday: not until the samples match the code."

---

## Fix list

Ordered by how much each one costs you with a sceptical reader. Each is tied to
the moment in the transcript that produced it.

### 1 — "Verified" ninety times, under a banner that says "located"
*Transcript 0:30.* The product's strongest claim, contradicted in the same
scroll as the paragraph that makes it.

**Change:** in `asset_researcher/ui/document.py`, the citations table cell
`"status": "Verified" if c.verified else c.status` → `"Located"`. Same in
`ui/export.py`. Add a test asserting the string `Verified` appears in no
rendered report, HTML or Markdown.

### 2 — Shipped sample notes are the pre-rename build
*Transcript 0:19.* The home page's primary action opens six documents carrying
every heading `docs/VOCABULARY.md` classified as unsourceable.

**Change:** re-run `scripts/publish-sample.py` and re-pack the sealed archive
for all six tickers. Add a test that decrypts the packed samples and asserts
their `<h2>` set is a subset of the labels `document.sections()` currently
emits, so a rename can never again leave the samples behind.

### 3 — Three renderers, three vocabularies, and a stated invariant that is false
*Transcript 0:34.* `document.py`, the HTML export and the Markdown export emit
different headings; "Implied expectations" exists only in the HTML export.
Both `app.py` and the user-facing About page claim they cannot drift.

**Change:** make the label live on the section definition and have all three
renderers read it. Add a test that renders one fixture report three ways and
asserts the heading sets are identical. Until that lands, correct the sentence
in `docs/FOR-REVIEWERS.md` to claim only what holds — the *order*.

### 4 — Browser Back destroys a finished report
*Transcript 0:41.* Back forces a reload, a reload ends the Streamlit session,
and `session_state["report"]` goes with it. Two dollars and ninety seconds,
gone to a trackpad swipe, with no warning.

**Change:** persist the finished report to disk under a run id, put the run id
in the query string, and rehydrate from it on load. This also gives you
shareable and refreshable report URLs. Interim mitigation: an
`onbeforeunload` confirmation while a report is on screen.

### 5 — No logging anywhere, and an exception string printed to the browser
*Transcript 0:43.* Zero `logging` imports in 21,000 lines; `app.py` renders
`f"...{exc}"` into the page, bypassing the hardened
`showErrorDetails = "none"`.

**Change:** structured logging at each stage boundary — ticker, stage,
duration, outcome, and the source and status code on failure. In the UI, show
a fixed message plus a short correlation id; log the exception, don't print it.

### 6 — "Spends one live API call", and three disagreeing cost figures
*Transcript 0:06.* Home says one call; the code reserves $2.00; `docs/DEPLOY.md`
says $1.30; the pipeline makes at least three model calls.

**Change:** one figure, derived from `ESTIMATED_REPORT_COST_USD`, used on the
home screen and in the deploy doc. Wording: "about a minute, and roughly two
dollars of model time."

### 7 — No retries on the fetch path
*Transcript 0:43.* Timeouts are set; retries are absent. One transient 503
mid-run kills a report whose money is already spent.

**Change:** three attempts with exponential backoff on EDGAR and Finnhub reads,
and on a terminal failure, record the already-settled spend in the message so
the user knows what the retry will cost.

### 8 — The spend cap rests on an ephemeral file
*Transcript 0:43.* `data/spend.json` is gitignored and the deploy target's disk
does not survive container restarts, so the daily cap resets silently.

**Change:** set a hard spend limit on the Anthropic account and state in
`docs/DEPLOY.md` that it, not the JSON file, is the binding cap. Correct the
docstring's "persisted across restarts" to name the condition.

### 9 — The gate identifies nothing
*Transcript 0:00.* A wordmark and a password box. No statement of what the
system is, no route for a reviewer without the passphrase, and Streamlit's
"Deploy" button visible pre-auth.

**Change:** one line under the wordmark — what this is, that it's a private
demo, and who to contact. Hide Streamlit's toolbar. On a URL carrying an
invalid `k`, say that the link's key is not valid rather than showing a bare
box.

### 10 — "mandate" survives in the note after being removed from the form
*Transcript 0:26.* Five occurrences in the note's prose and captions; the field
that used to explain it now says "How you invest".

**Change:** use the form's vocabulary in the note — "Over your horizon",
"what your strategy cares about" — or define the word once where it first
appears. Not both vocabularies in one product.

### 11 — The textarea still slices its own default text
*Transcript 0:38.* Fixed at `height=150`; at 375px the preset is cut through
the x-height of line six — the exact failure a code comment claims to have
fixed.

**Change:** let the field size to its content, or shorten the presets so the
longest fits at the narrowest supported width. Assert it in a width-parameterised
UI test.

### 12 — The explanation is set in the smallest type on the page
*Transcript 0:38.* Field captions are 11px at ~5.1:1 contrast and carry the
entire account of what the tool does and does not change.

**Change:** 13–14px minimum, darker. This is the first thing an enterprise
accessibility reviewer measures.

### 13 — A stale, hand-maintained test count in the interface
*Transcript 0:11.* The About page says "424 tests ... about five seconds". It
is 438 in fifteen.

**Change:** generate the sentence, or make a test fail when it is wrong.

### 14 — The How it works page is written for a repository reader
*Transcript 0:11.* Thirteen undefined terms, no plain-English summary, and the
best content in the product — *What it does not do* — sits 900 words down the
second of three doors.

**Change:** a four-line plain summary at the top of the in-product page, and
surface *What it does not do* on the home screen. It is the credential; stop
burying it.

### 15 — Sample notes render in a frame inside a frame
*Transcript 0:19.* Nested scrollbars, the note's own index trapped in the
inner one, and a code comment that already names the correct fix.

**Change:** give each sample its own route and render it as the page, not in
`components.html`. Also widen `st.columns([1, 1, 3])` on that screen so "Back"
and "Build one instead" read as one choice rather than two strangers.
