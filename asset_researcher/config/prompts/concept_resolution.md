You are mapping a company's actual XBRL financial-statement tag names onto a
canonical set of financial metrics. You are given only the LIST of tag names
this filer uses, no values. Your job is purely semantic: which tag name
means "revenue", which means "net income", and so on.

Rules:
- Map each canonical metric to the XBRL concept name(s) from the provided
  list whose values sum to that metric. Use a single concept whenever one
  concept fully captures the metric. If no concept in the list clearly
  corresponds, return an empty list, do not guess.

- **Use multiple concepts ONLY when they are mutually exclusive components
  that must be added together, and never when one already contains another.**
  Double-counting produces a confidently wrong number, which is worse than
  an incomplete one. Worked example for `total_debt`:
    - `LongTermDebt` already includes `LongTermDebtCurrent` and
      `LongTermDebtNoncurrent`. Summing all three triple-counts.
    - `CommercialPaper` and `OtherShortTermBorrowings` are separate
      borrowings not included in `LongTermDebt`.
    - Correct answer: `[LongTermDebt, CommercialPaper, OtherShortTermBorrowings]`
      (whichever of these the filer actually reports).
  If you are unsure whether two concepts overlap, return only the single
  most complete one.
- Prefer the most specific, most commonly-reported concept when several
  plausible tags exist (e.g. prefer a "...ExcludingAssessedTax" revenue
  variant over a generic "Revenues" tag if the company's filings favor the
  specific one, you cannot see which is more populated, so when genuinely
  uncertain between close variants, pick the more standard/generic GAAP tag
  and mark confidence as "medium").
- Set confidence to "high" only when the tag name is an unambiguous, standard
  match for the canonical metric. Use "medium" for a reasonable but not
  certain match, and "low" for a guess you are not confident in.
- Every canonical metric listed below must appear exactly once in your
  output, even if xbrl_concepts is an empty list.

Canonical metrics to map:
{canonical_metrics}

Available XBRL concepts for this filer. Each carries the last year the
filer actually reported it:
{available_concepts}

PREFER A CONCEPT THE FILER STILL REPORTS. A tag whose last year is well
behind the others is one this company stopped using, and a mapping to it
produces a series that looks complete and stopped years ago - which is
worse than no mapping, because nothing downstream can tell the
difference. Two real cases: `LongTermDebtNoncurrent` was chosen for a
filer's total debt and last appeared in 2011 at $37m against real debt
near $3bn, and a capital-expenditure tag was chosen that stopped in
2013, so a discounted cash flow was built from decade-old cash flows.

Where several concepts fit, choose the one reported through the most
recent year. Where the only fit is clearly abandoned, return an empty
list for that metric rather than mapping to it.
