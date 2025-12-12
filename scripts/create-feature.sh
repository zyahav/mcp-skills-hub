#!/bin/bash
# create-feature.sh - Create a new feature branch with worktree
# Usage: ./scripts/create-feature.sh <feature-name>
# Example: ./scripts/create-feature.sh media-hub-refactor

set -e


# Get directory of this script (scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# The current worktree root (mcp-skills-hub-dev)
CURRENT_WORKTREE="$SCRIPT_DIR/.."

# We create worktrees inside the current worktree (nested)
TARGET_ROOT="$CURRENT_WORKTREE"

cd "$TARGET_ROOT"

if [ -z "$1" ]; then
    echo "Usage: $0 <feature-name>"
    echo "Example: $0 media-hub-refactor"
    exit 1
fi

FEATURE_NAME="$1"
BRANCH_NAME="feature/$FEATURE_NAME"
WORKTREE_DIR="$TARGET_ROOT/feature-$FEATURE_NAME"

# Check if already exists
if [ -d "$WORKTREE_DIR" ]; then
    echo "❌ Worktree already exists: $WORKTREE_DIR"
    exit 1
fi

# Create branch from dev and worktree
echo "📦 Creating feature branch: $BRANCH_NAME"
# We run git worktree add from the current worktree (or root), git handles the linking.
# We specify the full path for the new worktree.
git worktree add "$WORKTREE_DIR" -b "$BRANCH_NAME" dev

# Copy .env from CURRENT_WORKTREE (dev environment) if exists
if [ -f "$CURRENT_WORKTREE/.env" ]; then
    cp "$CURRENT_WORKTREE/.env" "$WORKTREE_DIR/.env"
    echo "✅ Copied .env from dev to worktree"
fi

echo ""
echo "✅ Feature created!"
echo "   Branch: $BRANCH_NAME"
echo "   Folder: $WORKTREE_DIR"
echo ""
echo "To start working:"
echo "   cd $WORKTREE_DIR"
