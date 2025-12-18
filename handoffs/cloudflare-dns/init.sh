#!/bin/bash
# init.sh - Bootstrap script for Cloudflare DNS Manager MCP development
# Run this at the start of each session to restore environment state

set -e

MONOREPO_ROOT="/Users/zyahav/Documents/dev/mcp-skills-hub-monorepo/mcp-skills-hub-dev"
SKILL_DIR="$MONOREPO_ROOT/mcps/cloudflare-dns"
HANDOFF_DIR="$MONOREPO_ROOT/handoffs/cloudflare-dns"

echo "=== Cloudflare DNS Manager MCP - Session Init ==="
echo ""

# 1. Navigate to project
cd "$MONOREPO_ROOT"
echo "[1/5] Working directory: $(pwd)"

# 2. Show git status
echo ""
echo "[2/5] Git status:"
git status --short

# 3. Show recent commits
echo ""
echo "[3/5] Recent commits:"
git log --oneline -5

# 4. Check if dependencies installed
echo ""
echo "[4/5] Dependencies:"
if [ -d "$SKILL_DIR/node_modules" ]; then
    echo "  ✓ node_modules exists"
else
    echo "  ✗ node_modules missing - run: cd mcps/cloudflare-dns && npm install"
fi

# 5. Show next milestone from feature_list.json
echo ""
echo "[5/5] Next incomplete milestone:"
if command -v jq &> /dev/null; then
    jq -r '.[] | select(.passes == false) | "  → Milestone \(.milestone): \(.description)"' "$HANDOFF_DIR/feature_list.json" | head -1
else
    echo "  (install jq for auto-detection, or read feature_list.json)"
fi

echo ""
echo "=== Ready. Read claude-progress.txt for full context. ==="
