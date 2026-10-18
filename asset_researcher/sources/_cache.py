"""Shared disk cache for HTTP responses.

Used by every external client (EDGAR, Finnhub) so repeated runs against the same
ticker don't re-fetch, and so a rate-limited API doesn't get hammered during
development. Not a `Source` itself, a plumbing detail sources use.

Cache key is caller-supplied (not derived from the URL) so callers control
invalidation granularity explicitly rather than by accident.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DiskCache:
    directory: Path

    def __post_init__(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)

    def _paths(self, key: str) -> tuple[Path, Path]:
        # Cache keys are constructed by callers (e.g. "cik-320193"), not raw
        # URLs, so a simple filesystem-safe substitution is sufficient here.
        safe = key.replace("/", "_").replace(":", "_")
        return self.directory / f"{safe}.body", self.directory / f"{safe}.meta.json"

    def get(self, key: str, ttl_seconds: float | None) -> bytes | None:
        """Returns cached bytes if present and (ttl_seconds is None, meaning
        cache forever, or the entry is still within ttl_seconds). None on miss."""
        body_path, meta_path = self._paths(key)
        if not body_path.exists() or not meta_path.exists():
            return None
        meta = json.loads(meta_path.read_text())
        if ttl_seconds is not None and (time.time() - meta["fetched_at"]) > ttl_seconds:
            return None
        return body_path.read_bytes()

    def put(self, key: str, data: bytes) -> None:
        body_path, meta_path = self._paths(key)
        body_path.write_bytes(data)
        meta_path.write_text(json.dumps({"fetched_at": time.time()}))
