"""The few figures a built note can be asked for from outside it.

The index on the first screen lists documents. It used to list four
columns because four were all anything had bothered to read, and the
screen was mostly empty as a result. These are the rest - and every
one of them is READ OUT of the rendered note rather than recomputed
from the report object.

That is not a convenience. This product's whole argument is that every
figure traces to a filing, and an index that recomputes its own
numbers is the one place where a figure would appear that the document
behind it does not contain. If the note does not say it, the cell is
empty.

Parsed by content, never by position. The chips a note prints differ:
a filer whose discounted cash flow came out negative gets a third
chip, which sits between the two read here, so anything counting chips
reads the wrong one on half the shipped notes.
"""

from __future__ import annotations

import re

_TAGS = re.compile(r"<[^>]+>")

# A chip is an anchor into the provenance section. Matched on its text.
_CHIPS = re.compile(
    r'<a[^>]*href="#s-provenance"[^>]*>(.*?)</a>', re.S
)
_CITED = re.compile(r"\A(\d+\s*/\s*\d+)\s+cited\Z")
_FILED = re.compile(r"\AFiled\s+(\S+)\Z")

# One statistic in the strip under the masthead, by its own label.
_STAT = (
    r'<div class="ar-stat-label">\s*{label}\s*</div>\s*'
    r'<div class="ar-stat-value[^"]*">(.*?)</div>'
)
_PRICE = re.compile(_STAT.format(label="Traded price"), re.S)
_LEAD = re.compile(
    r'<div class="ar-stat lead">\s*<div class="ar-stat-label">(.*?)</div>\s*'
    r'<div class="ar-stat-value[^"]*">(.*?)</div>',
    re.S,
)

# The note's own opening paragraph, which is its thesis.
#
# The index carried free cash flow yield and the filed CAGR for a
# while. They were comparable and they were filed, and they were still
# the wrong two columns: they are facts about the COMPANY, and a reader
# standing in front of an index of reports he has already read wants
# the report. What was this one about. What did it find.
#
# The note already answers that in its first paragraph, in two
# sentences it wrote itself - "At 23 times free cash flow the price
# requires 6.8% annual growth. The filed record compounded at 12.5%
# over 5 years." That sentence contains the multiple and the growth
# rate, so it subsumes both columns it replaces, and it reads as the
# thing it is rather than as two ratios a reader has to recombine.
#
# Lifted verbatim rather than summarised. A second sentence written
# here would be a second source of truth about what the report says,
# which is the exact fault that once put two free cash flow series in
# one note.
_TAKEAWAY = re.compile(r'<div class="ar-summary">\s*<p>(.*?)</p>', re.S)

FIELDS = ("price", "filed", "cited", "metric", "value", "takeaway")


def _plain(fragment: str) -> str:
    """The text a reader sees, with any markup inside it removed."""
    return " ".join(_TAGS.sub("", fragment).split())


def summarise(html: str) -> dict[str, str]:
    """What this note can be listed with. Empty strings for what it
    does not say, which is a normal answer rather than a failure: a
    note that declined to produce a lead statistic has no lead
    statistic, and borrowing one from somewhere else is the precise
    thing this index must not do."""
    out = {name: "" for name in FIELDS}
    text = html or ""

    for chip in _CHIPS.findall(text):
        plain = _plain(chip)
        cited = _CITED.match(plain)
        if cited:
            out["cited"] = cited.group(1).replace(" ", "")
            continue
        filed = _FILED.match(plain)
        if filed:
            out["filed"] = filed.group(1)

    price = _PRICE.search(text)
    if price:
        out["price"] = _plain(price.group(1))

    lead = _LEAD.search(text)
    if lead:
        out["metric"] = _plain(lead.group(1))
        out["value"] = _plain(lead.group(2))

    said = _TAKEAWAY.search(text)
    if said:
        out["takeaway"] = _plain(said.group(1))

    return out
