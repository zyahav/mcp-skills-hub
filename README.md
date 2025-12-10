# MCP Skills Hub

A modular Model Context Protocol (MCP) server that acts as a hub for various local "skills" (tools). It allows you to expose multiple standalone scripts or tools as a single MCP server to Claude Desktop or other MCP clients.

## 🚀 Included Skills

- **youtube_download**: Download videos or audio from YouTube (uses `yt-dlp`).
- **whisper_local**: Transcribe audio files locally (uses `openai-whisper`).
- **video_snapshot**: Extract high-quality image frames from videos at specific timestamps (uses `ffmpeg`).
- **mp4_to_mp3**: Convert video files to audio.
- **tiktok_download**: Download TikTok videos.

## 🛠️ Prerequisites

- **Python 3.10+** (tested with 3.14 via Homebrew)
- **ffmpeg** (for media processing): `brew install ffmpeg`
- **yt-dlp** (for downloads): `brew install yt-dlp`

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/zyahav/mcp-skills-hub.git
    cd mcp-skills-hub
    ```

2.  **Install Python dependencies:**
    ```bash
    pip3 install -r requirements.txt
    ```

## ⚙️ Configuration (Claude Desktop)

To use these skills in Claude Desktop, add the server to your configuration file:

**File:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "skills-hub": {
      "command": "/opt/homebrew/bin/python3",
      "args": [
        "/absolute/path/to/mcp-skills-hub/hub.py"
      ]
    }
  }
}
```

> **Note:** Replace `/absolute/path/to/...` with the actual path where you cloned this repo.
> Ensure you use the python executable that has the requirements installed.

## ➕ Adding New Skills

The Hub is designed to be easily extensible. To add a new skill:

1.  **Create a directory** in `skills/`:
    ```bash
    mkdir skills/my_new_skill
    ```

2.  **Create a `skill.json` manifest** inside that directory:
    ```json
    {
      "name": "my_new_skill",
      "description": "Description of what this skill does",
      "command": ["python3", "server.py"],
      "timeout": 60
    }
    ```

3.  **Implement your tool** (e.g., `server.py`):
    - It must speak the MCP protocol (stdio).
    - It can use `mcp` python SDK.
    - The Hub will automatically spawn this process when started and proxy requests to it.

4.  **Restart Claude Desktop**. The new tool will appear automatically!

## 🧪 Testing & Verification

We include a regression test suite to verify that all skills are working correctly.

### Running Tests Manually
```bash
python3 -m unittest tests/test_skills.py
```

### Watch Mode (Recommended for Development)
To automatically run tests whenever you change a file:
```bash
./watch_tests.sh
```

## 🐛 Debugging

Logs are written to `hub_debug.log` in the root directory.
If tools aren't showing up, check this file for startup errors.
