> **Superseded, 2026-11-20.** The six notes this audit examined were
> built on 19-20 October and have been replaced. Ford and Truist were
> dropped on the recommendations below; Cintas and Fastenal replace
> them, chosen because every load-bearing line resolves current, which
> was verified before paying to build them. Lumen's -91% target, the
> single worst output described here, is gone: the discounted cash flow
> now declines because the filer's capital-expenditure concept stops at
> FY2013, which is the defect this audit inferred and the rebuild
> confirmed.
>
> Kept because the reasoning is the record of how the set was chosen,
> and because an audit that is quietly deleted once it is acted on
> leaves no evidence that it was.

# Sample set audit

Notes generated 19–20 October 2026. Audited 20 November 2026 against events through that date.

Scope: the six notes in `build/site/` — COST, ADP, O, TFC, F, LUMN. Each gets three verdicts (was it right / was it ever sound / is it stale in an embarrassing way) and a recommendation.

Known and intended: O and TFC produce no DCF, because an enterprise DCF does not describe a REIT or a bank. That is correct behaviour and is not counted against either note.

---

## Headline finding first: the hallucination claim survives

The most damaging possible finding would have been a figure in the prose that is not in the filings. I spot-checked numbers across four notes against the primary documents and **found none**.

| Note | Prose figure checked | Filing | Result |
| --- | --- | --- | --- |
| COST | 939 warehouses at 30 Aug 2026, 914 a year earlier | FY2026 10-K, Item 1 | Correct |
| COST | 647 US/PR, 115 Canada; other-international country split summing to 177 | FY2026 10-K (647/115/177) + 8-K exhibit | Correct, and the country list sums exactly to the 10-K's "Other International 177" |
| ADP | FY2024 PSU three-year rTSR at the 36.3rd percentile of the S&P 500, downward modifier | FY2026 DEF 14A | Correct (modifier 89.1%, payout 109.4%) |
| ADP | PSU weights two-thirds adjusted net income growth / one-third revenue ex-ZMPT | FY2026 DEF 14A | Correct (67% / 33%) |
| ADP | Bookings the one bonus metric below target in FY2026 | FY2026 DEF 14A | Correct (5.6% actual vs 6.8% target) |
| LUMN | Two agencies upgraded Feb 2026, Fitch by two notches | Feb 2026 announcement, Q3 2026 10-Q | Correct (Fitch CCC+ → B; Moody's B3 → B2 one notch; S&P affirmed issuer rating at B-) |
| F | FY2024 revenue 184,992 / net income 5,879; FY2025 diluted EPS $(2.06) | FY2025 10-K | Correct ($(2.06) × 3,979 shares reconciles to the filed $(8,182)m net loss) |

**But the notes tell the reader the opposite.** The COST and ADP provenance blocks read:

> "1 figure in the prose could not be matched to a filed value (939,). Figures in the tables are as filed; **treat any number in the prose as unsupported.**"

The two "unmatched" figures are `939` (the warehouse count, which comes from Item 1 narrative, not XBRL) and `500` (from "the S&P 500"). Both are false positives of the provenance checker. The result is that the tool's two cleanest notes carry a banner instructing a portfolio manager to disbelieve every number in their prose, **because one of them mentioned the S&P 500**. This is the single highest-leverage fix in the set and it is a one-line change to the checker, not a regeneration.

---

## The second problem: three of six notes lead with an indefensible number

The headline block is the first thing a PM reads. Three of six open with a probability-weighted target that no analyst would say out loud:

| Note | Price (19 Oct) | Target | Implied |
| --- | --- | --- | --- |
| F | $12.18 | **$80.92** | **+564.4%** |
| LUMN | $4.46 | **$0.40** | **−91.1%** |
| COST | $995.53 | $592.39 | −40.5% |

Each note then disclaims its own headline further down ("A gap of that size is more often a defect in the assumptions than a mispricing; treat the target as illustrative"). The self-awareness is to the tool's credit, but the disclaimer arrives three sections after the number. On Ford the mechanism is fully traceable: FY2025 derived free cash flow of $12,467m is computed from consolidated operating cash flow of $21,282m — which blends Ford Credit origination and collection flows with industrial cash, and is flattered by $15,974m of D&A that includes the Model e impairment — less $8,815m of capex. Ford's own guidance for FY2026 adjusted free cash flow is $6–7bn. The model capitalises roughly double the real figure, on a −7.6% growth base, and gets $80.92. It is not a hallucination; it is a definable modelling error with a very loud output.

Recommendation: suppress the target and implied-upside lines entirely whenever the DCF diagnostics flag a divergence above some threshold, exactly as is already done for O and TFC (`NM`). The implied-expectations framing — "the price requires 17.1% annual growth against a filed 11.8%" — is the genuinely good output and it survives on its own.

---

## COSTCO WHOLESALE (COST)

**The argument.** At 47× free cash flow the price requires 17.1% annual FCF growth against a filed 11.8% five-year CAGR. The variant view: the sustainable component of FY2026 margin expansion cannot be separated from the IEEPA tariff refund, which management booked partly against merchandise cost and partly as interest income with no disaggregation; management intends to recycle further refunds into member value, so FY2027 faces price reinvestment against a flattered base without a matching credit. Secondary variant: the cash build and a compensation plan keyed only to net sales and pre-tax income are a return-on-capital drag.

**Events since 19 October.** Q1 FY2027 has **not** reported — it is due 10 December 2026 (quarter ends 30 November; consensus ~$4.92 EPS on ~$74.4bn). The note's nearest catalyst, the FY2026 proxy, is also still ahead. What has moved is the refund question itself: Costco is among 1,000+ businesses with protective Court of International Trade filings following the Supreme Court's 20 February 2026 ruling that IEEPA does not authorise tariffs, and it now faces multiple proposed consumer class actions (lead case in federal court in Seattle) alleging it raised prices on tariff grounds and then sought refunds for the same costs. Costco's defence is the exact commitment the note identified — that refunds go to lower prices — and the plaintiffs' objection is that this benefits future members rather than those who paid. CBP has accepted roughly $85bn of refunds for processing, with Amazon reported at ~$600m.

- **Was it right?** Untested but strengthened. The note said the refund quantum was "the single most consequential unknown in the file" and that management's reinvestment intention created an FY2027 margin problem. A month later that intention is the centre of litigation, which both confirms it was the right variable to isolate and adds a contingency the note does not mention.
- **Was it ever sound?** Yes, and this is the best-reasoned note in the set. It refuses to manufacture a dispute on the Walmart/Amazon point and says so. It states plainly where the data cannot support the argument (membership fee revenue, renewal rates, comparable sales, gross profit, inventory and payables are all absent from the supplied tags; no Beneish M-Score for want of two-year gross profit; debt tags break after FY2021 so leverage is "asserted rather than measured"). One real defect: the derived margin claims rest on a COGS ratio computed against total revenue that includes membership fees, which the note discloses but still leans on.
- **Stale?** Yes, on two counts. The $995.53 price and $441.1B market cap are a month old, and the Q1 FY2027 print lands three weeks from now — a PM will ask why the note does not anticipate it. The −40.5% headline on a long/compounder mandate is the bigger problem.

**→ REGENERATE.** Analysis sound; figures stale; suppress the target.

---

## AUTOMATIC DATA PROCESSING (ADP)

**The argument.** At 22× FCF the price requires only 5.7% growth against a filed 12.5% CAGR, so the setup is constructive. Variant view: the employment channel did decelerate and consolidated growth did not break, because price, bookings and client-funds float absorbed it — which means a growing share of growth now depends on the rate cycle and on price increases compounding against a competitive market. The material divergence: the float is presented as a revenue driver while the cost of funding the extended-maturity strategy sits in interest expense and is never netted in the narrative; net float contribution to pre-tax income cannot be isolated from the filed data. Nearest catalyst: "fiscal 2027 quarterly results and the bookings line specifically," bookings being the leading indicator of whether price is substituting for volume.

**Events since 19 October.** The catalyst fired nine days after publication. ADP reported Q1 FY2027 on **28 October 2026**: revenue +6% to $5.5bn, adjusted diluted EPS +13% to $2.82, and — directly against the note's framing — **a record first-quarter Employer Services new business bookings result**, with full-year bookings guidance held at 4–7%. Management raised FY2027 revenue growth guidance to about 6% from 5–6% and adjusted EPS growth to 10–12% from 9–11%; the 70–90bp adjusted EBIT margin expansion target was unchanged. Softness was confined to global offerings.

- **Was it right?** Weakened. The note nominated bookings as the discriminating variable and bookings came in at a Q1 record with guidance raised. That is the "price masking a demand slowdown" reading failing its own chosen test on the first datapoint. The float-netting critique is untouched by the quarter and remains valid.
- **Was it ever sound?** Yes. Every proxy and compensation figure I checked is exactly right, the float-funding asymmetry is a real and under-discussed point, and the note was explicit that the bear framing of the employment channel is "correct in mechanism and premature in timing" — an unusually honest hedge. It did not overreach.
- **Stale?** Badly. The nearest catalyst has passed, resolved against the note, and the note still presents it as forward-looking. This is the most embarrassing kind of staleness: not a wrong price, a wrong tense.

**→ REGENERATE.** The reasoning deserves a second run against the Q1 FY2027 print; the variant view will need to be re-argued or dropped.

---

## REALTY INCOME (O)

**The argument.** Spread compression already ran through the numbers in FY2022–FY2024, when per-share FFO, per-share operating cash flow and per-share net income all fell while the asset base compounded. FY2025 is the first year the per-share series inflected up, and it did so because issuance and acquisition volume both slowed, not because spreads widened. The question for a multi-year holder is whether slower growth is discipline or exhaustion, and FY2025 reads as discipline because asset yield improved throughout, so the binding constraint was cost of equity. Material divergence: management's cost-of-capital claim holds at the enterprise level and is contradicted at the per-share level for three consecutive years — external growth was funded at a cost that left no spread for existing holders once dilution is charged. "One year is not a trend." Nearest catalyst: Q3 and full-year 2026 results, "absent entirely from the supplied record."

**Events since 19 October.** Q3 2026 reported **2 November 2026**. AFFO per share $1.12 against $1.08 a year earlier (+3.7%), AFFO $1,061.1m. FY2026 AFFO guidance raised to $4.45–$4.46 from $4.44–$4.45. Net income per share guidance trimmed to $1.55–$1.56 from $1.59–$1.60. Occupancy guidance lifted above 98.5% with year-to-date occupancy at 98.8%. $2.6bn invested in the quarter and the $10bn full-year investment target reaffirmed. Lease-termination income guidance unchanged at $45–50m.

- **Was it right?** **Confirmed, and it is the only note in the set whose variant view has been positively vindicated.** The per-share inflection the note identified in FY2025 has extended into a second year with guidance going up, which is the "one year is not a trend" caveat resolving in the note's favour. The $10bn volume target is the one wrinkle: investment is reaccelerating, which tests the "discipline" reading — but it is reaccelerating alongside rising per-share AFFO, which is exactly the combination the note said would prove the cost-of-equity constraint had eased rather than the opportunity set having deteriorated.
- **Was it ever sound?** Yes. The per-share versus enterprise-level distinction is the correct lens on an externally-funded REIT and is the single sharpest piece of analysis in the sample. Supporting evidence is well chosen (decelerating diluted share growth, flat equity, the unused 2025 repurchase authorisation followed by two convert-funded repurchases in 2026 as evidence management thinks its own equity is cheap). Interest expense is `n.d.` for FY2024 and FY2025, which is a tag gap the note should flag more prominently given how much of the thesis is about cost of capital.
- **Stale?** Yes, but benignly. The data stops at FY2025 and the nearest catalyst has passed — but it passed *confirming* the note, so the regenerated version is strictly stronger. The `NM` target is correct and the note explains why.

**→ REGENERATE.** Best candidate in the set; a rerun turns a pending catalyst into a confirmed call.

---

## TRUIST FINANCIAL (TFC)

**The argument.** There isn't one. The Summary block says, verbatim:

> "No variant view was identified against the prevailing read, so this analysis says nothing the price does not already reflect."
> "No management narrative was reconciled against the filings."

The Financial trajectory section does real work — total assets at end-2025 near 2021 levels, net interest income peaking in 2023 and never regaining it, derived NIM declining in 2024 and 2025, pre-tax income negative in both 2023 and 2024 on management's own restructuring decisions, deposits down in 2022–2024 while total borrowings hit a series high and noninterest-bearing balances fell. That is a defensible and unflattering read of a bank replacing deposit funding with wholesale funding. But there is no variant view, no reconciliation, no target, and no `## Where this analysis departs from consensus` section at all.

**Events since 19 October.** Truist had already reported Q3 2026 **before the note was written**, and the note registers it only as "the third quarter of 2026 adds a further AFS repositioning loss and loan sale impact on preliminary figures." What the quarter actually contained: GAAP net income $684m / $0.56 diluted EPS, after a **$1.4bn pre-tax AFS repositioning loss ($0.90 per share)** and $66m of Regional Acceptance losses that drove reported noninterest income down to $84m; adjusted diluted EPS $1.16, **+12% year over year**, with adjusted ROTCE of 14.6% (+100bp); $8.6bn of lower-yielding agency MBS sold and $7.2bn bought at ~4.40% with 2.3-year duration; CET1 down 20bp to 10.7%; guided NII effects of about −$125m from the RAC sale against about +$40m from the repositioning; management framing a path to **16–18% ROTCE** and the CFO flagging a further **$17–18bn of AFS securities as actionable**. None of this is in the note. The note's own nearest catalyst — January 2027 Q4 results and 2027 guidance — is still correctly in the future, which is the one thing it has going for it.

- **Was it right?** Not assessable. A note that states it has no variant view cannot be right or wrong. Its descriptive read of funding mix and spread income is accurate and is not contradicted by the quarter.
- **Was it ever sound?** The trajectory section, yes. The note as a *deliverable*, no — it is a null result presented as a research note. Worse, the material for a variant view was sitting in a filing that predates the note by three days: a bank taking a $1.4bn securities loss to buy 4.40% paper, guiding to 16–18% ROTCE, and telling you there is another $17–18bn of the same trade available, against a filed record of no balance-sheet growth and no durable NII expansion through a full rate cycle. That is a thesis. The tool did not find it.
- **Stale?** The catalyst is fine. The problem is not staleness, it is emptiness.

**→ DROP FROM THE SAMPLE SET.** This is the one note that actively damages the pitch. A PM reading "this analysis says nothing the price does not already reflect" will reasonably conclude the tool cannot handle banks — and the evidence in front of them is that it missed a thesis available in a filing three days old. If a bank must be in the demo, it needs a rerun that reconciles the Q3 2026 release, not a cosmetic refresh.

---

## FORD MOTOR (F)

**The argument.** The consensus "cheap cyclical with a cash-flow floor" read is accepted on the cash and rejected on the quality: capex rose in every year FY2021–FY2025 while operating margin fell and then went negative, so the FY2025 write-off is the arithmetic consequence of the pattern rather than a departure from it — incremental invested capital has produced impairment rather than incremental operating profit. Secondary: part of the operating cash flow improvement is working-capital financed, and consolidated OCF blends Ford Credit flows so the headline is not distributable cash. Third: the screens showing Ford as a cheap EV multiple are "mechanically wrong for this filer" because the debt tags break after FY2017 and produce a net cash position. Nearest catalysts: FY2026 capex in the early-2027 10-K, and "within weeks of the report date," Q3 2026 and containment of the end-September F-150 supplier disruption inside the 28 July guidance range.

**Events since 19 October.** Q3 2026 reported **28 October 2026**, ten days after publication, and it resolved the note's own second catalyst in the *confirming* direction for management rather than for the note. Revenue $49.5bn; net income $2.0bn; adjusted EBIT $2.7bn; operating cash flow $5.4bn; adjusted free cash flow $4.7bn; adjusted EPS $0.49 against $0.40 expected. Full-year adjusted EBIT guidance **raised at the low end to $10.5–11bn from $10–11bn**, with no new special item for the supplier disruption; adjusted FCF guidance held at $6–7bn and capex at $9.5–10.5bn. Model e: $1.2bn revenue, $1.1bn EBIT loss, **improved 25% year over year**. Ford Blue $27.1bn revenue (−3%), $1.4bn EBIT (−10%); Ford Pro $17.8bn revenue (+2%), $1.7bn EBIT (−16%) on wholesales −4%. CFO Sherry House guided 2027 earnings roughly in line with 2026. The note's test was explicit — "reaffirmed full-year guidance with no new special item for the disruption confirms containment" — and that is what happened.

- **Was it right?** Partly, and the near-term test went against it. The structural point (capex up, operating profit not) is not refuted by one quarter, but Model e losses narrowing 25% and the EBIT floor being raised are the early shape of the discipline the note doubted. Ford Pro EBIT −16% on −4% wholesales is the one datapoint that supports the note's "mix is funding cost absorption" divergence.
- **Was it ever sound?** Mostly, with one genuine defect and one presentational disaster.
  - **Internal contradiction.** The variant view asserts "operating margin declined in every year through FY2024." The note's own financial summary shows operating margin rising from **3.3% in FY2021 to 4.0% in FY2022** before falling in FY2023 and FY2024, and the *Evidence* line directly beneath repeats the error as "operating margin down FY2022, FY2023, FY2024." The claim is contradicted by the table on the same page. This is the kind of thing a PM finds in thirty seconds.
  - **Missing filed figures.** FY2025 revenue and FY2025 net income are both printed as `n.d.`, which cascades into `n.d.` for FY2025 operating margin, net margin, FCF margin, cash conversion, accrual ratio and DSO. Both figures are in the FY2025 10-K ($187,267m and $(8,182)m) and the note's own FY2025 diluted EPS of $(2.06) is derived from the net loss it claims not to have. The headline consequently reports "cash conversion is 262.3% of net income **in FY2024**" — the flagship earnings-quality metric is a year stale purely because of a tag miss. Interest expense is also `n.d.` for FY2024 and FY2025 and is printed identically as 4,593 for FY2021 and FY2022.
  - The $80.92 / +564% headline, mechanism described above.
  - To the note's credit, the "screens are mechanically wrong for this filer" section is excellent and correctly diagnoses the tool's own broken debt tags before anyone else can.
- **Stale?** Yes. One of two near catalysts has passed and resolved against the note's tilt, and the price is a month old.

**→ DROP FROM THE SAMPLE SET** for this demo. The analysis has real merit, but a note whose first line says +564% upside, whose latest-year revenue is blank, and whose variant view contradicts its own table is three separate credibility hits in the first two screens. It becomes a strong note once the FY2025 tags resolve, the margin claim is corrected, and the DCF is suppressed — but that is a rebuild, not a refresh, and it should not be in the version the PM sees.

---

## LUMEN TECHNOLOGIES (LUMN)

**The argument.** The screenable picture (negative equity, no P/E, impaired EBITDA, high net debt to EBITDA) supports the sell-side's move to Neutral, but it is computed on a capital structure that no longer exists: the filed balance sheet predates the February 2026 redemption of the secured and superpriority notes and full repayment of the term loans out of divestiture proceeds, after which two agencies upgraded, Fitch by two notches. The material divergence: the deleveraging that mattered came from selling assets, not from operations, and specifically from selling the only growing consumer revenue line — balance-sheet repair at the cost of the earnings base. The sharpest point sits in the "Corroborated" section: the operating cash flow recovery behind the turnaround narrative is substantially customer prepayment under PCF agreements, recognised as deferred revenue, **with the matching capital expenditure still ahead of it** — "not a free cash flow conversion improvement in the sense the mandate uses the term; it is working capital timing with a contractual obligation attached." Nearest catalyst: "November 4, 2026, after market close: Third quarter 2026 results," with the named lines being deferred revenue against capex, net debt post-redemption, cost of revenue against revenue, and any PCF backlog disclosure.

**Events since 19 October.** The catalyst fired **on the predicted date, 4 November 2026**, and the note's central mechanism showed up in the print. Total revenue $2.715bn, −12% year over year, against ~$2.787bn consensus. Net loss $(265)m versus $(621)m a year earlier. Strategic revenue +10% to $1.28bn; strategic sales +30%; cumulative PCF contracts above $13.5bn. Adjusted EBITDA around $715m, with the 2026 EBITDA inflection reiterated. And **free cash flow of approximately $(76)m against +$1.7bn a year earlier** — the prepayment-then-capex sequence the note described, arriving on schedule. Ratings are unchanged from the February upgrades per the Q3 10-Q.

- **Was it right?** **Confirmed on the mechanism, and this is the most impressive single call in the sample.** The note named the swing from prepayment-inflated cash flow to capex-consumed cash flow before a $1.8bn year-over-year FCF reversal printed it, named the date the evidence would arrive, and named the exact lines to read. The PCF backlog disclosure it asked for came in at >$13.5bn. The operating story is better than the note's tone implies — revenue decline moderating, strategic +10%, loss halved — so the note is right on mechanism and somewhat harsh on trajectory.
- **Was it ever sound?** The *reasoning* yes, the *valuation* no, and the note says so. It discloses that "no capital expenditure figure was mapped for any recent fiscal year in the XBRL supplied; the only tagged capex periods end more than a decade ago," and that cash conversion "was 319.8% of net income in FY2021, the only period in which it could be measured." A DCF with no recent capex and one year of usable operating cash flow cannot produce a meaningful equity value, and it did not: it produced **$0.40, −91.1%**. The note then correctly observes that "any model of go-forward free cash flow built on this material rests on an unverified input" — while still printing the target in the first screen. Every narrative claim I checked is accurate.
- **Stale?** Yes, and conspicuously: the nearest catalyst is a specific past date printed in the Summary block. A PM reading "November 4, 2026, after market close" on 20 November reads a note that did not wait two weeks.

**→ REGENERATE**, conditional on suppressing the valuation block. The analytical quality here is the best argument for the tool in the whole set, and it is currently buried under a −91% target produced by a model with no capex input. If the valuation cannot be suppressed, drop it — the target will be the only thing anyone remembers.

---

## Recommendation: what the demo should show

**Fix first, before any regeneration (cheap, high leverage):**

1. **Repair the provenance checker's number matcher.** Excluding narrative integers and index names ("S&P 500") from the XBRL-match test removes the "treat any number in the prose as unsupported" banner from COST and ADP. This is the difference between "every figure is traceable" and a note that disavows itself.
2. **Gate the target and implied-upside lines on the DCF diagnostics.** The machinery to print `NM` already exists and is used for O and TFC. Any note whose model-versus-market gap exceeds the existing warning threshold should print `NM` and keep only the implied-expectations framing, which is the better output anyway.
3. **Fail loudly on a missing latest-year revenue or net income.** Ford's FY2025 blanks are the most concrete evidence of a pipeline defect in the set, and they propagated into the headline metric.

**Rerun (three):** **O**, **COST**, **LUMN**. O because its variant view has been confirmed by Q3 2026 and a rerun converts a pending call into a made one. COST because the argument is intact, the catalysts are still ahead (Q1 FY2027 on 10 December, FY2026 proxy), and the IEEPA class actions give the thesis a live edge. LUMN because the 4 November print vindicated it, and a note that calls a $1.8bn free-cash-flow reversal by naming the mechanism and the date is the single best demonstration of what this tool does.

**Rerun with the variant view re-argued (one):** **ADP**. The reasoning and the citations are clean, but the bookings call lost on the first datapoint and the note must address the 28 October print rather than anticipate it. The float-netting divergence stands on its own and is worth keeping.

**Replace (two):** **TFC** and **F**. Truist is a null note that missed a thesis sitting in a three-day-old filing; Ford pairs good reasoning with a +564% headline, a blank latest-year revenue and a claim its own table refutes. Replace them with two names that fit the quality/compounder mandate, file on a recent fiscal year end, and have clean debt and capex tags so the DCF is not an embarrassment — a services or distribution compounder such as **Cintas**, **Waste Management**, **Fastenal** or **TJX** would do. Verify in a dry run that the latest fiscal year's revenue, net income, total debt and capex all resolve **before** paying for the note.

**Proposed six: O, COST, LUMN, ADP + two clean-tag compounders.**

That set has one confirmed variant view (O), one confirmed mechanism call (LUMN), one live thesis with catalysts ahead of the meeting (COST), one honest earnings-quality divergence on a name the PM will know (ADP), and two names where the valuation machinery can be shown working end to end rather than disclaimed. It also keeps O in, which demonstrates the tool declining to produce a DCF for a REIT — discipline a PM will notice and credit.

**One thing worth saying out loud in the meeting.** Four of the six notes name a catalyst that has since fired, and in two cases the note named the date. The notes were right about *where to look*. They are stale only because they were generated a month ago and nothing has run since. That is a scheduling problem, not an analytical one, and it is the easiest objection in the room to answer — provided the notes shown have been rerun inside the last week.
