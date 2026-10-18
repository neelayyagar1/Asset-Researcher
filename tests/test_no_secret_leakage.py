"""Automated guard against secret leakage.

A one-time manual check protects nothing, this runs on every test invocation
so a key can never silently reach a tracked file, the git history, or a cache
artifact. If any test here fails, do not commit: rotate the exposed key first,
because git history is public the moment the repo is pushed.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
ENV_PATH = REPO_ROOT / ".env"

_SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules"}


def _load_env_secrets() -> dict[str, str]:
    """Reads real key values from .env. Never printed, only used as needles."""
    if not ENV_PATH.exists():
        return {}
    secrets = {}
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        # Only treat actual credentials as secrets. EDGAR_USER_AGENT is a
        # contact string that is *required* to be sent publicly to the SEC.
        if key.strip().endswith("_API_KEY") and value:
            secrets[key.strip()] = value
    return secrets


SECRETS = _load_env_secrets()
requires_secrets = pytest.mark.skipif(not SECRETS, reason="no populated .env to check")


def _repo_files() -> list[Path]:
    files = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if _SKIP_DIRS & set(path.parts):
            continue
        if path.name == ".env":
            continue  # the one place secrets are allowed to live
        files.append(path)
    return files


def test_env_is_ignored_by_git():
    result = subprocess.run(
        ["git", "check-ignore", ".env"], cwd=REPO_ROOT, capture_output=True, text=True
    )
    assert result.returncode == 0, ".env is NOT gitignored, a commit would expose it"


def test_env_is_not_tracked_by_git():
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", ".env"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, ".env is TRACKED by git, it would be pushed"


def test_cache_directories_are_ignored():
    """Finnhub authenticates via a `token` query parameter, so a cached
    response or a cached-by-URL key could embed the credential. The cache
    directory must never be committable."""
    result = subprocess.run(
        ["git", "check-ignore", "data/cache/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, "data/cache/ is not gitignored"


@requires_secrets
def test_no_secret_value_appears_in_any_repo_file():
    offenders = []
    for path in _repo_files():
        try:
            content = path.read_text(errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        for name, value in SECRETS.items():
            if value in content:
                offenders.append(f"{name} in {path.relative_to(REPO_ROOT)}")
    assert not offenders, f"Secret(s) found in repo files: {offenders}"


@requires_secrets
def test_no_secret_value_appears_in_git_history():
    """Checks every commit and blob, not just the working tree. A secret
    committed and then deleted still lives in history and is still exposed."""
    offenders = []
    for name, value in SECRETS.items():
        result = subprocess.run(
            ["git", "log", "-S", value, "--oneline", "--all"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            offenders.append(f"{name} in commits: {result.stdout.strip()}")
    assert not offenders, f"Secret(s) in git history. ROTATE THEM: {offenders}"


@requires_secrets
def test_no_secret_would_be_staged_by_git_add_all():
    """Belt-and-braces: simulates `git add -A` and inspects the result."""
    result = subprocess.run(
        ["git", "add", "-A", "--dry-run"], cwd=REPO_ROOT, capture_output=True, text=True
    )
    staged_paths = [
        line.split("'")[1] for line in result.stdout.splitlines() if "'" in line
    ]
    offenders = []
    for rel in staged_paths:
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        try:
            content = path.read_text(errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        for name, value in SECRETS.items():
            if value in content:
                offenders.append(f"{name} in {rel}")
    assert not offenders, f"`git add -A` would stage secrets: {offenders}"


def test_env_example_contains_no_real_values():
    """The committed template must have empty placeholders only."""
    example = REPO_ROOT / ".env.example"
    assert example.exists()
    for line in example.read_text().splitlines():
        if line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip().endswith("_API_KEY"):
            assert not value.strip(), f"{key.strip()} has a value in .env.example"
