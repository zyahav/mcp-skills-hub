#!/bin/bash
# delete-feature.sh - Delete a feature branch and worktree
# Usage: ./scripts/delete-feature.sh <feature-name>

set -e


# Get directory of this script (scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_WORKTREE="$SCRIPT_DIR/.."

cd "$CURRENT_WORKTREE"

if [ -z "$1" ]; then
    echo "Usage: $0 <feature-name>"
    exit 1
fi

FEATURE_NAME="$1"
BRANCH_NAME="feature/$FEATURE_NAME"
WORKTREE_DIR="$CURRENT_WORKTREE/feature-$FEATURE_NAME"

echo "🗑️  Deleting feature: $FEATURE_NAME"

# Remove worktree if exists
if [ -d "$WORKTREE_DIR" ]; then
    echo "removing worktree $WORKTREE_DIR..."
    git worktree remove "$WORKTREE_DIR" --force || rm -rf "$WORKTREE_DIR"
else
    echo "Worktree directory not found (skipping)"
fi

# Delete branch
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
    echo "Deleting branch $BRANCH_NAME..."
    git branch -D "$BRANCH_NAME"
else
    echo "Branch $BRANCH_NAME not found (skipping)"
fi

echo "✅ Feature deleted."
