#!/bin/bash

# Get the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Run the python script with unbuffered output
# Using generic python3 as path might vary, but -u is critical for MCP
python3 -u "$SCRIPT_DIR/server.py"
