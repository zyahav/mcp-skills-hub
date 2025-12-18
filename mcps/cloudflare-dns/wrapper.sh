#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BITWARDEN_CLI="$SCRIPT_DIR/../bitwarden/build/cli.js"

# Check for BW_SESSION
if [ -z "$BW_SESSION" ]; then
    echo "Error: BW_SESSION is not set. Please unlock Bitwarden first." >&2
    exit 1
fi

echo "Retrieving secrets from Bitwarden..." >&2

# Retrieve secrets using bitwarden-mcp CLI (centralized, safe, no jq)
export CLOUDFLARE_API_TOKEN=$(node "$BITWARDEN_CLI" get-secret "Cloudflare DNS Manager" "CLOUDFLARE_API_TOKEN")
export CLOUDFLARE_ZONE_ID=$(node "$BITWARDEN_CLI" get-secret "Cloudflare DNS Manager" "CLOUDFLARE_ZONE_ID")
export CLOUDFLARE_ZONE_NAME=$(node "$BITWARDEN_CLI" get-secret "Cloudflare DNS Manager" "CLOUDFLARE_ZONE_NAME" || true)

if [ -z "$CLOUDFLARE_API_TOKEN" ] || [ -z "$CLOUDFLARE_ZONE_ID" ]; then
    echo "Error: Failed to retrieve secrets from Bitwarden." >&2
    exit 1
fi

# Launch the MCP server
echo "Starting Cloudflare DNS MCP Server..." >&2
exec node "$SCRIPT_DIR/build/index.js"
