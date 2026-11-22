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
from html import unescape

_TAGS = re.compile(r"<[^>]+>")

# A chip is an anchor into the provenance section. Matched on its text.
_CHIPS = re.compile(
    r'<a[^>]*href="#s-provenance"[^>]*>(.*?)</a>', re.S
)
_CITED = re.compile(r"\A(\d+\s*/\s*\d+)\s+cited\Z")
# The whole of what follows "Filed", not one token: the chip prints a
# long date now and `\S+` matched "Aug" and dropped the rest, which on
# this screen is an empty Filed column rather than a wrong one.
_FILED = re.compile(r"\AFiled\s+(.+)\Z")

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

# ...and that first paragraph turned out to be the wrong sentence, for a
# reason only an index of six could show: it is the SAME sentence in
# five of them. "At N times free cash flow the price requires X% annual
# growth. The filed record compounded at Y% over 5 years." is a
# template with two numbers in it, so a column of six reads as one
# statement repeated, and the one thing a reader wants from an index -
# which of these was the one about the deleveraging - is the thing it
# cannot tell them.
#
# The variant perception is where a note says what it alone found. It
# is the product's own argument, in the report's words:
#
#   "The deleveraging is real and the capital intensity relief is the
#    part that has not been demonstrated."
#   "The filed data shows the cost-of-capital advantage eroding at the
#    margin."
#
# No two of those are alike, because no two companies are. The
# preamble ("Where this departs from consensus, at high confidence:")
# is the section's own label and says nothing about this company, so
# it is dropped; the first sentence after it is the finding.
_SUMMARY_BLOCK = re.compile(r'<div class="ar-summary">(.*?)</div>', re.S)
_PARA = re.compile(r"<p>(.*?)</p>", re.S)
_DEPARTS = re.compile(
    r"\AWhere this departs from consensus[^:]*:\s*(.+)\Z", re.S
)
# A sentence ends at a full stop followed by a capital. Guarded on the
# character BEFORE it, so "fiscal 2026. The" splits and "Inc. The"
# would too but "U.S. The" is the price of a one-line rule - neither
# half of a mis-split is wrong, only shorter.
_SENTENCE = re.compile(r"(?<=[a-z0-9)%])\.\s+(?=[A-Z])")

# The record the implied growth is asked to beat.
#
# The lead statistic alone was inert. "6.8%" under a column called
# Headline is a number with no question attached: a reader cannot tell
# whether the price is asking for more than this company has ever
# delivered or less, which is the entire point of solving a discounted
# cash flow backwards. Against the filed compound it becomes a
# judgement in one glance - 18.7% required against 11.8% delivered is a
# stretch, 2.8% required against (33.2%) delivered is a different kind
# of problem - and both figures are filed.
_FILED_GROWTH = re.compile(r"Filed FCF CAGR\s*([^<]+?)\s*<", re.S)

FIELDS = (
    "price", "filed", "cited", "metric", "value", "takeaway", "record",
)


def _plain(fragment: str) -> str:
    """The text a reader sees, with any markup inside it removed.

    Unescaped as well as stripped. These strings are re-escaped by the
    component that prints them, so leaving `&#x27;` in place sent
    `&amp;#x27;` to the page and a reader saw the entity rather than
    the apostrophe in "the company's recent history".
    """
    return " ".join(unescape(_TAGS.sub("", fragment)).split())


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

    out["takeaway"] = _finding(text)

    grown = _FILED_GROWTH.search(text)
    if grown:
        out["record"] = _plain(grown.group(1))

    return out


def _finding(text: str) -> str:
    """The one sentence this note alone says.

    The variant perception if the note has one, and the opening line if
    it does not - a note whose model declined to produce a departure
    has no finding to list, and printing the template sentence is a
    truthful fallback rather than an invented one.
    """
    block = _SUMMARY_BLOCK.search(text)
    if block:
        for para in _PARA.findall(block.group(1)):
            plain = _plain(para)
            departs = _DEPARTS.match(plain)
            if departs:
                first = _SENTENCE.split(departs.group(1), 1)[0].strip()
                # The split consumes the stop it matched on, and a
                # sentence in a column of sentences should end like one.
                return first if first.endswith(".") else first + "."

    said = _TAKEAWAY.search(text)
    return _plain(said.group(1)) if said else ""
