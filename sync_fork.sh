#!/usr/bin/env bash

# Sync fork with upstream while preserving local changes
# Usage: ./sync_fork.sh [branch]
# If no branch specified, defaults to current branch (usually main)

set -euo pipefail

BRANCH="${1:-$(git rev-parse --abbrev-ref HEAD)}"

# Ensure we are on the target branch
git checkout "$BRANCH"

# Fetch latest from upstream
git fetch upstream

# Rebase local commits onto upstream's branch
git rebase "upstream/$BRANCH"

# Push rebased history to origin (force‑with‑lease)
# Adjust if you prefer merge instead of rebase
git push origin "$BRANCH" --force-with-lease

echo "✅ Sync complete for $BRANCH"
