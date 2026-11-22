"""Figure formatting, defined once.

These lived in two modules as copies, which is how a zero market
capitalisation came to render as "NM" in both and a $499m small cap came to
render as "$0B" in both: the same defect, fixed nowhere, because fixing it
in one file left the other.

Every function here distinguishes three states a financial table must never
blur: a real figure, a figure that is not meaningful, and a figure that was
never reported.
"""

from __future__ import annotations

import math
import re

NM = "NM"  # a ratio whose denominator makes it meaningless
ND = "n.d."  # not disclosed, or not tagged


def _finite(value: float | None) -> bool:
    """NaN and infinity reach a renderer as "$nan" and "inf%" otherwise.

    Reachable because Python's own JSON parser accepts a bare NaN literal,
    so a malformed upstream payload can carry one all the way here.
    """
    return value is not None and math.isfinite(value)


def pct(value: float | None, digits: int = 1) -> str:
    if not _finite(value):
        return NM
    return f"{value * 100:,.{digits}f}%"


def signed_pct(value: float | None) -> str:
    """Growth and upside carry an explicit sign: the direction is the point."""
    if not _finite(value):
        return NM
    # `-0.0` is falsy but negative, and the naive prefix test produced
    # "+-0.0%" with both signs attached.
    if value == 0:
        return "0.0%"
    return f"{'+' if value > 0 else ''}{value * 100:,.1f}%"


def usd(value: float | None) -> str:
    if not _finite(value):
        return NM
    if value < 0:
        return f"(${abs(value):,.2f})"
    return f"${value:,.2f}"


def scaled_usd(value: float | None) -> str:
    """Dollars at a readable scale.

    Zero is a figure, not an absence: `if value else "NM"` reported a
    company with no market capitalisation as unmeasurable, which is the one
    thing a financial table must never do. Sub-billion values render in
    millions rather than collapsing to "$0B".
    """
    if not _finite(value):
        return NM
    magnitude = abs(value)
    if magnitude >= 1e9:
        rendered = f"${magnitude / 1e9:,.1f}B"
    elif magnitude >= 1e6:
        rendered = f"${magnitude / 1e6:,.0f}M"
    elif magnitude >= 1e3:
        rendered = f"${magnitude / 1e3:,.0f}K"
    else:
        rendered = f"${magnitude:,.0f}"
    return f"({rendered})" if value < 0 else rendered


# ------------------------------------------------------------------ dates

_ISO_DAY = re.compile(r"\A(\d{4})-(\d{2})-(\d{2})\Z")
_MONTHS = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)


def filed_date(value: str) -> str:
    """A filing date as a reader in New York writes one.

    ISO is the right format for a key, a filename and a sort, and this
    product uses it for all three. It is the wrong format for a line of
    prose beside a company's name: "Filed 2026-08-05" is a record
    locator, and the chip it sits in is read as a sentence.

    Anything that is not a plain ISO day comes back untouched, because
    a date this cannot parse is a date it has no business rewriting.
    """
    match = _ISO_DAY.match(value.strip())
    if not match:
        return value
    year, month, day = (int(part) for part in match.groups())
    if not 1 <= month <= 12:
        return value
    return f"{_MONTHS[month - 1]} {day}, {year}"
