#!/usr/bin/env python3
"""Apply presentation-only fixes to sample notes that are already built.

**This is a stopgap, and it should be deleted once the notes are rebuilt.**

A note costs an API call to produce, so the six shipped samples are
artifacts rather than something a deployment regenerates. When a label or
a section name changes in the renderer, the built artifacts do not
follow: they keep whatever wording was current when they were made. That
is usually fine, because the next rebuild catches up.

It stopped being fine when the renderer's vocabulary was corrected and
the API key was rotated in the same window. The samples - the first thing
a reader opens, and the free path into the product - were left showing
exactly the wording an audit had just condemned, with no way to rebuild
them.

What this changes is text a reader sees and nothing else. Section
headings, one status label, and an appended script. It does not touch a
figure, a citation, a quote, a source URL or any id - the anchors keep
their original slugs, so every section link keeps working. Anything that
would alter the analysis belongs in a rebuild, not here.

    python scripts/patch-samples.py            # report what would change
    python scripts/patch-samples.py --write    # apply it
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "build" / "site"

# Visible text only. The left side is what the old renderer emitted; the
# right side is what the current one emits, with the reasoning for each
# recorded in docs/VOCABULARY.md.
HEADINGS = {
    "Summary": "Investment summary",
    "Variant view": "Variant perception",
    "Market pricing": "Current valuation",
    "Implied expectations": "Price-implied expectations",
    "Counter-case": "Bear case",
    "Reconciliation": "Management vs. filed figures",
    "Health": "Distress and manipulation screens",
    "Questions": "Questions for management",
    "Note": "Business description",
}


def _patch(html: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}

    # The citations table said "Verified" where the whole product claims
    # it says "Located": the check establishes that the quoted text sits
    # where the citation says it does, and nothing about whether it
    # supports the claim built on it.
    html, n = re.subn(r">Verified<", ">Located<", html)
    if n:
        counts["Verified -> Located"] = n

    # Section headings and their entries in the navigation bar. Matched on
    # the full element so a word like "Summary" inside a sentence is not
    # touched, and the href is left alone so the anchors still resolve.
    for old, new in HEADINGS.items():
        total = 0
        html, n = re.subn(
            rf'(<h2 class="ar-sec-label"[^>]*>){re.escape(old)}(</h2>)',
            rf"\g<1>{new}\g<2>", html,
        )
        total += n
        html, n = re.subn(
            rf'(<a href="#[^"]+">){re.escape(old)}(</a>)',
            rf"\g<1>{new}\g<2>", html,
        )
        total += n
        if total:
            counts[f"{old} -> {new}"] = total

    # The section bar could not jump, because inside the app the note is
    # an iframe whose baseURI is the parent page, so "#s-valuation"
    # resolved against the wrong document. Resolving by id and scrolling
    # depends on no base URL. Appended only where it is not already there.
    if "nav.ar-nav a" not in html:
        from asset_researcher.ui.export import _JUMP_SCRIPT

        html = html.replace("</body>", f"{_JUMP_SCRIPT}</body>", 1)
        counts["section links made to scroll"] = 1

    return html, counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true",
                        help="apply the changes; otherwise only report them")
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    if not SITE.is_dir():
        print(f"No {SITE}.", file=sys.stderr)
        return 1

    pages = [p for p in sorted(SITE.glob("*.html")) if p.stem != "index"]
    if not pages:
        print(f"{SITE} holds no notes.", file=sys.stderr)
        return 1

    for page in pages:
        before = page.read_text(encoding="utf-8")
        after, counts = _patch(before)
        label = "patched" if args.write else "would patch"
        if not counts:
            print(f"{page.stem}: already current")
            continue
        print(f"{page.stem}: {label}")
        for what, n in counts.items():
            print(f"    {n:>3}  {what}")
        if args.write:
            page.write_text(after, encoding="utf-8")

    if not args.write:
        print("\nNothing written. Re-run with --write to apply.")
    else:
        print("\nRe-pack with scripts/pack-samples.py, then commit the blob.")
        print("These notes still carry the figures they were built with.")
        print("Rebuild them properly once the API key works again.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
