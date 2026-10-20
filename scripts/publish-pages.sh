#!/usr/bin/env bash
# Publish build/site to the gh-pages branch.
#
# GitHub Pages is the cheapest host for the sample notes: the repository
# already exists, there is no second account, no build minutes are spent
# and the pages are static files. Generation happens locally and
# deliberately, because every note costs an API call and nothing should
# spend money on a git push.
#
#   python scripts/publish-sample.py --ticker AAPL --ticker JPM
#   bash scripts/publish-pages.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE="$ROOT/build/site"

[ -d "$SITE" ] || {
    echo "No $SITE. Run scripts/publish-sample.py first." >&2
    exit 1
}
[ -f "$SITE/index.html" ] || {
    echo "$SITE has no index.html; the sample build did not finish." >&2
    exit 1
}

cd "$ROOT"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
REMOTE="$(git remote get-url origin)"

# A worktree rather than a branch switch, so an interrupted publish cannot
# leave the working copy on gh-pages with the site's files staged over the
# source.
TMP="$(mktemp -d)"
trap 'git worktree remove --force "$TMP" 2>/dev/null || true; rm -rf "$TMP"' EXIT

if git show-ref --quiet refs/heads/gh-pages; then
    git worktree add "$TMP" gh-pages >/dev/null
else
    git worktree add --detach "$TMP" >/dev/null
    git -C "$TMP" checkout --orphan gh-pages >/dev/null
    git -C "$TMP" rm -rf . >/dev/null 2>&1 || true
fi

find "$TMP" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -R "$SITE"/. "$TMP"/
# Pages runs Jekyll by default, which ignores files beginning with an
# underscore and rewrites some paths. These are plain files.
touch "$TMP/.nojekyll"

git -C "$TMP" add -A
if git -C "$TMP" diff --cached --quiet; then
    echo "No change to publish."
    exit 0
fi
git -C "$TMP" commit -q -m "Publish sample notes $(date -u +%Y-%m-%d)"
git -C "$TMP" push -q origin gh-pages

SLUG="$(echo "$REMOTE" | sed -E 's#.*[:/]([^/]+)/([^/.]+)(\.git)?$#\1.github.io/\2#')"
echo "Published. Enable Pages once at:"
echo "  ${REMOTE%.git}/settings/pages  ->  branch gh-pages, folder /"
echo "Then the notes are at:  https://${SLUG}/"
echo "(you are still on $BRANCH)"
