#!/bin/bash
set -e

# Bitwarden MCP requires BW_SESSION to be set
if [ -z "$BW_SESSION" ]; then
    echo "Error: BW_SESSION is not set. Please unlock Bitwarden first:" >&2
    echo "  export BW_SESSION=\$(bw unlock --raw)" >&2
    exit 1
fi

# Launch the MCP server
exec node "$(dirname "$0")/build/index.js"
