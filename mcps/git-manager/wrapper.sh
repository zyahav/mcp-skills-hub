#!/bin/bash

# Get the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

LOGFILE="/tmp/git_manager_wrapper.log"
echo "==========================================" >> "$LOGFILE"
echo "Wrapper started at $(date)" >> "$LOGFILE"
echo "Script Dir: $SCRIPT_DIR" >> "$LOGFILE"

# Check for required environment variable
if [ -z "$GIT_MANAGER_REPO_ROOT" ]; then
    echo "ERROR: GIT_MANAGER_REPO_ROOT environment variable is required" >> "$LOGFILE"
    echo "Set it in your MCP configuration to point to your monorepo root" >> "$LOGFILE"
    # Still try to run - server.py will give detailed error
fi

echo "GIT_MANAGER_REPO_ROOT: ${GIT_MANAGER_REPO_ROOT:-NOT SET}" >> "$LOGFILE"

# Run the python script
# IMPORTANT: do NOT redirect stdout, or JSON-RPC messages will be lost!
/opt/homebrew/bin/python3 -u "$SCRIPT_DIR/server.py" 2>> "$LOGFILE"

EXIT_CODE=$?
echo "Python exited with code $EXIT_CODE" >> "$LOGFILE"
exit $EXIT_CODE
