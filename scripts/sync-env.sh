#!/bin/bash
# sync-env.sh - Copy master .env to all feature worktrees
# Usage: ./scripts/sync-env.sh

set -e


# Get directory of this script (scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_WORKTREE="$SCRIPT_DIR/.."

# We are copy FROM the current worktree's .env (dev environment)
if [ ! -f "$CURRENT_WORKTREE/.env" ]; then
    echo "❌ No .env file found in $CURRENT_WORKTREE!"
    exit 1
fi

cd "$CURRENT_WORKTREE"

echo "🔄 Syncing .env from dev to nested worktrees..."

# Find all directories starting with feature-
found=0
for dir in feature-*/; do
    if [ -d "$dir" ]; then
        cp "$CURRENT_WORKTREE/.env" "${dir}.env"
        echo "✅ Updated ${dir}.env"
        found=1
    fi
done

if [ "$found" -eq 0 ]; then
    echo "No feature worktrees found."
fi

echo "Done."
