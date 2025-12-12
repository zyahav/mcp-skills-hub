#!/bin/bash
# list-features.sh - Show all active worktrees and branches
# Usage: ./scripts/list-features.sh

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== WORKTREES ==="
git worktree list
echo ""

echo "=== BRANCHES ==="
git branch -a
echo ""

echo "=== FOLDER STRUCTURE ==="
ls -d */ 2>/dev/null | grep -E "(mcp-skills-hub|feature-)" || echo "No worktrees found"
