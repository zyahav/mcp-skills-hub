#!/bin/bash
# Live integration test for Bitwarden MCP
# 
# Prerequisites:
#   1. export BW_SESSION=$(bw unlock --raw)
#   2. Create test item in Bitwarden:
#      - Name: "MCP Test Item"
#      - Custom field: DUMMY_SECRET = "test-secret-value"
#      - Custom field: PUBLIC_NOTES = "true"
#      - Notes: "These are test notes"

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MCP_DIR="$SCRIPT_DIR"

echo "=== Bitwarden MCP Integration Test ==="
echo

# Check BW_SESSION
if [ -z "$BW_SESSION" ]; then
    echo "❌ BW_SESSION is not set"
    echo "   Run: export BW_SESSION=\$(bw unlock --raw)"
    exit 1
fi
echo "✓ BW_SESSION is set"

# Check vault status
STATUS=$(bw status | jq -r '.status')
if [ "$STATUS" != "unlocked" ]; then
    echo "❌ Vault is not unlocked (status: $STATUS)"
    exit 1
fi
echo "✓ Vault is unlocked"

# Test CLI: get-secret
echo
echo "Testing CLI: bitwarden-mcp get-secret..."
SECRET=$(node "$MCP_DIR/build/cli.js" get-secret "MCP Test Item" "DUMMY_SECRET" 2>&1) || {
    echo "❌ CLI get-secret failed: $SECRET"
    exit 1
}
echo "✓ CLI get-secret returned: $SECRET"

# Test CLI: get-notes
echo
echo "Testing CLI: bitwarden-mcp get-notes..."
NOTES=$(node "$MCP_DIR/build/cli.js" get-notes "MCP Test Item" 2>&1) || {
    echo "❌ CLI get-notes failed: $NOTES"
    exit 1
}
echo "✓ CLI get-notes returned: $NOTES"

echo
echo "=== All tests passed! ==="
