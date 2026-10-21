"""A small Markdown to HTML converter for the finished note.

Streamlit renders Markdown into a container this code cannot add a class to,
and its own Markdown processor will not run on content inside a block-level
`<div>`. So the note cannot be both rendered as Markdown and set in the
measure, type and citation styling the rest of the page uses.

Converting it here solves that and pays for itself twice: the same function
produces the standalone HTML export, so a report saved to a file and a report
read in the browser come out of one code path rather than two that drift.

The subset is exactly what Call A emits and no more: level two and three
headings, paragraphs, unordered lists, bold, and inline links. Anything else
is escaped and shown as text. A general Markdown library would be the wrong
dependency here, because the risk worth guarding against is not an
unsupported construct, it is unescaped model output reaching the page as
markup.
"""

from __future__ import annotations

import re
from html import escape

# Ordered: links are extracted before bold so a bold label inside a link
# label cannot break the link, and both run on already-escaped text.
# An optional title after the URL, which is how a citation marker says
# where it leads. Without it the marker's accessible name was the literal
# "[1". The title is already HTML-escaped when this runs, so the quotes
# in the source text are &quot; by the time the pattern sees them.
_LINK = re.compile(
    r"\[([^\]]+)\]\(([^)\s]+)(?:\s+&quot;([^)]*?)&quot;)?\)"
)
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_CODE = re.compile(r"`([^`]+)`")
# Single asterisks, matched only after the double-asterisk pass has run,
# so bold is never chewed into two emphases. The document leans on this
# in its sharpest sentence - "the interface says *located*, not
# *verified*" - where six literal asterisks were surviving into the page.
_EMPHASIS = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_SAFE_URL = re.compile(r"^(https?://|/|#)", re.IGNORECASE)


def _inline(text: str) -> str:
    """Escape, then re-admit the two inline constructs the note uses.

    URLs are checked against a scheme allowlist. A citation marker is built
    by this project from a filing URL, but the renderer is also pointed at
    model prose, and `javascript:` in a link target is the one way a
    Markdown link becomes an execution path.
    """
    out = escape(text, quote=True)

    def link(match: re.Match[str]) -> str:
        label, url, title = match.group(1), match.group(2), match.group(3)
        if not _SAFE_URL.match(url):
            return label
        name = f' title="{title}" aria-label="{title}"' if title else ""
        return (
            f'<a href="{url}" target="_blank" rel="noopener noreferrer"'
            f"{name}>{label}</a>"
        )

    out = _LINK.sub(link, out)
    out = _BOLD.sub(lambda m: f"<strong>{m.group(1)}</strong>", out)
    out = _EMPHASIS.sub(lambda m: f"<em>{m.group(1)}</em>", out)
    # Backticks last, so a span cannot swallow a link or a bold run. The
    # text inside was escaped with everything else, which is what makes it
    # safe to emit as markup here.
    return _CODE.sub(lambda m: f"<code>{m.group(1)}</code>", out)


def to_html(markdown: str, base_level: int = 3) -> str:
    """The note as HTML, without a wrapping element.

    `base_level` is the heading level a top-level `#` becomes. The default
    of 3 suits prose nested inside a report section, whose own label is an
    h2. A standalone document passes 2, so its title is the page's title
    rather than something smaller than its own subheadings.
    """
    if not markdown or not markdown.strip():
        return ""

    blocks: list[str] = []
    paragraph: list[str] = []
    items: list[str] = []
    quote: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(f"<p>{_inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def flush_list() -> None:
        if items:
            body = "".join(f"<li>{_inline(i)}</li>" for i in items)
            blocks.append(f"<ul>{body}</ul>")
            items.clear()

    def flush_quote() -> None:
        if quote:
            blocks.append(f"<blockquote><p>{_inline(' '.join(quote))}</p></blockquote>")
            quote.clear()

    def level(offset: int) -> int:
        # Clamped at 6, which is as deep as HTML goes.
        return min(6, base_level + offset)

    for raw in markdown.splitlines():
        line = raw.rstrip()
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            flush_list()
            flush_quote()
            continue

        for marker, offset in (("### ", 2), ("## ", 1), ("# ", 0)):
            if stripped.startswith(marker):
                flush_paragraph()
                flush_list()
                flush_quote()
                tag = f"h{level(offset)}"
                text = _inline(stripped[len(marker):].strip())
                blocks.append(f"<{tag}>{text}</{tag}>")
                break
        else:
            if stripped.startswith(">"):
                flush_paragraph()
                flush_list()
                quote.append(stripped.lstrip(">").strip())
                continue

            if stripped.startswith(("- ", "* ")):
                flush_paragraph()
                flush_quote()
                items.append(stripped[2:].strip())
                continue

            # A line that is indented, or that merely follows a bullet
            # without starting one, continues that bullet. It used to end
            # the list and open a paragraph, so every bullet wrapped at
            # the source's margin was severed into a one-item list plus an
            # orphan sentence. In a hand-written document where every
            # bullet wraps, that was all of them.
            if items and (raw[:1].isspace() or not paragraph):
                items[-1] += " " + stripped
                continue

            flush_list()
            flush_quote()
            paragraph.append(stripped)
            continue
        continue

    flush_paragraph()
    flush_list()
    flush_quote()
    return "".join(blocks)
