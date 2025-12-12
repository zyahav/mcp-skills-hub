# MCP Skills Hub - Restructure Walkthrough

## Summary
The `mcp-skills-hub` has been restructured into a **domain-separated architecture**.
- **Physical Unity**: All code remains in one monorepo.
- **Logical Separation**: Capabilities are split into distinct MCP servers (`media-hub` and `disk-manager`).
- **Access Control**: Agents are defined in `agents/` and launched via `launch/agent-launcher.sh`.

## Directory Structure
```
mcp-skills-hub-dev/
├── agents/            (Capability definitions)
│   ├── media-agent.json    ← Only sees media-hub
│   ├── disk-agent.json     ← Only sees disk-manager
│   └── admin-agent.json    ← Sees everything
├── mcps/
│   ├── media-hub/     (Low-risk: YouTube, Whisper, etc.)
│   │   ├── hub.py
│   │   ├── wrapper.sh
│   │   ├── skill.json
│   │   └── skills/
│   │       ├── youtube_download/
│   │       ├── mp4_to_mp3/
│   │       ├── transcribe/
│   │       ├── video_snapshot/
│   │       └── tiktok_download/
│   └── disk-manager/  (High-risk: Cleanup, disk usage)
│       ├── server.py
│       ├── wrapper.sh
│       └── skill.json
└── launch/
    └── agent-launcher.sh
```

## Setup Instructions

### 1. Update Gemini Settings
Update your `~/.gemini/settings.json` to point to the new MCP locations:

```json
"mcpServers": {
    "media-hub": {
        "command": "/bin/bash",
        "args": [
            "/Users/zyahav/Documents/dev/mcp-skills-hub-monorepo/mcp-skills-hub-dev/mcps/media-hub/wrapper.sh"
        ]
    },
    "disk-manager": {
        "command": "/bin/bash",
        "args": [
            "/Users/zyahav/Documents/dev/mcp-skills-hub-monorepo/mcp-skills-hub-dev/mcps/disk-manager/wrapper.sh"
        ]
    }
}
```

### 2. Verify with Gemini CLI
Test access to specific domains:

```bash
# Verify media capabilities only
gemini --allowed-mcp-server-names media-hub

# Verify disk capabilities only
gemini --allowed-mcp-server-names disk-manager

# Access both (admin mode)
gemini --allowed-mcp-server-names media-hub,disk-manager
```

### 3. Using the Agent Launcher
The `launch/agent-launcher.sh` script enforces session-scoped access:

```bash
# Launch with media-only access
./launch/agent-launcher.sh media-agent

# Launch with disk-only access
./launch/agent-launcher.sh disk-agent

# Launch with full access
./launch/agent-launcher.sh admin-agent
```

## Verification Checklist
- [x] File Structure created
- [x] Wrappers created for both hubs
- [x] Agent definitions created
- [ ] Gemini settings updated
- [ ] Test media-hub tools
- [ ] Test disk-manager tools
