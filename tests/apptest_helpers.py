"""Reading an AppTest page the way a reader sees it.

`at.markdown` returns every markdown block the script wrote, and the
first of those is the entire stylesheet - about 60KB of CSS carrying
every selector and every explanatory comment as plain text. Joining
them and searching for a substring therefore matches the CSS, not the
page.

That mistake was made three times in this suite before it was named:

  - a test asserted "ar-topbar" to prove the bar rendered, and passed
    with the write() that emits it blanked out, because the stylesheet
    declares `.ar-topbar`;
  - the same for "ar-report-view";
  - a test asserted the gate had NOT opened by looking for "Get
    started", and reported an authentication bypass on eleven hostile
    passphrases. The gate had not opened. "Get started" appears in a CSS
    comment about how the columns stack on a phone.

The last one is the dangerous shape: a false POSITIVE on a security
property, which would have sent someone looking for a bypass that does
not exist - or, inverted, could hide one that does.

Use `page_text` for anything a reader reads, and `rendered_markup` when
the assertion is genuinely about emitted HTML.
"""

from __future__ import annotations


def _blocks(at) -> list[str]:
    return [m.value for m in at.markdown if isinstance(m.value, str)]


def _is_stylesheet(block: str) -> bool:
    return "<style>" in block or "@import url(" in block


def rendered_markup(at) -> str:
    """Every markdown block except the stylesheet, joined."""
    return " ".join(b for b in _blocks(at) if not _is_stylesheet(b))


def page_text(at) -> str:
    """What a reader sees: markup stripped, stylesheet excluded."""
    import re

    markup = rendered_markup(at)
    markup = re.sub(r"<!--.*?-->", " ", markup, flags=re.S)
    markup = re.sub(r"<[^>]+>", " ", markup)
    return re.sub(r"\s+", " ", markup).strip()
