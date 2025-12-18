# MCP Skill Creation Blueprint

> **Purpose:** This file contains everything needed to create a new MCP skill. An LLM reading ONLY this file should be able to implement a fully working skill without examining any other files.

---

## ⚠️ BOUNDARIES — READ FIRST ⚠️

When creating a new skill, the agent has **strict boundaries**. Violating these boundaries will cause the verification test to fail and the changes will be rejected.

### ✅ ALLOWED Actions

| Action | Location | Example |
|--------|----------|---------|
| Create new skill directory | `mcps/<new-skill-name>/` | `mcps/google-workspace/` |
| Create files in new skill | `mcps/<new-skill-name>/*` | `server.py`, `skill.json`, `wrapper.sh`, `requirements.txt` |
| Create sub-skills (hub pattern) | `mcps/<new-skill-name>/skills/*/` | `mcps/google-hub/skills/gmail/` |
| Add skill to agent | `agents/*.json` | Add entry to `allowed_mcps` array |
| Create secrets directory | `~/.mcp-secrets/<skill-name>/` | Outside repo, for OAuth tokens |

### ❌ FORBIDDEN Actions — NEVER DO THESE

| Action | Why |
|--------|-----|
| Modify existing skills | `mcps/git-manager/*`, `mcps/disk-manager/*`, `mcps/media-hub/*` are OFF LIMITS |
| Modify root documents | `ARCHITECTURE.md`, `SKILL_BLUEPRINT.md`, `README.md`, `HANDOFF.md` are READ-ONLY |
| Touch launch scripts | `launch/*` is infrastructure, not skill code |
| Modify `.env` or `.gitignore` | Environment config is separate concern |
| Delete any files | Skills are additive only |
| Create files at repo root | No new root-level files |
| Modify `.github/*` | CI/CD is separate concern |

### 🧪 Verification

Before pushing, ALWAYS run:
```bash
./scripts/verify-skill-creation.sh <skill-name>
```

This script will:
1. Check that ONLY expected files were created/modified
2. Verify no existing skills were touched
3. Verify no protected files were modified
4. Confirm the new skill has valid structure

**If verification fails, do NOT push. Review and fix the changes.**

---

## Project Structure Overview

```
mcp-skills-hub-dev/
├── mcps/                           # All MCP servers live here
│   ├── git-manager/                # Simple MCP (single server.py)
│   ├── disk-manager/               # Simple MCP
│   └── media-hub/                  # Hub MCP (spawns sub-skills)
│       └── skills/                 # Sub-skills directory
│
├── agents/                         # Agent definitions (capability gating)
│   ├── media-agent.json
│   └── dev-agent.json
│
└── launch/                         # Launcher scripts
```

---

## Two Patterns for Skills

### Pattern 1: Simple MCP (Recommended for most cases)

Use when: All tools belong to one cohesive domain.

```
mcps/your-skill-name/
├── server.py          # All tools implemented here
├── skill.json         # Manifest file
├── wrapper.sh         # Optional: startup wrapper
└── requirements.txt   # Optional: Python dependencies
```

### Pattern 2: Hub MCP (For complex domains with sub-skills)

Use when: You need to compose multiple independent sub-skills that could be used separately.

```
mcps/your-hub-name/
├── hub.py             # Process manager (spawns sub-skills)
├── skill.json         # Hub manifest
├── wrapper.sh
├── requirements.txt
└── skills/            # Sub-skills directory
    ├── sub-skill-a/
    │   ├── server.py
    │   └── skill.json
    └── sub-skill-b/
        ├── server.py
        └── skill.json
```

---

## File Templates

### skill.json (Manifest)

```json
{
    "name": "your_skill_name",
    "description": "One-line description of what this skill does. List tools: tool1, tool2, tool3",
    "command": ["python3", "server.py"],
    "timeout": 120
}
```

**Rules:**
- `name`: lowercase, underscores allowed, no spaces
- `description`: Include tool names so agents know what's available
- `command`: Array of command + args. Use `python3` (launcher resolves to correct interpreter)
- `timeout`: Max seconds for tool execution

---

### server.py (Simple MCP Template)

```python
#!/usr/bin/env python3
"""
YOUR_SKILL_NAME - Brief description

Detailed explanation of what this skill does.
"""

import asyncio
import os
from typing import Optional

from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field

# Initialize server
SKILL_NAME = os.environ.get("MCP_SKILL_NAME", "your_skill_name")
server = Server(SKILL_NAME)


# ============== ARGUMENT MODELS ==============

class EmptyArgs(BaseModel):
    """No arguments required."""
    pass


class ExampleArgs(BaseModel):
    """Arguments for example_tool."""
    required_param: str = Field(description="Description of this parameter")
    optional_param: Optional[str] = Field(default=None, description="Optional parameter")
    flag_param: bool = Field(default=False, description="A boolean flag")


# ============== TOOL DEFINITIONS ==============

TOOLS = {
    "tool_one": {
        "description": "What this tool does. Be specific.",
        "schema": EmptyArgs,
    },
    "tool_two": {
        "description": "Another tool with parameters.",
        "schema": ExampleArgs,
    },
}


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name=name,
            description=info["description"],
            inputSchema=info["schema"].model_json_schema(),
        )
        for name, info in TOOLS.items()
    ]


# ============== TOOL ROUTER ==============

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "tool_one":
            result = do_tool_one()
        elif name == "tool_two":
            args = ExampleArgs(**arguments)
            result = do_tool_two(args.required_param, args.optional_param, args.flag_param)
        else:
            result = f"Unknown tool: {name}"
        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ============== IMPLEMENTATION FUNCTIONS ==============

def do_tool_one() -> str:
    """Implementation of tool_one."""
    return "Tool one executed successfully"


def do_tool_two(required: str, optional: Optional[str], flag: bool) -> str:
    """Implementation of tool_two."""
    result = [f"Required: {required}"]
    if optional:
        result.append(f"Optional: {optional}")
    if flag:
        result.append("Flag is enabled")
    return "\n".join(result)


# ============== MAIN ==============

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
```

---

### wrapper.sh (Optional)

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv if exists
if [[ -f "venv/bin/activate" ]]; then
    source venv/bin/activate
fi

exec python3 server.py "$@"
```

Make executable: `chmod +x wrapper.sh`

---

## Agent Definition (agents/*.json)

To make a skill available to an agent, add it to `allowed_mcps`:

```json
{
  "name": "your-agent-name",
  "description": "What this agent does",
  "allowed_mcps": [
    {
      "id": "your-skill-name",
      "args": [],
      "env": {}
    }
  ],
  "env_allowlist": ["HOME", "USER", "PATH"],
  "transport_preference": "stdio"
}
```

**Rules:**
- `id` must match the directory name under `mcps/`
- `args` are passed to the skill command
- `env` are additional environment variables
- `env_allowlist` controls which host env vars are passed through

---

## Hub Pattern (hub.py Template)

Only use if you need sub-skills. The hub spawns child processes and proxies JSON-RPC.

```python
#!/usr/bin/env python3
import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Dict

from mcp.server import Server
from mcp.types import Tool, TextContent

ROOT = Path(__file__).parent
SKILLS_DIR = ROOT / "skills"
SERVER_NAME = "your-hub-name"

server = Server(SERVER_NAME)

PROCESSES: Dict[str, asyncio.subprocess.Process] = {}
MANIFESTS: Dict[str, dict] = {}
TOOL_MAPPING: Dict[str, str] = {}  # tool_name -> skill_name
SKILL_LOCKS: Dict[str, asyncio.Lock] = {}
STARTUP_EVENT = asyncio.Event()


async def load_skills_and_initialize():
    """Load and initialize all sub-skills."""
    if not SKILLS_DIR.exists():
        STARTUP_EVENT.set()
        return

    # Spawn processes
    for skill_dir in SKILLS_DIR.iterdir():
        manifest_path = skill_dir / "skill.json"
        if not manifest_path.exists():
            continue
        await spawn_skill(skill_dir, manifest_path)

    # Initialize handshakes
    for name, proc in PROCESSES.items():
        await initialize_skill_process(name, proc)

    # Build tool mapping
    await populate_tool_mapping()
    STARTUP_EVENT.set()


async def spawn_skill(skill_dir: Path, manifest_path: Path):
    """Spawn a sub-skill process."""
    try:
        manifest = json.loads(manifest_path.read_text())
        name = manifest["name"]
        cmd = manifest["command"].copy()
        
        if cmd[0] == "python3":
            cmd[0] = sys.executable

        env = os.environ.copy()
        env["MCP_SKILL_NAME"] = name

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=skill_dir,
            env=env,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=sys.stderr,
        )

        PROCESSES[name] = process
        MANIFESTS[name] = manifest
        SKILL_LOCKS[name] = asyncio.Lock()
    except Exception as e:
        print(f"Failed to load skill {skill_dir.name}: {e}", file=sys.stderr)


async def initialize_skill_process(name: str, proc):
    """MCP handshake with sub-skill."""
    lock = SKILL_LOCKS.get(name)
    if not lock:
        return
    
    async with lock:
        try:
            init_req = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": SERVER_NAME, "version": "1.0"}
                },
                "id": 0
            }
            proc.stdin.write((json.dumps(init_req) + "\n").encode())
            await proc.stdin.drain()
            
            line = await proc.stdout.readline()
            if not line:
                return
            
            proc.stdin.write((json.dumps({
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }) + "\n").encode())
            await proc.stdin.drain()
        except Exception as e:
            print(f"Error initializing {name}: {e}", file=sys.stderr)


async def populate_tool_mapping():
    """Build tool -> skill mapping."""
    TOOL_MAPPING.clear()
    for name, proc in PROCESSES.items():
        lock = SKILL_LOCKS.get(name)
        if not lock:
            continue
        async with lock:
            try:
                request = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
                proc.stdin.write((json.dumps(request) + "\n").encode())
                await proc.stdin.drain()
                
                line = await proc.stdout.readline()
                if line:
                    response = json.loads(line.decode())
                    for t in response.get("result", {}).get("tools", []):
                        TOOL_MAPPING[t["name"]] = name
            except Exception as e:
                print(f"Error listing tools for {name}: {e}", file=sys.stderr)


@server.list_tools()
async def list_tools():
    await STARTUP_EVENT.wait()
    tools = []
    for name, proc in PROCESSES.items():
        lock = SKILL_LOCKS.get(name)
        if not lock:
            continue
        async with lock:
            try:
                request = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
                proc.stdin.write((json.dumps(request) + "\n").encode())
                await proc.stdin.drain()
                
                line = await proc.stdout.readline()
                if line:
                    response = json.loads(line.decode())
                    for t in response.get("result", {}).get("tools", []):
                        tools.append(Tool(**t))
            except Exception:
                pass
    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    await STARTUP_EVENT.wait()
    
    skill_name = TOOL_MAPPING.get(name, name)
    proc = PROCESSES.get(skill_name)
    lock = SKILL_LOCKS.get(skill_name)
    
    if not proc or not lock:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
        "id": 1
    }

    async with lock:
        try:
            proc.stdin.write((json.dumps(request) + "\n").encode())
            await proc.stdin.drain()
            
            line = await proc.stdout.readline()
            if not line:
                return [TextContent(type="text", text="Empty response")]
            
            response = json.loads(line.decode())
            if "error" in response:
                return [TextContent(type="text", text=f"Error: {response['error']}")]
            
            return response.get("result", {}).get("content", [])
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    asyncio.create_task(load_skills_and_initialize())
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Step-by-Step: Creating a New Simple Skill

1. **Create directory:**
   ```bash
   mkdir -p mcps/your-skill-name
   ```

2. **Create skill.json:**
   ```bash
   # mcps/your-skill-name/skill.json
   ```

3. **Create server.py** using the template above

4. **Test locally:**
   ```bash
   cd mcps/your-skill-name
   python3 server.py
   # Should start without errors (waiting for JSON-RPC input)
   ```

5. **Add to an agent** in `agents/your-agent.json`

6. **Dependencies** (if needed):
   ```bash
   echo "some-package" >> mcps/your-skill-name/requirements.txt
   pip install -r mcps/your-skill-name/requirements.txt
   ```

---

## Common Patterns

### Argument Validation (Pydantic)

```python
from pydantic import BaseModel, Field, field_validator

class MyArgs(BaseModel):
    path: str = Field(description="File path")
    
    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("path cannot be empty")
        return v.strip()
```

### Returning Structured Output

```python
def do_something() -> str:
    output = ["=== HEADER ===\n"]
    output.append("Line 1")
    output.append("Line 2")
    output.append("\n✅ Success!")
    return "\n".join(output)
```

### Running Shell Commands

```python
import subprocess
from pathlib import Path

def run_command(cmd: list, cwd: Path = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        timeout=60,
    )
```

### Environment Variables

```python
import os

# Get with default
value = os.environ.get("MY_VAR", "default")

# Required (fail if missing)
value = os.environ["REQUIRED_VAR"]
```

---

## Skills with Authentication

For skills requiring OAuth or API keys:

1. **Store credentials outside the repo:**
   ```
   ~/.mcp-secrets/
   └── your-skill/
       ├── credentials.json   # OAuth client secret
       └── token.json         # User authorization
   ```

2. **Reference in code:**
   ```python
   from pathlib import Path
   
   SECRETS_DIR = Path.home() / ".mcp-secrets" / "your-skill"
   CREDENTIALS_FILE = SECRETS_DIR / "credentials.json"
   TOKEN_FILE = SECRETS_DIR / "token.json"
   
   if not CREDENTIALS_FILE.exists():
       raise RuntimeError(f"Missing credentials. Run setup script first.")
   ```

3. **Add to .gitignore:**
   ```
   # Never commit secrets
   **/credentials.json
   **/token.json
   .mcp-secrets/
   ```

4. **Create a setup script** (`setup_auth.py`) that users run once.

---

## Checklist Before Committing

- [ ] `skill.json` has correct `name` and `description`
- [ ] `server.py` runs without errors
- [ ] All tools listed in TOOLS dict
- [ ] Pydantic models for all arguments
- [ ] No hardcoded paths (use Path relative to script)
- [ ] No secrets in code
- [ ] Added to appropriate agent JSON
- [ ] Tested tool calls manually

---

## Quick Reference

| What | Where |
|------|-------|
| Create new skill | `mcps/skill-name/` |
| Skill manifest | `skill.json` |
| Tool implementation | `server.py` |
| Agent capabilities | `agents/*.json` |
| Secrets | `~/.mcp-secrets/skill-name/` |

---

## Existing Skills Reference

| Skill | Pattern | Tools |
|-------|---------|-------|
| `git-manager` | Simple | list_worktrees, create_feature, merge_feature, etc. |
| `disk-manager` | Simple | get_disk_status, scan_junk, execute_cleanup, etc. |
| `media-hub` | Hub | youtube_download, transcribe, mp4_to_mp3, etc. |

---

*Last updated: Session handoff document for skill creation.*
