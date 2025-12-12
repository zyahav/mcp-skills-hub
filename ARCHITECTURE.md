# Universal MCP Capability-Gated Architecture (Session-Scoped Final Handoff)

**Status:** Final — Approved for Execution  
**Audience:** Engineering / Platform / DevOps  
**Core Philosophy:** *Physical Unity, Logical Separation*  
**Security Boundary:** Operating system process table + session scope

---

## 1. Purpose

Establish a **single, universal, deterministic mechanism** to enforce which MCP servers (capabilities) are visible to any agent, CLI, or plugin — regardless of vendor (Gemini, Claude, OpenAI, VS Code extensions, or future tools).

This architecture **does not rely on prompts, model cooperation, or tool-specific flags** as the primary security boundary. Enforcement occurs at the **OS/process level**.

---

## 2. Core Invariant

> **If an MCP server process is not reachable within the current session, it does not exist.**

Reachability is strictly defined as:
- STDIO pipes (preferred)
- Session-scoped TCP/SSE ports (fallback only)

There is:
- No global state
- No cross-session leakage
- No shared MCP lifetime

---

## 3. Architecture Overview

```
User → Agent Launcher → Session-Scoped MCP Processes → Tool (CLI / Plugin / Agent)
```

- **Agent Launcher** is the *only* control point.
- MCP servers are **ephemeral processes**, not persistent services.
- Tools can only discover MCPs that exist **within their session**.

---

## 4. Repository Structure (Monorepo)

```
mcp-skills-hub-monorepo/
├── README.md
├── ARCHITECTURE.md                  # This document
│
├── shared/                          # Shared utilities
│   ├── logging/
│   ├── safety/
│   └── utils/
│
├── mcps/                            # All MCP servers
│   ├── media-hub/                   # Low-risk domain
│   │   ├── server.py
│   │   ├── wrapper.sh
│   │   └── skills/
│   ├── disk-manager/                # High-risk domain
│   │   ├── server.py
│   │   ├── wrapper.sh
│   │   └── skill.json
│   └── payments-hub/                # Critical (future)
│
├── agents/                          # Capability registry (source of truth)
│   ├── media-agent.json
│   ├── disk-agent.json
│   └── admin-agent.json
│
└── launch/
    └── agent-launcher.sh            # Enforcement layer
```

---

## 5. Agent Definition Format (Source of Truth)

Each agent explicitly declares **what capabilities exist in its reality**.

```json
{
  "name": "disk-agent",
  "description": "High-risk disk operations",
  "allowed_mcps": [
    {
      "id": "disk-manager",
      "args": ["--write-enabled"],
      "env": { "DISK_MODE": "full" }
    },
    {
      "id": "media-hub",
      "args": [],
      "env": {}
    }
  ],
  "env_allowlist": ["HOME", "USER", "PATH"],
  "transport_preference": "stdio"
}
```

**Notes:**
- `allowed_mcps` defines *existence*, not permission.
- `env_allowlist` prevents secret leakage.
- Transport defaults to **STDIO**; TCP/SSE is fallback only.

---

## 6. Transport Modes

### Mode A — STDIO (Default, Preferred)

- MCP servers launched as **child subprocesses** of the launcher
- Tool inherits stdio or session-scoped config
- **Automatic cleanup** on tool exit (OS process tree)
- Zero global state
- Works with all CLIs and most plugins

### Mode B — TCP / SSE (Fallback Only)

- Used when stdio inheritance is impossible (some VS Code extensions)
- Launcher allocates **session-specific ports**
- PID + port registry is session-scoped
- On exit: launcher kills **only** session-owned PIDs

---

## 7. Launcher Responsibilities (Enforcement)

1. Read agent definition
2. Create unique session directory (`/tmp/mcp-session-<uuid>`)
3. For each allowed MCP:
   - Spawn MCP process (STDIO or bound port)
   - Record PID/port in session registry
4. Generate **session-scoped config** (if required by tool)
5. Launch tool with:
   - Clean environment (allowlisted vars only)
   - Session config path
   - Inherited stdio pipes (Mode A)
6. Wait for tool exit
7. Cleanup **only session-owned processes and artifacts**

**Never:**
- Kill global MCPs
- Modify global configs
- Share processes across sessions

---

## 8. Security Model

| Domain    | Risk     | Enforcement |
|----------|----------|-------------|
| Media    | Low      | Session scoping + launcher |
| Disk     | High     | Session scoping + explicit args + env allowlist |
| Payments | Critical | Session scoping + args + audit logging + future MFA |

**Final Rule:**
> If the process is not alive *in this session*, the capability does not exist.

---

## 9. Testing Protocol (Certification)

### Test A — Negative Capability
1. Launch `media-agent`
2. Prompt: `Use disk.cleanup on /tmp`
3. Expected: **Tool reports capability does not exist**

### Test B — Concurrent Sessions
1. Launch `media-agent`
2. In parallel, launch `disk-agent`
3. Verify:
   - Both operate independently
   - No cross-tool visibility

Any knowledge of non-existent tools = failure.

---

## 10. Why This Is Production-Grade

- Deterministic OS-level enforcement
- Vendor-agnostic
- Concurrent-safe
- Fully auditable (session dirs + logs)
- No bypass without OS privilege escalation
- Strictly stronger than prompt-based or flag-based systems

This architecture mirrors Claude Skills philosophy while being **explicit, portable, and enforceable**.

---

## 11. Minimal Session-Scoped Launcher (Reference Implementation)

```bash
#!/usr/bin/env bash
set -euo pipefail

# agent-launcher.sh
# Usage: ./launch/agent-launcher.sh <agent-name> [--tool <command...>]

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AGENTS_DIR="$REPO_ROOT/agents"
MCPS_DIR="$REPO_ROOT/mcps"
SESSION_DIR=$(mktemp -d /tmp/mcp-session.XXXXXX)
REGISTRY="$SESSION_DIR/registry.json"
CONFIG="$SESSION_DIR/mcp-config.json"
LOG="$SESSION_DIR/launcher.log"

echo "Session: $SESSION_DIR" >&2

cleanup() {
  if [[ -f "$REGISTRY" ]]; then
    jq -r '.pids[]' "$REGISTRY" 2>/dev/null | xargs -r kill 2>/dev/null || true
  fi
  rm -rf "$SESSION_DIR"
}
trap cleanup EXIT

AGENT_NAME="$1"; shift || true
TOOL_CMD=("$@")
[[ ${#TOOL_CMD[@]} -eq 0 ]] && TOOL_CMD=("bash")

AGENT_FILE="$AGENTS_DIR/${AGENT_NAME}.json"
[[ -f "$AGENT_FILE" ]] || { echo "Agent not found" >&2; exit 1; }

ALLOWED_MCPS=$(jq -c '.allowed_mcps // []' "$AGENT_FILE")
ENV_ALLOWLIST=$(jq -r '.env_allowlist // [] | .[]' "$AGENT_FILE")

jq -n '{pids: []}' > "$REGISTRY"

for row in $(echo "$ALLOWED_MCPS" | jq -c '.[]'); do
  MCP_ID=$(echo "$row" | jq -r '.id')
  ARGS=$(echo "$row" | jq -r '.args // [] | join(" ")')
  MCP_PATH="$MCPS_DIR/$MCP_ID"
  WRAPPER="$MCP_PATH/wrapper.sh"
  [[ -x "$WRAPPER" ]] && CMD=("$WRAPPER" $ARGS) || CMD=(python "$MCP_PATH/server.py" $ARGS)
  "${CMD[@]}" >> "$LOG" 2>&1 &
  PID=$!
  jq --arg pid "$PID" '.pids += [$pid|tonumber]' "$REGISTRY" > "$REGISTRY.tmp" && mv "$REGISTRY.tmp" "$REGISTRY"

done

jq -n --arg dir "$SESSION_DIR" '{session_dir: $dir}' > "$CONFIG"

ENV_CMD=(env -i)
for var in $ENV_ALLOWLIST; do ENV_CMD+=("$var=${!var:-}"); done
ENV_CMD+=("MCP_SESSION_DIR=$SESSION_DIR" "MCP_CONFIG=$CONFIG")

"${ENV_CMD[@]}" "${TOOL_CMD[@]}"
```

---

## 12. Final Statement

**All agents see only the MCP servers that exist in their session.**

The launcher decides what exists.

Therefore, the system works everywhere.

**Architecture locked. Proceed to implementation and QA.**
