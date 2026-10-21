#!/usr/bin/env python3
"""Seal the built sample notes into the encrypted blob the app ships.

The notes cost an API call each to build and should not be rebuilt by a
deployment, so they travel in the repository. They should also not be
readable by anyone who browses that repository, so they travel sealed
under the demo passphrase.

    python scripts/publish-sample.py --ticker COST --ticker O
    DEMO_PASSPHRASE='...' python scripts/pack-samples.py

Writes asset_researcher/samples/notes.enc, which is committed. Re-run it
whenever the notes are rebuilt or the passphrase changes.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from asset_researcher.hosting.samples import SAMPLES_PATH, pack, unpack  # noqa: E402

SITE = ROOT / "build" / "site"
_TITLE = re.compile(r"<title>(.*?)</title>", re.S)


def main() -> int:
    passphrase = os.environ.get("DEMO_PASSPHRASE", "")
    if not passphrase:
        print(
            "Set DEMO_PASSPHRASE to the phrase the demo is shared under.\n"
            "It is the key: the app derives the same one to open this.",
            file=sys.stderr,
        )
        return 1

    if not SITE.is_dir():
        print(f"No {SITE}. Run scripts/publish-sample.py first.", file=sys.stderr)
        return 1

    notes: dict[str, str] = {}
    titles: dict[str, str] = {}
    for page in sorted(SITE.glob("*.html")):
        # The index is rebuilt by the app against whatever is in the
        # archive, so shipping the static one would only go stale.
        if page.stem == "index":
            continue
        html = page.read_text(encoding="utf-8")
        notes[page.stem] = html
        match = _TITLE.search(html)
        titles[page.stem] = (
            match.group(1).replace(" research note", "").strip()
            if match
            else page.stem.upper()
        )

    if not notes:
        print(f"{SITE} holds no notes.", file=sys.stderr)
        return 1

    blob = pack(notes, titles, passphrase)
    SAMPLES_PATH.parent.mkdir(parents=True, exist_ok=True)
    SAMPLES_PATH.write_bytes(blob)

    # Open it again before claiming success. A blob that cannot be read
    # back is worse than none: it would commit cleanly and fail in front
    # of a reviewer.
    reopened = unpack(blob, passphrase)
    assert {s.slug for s in reopened} == set(notes), "archive did not round-trip"

    raw = sum(len(h.encode("utf-8")) for h in notes.values())
    print(f"Sealed {len(notes)} notes into {SAMPLES_PATH.relative_to(ROOT)}")
    for sample in reopened:
        print(f"  {sample.slug:8s} {sample.title}")
    print(f"{raw / 1e6:.1f}MB of HTML -> {len(blob) / 1e6:.1f}MB sealed")
    print("Commit it. Without the passphrase it is a blob.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
