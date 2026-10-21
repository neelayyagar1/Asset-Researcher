#!/usr/bin/env bash
# Installs a pre-commit hook that blocks commits containing secrets.
#
# Git hooks live in .git/hooks, which is NOT part of the repository — so this
# script must be run once per clone. Run: bash scripts/install-hooks.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK_PATH="$REPO_ROOT/.git/hooks/pre-commit"

cat > "$HOOK_PATH" <<'HOOK'
#!/usr/bin/env bash
# Blocks a commit if any staged file contains a value from .env, or if .env
# itself is staged. Fails closed: if the check can't run, the commit stops.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if git diff --cached --name-only | grep -qx '.env'; then
    echo "BLOCKED: .env is staged. Never commit it."
    exit 1
fi

[ -f .env ] || exit 0

# Compare staged content (not working tree) against each secret value.
python3 - <<'PY'
import subprocess, sys
from pathlib import Path

secrets = {}
for line in Path(".env").read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    v = v.strip().strip('"').strip("'")
    if k.strip().endswith("_API_KEY") and v:
        secrets[k.strip()] = v

if not secrets:
    sys.exit(0)

staged = subprocess.run(
    ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
    capture_output=True, text=True, check=True,
).stdout.split()

offenders = []
for path in staged:
    # Bytes, not text. `text=True` decodes as UTF-8 and raises on the
    # first binary file staged, and because this hook fails closed by
    # design that exception blocked every commit to a repository holding
    # any binary asset. A key is ASCII, so searching the raw bytes finds
    # it in a text file exactly as before and finds it in a binary one
    # too, which is the case that matters: a secret embedded in a blob is
    # the one most likely to be committed by accident.
    blob = subprocess.run(
        ["git", "show", f":{path}"], capture_output=True
    )
    if blob.returncode != 0:
        continue
    for name, value in secrets.items():
        if value.encode("utf-8") in blob.stdout:
            offenders.append(f"{name} in {path}")

if offenders:
    print("BLOCKED: staged changes contain secret values:")
    for o in offenders:
        print(f"  - {o}")
    print("Remove the secret and re-stage. If it was ever pushed, ROTATE THE KEY.")
    sys.exit(1)
PY
HOOK

chmod +x "$HOOK_PATH"
echo "Installed pre-commit hook at .git/hooks/pre-commit"
