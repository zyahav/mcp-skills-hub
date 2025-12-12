#!/bin/bash
# merge-feature.sh - Merge feature -> dev, or release (dev -> main)
# Usage: 
#   ./scripts/merge-feature.sh <feature-name>   (Merges feature/<name> into dev)
#   ./scripts/merge-feature.sh release          (Merges dev into main)

set -e


# Get directory of this script (scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_WORKTREE="$SCRIPT_DIR/.."
# In a worktree setup, we assume we are running this from the DEV worktree.
cd "$CURRENT_WORKTREE"

if [ -z "$1" ]; then
    echo "Usage:"
    echo "  $0 <feature-name>   (Merges feature/<name> into dev)"
    echo "  $0 release          (Merges dev into main)"
    exit 1
fi

NAME="$1"

if [ "$NAME" == "release" ]; then
    # Merge dev -> main
    echo "🚀 Preparing release: dev -> main"
    
    # Check where 'main' branch is checked out
    # git worktree list format: /path/to/tree  git-ref  [branch]
    MAIN_WT_PATH=$(git worktree list | grep "\[main\]" | awk '{print $1}')
    
    if [ -z "$MAIN_WT_PATH" ]; then
        # Main might be the current dir (unlikely if we are in dev worktree) or just not checked out? 
        # Fallback to simple checkout if not found as worktree
        echo "⚠️  Could not locate worktree for 'main'. Attempting local checkout..."
        git checkout main
    else
        echo "📂 Switching to main worktree at: $MAIN_WT_PATH"
        cd "$MAIN_WT_PATH"
    fi

    # Ensure on main
    git checkout main
    git pull origin main
    
    # Merge dev
    git merge dev
    
    echo "✅ Merged dev into main."
    echo "Pushing to remote..."
    git push origin main
    
    echo "✅ Release complete!"
    
else
    # Merge feature -> dev
    FEATURE_BRANCH="feature/$NAME"
    
    # Check if branch exists
    if ! git show-ref --verify --quiet "refs/heads/$FEATURE_BRANCH"; then
        echo "❌ Branch '$FEATURE_BRANCH' does not exist."
        exit 1
    fi

    echo "🔀 Merging $FEATURE_BRANCH -> dev"

    # Ensure we are on dev branch in current worktree
    # If this worktree is locked to dev, checkout dev is fine.
    git checkout dev
    git pull origin dev

    # Merge feature
    git merge "$FEATURE_BRANCH"

    echo "✅ Merged $FEATURE_BRANCH into dev."
    echo "Pushing to remote..."
    git push origin dev
    
    echo "✅ Merge complete!"
fi
