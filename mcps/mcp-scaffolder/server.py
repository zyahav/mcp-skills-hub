#!/usr/bin/env python3
"""
MCP Scaffolder - Standard Skill Generator
"""

import asyncio
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

import argparse
import sys

# Try imports for Server mode
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Mock classes for type hints if needed, or just warn later
    Server = object 

from pydantic import BaseModel, Field, field_validator

# Initialize server if possible
SKILL_NAME = "mcp-scaffolder"
if MCP_AVAILABLE:
    server = Server(SKILL_NAME)
else:
    server = None

# Path resolution
SCRIPT_DIR = Path(__file__).resolve().parent
MCPS_DIR = SCRIPT_DIR.parent
MONOREPO_ROOT = MCPS_DIR.parent 
# Note: In a worktree, contents are at root. 
# We assume we are running from the root of the worktree or repo.
# If running from mcps/mcp-scaffolder/server.py:
# SCRIPT_DIR = .../mcps/mcp-scaffolder
# MCPS_DIR = .../mcps
# WORKTREE_ROOT = .../

WORKTREE_ROOT = MCPS_DIR.parent

# ============== TEMPLATES ==============

TEMPLATE_FEATURE_LIST = """[
  {{
    "milestone": 1,
    "category": "scaffolding",
    "description": "Project Scaffolding",
    "deliverables": [
      "mcps/{skill_name}/package.json",
      "mcps/{skill_name}/src/index.ts"
    ],
    "passes": true,
    "verified_at": "{date}",
    "commit": "Initial Commit"
  }}
]"""

TEMPLATE_PROGRESS = """# Progress Log: {skill_name}

## Session {date}
- [INIT] Scaffolding created by mcp-scaffolder.
"""

TEMPLATE_RESUME = """# 🚀 Resume Instructions: {skill_name}

**Status:** 🟡 STARTING
**Archon Project ID:** `{archon_project_id}`

## Immediate Tasks
1. Review feature_list.json
2. Implement core logic in mcps/{skill_name}/src/
3. Update agents to include this new skill.
"""

TEMPLATE_LESSONS = """# 🧠 Lessons Learned: {skill_name}

## Known Pitfalls
- [ ] Add new items here
"""

TEMPLATE_PACKAGE_JSON = """{{
  "name": "mcp-{skill_name}",
  "version": "0.1.0",
  "type": "module",
  "bin": {{
    "mcp-{skill_name}": "./build/index.js"
  }},
  "scripts": {{
    "build": "tsc && chmod +x build/index.js",
    "start": "node build/index.js",
    "watch": "tsc --watch"
  }},
  "dependencies": {{
    "@modelcontextprotocol/sdk": "latest",
    "zod": "^3.0.0"
  }},
  "devDependencies": {{
    "typescript": "^5.0.0",
    "@types/node": "^20.0.0"
  }}
}}"""

TEMPLATE_TSCONFIG = """{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "./build",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules"]
}"""

TEMPLATE_README = """# MCP: {skill_name}

{description}

## Usage
Add to your generic mcp-settings or agent configuration.
"""

TEMPLATE_INDEX_TS = """#!/usr/bin/env node

import {{ Server }} from "@modelcontextprotocol/sdk/server/index.js";
import {{ StdioServerTransport }} from "@modelcontextprotocol/sdk/server/stdio.js";
import {{
  CallToolRequestSchema,
  ListToolsRequestSchema,
}} from "@modelcontextprotocol/sdk/types.js";
import {{ z }} from "zod";

const server = new Server(
  {{
    name: "{skill_name}",
    version: "0.1.0",
  }},
  {{
    capabilities: {{
      tools: {{}},
    }},
  }}
);

server.setRequestHandler(ListToolsRequestSchema, async () => {{
  return {{
    tools: [
      {{
        name: "example_tool",
        description: "An example tool",
        inputSchema: {{
          type: "object",
          properties: {{
            message: {{ type: "string" }},
          }},
          required: ["message"],
        }},
      }},
    ],
  }};
}});

server.setRequestHandler(CallToolRequestSchema, async (request) => {{
  if (request.params.name === "example_tool") {{
    const message = String(request.params.arguments?.message);
    return {{
      content: [{{ type: "text", text: `Echo: ${{message}}` }}],
    }};
  }}
  throw new Error("Tool not found");
}});

const transport = new StdioServerTransport();
await server.connect(transport);
"""

# ============== HELPER FUNCTIONS ==============

def run_git(args: List[str], cwd: Path = None) -> subprocess.CompletedProcess:
    """Run a git command and return the result."""
    cmd = ["git"] + args
    return subprocess.run(
        cmd,
        cwd=str(cwd or WORKTREE_ROOT),
        text=True,
        capture_output=True,
    )

def format_result(proc: subprocess.CompletedProcess) -> str:
    """Format command result for output."""
    parts = []
    if proc.stdout.strip():
        parts.append(proc.stdout.strip())
    if proc.stderr.strip():
        parts.append(f"stderr: {proc.stderr.strip()}")
    if proc.returncode != 0:
        parts.append(f"exit code: {proc.returncode}")
    return "\n".join(parts) if parts else "(no output)"

# ============== ARGUMENT MODELS ==============

class ScaffoldArgs(BaseModel):
    skill_name: str = Field(description="Name of the skill (e.g., 'weather-api'). lowercase, hyphens only.")
    description: str = Field(description="Short description of the skill purpose.")
    archon_project_id: str = Field(description="UUID of the Archon Project tracking this skill.", default="PENDING")
    
    @field_validator("skill_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("skill_name cannot be empty")
        v = v.strip()
        if any(c.isupper() for c in v):
            raise ValueError("skill_name must be lowercase")
        if any(c in v for c in " /\\"):
            raise ValueError("skill_name cannot contain spaces or path separators")
        return v

# ============== TOOL DEFINITIONS ==============

if MCP_AVAILABLE and server:
    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="scaffold_skill",
                description="Create a new MCP skill with standard directory structure, files, and git commit.",
                inputSchema=ScaffoldArgs.model_json_schema(),
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name != "scaffold_skill":
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        
        try:
            args = ScaffoldArgs(**arguments)
            result = do_scaffold_skill(args.skill_name, args.description, args.archon_project_id)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

# ============== IMPLEMENTATION ==============

def do_scaffold_skill(skill_name: str, description: str, archon_project_id: str) -> str:
    output = [f"=== SCAFFOLDING SKILL: {skill_name} ===\n"]
    
    handoff_dir = WORKTREE_ROOT / "handoffs" / skill_name
    mcp_dir = WORKTREE_ROOT / "mcps" / skill_name
    src_dir = mcp_dir / "src"
    
    # 1. Validation
    # NOTE: Modified to allow overwrite of handoffs if they exist, or just logic
    # Original: if handoff_dir.exists() or mcp_dir.exists(): return error
    if mcp_dir.exists():
        output.append(f"⚠️ MCPS dir exists: {mcp_dir}. Proceeding with caution (might overwrite).")
        # return f"❌ Skill already exists (directories detected).\nCheck: {handoff_dir}\nCheck: {mcp_dir}"
    
    # 2. Create Directories
    try:
        handoff_dir.mkdir(parents=True, exist_ok=True) # Changed to True
        mcp_dir.mkdir(parents=True, exist_ok=True) # Changed to True
        src_dir.mkdir(parents=True, exist_ok=True) # Changed to True
        output.append("✅ Created/Verified directories")
    except Exception as e:
        return f"❌ Failed to create directories: {e}"
        
    # 3. Write Files
    from datetime import date
    today = date.today().isoformat()
    
    files = {
        # Handoffs
        handoff_dir / "feature_list.json": TEMPLATE_FEATURE_LIST.format(skill_name=skill_name, date=today),
        handoff_dir / "progress.txt": TEMPLATE_PROGRESS.format(skill_name=skill_name, date=today),
        handoff_dir / "RESUME.md": TEMPLATE_RESUME.format(skill_name=skill_name, archon_project_id=archon_project_id),
        handoff_dir / "LESSONS_LEARNED.md": TEMPLATE_LESSONS.format(skill_name=skill_name),
        
        # MCPs
        mcp_dir / "package.json": TEMPLATE_PACKAGE_JSON.format(skill_name=skill_name),
        mcp_dir / "tsconfig.json": TEMPLATE_TSCONFIG,
        mcp_dir / "README.md": TEMPLATE_README.format(skill_name=skill_name, description=description),
        mcp_dir / "skill.json": json.dumps({
            "name": skill_name,
            "version": "0.1.0",
            "description": description,
            "tools": ["example_tool"]
        }, indent=2),
        src_dir / "index.ts": TEMPLATE_INDEX_TS.format(skill_name=skill_name),
    }
    
    for path, content in files.items():
        # Check if exists to avoid overwriting handoffs blindly?
        # Scaffolder usually assumes fresh start.
        # But if running on existing handoffs, we might want to skip overwriting progress.
        if path.exists() and "handoffs" in str(path):
             output.append(f"   Skipping existing handoff file: {path.name}")
             continue
             
        with open(path, "w") as f:
            f.write(content)
        output.append(f"   Created: {path.relative_to(WORKTREE_ROOT)}")
        
    output.append("✅ Written all template files")
    
    # 4. Git Integration
    output.append("\n=== GIT INTEGRATION ===")
    
    # Add files
    add_res = run_git(["add", str(handoff_dir), str(mcp_dir)])
    if add_res.returncode != 0:
        output.append(f"❌ Git add failed:\n{format_result(add_res)}")
        return "\n".join(output)
    
    output.append(f"Staged {skill_name} files...")
    
    # Commit
    commit_msg = f"feat: Scaffold {skill_name}\n\nGenerated by mcp-scaffolder."
    commit_res = run_git(["commit", "-m", commit_msg])
    
    if commit_res.returncode == 0:
        output.append(f"✅ Committed: {format_result(commit_res)}")
    else:
        output.append(f"⚠️ Commit failed (maybe nothing to commit?):\n{format_result(commit_res)}")
        
    output.append(f"\n✅ Skill {skill_name} is ready!")
    
    return "\n".join(output)

# ============== MAIN ==============

async def main():
    if not MCP_AVAILABLE:
        print("❌ MCP SDK not found. Install 'mcp' package (Requires Python >=3.10) or use CLI mode.", file=sys.stderr)
        sys.exit(1)
        
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP Scaffolder")
    parser.add_argument("--skill-name", help="Name of the skill to scaffold")
    parser.add_argument("--description", help="Description of the skill", default="New MCP Skill")
    parser.add_argument("--archon-project-id", help="Archon Project ID", default="PENDING")
    
    # Parse known args (allows extra args from wrapper to be ignored if needed)
    args, unknown = parser.parse_known_args()
    
    if args.skill_name:
        # CLI Mode
        try:
            # Validate name using Pydantic logic if possible, or just raw
            ScaffoldArgs.validate_name(args.skill_name)
            
            result = do_scaffold_skill(args.skill_name, args.description, args.archon_project_id)
            print(result)
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Server Mode
        asyncio.run(main())
