#!/bin/bash
# create-feature.sh - Create a new feature branch with worktree
# Usage: ./scripts/create-feature.sh <feature-name>
# Example: ./scripts/create-feature.sh media-hub-refactor

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [ -z "$1" ]; then
    echo "Usage: $0 <feature-name>"
    echo "Example: $0 media-hub-refactor"
    exit 1
fi

FEATURE_NAME="$1"
BRANCH_NAME="feature/$FEATURE_NAME"
WORKTREE_DIR="$REPO_ROOT/feature-$FEATURE_NAME"

# Check if already exists
if [ -d "$WORKTREE_DIR" ]; then
    echo "❌ Worktree already exists: $WORKTREE_DIR"
    exit 1
fi

# Create branch from dev and worktree
echo "📦 Creating feature branch: $BRANCH_NAME"
git worktree add "$WORKTREE_DIR" -b "$BRANCH_NAME" dev

# Copy .env if exists
if [ -f "$REPO_ROOT/.env" ]; then
    cp "$REPO_ROOT/.env" "$WORKTREE_DIR/.env"
    echo "✅ Copied .env to worktree"
fi

echo ""
echo "✅ Feature created!"
echo "   Branch: $BRANCH_NAME"
echo "   Folder: $WORKTREE_DIR"
echo ""
echo "To start working:"
echo "   cd $WORKTREE_DIR"
