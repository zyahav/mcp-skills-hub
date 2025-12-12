#!/bin/bash
# list-features.sh - Show all active worktrees and branches
# Usage: ./scripts/list-features.sh


# Get directory of this script (scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_WORKTREE="$SCRIPT_DIR/.."

cd "$CURRENT_WORKTREE"

echo "=== WORKTREES ==="
git worktree list
echo ""

echo "=== BRANCHES ==="
git branch -a
echo ""

echo "=== FOLDER STRUCTURE ==="
ls -d feature-*/ 2>/dev/null || echo "No nested feature worktrees found"
