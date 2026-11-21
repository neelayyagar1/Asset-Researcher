"""Rendered reports a visitor generated, on disk.

A report used to live only in `st.session_state`, which means it lived
only as long as the websocket. That was tolerable while every route
through the app was a Streamlit widget, because a widget click reruns
the script without reloading the page. It stopped being tolerable the
moment the index on the first screen became a table of links: a link
is a page load, a page load is a new session, and a new session has no
report in it.

So the rendered document is written down as soon as it exists. The
session still holds the live report object - that is what the report
screen draws from, and what the Markdown export needs - but the HTML a
reader can go back to is a file, and the index can point at it without
being able to destroy it.

This is deliberately a directory of files rather than a database. The
deployment's filesystem is ephemeral, which is the right lifetime for
this: a visitor's reports survive their reloads and do not outlive the
container.

Each visitor gets a subdirectory of their own, named by a scope the
caller supplies. Without one, the store was a single directory shared
by every visitor to the deployment, and a reviewer who generated a
report on a name they were considering put that name at the top of
the index for everyone else holding the link. On a tool shown to
portfolio managers the ticker someone chose to research is itself the
sensitive thing, so the default had it exactly backwards.

The scope is joined to a path, so it is validated the same way a slug
is, and for the same reason.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# A slug arrives in a query string, so it is a hostile string until it
# matches this. Lowercase letters, digits and hyphens only: no dot, so
# `..` cannot be spelled; no separator, so no path can be. Checked
# before the name is joined to a directory rather than after, because
# `Path(dir) / "../x"` resolves outside `dir` at join time and a check
# written downstream of that is checking the wrong thing.
_SLUG = re.compile(r"\A[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_MAX_SLUG = 64


@dataclass(frozen=True)
class Saved:
    """One rendered report, as it is listed and as it is read back."""

    slug: str
    title: str
    html: str
    built: datetime


def directory(scope: str = "") -> Path:
    """Where one visitor's reports are kept.

    Overridable by REPORTS_DIR, so tests never touch a real one. An
    empty scope is the shared root, which is right for a local run by
    one person and wrong for a deployment; the app always passes one.
    """
    root = Path(os.environ.get("REPORTS_DIR") or ".reports")
    return root / scope if scope else root


def _valid(slug: str) -> bool:
    return bool(slug) and len(slug) <= _MAX_SLUG and bool(_SLUG.match(slug))


def _slugify(ticker: str, when: datetime) -> str:
    stem = re.sub(r"[^a-z0-9]+", "-", ticker.lower()).strip("-") or "report"
    return f"{stem}-{when.strftime('%Y%m%d-%H%M%S-%f')}"


def save(ticker: str, title: str, html: str, scope: str = "") -> Saved:
    """Write a rendered report down, and return how to find it again.

    The timestamp carries microseconds because two reports on one
    ticker in one second is not a hypothetical: it is what happens when
    a reader presses the button twice, and a collision would have the
    second silently overwrite the first.
    """
    if scope and not _valid(scope):
        raise ValueError("a report scope must be a slug")
    when = datetime.now(timezone.utc)
    entry = Saved(_slugify(ticker, when), title, html, when)
    home = directory(scope)
    home.mkdir(parents=True, exist_ok=True)
    (home / f"{entry.slug}.json").write_text(
        json.dumps(
            {
                "title": entry.title,
                "html": entry.html,
                "built": entry.built.isoformat(),
            }
        ),
        encoding="utf-8",
    )
    return entry


def _read(path: Path, slug: str) -> Saved | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    try:
        built = datetime.fromisoformat(raw["built"])
    except (KeyError, TypeError, ValueError):
        return None
    if not isinstance(raw.get("html"), str):
        return None
    return Saved(slug, str(raw.get("title") or slug), raw["html"], built)


def load(slug: str, scope: str = "") -> Saved | None:
    """One saved report, or None for anything that is not one.

    Both the slug and the scope arrive from a query string, so both
    are checked before either is joined to a path.
    """
    if not _valid(slug) or (scope and not _valid(scope)):
        return None
    return _read(directory(scope) / f"{slug}.json", slug)


def listing(scope: str = "") -> list[Saved]:
    """Every saved report, newest first.

    Ordered by the recorded build time rather than by filename or by
    mtime: the filename happens to sort the same way today and would
    stop doing so the moment the stem changes, and mtime is a property
    of the file rather than of the report.
    """
    if scope and not _valid(scope):
        return []
    home = directory(scope)
    try:
        files = sorted(home.glob("*.json"))
    except OSError:
        return []
    found = []
    for path in files:
        if not _valid(path.stem):
            continue
        entry = _read(path, path.stem)
        if entry is not None:
            found.append(entry)
    return sorted(found, key=lambda s: s.built, reverse=True)
