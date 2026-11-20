# PM review — simulated

A simulated 35-minute meeting between the author of Asset Researcher and a senior
long-biased fundamental portfolio manager who knows him slightly. The PM's lines are
constructed from what is actually in the repository, the six sample notes, the two
audits, and a walk through the running tool. Every number he challenges is a number
the tool really prints.

This is written to be useful, not kind.

---

## 1. Transcript

**MERCER:** You've got until my 11:30. Don't pitch me. Open the thing and let me read
something.

**NEELAY:** Sure. These are six sample notes, pre-built. Which one do you —

**MERCER:** Whichever one you'd show a client. No, actually — don't choose. Give me
the list.

**NEELAY:** Costco, ADP, Realty Income, Truist, Ford, Lumen.

**MERCER:** Ford. Everyone thinks they have a view on Ford.

**NEELAY:** *(clicks)* This is the top of the note. Price, market cap, a probability-
weighted target, implied upside, and then —

**MERCER:** Stop. Five hundred and sixty-four percent.

**NEELAY:** Yes. That's —

**MERCER:** Five hundred and sixty-four percent upside on Ford. Eighty dollars and
ninety-two cents. Where does that number come from?

**NEELAY:** It's a discounted cash flow. Ten years of projected free cash flow plus a
terminal value, discounted, net debt subtracted, divided by diluted shares. Three
scenarios, probability-weighted.

**MERCER:** Where does the eighty-ninety-two come from.

**NEELAY:** The base free cash flow is a three-year average of operating cash flow less
capex. For FY2025 that's about $12.5 billion.

**MERCER:** Ford's own guidance is six to seven billion of adjusted free cash flow.
You've got twelve and a half. Why?

**NEELAY:** Because the operating cash flow line in the filings is consolidated. It
includes Ford Credit — originations and collections of a finance book — and it's
inflated by depreciation and amortisation that includes the Model e impairment. The
note actually says that, further down, in the valuation section.

**MERCER:** So the model knows the input is wrong and uses it anyway.

**NEELAY:** The valuation section says the DCF is not usable and should be read as a
diagnostic of the input data. It says it carries a net cash position which can't be
right for a group consolidating a captive finance company.

**MERCER:** Then why is the unusable number in sixty-point type at the top of the page
and the sentence explaining it four screens down?

**NEELAY:** That's a sequencing failure. It's a real one. I don't have a defence.

**MERCER:** Good. Keep answering like that. Next — what discount rate?

**NEELAY:** Eight and a half percent.

**MERCER:** On Ford.

**NEELAY:** Yes.

**MERCER:** What did you use on Costco?

**NEELAY:** Eight and a half.

**MERCER:** Lumen?

**NEELAY:** Eight and a half.

**MERCER:** You're discounting a levered cyclical auto manufacturer with a captive
finance arm, a membership retailer with bond-like cash flows, and a distressed telco
with negative equity at the same cost of capital.

**NEELAY:** Yes. It's labelled a convention, not a derived figure. The assumption row
says "not derived from this filer's capital structure, replace with your own cost of
capital."

**MERCER:** Why eight and a half?

**NEELAY:** It's roughly a long-run equity cost of capital for a US large cap.

**MERCER:** Why is roughly good enough?

**NEELAY:** Because building a real WACC needs a beta, a target capital structure and
a cost of debt, and the debt tags in XBRL break for a lot of filers — Ford's collapse
after FY2017, Costco's after FY2021 — so a computed WACC would be wrong in a way the
reader couldn't see. A stated convention is wrong in a way they can.

**MERCER:** That's a decent answer. Here's the third why. Why ship the target at all,
if the only honest version of it is "we didn't model this company's cost of capital"?

**NEELAY:** *(pause)* I don't think I should. The audit I ran last week says the same
thing — suppress the target whenever the model-versus-market gap trips the diagnostic,
the way it already does for the REIT and the bank. It prints "NM" for those two. It
should have printed NM here.

**MERCER:** Then why hasn't it?

**NEELAY:** Because I found it three days ago and I haven't shipped the fix.

**MERCER:** So I'm reading a known-broken screen.

**NEELAY:** You're reading a screen I know is broken, yes.

**MERCER:** Fine. Scroll. What's this — "where this analysis departs from consensus."

**NEELAY:** That's the variant perception section. Prevailing read on the left,
the tool's read against it.

**MERCER:** *(reads)* "Capital expenditure rose in every year of the filed series while
operating margin declined in every year through FY2024 and then went negative." Okay.
That's a real argument. Incremental capital earning nothing. I'd listen to that.
Show me the table.

**NEELAY:** Financial summary is down here.

**MERCER:** *(long pause)* Your operating margin goes 3.3 in FY2021 to 4.0 in FY2022.
That's up. Your sentence says it declined in every year.

**NEELAY:** …Yes. It does.

**MERCER:** And the evidence line underneath repeats it. "Operating margin down FY2022,
FY2023, FY2024." Your own table on the same page says FY2022 was up.

**NEELAY:** That's a contradiction between the generated prose and the rendered table.
The prose is written by a model that's given the series and forbidden from printing
figures; the table is rendered from the filed values. The model got the direction of
one year wrong and nothing caught it.

**MERCER:** Your whole pitch is that the model can't write a number. It didn't write a
number. It wrote a *direction*, which is the thing I actually trade on, and it got it
wrong, and your guarantee doesn't cover directions.

**NEELAY:** That's correct. The guarantee covers figures and citation offsets. It does
not cover a claim about the shape of a series. There's no checker for that.

**MERCER:** Could there be?

**NEELAY:** Yes, and it's cheap — the series is in memory, "rose/fell in every year" is
a monotonicity test. I haven't built it.

**MERCER:** Write it down. What's this, FY2025 revenue — "n.d."

**NEELAY:** Not disclosed. The tag didn't resolve.

**MERCER:** Ford's FY2025 revenue is in the 10-K. It's a hundred and eighty-seven
billion. You're telling me the most-read number in the most-read filing in America
didn't resolve.

**NEELAY:** The concept resolver didn't map it for this filer. It cascades — net income
is blank too, so FY2025 operating margin, net margin, FCF margin, cash conversion and
the accrual measure are all blank, and the headline falls back to FY2024. That's why
the summary line says cash conversion was 262% of net income "in FY2024" on a note
dated October 2026.

**MERCER:** So the latest year is missing and the tool doesn't stop.

**NEELAY:** It doesn't. It should fail loudly on a missing latest-year revenue or net
income. It currently degrades silently.

**MERCER:** That's the one, you know. That's the answer that would end the meeting at a
real fund. Not the five hundred percent — I can see that's a model artefact, you told
me it was. But a pipeline that can't tell the difference between "this company didn't
report revenue" and "I failed to read it" is a pipeline I can't put between me and a
filing. Everything downstream of it is unfalsifiable.

**NEELAY:** Understood.

**MERCER:** Close Ford. Give me the one you're proudest of.

**NEELAY:** Realty Income.

**MERCER:** Why that one?

**NEELAY:** Because it declines to value the company, and because the central finding
is one I didn't expect. Realty Income says scale plus cost of capital lets it buy
accretively. The enterprise numbers agree — revenue, operating cash flow, FFO before
disposals all grow every year. The per-share series disagrees. Diluted shares grew
faster than FFO in FY2022, FY2023 and FY2024, so per-share FFO, per-share operating
cash flow and per-share net income all fell for three straight years while the asset
base compounded.

**MERCER:** *(reads for a while)* Right. Okay. That's the actual trade on that name and
it's the thing a screen will never show you, because a screen shows you the enterprise.
And the pay plan point —

**NEELAY:** Half the long-term award is relative TSR, a quarter is a leverage ratio, a
quarter is dividend-per-share growth. Both of the management-controlled metrics improve
when you issue equity. There's no return-on-capital metric anywhere in the plan. And
the 2023–2025 award certified above target, over exactly the three years per-share cash
earnings fell.

**MERCER:** That's good. I'll say that plainly, because I'm not going to say much else
nice: that is a genuinely good piece of work. Nobody on my team reads the comp plan
against the per-share series. They read the comp plan, they go "three quarters at risk,
fine", and they move on. Connecting the metric design to the dilution is an analyst
move and it's the first thing today that would have changed what I asked management on
a call.

**NEELAY:** Thank you.

**MERCER:** Don't relax. Where's the valuation on this one?

**NEELAY:** There isn't one. The target says NM. The model discounts unlevered cash flow
to an enterprise value and bridges across net debt, which doesn't describe a REIT valued
on FFO against asset value. So it refuses. Truist is refused for the inverse reason —
deposits are the funding of a bank, not a claim to subtract.

**MERCER:** That's the second thing I like and it's a bigger one than you think. A tool
that always produces a number produces one for the names where it shouldn't. You've got
a sector gate that says no. Keep it. Now — your note says Price over FFO fourteen seven.
Whose FFO?

**NEELAY:** Derived. Net income plus depreciation and amortisation, before gains on
disposal.

**MERCER:** Not Nareit FFO.

**NEELAY:** No. The filer's own FFO tag didn't map, so it's constructed. The note
discloses it and says if management's AFFO shows a different per-share path the central
finding weakens materially.

**MERCER:** It would more than weaken. AFFO strips straight-line rent and above- and
below-market lease amortisation. On a serial acquirer those adjustments are not small
and they move in the same direction as the acquisitions. Your entire three-year
per-share decline could be an artefact of a measure the company doesn't use and the
market doesn't price.

**NEELAY:** I can't rule that out from the filed data.

**MERCER:** You can't rule it out, or you haven't checked?

**NEELAY:** Haven't checked. The company reports AFFO per share every quarter in its
supplement. It isn't in the XBRL the tool reads, so it isn't in the note, so I didn't
look at it.

**MERCER:** Then your best finding is currently unverified against the number the entire
sector trades on. You see the problem. The finding might well be right — the direction
is plausible and the FY2025 inflection story hangs together — but you brought me a
conclusion you could have checked in ninety seconds against a press release and didn't,
because the pipeline doesn't read press releases.

**NEELAY:** Yes. That's fair and it's the sharpest thing anyone's said to me about it.

**MERCER:** What's this table at the bottom. Comps.

**NEELAY:** Peer set from Finnhub, not screened. It's labelled as a starting point.

**MERCER:** Kimco. Revenue sixteen point eight.

**NEELAY:** …Million.

**MERCER:** Kimco does about two billion of revenue. And your fiscal year end on that
row says December 2022.

**NEELAY:** The peer fundamentals come from a fixed tag list rather than the per-company
concept resolution used for the subject. If the tag doesn't resolve for that filer you
get a partial value or a stale year, and the footnote says treat the enterprise-value
multiples as indicative.

**MERCER:** The footnote says "indicative". The row says sixteen point eight. A footnote
doesn't rescue a number that's wrong by two orders of magnitude — it just means you knew
and printed it anyway. And every EV/EBITDA cell in that table says NM, so the only
column with content is a P/E that runs from twelve to forty-nine across eight REITs,
which tells me nothing because REIT P/Es are noise against the depreciation load. Your
own note says that. So the comp table, on your best name, contains zero usable
information and one false number.

**NEELAY:** The right answer is to drop a peer row entirely when its fundamentals don't
resolve, rather than print a partial one.

**MERCER:** Or drop the table. What does this do that a screen plus an analyst doesn't?

**NEELAY:** The assembly. A screen gives you the enterprise series. It doesn't read the
proxy, it doesn't read Item 1A, and it doesn't put a management claim next to the filed
figure that contradicts it. That reconciliation is the output — the Realty Income
per-share finding comes out of putting the cost-of-capital sentence from the 10-K beside
the share count.

**MERCER:** An analyst does that.

**NEELAY:** An analyst does that in three or four hours, for one name. This does it in a
minute, for any US filer, and it tells you which claims it checked and which it couldn't.

**MERCER:** In a minute, with a wrong revenue line, a target it says to ignore, and a
peer table with Kimco at sixteen million dollars. My analyst takes four hours and the
revenue is right. Four hours of a junior's time is not my constraint. My constraint is
being wrong. You've optimised the thing I have plenty of.

**NEELAY:** I think that's true for you. I don't think it's true for a two-person
family office or an RIA with no analyst, which is closer to who this is for.

**MERCER:** Then why are you showing it to me?

**NEELAY:** Because I wanted it judged by the hardest reader before I decided who it
was for. That's a real answer but it isn't a flattering one.

**MERCER:** It's the right order, at least. Most people do it backwards. But hear what
you just said — you don't know who it's for. That's not a marketing gap, it's a design
gap, because the answer changes the product. A family office wants the note. A PM wants
the *diff* — what changed since I last looked. Those are different tools.

**NEELAY:** Noted. Literally.

**MERCER:** Show me the one that impressed you most, since I've been doing the choosing.

**NEELAY:** Lumen. In October the note argued that the operating cash flow recovery
behind the turnaround story was substantially customer prepayment under long-term
capacity contracts, booked as deferred revenue, with the matching capital expenditure
still ahead of it. It said that's working-capital timing with a contractual obligation
attached, not a conversion improvement. It named the date the evidence would arrive —
November 4th, after the close — and named the lines to read: deferred revenue against
capex, net debt after the February redemption, and any backlog disclosure.

**MERCER:** And?

**NEELAY:** Q3 printed on November 4th. Free cash flow was about negative seventy-six
million against positive one point seven billion a year earlier. The backlog disclosure
came in above thirteen and a half billion.

**MERCER:** *(pause)* Now that is a call. A one-point-eight-billion swing, mechanism
named in advance, date named in advance. If you'd opened with that I'd have sat up.

**NEELAY:** The reason I didn't open with it is the headline on that note says the stock
is worth forty cents against four forty-six. Minus ninety-one percent.

**MERCER:** Of course it does. Why?

**NEELAY:** No capex is tagged for any recent year — the only tagged capex periods end
more than a decade ago — and there's one usable year of operating cash flow. So the
model built a cash flow projection with no investment line.

**MERCER:** So the single best piece of analysis in your sample sits underneath a number
that tells me you can't read a cash flow statement. Nobody gets to the good part. You
understand that the forty cents is not a presentational problem — it's the only thing
anyone will quote back to you.

**NEELAY:** Yes.

**MERCER:** What about this one. Truist.

**NEELAY:** I'd skip it.

**MERCER:** Why.

**NEELAY:** Because the summary says, verbatim, "No variant view was identified against
the prevailing read, so this analysis says nothing the price does not already reflect."
And no management claims were reconciled.

**MERCER:** A note that tells me it has nothing to say.

**NEELAY:** Yes. I'd argue that's better than manufacturing a thesis.

**MERCER:** It is better than manufacturing a thesis. It is not better than *finding*
one, and there was one sitting right there. Truist took a one-point-four-billion
securities loss in Q3 to reinvest at four-forty, guided to sixteen to eighteen percent
ROTCE, and the CFO said there's another seventeen to eighteen billion of the same trade
available. Against a balance sheet that hasn't grown since 2021 and net interest income
that peaked in 2023. That is a thesis, it's in a filing that predates your note by three
days, and your tool read the filing and came back with nothing.

**NEELAY:** The note registers the quarter in one clause. It says the third quarter
"adds a further AFS repositioning loss and loan sale impact on preliminary figures."

**MERCER:** It saw it and didn't know what it was looking at. That's worse than missing
it.

**NEELAY:** I agree. It's coming out of the sample set.

**MERCER:** Let me see the navigation on the document for a second. *(scrolls)* "Variant
view." "Counter-case." "What must be true." "Market pricing." "Trajectory."

**NEELAY:** Those are section headings.

**MERCER:** Nobody on a desk says "variant view". The phrase is variant perception —
it's Steinhardt's, it's thirty years old, and it's one word away from what you wrote.
"Counter-case" isn't a thing at all; it's the bear case, or risks to the thesis.
"What must be true" is a McKinsey deck. "Trajectory" is nothing. I don't say this to be
pedantic — I say it because a PM reads five headings, concludes you've never sat on a
desk, and reads the sixth section with that assumption in place. You're spending
credibility you need later on words that cost nothing to fix.

**NEELAY:** I know. I audited exactly that last week — every reader-facing term against
CFA Institute material, Nareit, FDIC, the filings. The audit says what you just said,
with sources. "Variant view" returns no professional usage. "Counter-case" returns none.
"Implied expectations" should be "price-implied expectations," which is Mauboussin's.

**MERCER:** So you know and it's still on the screen.

**NEELAY:** The form fields are fixed. The document headings aren't. Which is actually
worse than it sounds, because —

**MERCER:** Because the downloaded file and the screen now say different things.

**NEELAY:** Yes. The export says "Where this analysis departs from consensus" and
"Financial trajectory." The screen says "Variant view" and "Trajectory."

**MERCER:** Your own write-up says — I read it on the train — the screen and the
exported file render from one ordered section list "so they cannot drift."

**NEELAY:** They've drifted.

**MERCER:** Then that sentence is false, and it's false in the document whose entire job
is to make me believe the careful sentences. If you tell me a thing is structurally
impossible and I find it on page two, I stop grading the work and start grading you.
Delete the sentence or make it true. Preferably make it true.

**NEELAY:** Make it true. It's one render path.

**MERCER:** What else have you got that you know is wrong and haven't fixed? Ask
yourself that before the next meeting and bring the list, because I will find them and
it is much better coming from you.

**NEELAY:** There's one more that matters. On a bank, there's a metric labelled
"Nonperforming Loan Ratio" that computes nonperforming loans over *total assets*. The
accepted definition is over total gross loans. The label makes the number read roughly
half of what a reader thinks it is.

**MERCER:** That's not a wording problem, that's a wrong number with a right-sounding
name, which is the worst category. How did it get there?

**NEELAY:** Carelessness. The same config file does the honest thing two rows above —
there's a metric called "Net interest income / total assets" precisely because the tool
can't build average earning assets and won't claim NIM. The discipline was there and
this row broke it.

**MERCER:** The NIM one is right, for what it's worth. Not claiming NIM when you can't
build the denominator is exactly what I'd want. Which makes the NPL row read like
someone else wrote it.

**NEELAY:** Same person. Different day.

**MERCER:** *(gestures at the screen)* And it's logged you out again.

**NEELAY:** It does that. The session drops back to the passphrase gate on a reconnect.
It's happened three times this morning.

**MERCER:** In a thirty-minute meeting your demo logged out three times. In front of
someone you don't know, that's the whole meeting. Fix it before the mislabelled ratio.

**NEELAY:** Fair.

**MERCER:** Last thing. You've got six notes. Four of them name a catalyst that has
already happened — ADP's bookings number, Ford's Q3, Realty Income's Q3, Lumen's
November 4th. Two of those resolved against the note's own argument. ADP nominated
bookings as the discriminating variable and bookings printed a Q1 record with guidance
raised.

**NEELAY:** That's in my audit too. ADP's variant view lost on the first datapoint it
chose.

**MERCER:** I want to be careful here, because that's the one I'd defend you on. A note
that names its test and loses it is doing research correctly. That's falsifiability and
most of the street never offers it. The problem isn't that ADP was wrong. The problem is
that the note still writes the test in the future tense, a month after it was marked. If
you'd shown me the same note with a line saying "this call was tested on October 28th
and failed, here's what survives" — the float-funding point, which is good, by the way,
nobody nets the cost of the extended-maturity book against the float revenue — I'd think
better of the tool, not worse.

**NEELAY:** That's a feature I hadn't thought of. Re-run against the catalyst and score
the prior note.

**MERCER:** That's your product, possibly. Not the note. The note is a commodity. The
scorecard isn't. Nobody keeps an honest record of their own calls because it's painful
and manual, and you've got a machine that already writes down the test and the date.

**NEELAY:** That's the most useful thing I've heard today.

**MERCER:** It's also three features away. I've got to go. Blunt version?

**NEELAY:** Please.

**MERCER:** The reasoning layer is better than it has any right to be. Realty Income's
per-share-versus-enterprise point is a real analyst's insight and the Lumen call is
genuinely impressive. The data layer underneath it is not fit to show anyone — a blank
revenue line on Ford, Kimco at sixteen million dollars, no capex on Lumen, a five
hundred percent target, a ratio labelled wrong. Right now the good part is strapped to
the bad part and the bad part is what's at the top of every page, in the largest font
you own. Don't take this into a room until the number at the top of the page is one
you'd defend.

**NEELAY:** How long would you give it?

**MERCER:** Two weeks of the fixes you already know about, and then show me the
scorecard idea, not the note. Send me the Realty Income one though. I want to look at
the comp plan point properly.

---

## 2. Where he drew blood

Every moment the presenter could not answer, and the honest answer.

**1. "Ford's guidance is six to seven billion and you've got twelve and a half. Why?"**
Answered, but the real answer is worse than the one given. The honest version: the model
takes a three-year average of *consolidated* operating cash flow less capex and calls it
free cash flow. For any filer with a captive finance arm, a large REIT securitisation
book or heavy deferred revenue, that number is not free cash flow in any sense a
practitioner uses, and the pipeline has no test that detects the condition. It is not a
Ford bug; it is a class of filer the model silently mis-handles.

**2. "Why is eight and a half percent good enough?" (the third why)**
The presenter got two levels deep and conceded at the third. The honest answer he should
have given immediately: *it isn't good enough, and the target is therefore not an output
of this tool — it is a placeholder that should never have been rendered as a price.* The
correct product decision is that the DCF produces one thing only, the price-implied
growth rate, and never a per-share value. The implied-expectations framing ("the price
requires 17.1% annual FCF growth against a filed 11.8%") needs no cost of capital at
all and is the stronger output.

**3. "Your table says FY2022 margin went up. Your sentence says every year declined."**
No answer available. Honest version: the no-model-writes-a-number guarantee protects
figures and citation offsets and does not extend to claims about the *shape* of a
series, which is the class of claim an investor actually acts on. The guarantee is
narrower than the marketing implies, and the gap should be stated in the same breath as
the guarantee, not discovered by the reader.

**4. "Ford's FY2025 revenue is in the 10-K and you printed n.d."**
This is where the meeting was lost. Honest version: the tool cannot currently
distinguish "the filer did not report this" from "I failed to resolve the concept," and
it degrades silently in both cases. Until a missing latest-year revenue or net income is
a hard failure, no output of the pipeline is trustworthy without manual check — which is
the exact work the tool claims to remove.

**5. "You can't rule it out, or you haven't checked?" (Realty Income AFFO)**
Conceded. Honest version: the central finding of the best note in the set is computed on
a derived FFO (net income + D&A before disposals) because the filer's FFO tag did not
map, and it has never been compared with the AFFO per share the company publishes every
quarter and the sector trades on. The finding may well survive — but it is, today,
unverified against the sector's own measure, and that check is a ten-minute manual task
that should have been done before showing it to anybody.

**6. "Kimco revenue sixteen point eight."**
Conceded immediately, but the implication was not: a disclosed caveat does not convert a
wrong number into an indicative one. Honest version: peer rows whose fundamentals do not
resolve must be dropped, not printed with a footnote. As rendered, the comparables table
on the strongest note carries one false figure and no usable column.

**7. "What does this do that a screen plus an analyst doesn't?"**
The answer given — speed of assembly — is the answer this PM least cares about and he
said so. The honest answer, which the presenter only reached indirectly: for a reader
with no analyst, it is the analyst; for a reader *with* an analyst, the product is not
the note at all but the structured, dated, falsifiable record of what was claimed and
when it was tested. The tool already generates both halves and ships neither as the
headline.

**8. "Why are you showing it to me, if you don't know who it's for?"**
Honestly answered, and it cost him. "I wanted it judged by the hardest reader first" is
true and defensible, but it told the PM the product has no defined user, which reframed
every subsequent flaw as a symptom rather than a bug.

**9. "Your own document says the screen and the export cannot drift."**
No defence. They have drifted: `ui/document.py` renders "Trajectory", "Variant view" and
"What must be true"; `ui/export.py` renders "Financial trajectory", "Where this analysis
departs from consensus" and "Disconfirming evidence". A falsifiable claim in the
credibility document, falsified on the screen in the room.

**10. "It's logged you out again."**
Nothing to say. The gate drops the session on reconnect; `?view=…` deep links render the
home screen after re-entry; several primary buttons have no accessible name at all.

---

## 3. What he would actually say afterwards

To a colleague, in the corridor, unprompted:

> Kid built something real, which I wasn't expecting. There's a piece in there on Realty
> Income — he's got the enterprise numbers growing and the per-share numbers going
> backwards for three straight years, and then he lines that up against the comp plan,
> which pays out on leverage and dividend growth, both of which you improve *by issuing
> stock*. And it certified above target over exactly those three years. That's not a
> screen. That's an analyst's point and I haven't heard anyone make it on that name.
>
> And there's a Lumen note from October that said the cash flow was customer prepayments
> with the capex still to come, named November 4th as the date it would show, and the
> print was a one-point-eight-billion free cash flow reversal. Called the mechanism and
> the date.
>
> So why am I not interested? Because the top of the Ford page says the stock is worth
> eighty dollars. It's twelve. Five hundred and sixty percent. And the latest year's
> revenue on the same page is blank — blank, on Ford — because his plumbing couldn't
> find it and didn't think that was worth stopping for. Kimco's revenue in his comp
> table is sixteen million dollars. Lumen's worth forty cents because he has no capex.
> He knows about all of it, which I'll give him, but he showed it to me anyway.
>
> Here's the thing. The analysis is a person's work and the data is a student's, and
> they're in the same document, and the student's half is in the big font at the top.
> I can't un-see the blank revenue line. Once I know the pipeline can fail silently I
> have to check everything, and if I'm checking everything I'll just have Sarah do it.
>
> Two things I'd actually use, if he built them. One, make it refuse. It already refuses
> to value a REIT and a bank and that's the best instinct in the whole thing — make it
> refuse a target whenever the model disagrees with the market by more than it can
> explain. Two, and this is the real one: it writes down what it expects and the date
> the evidence lands. Then it never goes back and marks it. If he turned that into a
> scorecard — here's what we said, here's what happened, here's what survived — I'd pay
> for that, because nobody keeps that record honestly, including me. The notes are a
> commodity. The marked record isn't.
>
> He's got the instincts. He doesn't yet have the discipline to hold a thing back. Which
> at his age is the normal failure mode and it's fixable in one meeting, which is this
> one.

---

## 4. Fix before the next meeting

Ordered by what cost him the room, soonest first. Each item names the moment it comes
from.

**1. Stop the session dropping. — "It's logged you out again."**
Three logouts in thirty minutes ends a meeting regardless of content. The gate must
survive a Streamlit reconnect, and a `?view=` deep link must restore that view after
re-entry rather than bouncing to home. Add accessible names to the three primary
buttons while in there — they currently expose no name at all, which is also why the
demo is impossible to drive by keyboard.

**2. Hard-fail on a missing latest-year revenue or net income. — "Ford's FY2025 revenue
is in the 10-K."**
This is the fix that decides whether anything else matters. The pipeline must
distinguish "not reported" from "not resolved" and refuse to render a note in the second
case. Nothing downstream is trustworthy until it does, and he said so in exactly those
terms.

**3. Suppress the price target whenever the DCF diagnostic trips. — "Five hundred and
sixty-four percent."**
The `NM` machinery exists and already runs for the REIT and the bank. Gate the target
and implied-upside lines on the existing model-versus-market threshold, and keep the
price-implied growth framing, which needs no cost of capital and is the better output.
Ford at +564%, Lumen at −91% and Costco at −40.5% all disappear on one change. Consider
removing the per-share target permanently: the eight-and-a-half-percent convention
cannot survive the third "why" and he got there in under a minute.

**4. Repair the provenance checker's number matcher. — not raised in the room, and it
would have been.**
Costco and ADP — the two cleanest notes — carry a banner reading "treat any number in
the prose as unsupported", triggered by the warehouse count `939` and the `500` in
"S&P 500". He did not open either one. If he had, the tool's two best notes would have
instructed him to disbelieve themselves.

**5. Add a direction checker over the filed series. — "Your table says FY2022 went up."**
"Rose/fell in every year" is a monotonicity test against a series already in memory.
Any prose claim about the shape of a series that the series contradicts should block the
render. This closes the gap between what the guarantee covers (figures) and what the
reader acts on (directions).

**6. Drop unresolved peer rows instead of footnoting them. — "Kimco revenue sixteen
point eight."**
If a peer's fundamentals do not resolve per-company, the row does not print. If fewer
than four rows survive, the table does not print. A caveat under a wrong number reads as
knowing and shipping it.

**7. Verify the Realty Income finding against reported AFFO per share. — "You can't rule
it out, or you haven't checked?"**
Manual, this week, before the note is sent as promised. Derived FFO (net income + D&A
before disposals) versus the company's published AFFO per share for FY2022–FY2025. If
the per-share decline survives the sector's own measure, say so in the note in one line;
if it does not, the note's central claim must be rewritten. Either way this cannot be
left as "the supplied data cannot test it."

**8. Make the screen/export claim true. — "Your own write-up says they cannot drift."**
`ui/document.py` and `ui/export.py` must take their headings from one list. While doing
it, land the vocabulary audit's first five: variant view → **variant perception**,
counter-case → **bear case**, what must be true → **conditions for the current price**
(or fold into price-implied expectations), trajectory → **financial analysis**, market
pricing → **current valuation**. And fix `npl_ratio`: label it **"Nonperforming loans /
total assets"**, which is what it computes.

**9. Cut Truist and Ford from the sample set; re-run O, COST and LUMN inside the last
week. — "A note that tells me it has nothing to say."**
Truist is a null note that missed a thesis in a three-day-old filing. Ford opens with
+564%, a blank latest-year revenue and a claim its own table refutes. Replace both with
clean-tag compounders whose latest-year revenue, net income, total debt *and* capex are
confirmed to resolve in a dry run before the note is paid for.

**10. Build the scorecard. — "That's your product, possibly."**
The one thing he said he would pay for. Each note already names its catalyst, the date,
and the confirming evidence. Re-run against the catalyst once it fires and render the
prior call marked: tested on this date, confirmed or failed, this is what survives. ADP
is the first entry and it is a loss — which is why it works. Lumen is the second and it
is a win called by mechanism and date. A tool that keeps an honest record of its own
calls is a different product from a tool that writes notes, and it is the one he asked
for.

**11. Answer "who is this for" in one sentence before walking into another room. —
"Then why are you showing it to me?"**
He is not the user and the meeting proved it: four hours of a junior's time is not his
constraint. The reader with no analyst is the user for the note; the reader with an
analyst is the user for the scorecard. Pick one per meeting and build the demo around
that reader.
