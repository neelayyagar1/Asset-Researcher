# Handover, 2026-11-20

What changed, what you need to do, and what is still open. Written to
be read in five minutes before you send the link.

**No secret values appear in this file.** This repository is public, and
a commit guard refused the first draft of this page for exactly that
reason, which is the guard working. Both values below live in your
Streamlit account and in the local `.env`, and nowhere else.

---

## Two things only you can do

Everything else is committed and pushed. Neither of these can be done
from the build machine.

### 1. The passphrase

Streamlit Cloud -> the app -> **⋮ -> Settings -> Secrets**, set
`DEMO_PASSPHRASE` to the short phrase you chose. Then **Reboot app**
from the same menu: saving secrets alone does not always re-read them,
and the reboot does.

The gate is case-sensitive but forgiving about the rest. It strips
surrounding whitespace and folds en and em dashes back to hyphens,
because a mail client rewrites a hyphen and the reader pastes what the
mail client gave them. A wrong attempt backs off rather than failing
silently.

### 2. The samples key

The six notes were rebuilt and re-sealed under a **new** key. The
deployment cannot open the archive until that key is copied across.

The value is on the `SAMPLES_KEY=` line of `.env` on the build machine.
Copy it into the same Secrets box as `SAMPLES_KEY`.

It is deliberately a different value from the passphrase. The sealed
blob is committed to a public repository, so sharing one secret between
them would turn that blob into an offline guessing oracle for the
secret that guards the API keys.

### Check it worked

Open the link, enter the passphrase, and confirm the home screen lists
six notes with a figure beside each. If the table reads "No notes yet",
the samples key did not take.

---

## What the reader sees

One link, one passphrase. Home lists the six notes that exist, each
with its own headline figure read out of the built document. Get
started is four numbered steps. One primary action.

The six: Realty Income, Costco, Lumen, ADP, Cintas, Fastenal. Ford and
Truist were dropped - Ford paired good reasoning with a +564% headline
and a blank FY2025 revenue, Truist was a null note that missed a thesis
sitting in a three-day-old filing.

---

## What changed, in order of how much it mattered

**A valuation defect that reached the output.** Four of the six filers
had a debt or capital-expenditure mapping pointing at an XBRL tag the
company had abandoned - ADP's total debt resolved to a concept last
filed in FY2011 at $37m, against real debt near $5bn. The series looked
complete, so nothing downstream objected, and the note bridged
enterprise value to equity across $4.4bn of net cash the company does
not have.

The cause was that the resolver received about 500 bare tag names and
no way to tell a live tag from a dead one. Each concept now carries the
last year the filer reported it. ADP's equity value falls from $134.2B
to $129.2B and its target from $357.68 to $345.10; Lumen stops
declining and leads with price-implied expectations, because its
capital expenditure now resolves to FY2025 instead of FY2013.

**Browser Back did nothing.** The listener was a JavaScript
SyntaxError: `\n` escapes were consumed by a non-raw Python string, so
the browser received a string literal split across two lines and the
script never parsed. The in-app Back buttons kept working because those
are server-side widgets, which is why the fault looked like "only your
buttons work". Back and Forward are both verified in a browser now.

**The shell was rebuilt.** It measured four container widths and three
competing centre axes on one screen, which is what "half centered and
centered to uncentered things" is, described from the outside. One
column now, declared once, inherited by everything. Perception-First
Design scores moved from L1 41 / L2 34 to L1 74 / L2 86, measured in
the live DOM rather than estimated.

**A note was shown through a letterbox.** Forty thousand pixels of
document in a two-thousand pixel frame: one eighteenth at a time,
through a scrollbar nested inside the page's own, with the note's
section index trapped in the frame. The frame is same-origin, so the
note now sizes it to its own content and the page scrolls once.

**Smaller, but visible to a reader:** the muted tone carrying the
product's one explanatory line failed contrast at 3.19:1; the first
control a keyboard user reaches had an invisible focus ring at 1.04:1;
one source was escaped twice so a reader was shown an HTML entity
instead of an ampersand; and the honest sentence about citations being
located rather than verified was dead code while the unqualified claim
shipped.

---

## One decision made on your behalf

Refreshing all six samples with the consensus block costs about $6.50,
which would have put the Anthropic account near its $60 cap with
nothing left for the demo itself. ADP was rebuilt, because it is the
one note whose headline order actually changed; the other five already
led with the implied growth requirement or declined a model outright.

So **ADP carries the published consensus distribution and the other
five do not**. Every note generated from now on carries it. If the cap
is higher than $60, say so and the remaining five take about ten
minutes and $5.50 to refresh.

## What is still open, stated rather than buried

- **The samples carry the figures they were built with.** They are
  artifacts, not live output. Each is a real run against real filings
  on the date it was built, and the date is on the note.
- **A note still wants a route of its own.** The frame sizes correctly
  now, but a page is the right shape.
- **No active-section indicator while scrolling.** The index marks your
  place after a click, not as you move.
- **Focus does not return to the trigger when the dialog closes.**
  Streamlit owns that dialog.
- **A report lives only in the session.** Download it to keep it; the
  browser's Back asks before discarding one.
- **Cintas has a pending UniFirst merger**, so its standalone valuation
  reads as overvalued and the note explains why. That is correct
  behaviour, and worth knowing before someone asks.
- **One discount rate, 8.5%, for every filer.** A company with no net
  debt and one with negative book equity get the same number. It is
  labelled a convention, which is honest and is not the same as having
  a view. This is why the note leads with the implied growth
  requirement, which is solved back from the traded price and does not
  depend on the rate, rather than with the modelled target, which does.
  A reviewer named this as the thing that would get the tool dismissed
  in one sentence, and he was right.
- **Consensus is a recommendation count, not an estimate.** It says how
  many analysts rate the name a buy, a hold or a sell. It does not say
  what they expect it to earn; that data is behind a paid tier. The
  prevailing views the note argues against are still read from the
  filings, and are labelled that way.

---

## If you want to check the work

    .venv/bin/python -m pytest -q          # 567 tests, no network, ~45s
    .venv/bin/python scripts/check-credentials.py

Reading, in the order that makes sense:

| File | What it answers |
|---|---|
| `docs/DECISIONS.md` | Why each choice is what it is |
| `docs/SKILLS-LOG.md` | What ran, what it found, and where it was wrong |
| `docs/reviews/PFD-EVALUATION.md` | The design scored before and after |
| `docs/VOCABULARY.md` | Every term, with citations |
| `docs/SAMPLE-AUDIT.md` | The superseded audit that chose this set |
| `DESIGN.md` | The design system, written from what was built |
