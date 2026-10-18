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
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
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
        label, url = match.group(1), match.group(2)
        if not _SAFE_URL.match(url):
            return label
        return (
            f'<a href="{url}" target="_blank" rel="noopener noreferrer">'
            f"{label}</a>"
        )

    out = _LINK.sub(link, out)
    return _BOLD.sub(lambda m: f"<strong>{m.group(1)}</strong>", out)


def to_html(markdown: str) -> str:
    """The note as HTML, without a wrapping element."""
    if not markdown or not markdown.strip():
        return ""

    blocks: list[str] = []
    paragraph: list[str] = []
    items: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(f"<p>{_inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def flush_list() -> None:
        if items:
            body = "".join(f"<li>{_inline(i)}</li>" for i in items)
            blocks.append(f"<ul>{body}</ul>")
            items.clear()

    for raw in markdown.splitlines():
        line = raw.rstrip()
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        if stripped.startswith("### "):
            flush_paragraph()
            flush_list()
            blocks.append(f"<h3>{_inline(stripped[4:].strip())}</h3>")
            continue

        if stripped.startswith("## "):
            flush_paragraph()
            flush_list()
            blocks.append(f"<h2>{_inline(stripped[3:].strip())}</h2>")
            continue

        if stripped.startswith("# "):
            flush_paragraph()
            flush_list()
            blocks.append(f"<h2>{_inline(stripped[2:].strip())}</h2>")
            continue

        if stripped.startswith(("- ", "* ")):
            flush_paragraph()
            items.append(stripped[2:].strip())
            continue

        flush_list()
        paragraph.append(stripped)

    flush_paragraph()
    flush_list()
    return "".join(blocks)
