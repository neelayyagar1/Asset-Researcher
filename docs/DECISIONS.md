# Every choice, and why

You asked to be able to defend every word, phrase and choice in this
version. This is that record. It is written so you can read a line, be
asked "why is it like that?", and answer without me.

It is organised by what someone would point at.

---

## 1. The screen that asks for a passphrase

**It shows the product's name and a field. Nothing else.**

It used to explain what the product was and why it was gated. That is the
right design for a page a stranger lands on cold. It is the wrong design
here, because everyone who reaches this screen was sent the link and the
passphrase by you — so the explanation answered a question nobody was
asking, and put three lines of prose between the reader and the only
thing they came to do.

**If challenged:** "Everyone who sees that screen already knows what this
is, because I told them when I sent the link."

**The passphrase is short and simple** — short enough to type from an
email without error. The previous one was six words, which is stronger
and worse: a reviewer who mistypes a six-word phrase blames the tool.

It is not written down here. This repository is public, so the live
passphrase lives only in the deployment's own configuration and in the
message you send a reviewer.

**Dashes are forgiven.** If a passphrase contains a hyphen, mail clients
autocorrect it to an en dash, and the reader pastes what the client gave
them. The gate folds all five dash characters to a hyphen before
comparing. This matters more than it sounds: before it was fixed, a
non-ASCII character made the comparison raise a `TypeError`, and the
first thing the product did was show a stack trace containing a home
directory path.

**The comparison is `hmac.compare_digest`, on bytes.** Constant-time on
content. It does not hide the secret's length and is not claimed to.

**After three wrong attempts the gate slows down,** doubling to a
thirty-second ceiling. It does not stop a determined attacker and is not
meant to; it removes the trivial scripted path, which is the one that
actually gets used.

---

## 2. The home screen

**One sentence: what goes in, what the tool reads, what comes out.**

What stood here before was *"Read the filings, then read what management
said about them"* over a second sentence about *"the narrative management
wrapped around it"*. That is writing that enjoys itself. A reader who has
not seen the product cannot tell from it what the product does, which is
the only job this screen has.

**If challenged:** "It says what it does in one sentence, in words that
need no finance to parse. The argument is in the three claims underneath
it."

**Three ways in, each labelled with what it costs.** Reading a sample is
instant and free. Building a report takes about a minute and costs about
a dollar in model usage. Saying so on the screen where the choice is made
is the difference between a reviewer who waits and one who leaves.

**"About a dollar" is measured, not estimated.** A report is four model
calls — concept resolution, mandate parsing, the cited narrative, the
reconciliation — and the last six builds measured between $1.03 and
$1.33. The screen used to say "one live API call", which was simply
untrue, and small untruths are what a careful reader generalises from.

---

## 3. Centring

**Every screen that is not a rendered note is centred, at every width.**

This was broken in three separate places at once, and the measurements
are worth keeping because they are the answer if anyone asks whether it
was really fixed. At 1440px: the content column was 1240 wide and
centred, and the gate inside it was 544 wide starting at x=124 — leaving
772px of empty paper to its right.

1. The column had a `max-width` and no auto margin.
2. The blocks inside it carried max-widths from when they sat against the
   left margin, also with no auto margins.
3. A Streamlit control is a flex child that shrink-wraps — measured at
   87px inside a 656px column — so justifying the parent moved nothing,
   and each control needed an auto inline margin of its own.

Measured after: title 448/448, field 544/544, button 677/677.

**A rendered note is deliberately not narrowed.** It is sixteen columns
wide. When the samples screen was first centred it squeezed the note's
frame to about 656px, which is under the 900px breakpoint — so a reader
on a 1440px screen got the *phone* layout of the note, including the rule
that unsticks the table header. That is why the comparables header looked
cut off. The heading centres; the column stays full width.

**Running prose sets flush left.** A centred paragraph of several lines
has a ragged left edge and is measurably slower to read. So the written
page centres its heading and nothing else.

---

## 4. Vocabulary

Every user-facing term was checked against real usage, with sources, in
`docs/VOCABULARY.md`. Three kinds of problem came back.

### One was factual, not stylistic

`npl_ratio` was labelled **"Nonperforming Loan Ratio"** and divides
nonperforming loans by **total assets**. The ratio that name refers to —
World Bank series FB.AST.NPER.ZS, and every bank's own disclosure —
divides by **gross loans**. Total assets is the larger denominator, so
the figure printed at roughly half what a bank analyst reading the label
would expect.

Gross loans are not in the canonical metric set, so it is now named for
the arithmetic it actually performs: **"Nonperforming loans / total
assets"**. That is the same rule already applied to `nim_on_assets` two
entries below it.

**This is the one that would have caught you.** A PM reads "NPL ratio",
knows roughly what it should be for that bank, sees half of it, and stops
trusting everything else.

### Several terms had no professional usage at all

| Was | Is | Why |
|---|---|---|
| Counter-case | **Bear case** | "Counter-case" appears in no filing, no CFA material, no published note. "Bear case" is the published convention and describes the same content. |
| Variant view | **Variant perception** | "Variant view" does not exist. "Variant perception" does, and is quotable from CFA Institute's own material on Steinhardt. One word apart; only one is citable. |
| Reconciliation | **Management vs. filed figures** | Worse than unused — *taken*. Under Regulation G and Item 10(e) of Reg S-K, "reconciliation" means non-GAAP to GAAP. A PM opening that section expects an adjustments bridge and finds a narrative check. |
| Implied expectations | **Price-implied expectations** | The term from Mauboussin and Rappaport's *Expectations Investing*. One adjective buys a named, respected framework instead of a phrase we coined. |
| Health | **Distress and manipulation screens** | "Health" hid the three things that are the credibility. It now names Altman, Piotroski and Beneish outright. |
| Summary | **Investment summary** | The conventional heading. |
| Market pricing | **Current valuation** | The conventional heading. |
| Questions | **Questions for management** | Says who the questions are *for*. |
| Note | **Business description** | "Note" was an internal name that escaped into the interface. |

### "Mandate" survives, and the field it was on does not

The citation is strong — CFA Institute Standard III(C) uses *"mandate,
strategy, or style"* in sequence. But a mandate is a **document agreed
between an asset owner and a manager**. It is not a line somebody types
into a box, and "Long-only, quality compounders" is a *style*.

So the field is **"Strategy"**, the box under it is **"How you invest"**,
and the word stays where the object genuinely is one — in the note's
"Prepared for" line.

**If challenged on "mandate":** "It is a real term — CFA Standard III(C)
— but a mandate is a document, not a text box, so the field is called
Strategy."

### The preset descriptions

Their nouns were already desk-literate. Two sentences gave them away:
*"Catalysts matter more than terminal value to us"* and *"Long-run
terminal value is largely irrelevant to us."* No portfolio manager
volunteers a statement about terminal value. That is a statement about a
discounted cash flow, written by someone who knew the tool runs one. Both
cut.

---

## 5. The form

**Every field says what it is, underneath it, in plain words.**

Your reviewer read "Mandate" and could not tell whether it was real
vocabulary or invented; read "Additional sources" and could not tell what
it wanted or what would happen to it. Both are fair reactions to a
one-word label with nothing around it.

The answer is **not** to drop the terms. A PM should see the word they
would use. The fix is to say what it means once, underneath.

- **Ticker** — "matched against the SEC's own list", so a reader knows
  why an unknown symbol is refused by name.
- **Strategy / How you invest** — what it changes (which findings lead,
  and in what order) and what it does **not** change (not one reported
  figure, citation, or disclosed disagreement). That second half is the
  important one: it is the answer to "so the tool tells me what I want to
  hear?"
- **Other documents to read (URLs, optional)** — empty means filings
  only; paste a public page and it is read alongside them, labelled a
  secondary source, attributed as opinion, never mixed into the filed
  figures.

---

## 6. Correctness fixes a reviewer would have found

### The citations table said "Verified" ninety times

This product rests on one sentence: locating a quote establishes that the
text sits where the citation says, and establishes **nothing** about
whether it supports the claim built on it. The guide says it. The
in-product page says it. And the citations table contradicted it — 90
occurrences in the Realty Income note against one "Located" — because the
checker's field is named `verified` and the variable name reached the
label.

**That was the single most damaging thing in the product**, because it
undercut its own best argument, in public, at scale. A test now fails if
that word reappears anywhere a reader can see it.

### Two notes led with a target nothing had checked

Ford showed **+564.4%** upside and Lumen **−91.1%**, at the largest type
size on the page.

One inverted clause:

```python
model_is_load_bearing = implied is None or implied.caveat is None
```

A **failed** reverse solve was read as a clean bill of health: when the
solve could not run there was no caveat to object with, so the code fell
through to the full-confidence branch and promoted the number it had
least reason to trust. A model is load-bearing only when it was solved
*and* nothing drew a caveat.

An absolute bound sits on top: outside −75% to +300%, the target is
demoted whatever the caveat says. Ordinary disagreement is still shown —
a model calling a stock worth 40% of its price is a real call.

### Section links did nothing

Every section name in every sample was dead. Inside the app a note is an
iframe whose `baseURI` is the **parent page** — measured as
`http://host/?k=…&view=samples` — so `#s-valuation` resolved against the
app's own URL rather than the note. Clicking tried to navigate the frame
instead of scrolling it. Links now resolve their target by id and scroll
to it, which depends on no base URL and works identically in the app and
in the downloaded file.

### The spend caps did not bind

Forty concurrent starts against a $10 cap all passed, committing about
$52, because the code checked the counter and then spent — so every
request inside that window saw the same pre-spend total. The estimate is
now reserved under a lock *before* the run and settled against the real
cost after. A test holds forty threads on a barrier and proves five get
through.

### Tracebacks were not suppressed

`showErrorDetails = false` is a legacy alias Streamlit maps to
`"stacktrace"`: it redacted the message and still shipped the traceback,
with absolute paths and source lines, to the browser. It is `"none"` now.
This one is worth knowing because it is a control that *looked* like it
was in place.

### The newest column must be complete

A missing tag in the most recent year cascades: every ratio built on it
renders `n.d.`, the earnings-quality sentence quietly reports the year
before and reads as current, and the note looks complete while showing a
stale picture. An error now, because the response is to fix the mapping
and rebuild.

---

## 7. What is deliberately still true

Say these before you are asked.

- **The samples carry figures built on 19–20 October 2026.** They have
  been patched for vocabulary and the "Located" label, not rebuilt,
  because the API key stopped authenticating. Several of their named
  catalysts have since fired — two against the note's own argument. That
  is in `docs/SAMPLE-AUDIT.md`, and it is a *feature* of having dated,
  falsifiable calls, but only if you say it first.
- **The model is forbidden from writing a number. It is not forbidden
  from writing a direction.** Ford's variant perception says operating
  margin "declined in every year through FY2024" while the table on the
  same page shows 3.3% → 4.0% in FY2022. Nothing currently catches a
  claimed trend that the series contradicts.
- **Multiples are trailing on the last reported fiscal year**, not twelve
  months.
- **The discount rate is a convention**, not derived from the filer's
  capital structure.
- **Citations are verified for provenance, not for whether the claim is a
  fair reading of the quote.**
- **The link grants access.** The `?k=` token in the URL means anyone
  holding the link is in without the passphrase. That was the deliberate
  price of making the browser's Back work.
- **`n.d.` cannot currently distinguish** "the filer did not report this"
  from "the concept failed to resolve". Both print the same token.

---

## 8. Things changed only for appearance

Nothing in this section altered a figure, a citation or a behaviour.

- Narrow screens centred (§3).
- Form labels left-aligned inside a centred column, because a label
  centred over its own field is harder to scan down.
- Streamlit's "Press Enter to apply" hint hidden — it rendered half
  inside the field and half under the reveal toggle.
- Streamlit's input wrapper themed: it was a white 8px-rounded box around
  a square cream field on cream paper, which was the one element on the
  first screen that said "Streamlit app".
- Equal columns on the home row, one per button, so labels stop wrapping.
- EDGAR conformed names made fit to show: "COSTCO WHOLESALE CORP /NEW"
  becomes "Costco Wholesale Corp." — `/NEW` is a filing-system artifact,
  and a reader who sees it concludes nothing was normalised on the way
  out.

---

## 9. What would break if it changed

If anyone proposes an edit, these are the invariants worth defending.

| Invariant | Why |
|---|---|
| No figure in a table is model-written | The entire claim |
| "Located", never "Verified" | §6 |
| A refusal states its reason in place | A refusal that withholds why reads as an error |
| Negatives in parentheses | Accounting convention; a minus sign is lost in a right-aligned column |
| NM, n.d. and blank stay distinct | Three different states; collapsing them is the one thing a financial table must not do |
| The gate sits above anything that spends | A test asserts the ordering, because the file runs top to bottom |
