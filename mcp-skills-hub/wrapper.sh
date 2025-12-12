#!/bin/bash

# Get the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

LOGFILE="/tmp/mcp_wrapper.log"
echo "==========================================" >> "$LOGFILE"
echo "Wrapper started at $(date)" >> "$LOGFILE"
echo "User: $(whoami)" >> "$LOGFILE"
echo "Env PATH: $PATH" >> "$LOGFILE"
echo "Python Path: /opt/homebrew/bin/python3" >> "$LOGFILE"
echo "Script Dir: $SCRIPT_DIR" >> "$LOGFILE"

# Run the python script.
# IMPORTANT: do NOT redirect stdout (>> log), or Claude won't see the JSON-RPC messages!
# Only redirect stderr to the log.
/opt/homebrew/bin/python3 -u "$SCRIPT_DIR/hub.py" 2>> "$LOGFILE"

EXIT_CODE=$?
echo "Python exited with code $EXIT_CODE" >> "$LOGFILE"
exit $EXIT_CODE
