#!/bin/bash
# list-features.sh - Show all active worktrees and branches
# Usage: ./scripts/list-features.sh


# Get directory of this script (scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_WORKTREE="$SCRIPT_DIR/.."
MONOREPO_ROOT="$(cd "$CURRENT_WORKTREE/.." && pwd)"

cd "$MONOREPO_ROOT"

echo "=== WORKTREES ==="
git worktree list
echo ""

echo "=== BRANCHES ==="
git branch -a
echo ""

echo "=== FOLDER STRUCTURE ==="
ls -d */ 2>/dev/null | grep -E "(mcp-skills-hub|feature-)" || echo "No worktrees found"
