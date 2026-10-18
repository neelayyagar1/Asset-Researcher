"""Prompt loading, with the shared style block appended once.

The register rules (no em-dashes, no consultant vocabulary, sentence case,
every sentence carries information) apply to both writing prompts and to
neither of the two mechanical ones. They used to be pasted into
`narrative.md` and `reconciliation.md` identically, alongside a
`_style.md` that nothing loaded, so there were three copies and editing one
silently changed nothing.

Now there is one copy. `shared_style.md` is appended at load time to the
prompts that ask for prose, and left off the ones that ask for a mapping.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_PROMPTS = Path(__file__).resolve().parent / "prompts"
_SHARED_STYLE = "shared_style.md"

# The prompts that produce prose a reader will see. Concept resolution and
# mandate parsing return structured data, so the register rules are noise in
# their context window.
_NEEDS_STYLE = {"narrative.md", "reconciliation.md"}


@lru_cache(maxsize=None)
def load_prompt(name: str) -> str:
    """One prompt by filename, with the shared style block where it applies."""
    body = (_PROMPTS / name).read_text(encoding="utf-8").rstrip()
    if name not in _NEEDS_STYLE:
        return body + "\n"
    shared = (_PROMPTS / _SHARED_STYLE).read_text(encoding="utf-8").strip()
    return f"{body}\n\n{shared}\n"
