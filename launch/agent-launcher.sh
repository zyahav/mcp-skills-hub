#!/usr/bin/env bash
set -euo pipefail

# agent-launcher.sh
# Usage: ./launch/agent-launcher.sh <agent-name> [--tool <command...>]

# Resolve absolute path to the repo root
# This ensures it works regardless of where it's called from
LAUNCHER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$LAUNCHER_DIR")"
AGENTS_DIR="$REPO_ROOT/agents"
MCPS_DIR="$REPO_ROOT/mcps"
SESSION_DIR=$(mktemp -d /tmp/mcp-session.XXXXXX)
REGISTRY="$SESSION_DIR/registry.json"
CONFIG="$SESSION_DIR/mcp-config.json"
LOG="$SESSION_DIR/launcher.log"

echo "Session: $SESSION_DIR" >&2

cleanup() {
  if [[ -f "$REGISTRY" ]]; then
    # Kill all PIDs listed in the registry
    jq -r '.pids[]' "$REGISTRY" 2>/dev/null | xargs -r kill 2>/dev/null || true
  fi
  rm -rf "$SESSION_DIR"
}
trap cleanup EXIT

AGENT_NAME="$1"; shift || true
TOOL_CMD=("$@")
[[ ${#TOOL_CMD[@]} -eq 0 ]] && TOOL_CMD=("bash")

AGENT_FILE="$AGENTS_DIR/${AGENT_NAME}.json"
[[ -f "$AGENT_FILE" ]] || { echo "Agent not found: $AGENT_FILE" >&2; exit 1; }

ALLOWED_MCPS=$(jq -c '.allowed_mcps // []' "$AGENT_FILE")
ENV_ALLOWLIST=$(jq -r '.env_allowlist // [] | .[]' "$AGENT_FILE")

# Initialize registry
jq -n '{pids: []}' > "$REGISTRY"

echo "Launching MCPs for agent: $AGENT_NAME" >&2

for row in $(echo "$ALLOWED_MCPS" | jq -c '.[]'); do
  MCP_ID=$(echo "$row" | jq -r '.id')
  ARGS=$(echo "$row" | jq -r '.args // [] | join(" ")')
  MCP_PATH="$MCPS_DIR/$MCP_ID"
  
  # Determine command to launch MCP
  WRAPPER="$MCP_PATH/wrapper.sh"
  if [[ -x "$WRAPPER" ]]; then
      CMD=("$WRAPPER" $ARGS)
  elif [[ -f "$MCP_PATH/server.py" ]]; then
      CMD=(python3 "$MCP_PATH/server.py" $ARGS)
  else
      echo "Warning: No launcher found for MCP $MCP_ID at $MCP_PATH" >&2
      continue
  fi

  echo "Starting $MCP_ID..." >&2
  # Launch in background and redirect specific output if needed, or just let it handle its own logging
  # For now, capturing stderr to log file for debugging
  "${CMD[@]}" >> "$LOG" 2>&1 &
  PID=$!
  
  # Add PID to registry
  jq --arg pid "$PID" '.pids += [$pid|tonumber]' "$REGISTRY" > "$REGISTRY.tmp" && mv "$REGISTRY.tmp" "$REGISTRY"
done

jq -n --arg dir "$SESSION_DIR" '{session_dir: $dir}' > "$CONFIG"

# Build environment for the tool
ENV_CMD=(env -i)
# Copy allowlisted environment variables
for var in $ENV_ALLOWLIST; do 
    if [[ -n "${!var:-}" ]]; then
        ENV_CMD+=("$var=${!var}")
    fi
done
ENV_CMD+=("MCP_SESSION_DIR=$SESSION_DIR" "MCP_CONFIG=$CONFIG")

echo "Running tool command..." >&2
"${ENV_CMD[@]}" "${TOOL_CMD[@]}"
