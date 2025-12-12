# MCP Skills Hub - Restructure Walkthrough

## Summary
The `mcp-skills-hub` has been restructured into a **domain-separated architecture**.
- **Physical Unity**: All code remains in one monorepo.
- **Logical Separation**: Capabilities are split into distinct MCP servers (`media-hub` and `disk-manager`).
- **Access Control**: Agents are defined in `agents/` and launched via `launch/agent-launcher.sh`.

## New Directory Structure
```
mcp-skills-hub-monorepo/
├── mcps/
│   ├── media-hub/     (Low-risk: YouTube, Whisper, etc.)
│   └── disk-manager/  (High-risk: Cleanup, disk usage)
├── agents/            (Capability definitions)
│   ├── media-agent.json
│   ├── disk-agent.json
│   └── admin-agent.json
└── launch/
    └── agent-launcher.sh
```

## Setup Instructions

### 1. Update Gemini Settings
You must update your `~/.gemini/settings.json` to point to the new MCP locations.
Replace the old `mcp-skills-hub` entry with the following:

```json
"mcpServers": {
    "media-hub": {
        "command": "/bin/bash",
        "args": [
            "/Users/zyahav/Documents/dev/mcp-skills-hub-monorepo/mcp-skills-hub-dev/feature-implement-handoff-md/mcps/media-hub/wrapper.sh"
        ]
    },
    "disk-manager": {
        "command": "/bin/bash",
        "args": [
            "/Users/zyahav/Documents/dev/mcp-skills-hub-monorepo/mcp-skills-hub-dev/feature-implement-handoff-md/mcps/disk-manager/wrapper.sh"
        ]
    }
}
```
*(Verify the absolute paths match your actual location)*

### 2. Verify with Gemini CLI
Test access to specific domains:

```bash
# Verify media capabilities only
gemini --allowed-mcp-server-names media-hub

# Verify disk capabilities only
gemini --allowed-mcp-server-names disk-manager
```

### 3. Using the Agent Launcher (Future)
The `launch/agent-launcher.sh` script is ready for use with compatible tools to enforce session-scoped access.

```bash
./launch/agent-launcher.sh media-agent
```

## Verification Results
- **File Structure**: ✅ Verified
- **Wrappers**: ✅ Created for both hubs
- **Agent Definitions**: ✅ Created
