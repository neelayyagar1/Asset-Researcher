# Product

Asset Researcher. An equity research engine that reads a company's own SEC
filings and produces a sourced research note: the filed financial record, the
narrative management wrapped around it, and the places where the two do not
agree.

## Platform

web

## Stack

Python 3.12, Streamlit as the shell. The view layer is hand-built and owned:
design tokens and a single stylesheet (`asset_researcher/ui/theme.py`), HTML
component functions (`components.py`), inline SVG charts (`charts.py`), a
standalone HTML/Markdown export (`export.py`). No JS framework, no build step,
no component library. Streamlit injects its own DOM and emotion classes, which
the stylesheet overrides by `data-testid`.

## Users

One primary user: a portfolio manager or analyst at a small fundamental
equity fund, who today spends three to four hours assembling a pitch from the
10-K, recent 10-Qs, the proxy, 8-Ks, a peer screen, and news.

One decisive audience: the same person evaluating the builder. This is a
credibility artifact for cold outreach and hiring, not a school project. The
reader is a managing director or PM with decades in the seat; the register is
an associate producing work for them.

Both read dozens of research documents a week and find a figure by its
position on the page.

## Product Purpose

Do the assembly, which is mechanical and identical every time. Leave the
judgment, which is not. It issues no buy, sell or hold and no price target
presented as a conclusion; it produces structured evidence, an explicit
statement of what the current price requires an investor to believe, and the
strongest available case against its own thesis.

## Positioning

Against a chatbot over filings: a chatbot answers and the reader cannot tell
a quotation from a recollection. Against a Bloomberg or Koyfin screen: those
give the figures but not the reconciliation of narrative against them.
Against sell-side research: that is slower, broader, and conflicted.

The thing it owns is the reconciliation, management's claim set against the
company's own filed data, with the divergence named.

## Operating Context

A desktop browser, a working session of roughly a minute per report, read in
daylight beside a terminal and a spreadsheet. Output is read on screen and
also exported to a standalone file that gets forwarded, printed to PDF, and
opened again six weeks later.

Scenes that matter: the first ninety seconds of a stranger deciding whether
this is serious; an analyst checking a figure against the 10-K; a PM scanning
a comparables table for a number by its position.

## Capabilities and Constraints

- Every financial figure comes from the company's XBRL submissions. The model
  may not write a number; the renderer inserts filed values.
- Every narrative claim carries a citation resolved against stored source
  text. Locating a quote is not establishing that it supports the claim, and
  the interface must not imply otherwise.
- The counter-case is mandatory on every report.
- A report takes about a minute and costs about $1.30, so the waiting state
  is a real surface, not an edge case.
- Sections disappear rather than render empty, and say why.
- Streamlit owns the DOM. No client-side routing, no JS framework. Motion and
  interaction must be CSS-only or server-rerun.
- Three data sources: SEC EDGAR (authoritative), Finnhub (quotes and peers),
  user-supplied URLs (secondary, attributed as opinion).

## Brand Commitments

None inherited. No logo, no wordmark, no existing palette the user is
attached to. The current editorial/print look is the builder's own earlier
attempt and is explicitly up for replacement.

Two commitments that are product truth rather than taste: published research
conventions in tables and figures (fixed column order, dollars in millions,
negatives in parentheses, multiples to one decimal with a trailing x, NM
where a ratio is not meaningful, the subject separated from its peer set),
and no emoji anywhere.

## Evidence on Hand

Real generated output on Apple from live SEC filings, including a
comparables table, a discounted cash flow with assumptions and sensitivities,
a statement-ordered financial summary, citation-linked prose, and a
divergence between the model and the market that the report explains rather
than hides. 339 tests. A standalone export.

No customer logos, no testimonials, no usage numbers, no screenshots of
anyone else using it. Nothing commercial may be claimed.

## Product Principles

- Nothing is silently missing. Every gap is recorded with a reason.
- Claim less than you can prove. The interface says "located", not
  "verified", because that is what the check establishes.
- A figure that is computed must look different from a figure that was filed.
- The counter-case is as prominent as the case.

## Accessibility & Inclusion

Read on a laptop in daylight by one professional audience. Needs legible
figure contrast at small sizes, a visible focus state on every control, and
output that survives printing to PDF and pasting into a memo. No known
assistive-technology requirement beyond standard contrast and focus.

## Assumptions

Labeled per the init flow. These were inferred from the session rather than
asked in a fresh interview, because the facts above were established across
the build:

- The decisive audience is the hiring/outreach reader, over the daily user.
- Desktop-first; mobile is a courtesy, not a scene.
- No authentication is wanted. Nobody logs into this.
