"""Concept resolution must be able to tell a live tag from a dead one."""
from asset_researcher.sources.edgar.facts import Fact, RawXbrlFacts


def _facts() -> RawXbrlFacts:
    def f(end, val):
        return Fact(start=None, end=end, val=val, accn="a", fy=int(end[:4]),
                    fp="FY", form="10-K", filed=end, frame=None)
    return RawXbrlFacts(
        cik=1, entity_name="Example",
        concepts={
            "LongTermDebtNoncurrent": {"USD": [f("2011-06-30", 37e6)]},
            "DebtLongtermAndShorttermCombinedAmount": {
                "USD": [f("2024-06-30", 3.0e9), f("2026-06-30", 3.1e9)]
            },
        },
    )


def test_concepts_are_offered_with_the_last_year_they_were_reported():
    """A bare list of names cannot distinguish a tag the filer abandoned
    in 2011 from the one it uses now, and the resolver picked the dead
    one for ADP's total debt - $37m against real debt near $3bn."""
    listing = _facts().concept_listing()
    assert "LongTermDebtNoncurrent (through 2011)" in listing
    assert "DebtLongtermAndShorttermCombinedAmount (through 2026)" in listing
