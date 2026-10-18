# Asset Researcher

An equity research engine that reads a company's own filings and produces a
sourced research note: the filed financial record, the narrative management
wrapped around it, and the places where the two do not agree.

A ticker goes in. About a minute later a note comes out carrying a
comparable-company table, a discounted cash flow with its assumptions and
sensitivities, a reconciliation of management's claims against the reported
figures, and a mandatory section arguing against its own thesis. Every figure
is read from the company's XBRL submissions to the SEC. Every narrative claim
carries a citation resolved against the stored source text.

---

## The problem

A portfolio manager at a fundamental fund spends three to four hours
assembling a pitch from a known set of sources: the 10-K, recent 10-Qs, the
proxy, any 8-Ks, a peer screen, and whatever news moved the name. The sources
are the same every time and the assembly is mechanical. The judgment is not.

Quantitative shops automated the assembly years ago. Smaller fundamental shops
have not, because the tooling assumes a data budget they do not have. This is
the assembly, built on sources that are free and authoritative.

It does not form a view. There is no buy, sell or hold anywhere in the output.
What it produces is a structured account of the evidence, an explicit
statement of what the current price requires an investor to believe, and the
strongest available case against whatever thesis emerged.

## What makes it different from a chatbot over filings

A chatbot answers a question and the reader cannot tell a quotation from a
recollection. Three constraints exist to make that distinction checkable.

**The model may not write a number.** Financial figures come from the
company's XBRL submissions and are inserted by the renderer. Both writing
prompts forbid a figure in prose, and the verifier flags any that appear. The
cost is that the model writes "operating margin contracted, and the decline
outpaced the revenue slowdown" where it could have written "operating margin
fell 240bps to 29.1%". It is the only version a reader can trust without
checking.

**Citations are resolved, not asserted.** The first model call runs with the
Messages API's citations feature, which returns character offsets. Those
offsets are checked against the exact stored text the model was given. A
citation that cannot be located is rendered inline as "unverified" rather than
dropped.

The limit is stated everywhere it matters: locating a quote is not
establishing that the quote supports the claim built on it. The system checks
provenance, not inference, which is why citations are linked at the point of
each claim.

**The counter-case is mandatory.** Every report states the evidence against
its own thesis, what would falsify it, and what the source material could not
see. A report returning an empty disconfirming section has that section
replaced with a visible warning rather than rendered blank.

## What it does not do

Stated here rather than buried, because a roadmap that omits its gaps is
marketing.

- **Segment revenue is not broken out.** The SEC's `companyfacts` API is
  undimensioned, so segment detail needs the dimensional XBRL instance. The
  revenue build is consolidated.
- **Quarterly data is retrieved but unused.** Series construction filters to
  annual periods, so every multiple is on the last reported fiscal year, not
  trailing twelve months. On a filer eleven months past its year end that is
  stale, and the report says how stale in its header.
- **The discount rate is a convention**, not a derivation from the filer's
  capital structure. The assumptions table labels it as such, along with every
  other input that is not a filing.
- **Semantic citation support is unverified.** See above.

---

## Running it

Python 3.12. Three keys, two of them free.

```bash
git clone <this repository> && cd Asset-Researcher
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
cp .env.example .env     # then fill it in
bash scripts/install-hooks.sh
```

`.env` needs:

| Variable | Where from | Notes |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | console.anthropic.com | A report costs about $1.30 |
| `FINNHUB_API_KEY` | finnhub.io/register | Free tier is sufficient |
| `EDGAR_USER_AGENT` | your own contact | The SEC rejects requests without a real one, and startup rejects the placeholder |

Then:

```bash
.venv/bin/streamlit run app.py
```

### Front-end work without spending anything

A live report costs an API call and about a minute, which is too slow a loop
to lay out a table against.

```bash
.venv/bin/python scripts/preview.py --ticker AAPL
```

This runs the real retrieval path (EDGAR submissions, XBRL, Finnhub quotes and
peers) and substitutes the test fixtures for the two narrative calls, so every
figure, chart and comparables row is genuine. The output is stamped
`FIXTURE-DO-NOT-CIRCULATE` in its filename and at the top of the file, because
real filings plus placeholder prose is a document that makes false statements
about a listed company.

### Tests

```bash
.venv/bin/python -m pytest -q
```

314 tests, about four seconds, no network. The view layer is pure functions
from data to strings and nothing outside `app.py` imports Streamlit, which is
what lets the whole suite run without a server.

---

## How it is put together

```
asset_researcher/
  sources/      EDGAR and Finnhub clients, user-URL fetching with SSRF defence
  documents/    filing retrieval, text extraction, byte-exact storage, section
                selection by content density
  quant/        the deterministic spine: concept resolution, series building,
                derived metrics, health scores, comparables, valuation
  analysis/     the bundle, the two model calls, the finished report
  grounding/    citation verification against stored source text
  llm/          the provider interface; only claude.py imports the SDK
  ui/           tokens, HTML components, SVG charts, the export writer
  config/       prompts, metric taxonomy, settings, per-filer overrides
app.py          the Streamlit view, which computes nothing
```

The seam that matters is between gathering and reasoning. Everything above the
bundle is deterministic: HTTP, XBRL arithmetic, text extraction. Everything
below it is the model. A report can be regenerated from a stored bundle
without re-fetching, and a disputed number traced to the source that produced
it without re-running anything.

Two model calls rather than one, because the Messages API rejects a request
enabling both citations and structured output. The first produces the cited
descriptive sections; the second reasons over that output plus the filed
series and produces the analysis.

---

## Reading further

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** is the technical reference:
  why the system is shaped this way, and the decisions that are not obvious
  from the code. The source comments point at its numbered sections.
- **[docs/FOR-ANALYSTS.md](docs/FOR-ANALYSTS.md)** is for the person reading
  the output rather than maintaining the code. No programming assumed.
- **[docs/WALKTHROUGH.md](docs/WALKTHROUGH.md)** walks the product end to end
  and gives the reasoning behind each design and engineering choice.

## Data and licensing

SEC EDGAR filings and XBRL data are public domain. EDGAR's fair-access policy
requires a `User-Agent` identifying a real contact on every request and caps
throughput at ten requests a second; the client declares the contact from
`.env` and runs at eight.

Finnhub supplies quotes, company profiles, peer lists and news headlines. The
free tier restricts commercial use and redistribution. **Exported notes embed
Finnhub data**, so anything beyond personal evaluation needs a commercial
licence and the attribution its terms require.

This produces research assistance, not investment advice. It issues no
recommendation and should not be treated as one.
