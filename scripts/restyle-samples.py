#!/usr/bin/env python3
"""Refresh the stylesheet baked into each built sample note.

`export.report_to_html` embeds `theme.document_stylesheet()` at build
time, so a CSS fix made after a note was rendered does not reach it. The
six sample notes carry the stylesheet as it stood on the day they were
built, and nothing in the suite compares the two: every document-sheet
test asserts against `document_stylesheet()`, which is the function, not
against the artifact a reader actually opens.

That gap has already cost something twice. The Peers sticky-header defect
was fixed in theme.py and was still live in all six notes on the demo
site. And a later review of this branch found the blob a second rule
behind - the hardened `.ar-skip` - with the whole suite green, because
there was nothing to notice it.

Rebuilding the notes properly costs about six dollars of API calls and
thirty-five minutes, and would move the figures' as-of dates for no
reason. Nothing about a rendered body changes when theme.py does - only
the generated CSS - so the honest equivalent is to replace that one
block and leave everything else byte-identical.

This refuses to run if the body would differ by so much as a byte
outside the stylesheet. That check is what makes it a re-render of the
part that changed rather than an edit of a shipped artifact.

    python scripts/restyle-samples.py
    SAMPLES_KEY='...' python scripts/pack-samples.py

The second line is not optional. This script rewrites build/site, which
is not shipped; `pack-samples.py` is what seals the result into
asset_researcher/samples/notes.enc, which is. Running the first without
the second leaves the blob exactly as drifted as it was.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from asset_researcher.ui import theme  # noqa: E402

SITE = ROOT / "build" / "site"
BLOCK = re.compile(r"<style>.*?</style>", re.S)


def main() -> int:
    if not SITE.is_dir():
        print(f"No built notes at {SITE}.")
        print("Run scripts/publish-sample.py first, or fetch the build.")
        return 1

    current = theme.document_stylesheet()
    changed: list[str] = []
    for path in sorted(SITE.glob("*.html")):
        if path.name == "index.html":
            continue
        html = path.read_text()
        blocks = BLOCK.findall(html)
        if not blocks:
            print(f"  {path.name}: no <style> block, skipped")
            continue
        old = blocks[0]
        if old == current:
            print(f"  {path.name}: already current")
            continue
        before, after = html.split(old, 1)
        rebuilt = before + current + after
        # Everything outside that one block has to be untouched.
        if rebuilt.replace(current, "", 1) != html.replace(old, "", 1):
            print(f"  {path.name}: REFUSED, body would change")
            return 1
        path.write_text(rebuilt)
        changed.append(path.name)
        print(f"  {path.name}: stylesheet {len(old)} -> {len(current)}")

    print(f"\nrefreshed {len(changed)} note(s): {', '.join(changed) or 'none'}")
    if changed:
        print("Now re-seal them:  SAMPLES_KEY='...' python scripts/pack-samples.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
