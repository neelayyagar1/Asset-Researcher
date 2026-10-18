"""Persists the exact text sent to the model.

**Why this module exists.** The citations API returns character offsets, and
those offsets are meaningful only against the byte-identical string that was
sent. If the text is re-derived later from HTML, with a newer lxml, a tweaked
normalization rule, even a different whitespace decision, every stored offset
silently shifts. Citations would then point at the wrong text while still
looking perfectly valid: no exception, no failed check, just quotes that no
longer say what the report claims they say.

So extraction happens once, the result is written to disk verbatim, and every
later stage (verification, the UI's click-through-to-source) reads *this*
stored copy rather than re-extracting. Design plan §6 calls this out as the
critical implementation detail of the whole grounding approach.

Each document also stores the SHA-256 of its text. `load()` re-checks it on
read, so on-disk corruption surfaces as a loud error instead of quietly
misaligned citations.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path


class DocumentIntegrityError(RuntimeError):
    """Stored text no longer matches its recorded hash. Refuse to serve it.
    resolving citations against altered text is worse than failing."""


@dataclass(frozen=True)
class StoredDocument:
    """Text plus the provenance needed to cite it and to render a source link."""

    doc_id: str  # stable, unique: "{cik}/{accession}/{form}"
    cik: int
    form: str  # "10-K", "8-K", "DEF 14A", ...
    filing_date: str
    accession_number: str
    source_url: str
    title: str
    text: str
    sha256: str

    @property
    def char_count(self) -> int:
        return len(self.text)

    def slice(self, start: int, end: int) -> str:
        """Resolve a citation span. Bounds are clamped rather than raising:
        a citation that runs one character past the end should render, not
        take down the report. The verifier is what judges correctness."""
        if start < 0 or start >= len(self.text) or end <= start:
            return ""
        return self.text[start : min(end, len(self.text))]


def compute_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_doc_id(cik: int, accession_number: str, form: str) -> str:
    # Forms contain spaces and slashes ("DEF 14A", "10-K/A"); normalize so the
    # id is filesystem-safe.
    safe_form = form.replace(" ", "-").replace("/", "-")
    return f"{cik:010d}/{accession_number}/{safe_form}"


@dataclass
class DocumentStore:
    root: Path

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _paths(self, doc_id: str) -> tuple[Path, Path]:
        base = self.root / doc_id
        return base.with_suffix(".txt"), base.with_suffix(".json")

    def exists(self, doc_id: str) -> bool:
        text_path, meta_path = self._paths(doc_id)
        return text_path.exists() and meta_path.exists()

    def put(self, doc: StoredDocument) -> StoredDocument:
        text_path, meta_path = self._paths(doc.doc_id)
        text_path.parent.mkdir(parents=True, exist_ok=True)

        # Text is written as raw UTF-8 rather than inside the JSON so that the
        # bytes the model saw are exactly the bytes on disk, no escaping layer
        # sitting between them that could alter offsets.
        text_path.write_text(doc.text, encoding="utf-8")

        meta = {k: v for k, v in asdict(doc).items() if k != "text"}
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return doc

    def load(self, doc_id: str) -> StoredDocument | None:
        text_path, meta_path = self._paths(doc_id)
        if not (text_path.exists() and meta_path.exists()):
            return None

        text = text_path.read_text(encoding="utf-8")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

        actual = compute_sha256(text)
        if actual != meta["sha256"]:
            raise DocumentIntegrityError(
                f"Stored text for {doc_id} does not match its recorded hash "
                f"(expected {meta['sha256'][:12]}..., got {actual[:12]}...). "
                f"Citation offsets recorded against the original text would "
                f"resolve to the wrong passages. Delete the cached document "
                f"and re-fetch the filing."
            )

        return StoredDocument(text=text, **meta)
