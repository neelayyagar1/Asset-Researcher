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

Available XBRL concept names for this filer:
{available_concepts}
