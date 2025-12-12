#!/bin/bash
# sync-env.sh - Copy master .env to all feature worktrees
# Usage: ./scripts/sync-env.sh

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [ ! -f ".env" ]; then
    echo "❌ No .env file found in root!"
    exit 1
fi

echo "🔄 Syncing .env to worktrees..."

# Find all directories starting with feature-
found=0
for dir in feature-*/; do
    if [ -d "$dir" ]; then
        cp ".env" "${dir}.env"
        echo "✅ Updated ${dir}.env"
        found=1
    fi
done

if [ "$found" -eq 0 ]; then
    echo "No feature worktrees found."
fi

echo "Done."
