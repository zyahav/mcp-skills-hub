#!/bin/bash
set -e

# Check for BW_SESSION
if [ -z "$BW_SESSION" ]; then
    echo "Error: BW_SESSION is not set. Please unlock Bitwarden first."
    exit 1
fi

echo "Retrieving secrets from Bitwarden..."

# Retrieve secrets
# Retrieve secrets
# The item "Cloudflare DNS Manager" has custom fields, not standard password/notes
ITEM_JSON=$(bw get item "Cloudflare DNS Manager")
export CLOUDFLARE_API_TOKEN=$(echo "$ITEM_JSON" | jq -r '.fields[] | select(.name=="CLOUDFLARE_API_TOKEN") | .value')
export CLOUDFLARE_ZONE_ID=$(echo "$ITEM_JSON" | jq -r '.fields[] | select(.name=="CLOUDFLARE_ZONE_ID") | .value')

if [ -z "$CLOUDFLARE_API_TOKEN" ] || [ -z "$CLOUDFLARE_ZONE_ID" ]; then
    echo "Error: Failed to retrieve secrets from Bitwarden."
    exit 1
fi

# Launch the MCP server
echo "Starting Cloudflare DNS MCP Server..."
exec node "$(dirname "$0")/build/index.js"
