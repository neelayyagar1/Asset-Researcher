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

_YIELD = re.compile(_STAT.format(label="Free cash flow yield"), re.S)
_CAGR = re.compile(_STAT.format(label="Filed free cash flow CAGR"), re.S)

# Two FILED figures, carried out of every note into the index.
#
# The index used to list the note's LEAD statistic - a label in one
# column and its number in the next, under a header reading "Value".
# That header is unreadable on its own, because what the number means
# changes per row: 6.8% is a growth rate the price requires and 15.3x
# is a multiple, and the only thing that distinguished them lived in
# the column beside it. A column header has to be true of its column.
#
# These two are not. Free cash flow yield and the filed free cash flow
# CAGR mean the same thing in every row, come straight out of the
# filings rather than out of a model, and are the pair a reader
# actually compares across names: what the cash costs today, and what
# the cash has done. Every one of the six notes carries both, checked
# rather than assumed.
FIELDS = ("price", "filed", "cited", "metric", "value", "yield", "cagr")


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

    fcf = _YIELD.search(text)
    if fcf:
        out["yield"] = _plain(fcf.group(1))
    cagr = _CAGR.search(text)
    if cagr:
        out["cagr"] = _plain(cagr.group(1))

    return out
