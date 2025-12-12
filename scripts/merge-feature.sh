#!/bin/bash
# merge-feature.sh - Merge feature -> dev, or release (dev -> main)
# Usage: 
#   ./scripts/merge-feature.sh <feature-name>   (Merges feature/<name> into dev)
#   ./scripts/merge-feature.sh release          (Merges dev into main)

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

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
    
    # Ensure on main
    git checkout main
    git pull origin main
    
    # Merge dev
    git merge dev
    
    echo "✅ Merged dev into main."
    echo "Pushing to remote..."
    git push origin main
    
    # Switch back to dev
    git checkout dev
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

    # Checkout dev
    git checkout dev
    git pull origin dev

    # Merge feature
    git merge "$FEATURE_BRANCH"

    echo "✅ Merged $FEATURE_BRANCH into dev."
    echo "Pushing to remote..."
    git push origin dev
    
    echo "✅ Merge complete!"
fi
