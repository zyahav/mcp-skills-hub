# MCP Skills Hub

A collection of Model Context Protocol (MCP) servers for AI agents. Plug-and-play capabilities for Claude, Gemini, GPT, and any MCP-compatible client.

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/zyahav/mcp-skills-hub.git
cd mcp-skills-hub

# 2. Install dependencies
cd dashboard && npm install && cd ..

# 3. Run the dashboard to generate configs
node dashboard/server.js

# 4. Open http://localhost:3000 and copy your config
```

---

## Available MCPs

| MCP | Description | Risk Level |
|-----|-------------|------------|
| `media-hub` | YouTube download, MP4→MP3, transcription, TikTok download, video snapshots | Low |
| `disk-manager` | Disk usage monitoring, junk scanning, cleanup procedures | High |
| `git-manager` | Git operations, branch management, releases | Medium |
| `tunnel-manager` | Cloudflare tunnel management | Medium |
| `cloudflare-dns` | DNS record management | Medium |
| `bitwarden` | Password manager integration | High |
| `mcp-scaffolder` | Create new MCP servers from templates | Low |

---

## Installation

### Option A: Use the Dashboard (Recommended)

The dashboard auto-detects all MCPs and generates copy-paste configs.

```bash
# Start the dashboard
cd mcp-skills-hub
node dashboard/server.js

# Open in browser
open http://localhost:3000
```

The dashboard shows configs for:
- Claude Desktop
- Gemini CLI
- VSCode

### Option B: Run Dashboard as Background Service (macOS)

```bash
# Install as LaunchAgent (runs on startup)
cd mcp-skills-hub/dashboard
chmod +x install-service.sh
./install-service.sh

# Dashboard will always be available at http://localhost:3000
```

To uninstall:
```bash
launchctl unload ~/Library/LaunchAgents/com.zurielyahav.mcp-dashboard.plist
rm ~/Library/LaunchAgents/com.zurielyahav.mcp-dashboard.plist
```

### Option C: Manual Configuration

<details>
<summary>Claude Desktop</summary>

**Config file location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Add to config:**
```json
{
  "mcpServers": {
    "media-hub": {
      "command": "/bin/bash",
      "args": ["/path/to/mcp-skills-hub/mcps/media-hub/wrapper.sh"]
    },
    "disk-manager": {
      "command": "/bin/bash",
      "args": ["/path/to/mcp-skills-hub/mcps/disk-manager/wrapper.sh"]
    }
  }
}
```

Replace `/path/to/mcp-skills-hub` with your actual path.

</details>

<details>
<summary>Gemini CLI</summary>

**Config file location:**
- All platforms: `~/.gemini/settings.json`

**Add to config:**
```json
{
  "mcpServers": {
    "media-hub": {
      "command": "/bin/bash",
      "args": ["/path/to/mcp-skills-hub/mcps/media-hub/wrapper.sh"]
    },
    "disk-manager": {
      "command": "/bin/bash",
      "args": ["/path/to/mcp-skills-hub/mcps/disk-manager/wrapper.sh"]
    }
  }
}
```

**Restrict access to specific MCPs:**
```bash
gemini --allowed-mcp-server-names media-hub
```

</details>

<details>
<summary>VSCode</summary>

**Config file location:**
- macOS: `~/.vscode/settings.json`
- Windows: `%APPDATA%\Code\User\settings.json`
- Linux: `~/.config/Code/User/settings.json`

Add the same `mcpServers` block as above.

</details>

---

## MCP Details

### media-hub

Low-risk media processing tools.

**Tools:**
- `youtube_download` - Download YouTube videos
- `mp4_to_mp3` - Convert video to audio
- `transcribe` - Transcribe audio using Whisper
- `video_snapshot` - Extract frames from video
- `tiktok_download` - Download TikTok videos

**Requirements:**
- Python 3.8+
- ffmpeg
- yt-dlp

```bash
# Install requirements
pip install -r mcps/media-hub/requirements.txt
brew install ffmpeg  # macOS
```

### disk-manager

High-risk disk operations. All cleanup actions require explicit confirmation.

**Tools:**
- `get_disk_status` - Current disk usage
- `scan_junk` - Find cleanable files
- `get_procedures` - List cleanup procedures
- `execute_cleanup` - Run cleanup (requires confirm=true)
- `get_app_status` - App approval status
- `approve_app` - Approve an app
- `get_history` - Usage history
- `get_emergency_workflow` - Emergency cleanup steps

---

## Architecture

```
mcp-skills-hub/
├── README.md              # This file
├── dashboard/             # Config generator UI
│   ├── server.js          # Express server
│   ├── index.html         # Dashboard UI
│   └── install-service.sh # macOS LaunchAgent installer
├── mcps/                  # MCP servers
│   ├── media-hub/
│   │   ├── wrapper.sh     # Entry point
│   │   ├── hub.py         # Main server
│   │   └── skills/        # Individual tools
│   ├── disk-manager/
│   │   ├── wrapper.sh
│   │   └── server.py
│   └── .../
├── agents/                # Capability definitions
│   ├── media-agent.json   # Only media-hub access
│   ├── disk-agent.json    # Only disk-manager access
│   └── admin-agent.json   # Full access
└── launch/
    └── agent-launcher.sh  # Session-scoped launcher
```

**Key Principle:** Physical Unity, Logical Separation
- All code in one repo
- Each MCP is isolated
- Agents only see what they're allowed to see

---

## For AI Agents

### To install this for a user:

```bash
# Step 1: Clone
git clone https://github.com/zyahav/mcp-skills-hub.git /Users/Shared/tools/mcp-skills-hub

# Step 2: Install dashboard dependencies
cd /Users/Shared/tools/mcp-skills-hub/dashboard
npm install

# Step 3: Start dashboard
node server.js &

# Step 4: Get the config
curl http://localhost:3000/api/config | jq '.claude'

# Step 5: Update user's Claude config
# Location: ~/Library/Application Support/Claude/claude_desktop_config.json
```

### To verify installation:

```bash
# Check if MCPs are detected
curl http://localhost:3000/api/config | jq '.mcps[].name'

# Expected output:
# "media-hub"
# "disk-manager"
# "git-manager"
# ...
```

### To add a new MCP:

1. Create folder in `mcps/your-mcp-name/`
2. Add either:
   - `wrapper.sh` (preferred) - Shell script entry point
   - `server.py` - Python MCP server
   - `package.json` + `index.js` - Node.js MCP server
3. Dashboard will auto-detect it

---

## Troubleshooting

### MCP not showing in Claude/Gemini

1. Check config file path is correct
2. Verify the wrapper.sh is executable: `chmod +x mcps/*/wrapper.sh`
3. Restart the client application
4. Check logs:
   - Dashboard: `/tmp/com.zurielyahav.mcp-dashboard.out.log`
   - Media-hub: `mcps/media-hub/hub_debug.log`

### Dashboard won't start

```bash
# Check if port 3000 is in use
lsof -i :3000

# Kill existing process
kill $(lsof -t -i :3000)

# Restart
node dashboard/server.js
```

### Permission denied on wrapper.sh

```bash
chmod +x mcps/*/wrapper.sh
```

---

## License

MIT

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes in `mcps/your-feature/`
4. Submit a Pull Request

See [ARCHITECTURE.md](ARCHITECTURE.md) for design principles.
