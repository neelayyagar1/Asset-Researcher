"""Pre-built notes, carried in the repository without being readable.

The problem this solves is specific. The source belongs in a public
repository, because the code and its history are the thing worth showing.
The sample notes do not: they are the product's output, and a demo shared
with named reviewers should not be a page anyone can find. Committing
them plainly to a public repository publishes them, and keeping them out
of it means the deployed app has nothing to show without spending an API
call per visitor.

So they travel encrypted, under their own key. A reader of the public
repository sees a blob; the deployment holds the key and opens it.

**The key is deliberately not the gate passphrase.** It was, and that was
wrong. The blob is committed to a public repository, so it is
permanently downloadable by anyone, including from history after a
rotation. If it were sealed with the passphrase that guards the API key,
publishing it would hand an attacker an offline oracle for that
passphrase: unlimited guessing rate, no logs, no detection, against a
string a human picked to put in an email. Separating them means cracking
the blob yields these notes - public SEC filings - and nothing else.

SAMPLES_KEY is therefore machine-generated and long, not memorable, and
never typed by a reviewer. Nobody has to know it but the deployment.

What this is and is not:

**It is** a way to avoid publishing the output to the whole internet, and
it is honest about resting entirely on one shared passphrase. Anyone
holding that passphrase can decrypt the blob forever, including from an
old checkout after the passphrase is rotated, because the ciphertext is
in the git history. Rotating means re-packing and accepting that the old
blob remains readable to whoever already had the old phrase.

**It is not** protection for anything confidential. Every figure in these
notes comes from public SEC filings. If the content were sensitive it
would not belong in a public repository in any form, encrypted or not.

Scrypt for the derivation and Fernet for the sealing, so the payload is
authenticated and a tampered blob fails to decrypt rather than rendering
as markup inside a reviewer's browser. The scrypt parameters below are
the library's interactive-login defaults, which are calibrated for a
setting where guessing is rate-limited online - the opposite of a
ciphertext published forever. They are adequate here only because the key
is high-entropy; they would not be adequate for a human-chosen phrase,
and that is the second reason the two secrets are separate.

One more thing this does not hide: the blob is unpadded, so its size
reveals roughly how much HTML is inside. Immaterial for public filings.
"""

from __future__ import annotations

import base64
import io
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

# Interactive-login parameters. n=2**14 costs a fraction of a second once,
# which is unnoticeable behind a passphrase prompt, and makes a dictionary
# attack on the blob enormously more expensive than a plain hash would.
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_BYTES = 16

SAMPLES_PATH = Path(__file__).resolve().parents[1] / "samples" / "notes.enc"


@dataclass(frozen=True)
class Sample:
    """One pre-built note, ready to render."""

    slug: str
    title: str
    html: str


def _key(passphrase: str, salt: bytes) -> bytes:
    kdf = Scrypt(salt=salt, length=32, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))


def new_key() -> str:
    """A fresh sealing key, long enough that the KDF cost is irrelevant."""
    import secrets

    return secrets.token_urlsafe(32)


def pack(notes: dict[str, str], titles: dict[str, str], passphrase: str) -> bytes:
    """Seal a set of notes into one blob.

    Zipped before sealing, because these are HTML documents sharing a
    stylesheet and compress to a fraction of their size; the repository
    carries the blob forever and git stores no delta for ciphertext.
    """
    if not passphrase:
        raise ValueError("refusing to pack samples under an empty passphrase")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr("titles.json", json.dumps(titles, indent=1, sort_keys=True))
        for slug, html in sorted(notes.items()):
            archive.writestr(f"{slug}.html", html)

    salt = __import__("os").urandom(_SALT_BYTES)
    sealed = Fernet(_key(passphrase, salt)).encrypt(buffer.getvalue())
    # The salt travels in front of the token. It is not a secret; it
    # exists so the same passphrase does not produce the same key twice.
    return salt + sealed


def unpack(blob: bytes, passphrase: str) -> list[Sample]:
    """Open a blob, or raise ValueError.

    Raises rather than returning empty, so a wrong passphrase and a
    genuinely empty sample set cannot be confused by the caller.
    """
    if len(blob) <= _SALT_BYTES:
        raise ValueError("sample archive is truncated")

    salt, sealed = blob[:_SALT_BYTES], blob[_SALT_BYTES:]
    try:
        raw = Fernet(_key(passphrase, salt)).decrypt(sealed)
    except InvalidToken as exc:
        raise ValueError("passphrase does not open the sample archive") from exc

    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        titles = json.loads(archive.read("titles.json"))
        return [
            Sample(
                slug=name[: -len(".html")],
                title=titles.get(name[: -len(".html")], name),
                html=archive.read(name).decode("utf-8"),
            )
            for name in sorted(archive.namelist())
            if name.endswith(".html")
        ]


def load(passphrase: str, path: Path | None = None) -> list[Sample]:
    """The packed notes, or an empty list where none were shipped.

    A deployment without a sample archive is a normal state, not a
    failure: the live tool works without one. A wrong passphrase is a
    different matter and still raises.
    """
    target = path or SAMPLES_PATH
    if not target.exists():
        return []
    return unpack(target.read_bytes(), passphrase)
